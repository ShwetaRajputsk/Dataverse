import os
import io
import time
import re
import pandas as pd
import requests
from flask import Flask, render_template, request, jsonify, send_file, session, flash, redirect, url_for
from google.oauth2 import service_account
from googleapiclient.discovery import build
from serpapi import GoogleSearch
import gspread
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = os.urandom(24)

# API Credentials
GOOGLE_SHEET_CREDENTIALS = os.getenv("GOOGLE_SHEET_CREDENTIALS")
load_dotenv()

# Check if the variable is loaded correctly
GOOGLE_SHEET_CREDENTIALS = os.getenv("GOOGLE_SHEET_CREDENTIALS")
if not GOOGLE_SHEET_CREDENTIALS:
    raise ValueError("Google Sheets credentials file path is not set in the environment variables.")

load_dotenv()
SERP_API_KEY = os.getenv("SERP_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# initializes an empty list named query_results
query_results = []

@app.route('/')
def index():
    # Home Route:Displays the main page
    columns = session.get('columns', [])
    preview_data = session.get('preview_data', "")
    results = session.get('results', [])
    return render_template('index.html', columns=columns, data=preview_data, results=results)

def read_csv_with_delimiter(file):
    try:
        return pd.read_csv(file, sep=",")
    except:
        return pd.read_csv(file, sep=";")

@app.route('/upload', methods=['POST'])
def upload_csv():
    session.clear()
    file = request.files['file']
    if file and file.filename.endswith('.csv'):
        try:
            uploaded_data = read_csv_with_delimiter(file)
            session['uploaded_data'] = uploaded_data.to_dict()
            columns = uploaded_data.columns.tolist()
            preview_data = uploaded_data.to_html(classes='table table-bordered', index=False)
            session['columns'] = columns
            session['preview_data'] = preview_data
            return render_template('index.html', columns=columns, data=preview_data)
        except Exception as e:
            return f"Error reading CSV file: {str(e)}", 500
    return 'Invalid file format. Please upload a CSV file.', 400

def fetch_google_sheet_data(sheet_id):
    creds = service_account.Credentials.from_service_account_file(
        GOOGLE_SHEET_CREDENTIALS, scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=sheet_id, range="Sheet1").execute()
    values = result.get('values', [])
    if not values:
        return pd.DataFrame()
    header = values[0]
    data_rows = values[1:]
    df = pd.DataFrame.from_records(data_rows, columns=header)
    return df

@app.route('/connect-google-sheets', methods=['POST'])
def connect_google_sheets():
    sheet_id = request.form['sheet_id']
    try:
        uploaded_data = fetch_google_sheet_data(sheet_id)
        session['uploaded_data'] = uploaded_data.to_dict()
        columns = uploaded_data.columns.tolist()
        preview_data = uploaded_data.head().to_html(classes='table table-bordered')
        session['columns'] = columns
        session['preview_data'] = preview_data
        return render_template('index.html', columns=columns, data=preview_data)
    except Exception as e:
        return f"Error fetching Google Sheets data: {str(e)}", 500

def generate_query(prompt_template, entity, placeholder):
    return prompt_template.replace(f"{{{placeholder}}}", entity)

def perform_search(query, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            search = GoogleSearch({"q": query, "api_key": SERP_API_KEY})
            response = search.get_dict()
            if isinstance(response, dict) and "organic_results" in response:
                return response["organic_results"]
            elif isinstance(response, dict) and "error" in response:
                print(f"Error in SerpAPI call: {response['error']}")
                return []  # Return an empty list if there's an error
        except Exception as e:
            print(f"Exception in SerpAPI call: {str(e)}")
        retries += 1
        time.sleep(2 ** retries)
    return []  # Return an empty list after max retries if no results

def extract_contact_info(snippet):
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    phone_pattern = r"\+?[1-9][0-9]{1,2}\s?\(?[0-9]{3}\)?[ -]?[0-9]{3}[ -]?[0-9]{4}"
    address_keywords = ["address", "located at", "office at", "headquarters"]

    emails = re.findall(email_pattern, snippet)
    phones = re.findall(phone_pattern, snippet)
    address = None
    for keyword in address_keywords:
        if keyword in snippet.lower():
            address = snippet
            break

    return {
        "emails": emails if emails else ["No email found"],
        "phones": phones if phones else ["No phone number found"],
        "address": address if address else "No address found"
    }

@app.route('/query', methods=['POST'])
def run_query():
    global query_results
    if 'uploaded_data' not in session:
        return jsonify({"error": "Please upload a CSV or connect to Google Sheets first."}), 400

    uploaded_data = pd.DataFrame(session['uploaded_data'])
    prompt_template = request.form['prompt']
    selected_column = request.form['selected_column']
    placeholder = request.form['placeholder']
    write_to_google_sheet = request.form.get('write_to_google_sheet') == 'yes'
    sheet_id = request.form.get('sheet_id')

    if selected_column not in uploaded_data.columns:
        return jsonify({"error": "Selected column is not valid."}), 400

    query_results = []
    entities = uploaded_data[selected_column].dropna().unique()

    needs_email = "email" in prompt_template.lower()
    needs_phone = "phone" in prompt_template.lower()
    needs_address = "address" in prompt_template.lower()

    for entity in entities:
        search_query = generate_query(prompt_template, entity, placeholder)
        search_results = perform_search(search_query)

        extracted_info = {"emails": [], "phones": [], "address": None}
        if search_results:
            for result in search_results:
                # Check that result is a dictionary before accessing snippet
                if isinstance(result, dict):
                    snippet = result.get("snippet", "")
                    contact_info = extract_contact_info(snippet)

                    if needs_email:
                        extracted_info["emails"].extend(contact_info["emails"])
                    if needs_phone:
                        extracted_info["phones"].extend(contact_info["phones"])
                    if needs_address and not extracted_info["address"]:
                        extracted_info["address"] = contact_info["address"]
                else:
                    print(f"Unexpected result format: {result}")

            extracted_info["emails"] = list(set(extracted_info["emails"])) or ["No email found"]
            extracted_info["phones"] = list(set(extracted_info["phones"])) or ["No phone number found"]
            if not extracted_info["address"]:
                extracted_info["address"] = "No address found"
        else:
            extracted_info = {
                "emails": ["No relevant data found"],
                "phones": ["No relevant data found"],
                "address": "No relevant data found"
            }

        query_results.append({
            "entity": entity,
            "emails": extracted_info["emails"],
            "phones": extracted_info["phones"],
            "address": extracted_info["address"]
        })

    # Store results in the session 
    session['results'] = query_results

    if write_to_google_sheet and sheet_id:
        try:
            write_data_to_google_sheet(sheet_id, query_results)
        except Exception as e:
            return f"Error writing data to Google Sheets: {str(e)}", 500

    return render_template('index.html', columns=session.get('columns'), data=session.get('preview_data'), results=query_results)

@app.route('/download_csv', methods=['POST'])
def download_csv():
    global query_results
    if not query_results:
        return "No query results to download.", 400

    output = io.BytesIO()
    df = pd.DataFrame(query_results)
    df.to_csv(output, index=False)
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name="query_results.csv")

def write_data_to_google_sheet(sheet_id, data):
    try:
        creds = service_account.Credentials.from_service_account_file(
            GOOGLE_SHEET_CREDENTIALS, scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()

        sheet_metadata = sheet.get(spreadsheetId=sheet_id).execute()
        sheet_names = [s['properties']['title'] for s in sheet_metadata['sheets']]
        
        sheet_name = sheet_names[0]
        values = [["Entity", "Emails", "Phones", "Address"]]
        for result in data:
            values.append([
                result.get("entity", ""),
                ", ".join(result.get("emails", [])),
                ", ".join(result.get("phones", [])),
                result.get("address", "")
            ])
        
        range_name = f"{sheet_name}!A1"

        body = {'values': values}
        response = sheet.values().update(
            spreadsheetId=sheet_id, range=range_name,
            valueInputOption="RAW", body=body
        ).execute()

        return response
    except Exception as e:
        return f"Error writing data to Google Sheets: {str(e)}", 500
@app.route('/submit_to_google_sheet', methods=['POST'])
def submit_to_google_sheet():
    try:
        # Check if query results are available
        if not query_results:
            flash("No query results available to submit.", "error")
            return redirect(url_for('index'))

        # Google Sheets authentication
        creds = service_account.Credentials.from_service_account_file(
            GOOGLE_SHEET_CREDENTIALS,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(creds)

        # Open the Google Sheet by its key
        sheet = client.open_by_key('1OQP3UVXI6xMPqqwvkMu7shTCVPSWlImX3SFc1G4QRFE').sheet1

        # Determine the next available row
        next_row = len(sheet.get_all_values()) + 1

        # Loop through each query result and write data to specific columns
        for i, result in enumerate(query_results):
            row = next_row + i  # This sets the row to update for each result
            sheet.update_cell(row, 1, result['entity'])               
            sheet.update_cell(row, 2, ", ".join(result['emails']))    
            sheet.update_cell(row, 3, ", ".join(result['phones']))   
            sheet.update_cell(row, 4, result['address'])             

        flash("Data submitted to Google Sheet successfully!", "success")
        return redirect(url_for('index'))
    
    except Exception as e:
        flash(f"Error submitting data to Google Sheet: {e}", "error")
        print(f"Error submitting data to Google Sheet: {e}")
        return redirect(url_for('index'))
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))  # Default to 5000 if PORT is not set
    app.run(host="0.0.0.0", port=port)


