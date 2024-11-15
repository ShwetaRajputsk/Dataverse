# DataVerse

DataVerse is a web-based data extraction tool that enables users to harness the power of AI and automated web searches for information retrieval from CSV files or Google Sheets. It allows users to perform custom queries to extract specific information, such as email addresses, phone numbers, or addresses for entities like companies or individuals. 

## Features

- **CSV and Google Sheets Integration**: Easily upload a CSV file or connect to a Google Sheet for data extraction.
- **Dynamic Querying**: Define custom queries with placeholders to retrieve specific data, like email addresses or phone numbers.
- **Automated Search and Extraction**: Automatically fetch relevant information for each entity using integrated APIs.
- **Result Visualization**: Display extracted results in a table format and download them as a CSV.
- **Responsive UI**: A clean, user-friendly interface for seamless interaction.

## Table of Contents

- [Project Description](#project-description)
- [Setup Instructions](#setup-instructions)
- [Usage Guide](#usage-guide)
- [API Keys and Environment Variables](#api-keys-and-environment-variables)
- [Optional Features](#optional-features)
- [Technologies](#technologies)
- [Project Layout](#project-layout)

## Project Description

DataVerse provides a streamlined way to extract relevant information from data files, especially focusing on entities like companies and individuals. Using CSV or Google Sheets as a data source, DataVerse supports customized queries, allowing users to retrieve information such as email addresses, phone numbers, and physical addresses. This project is designed to simplify data retrieval with minimal user input, using AI to automate the process.

## Setup Instructions

### Prerequisites

- **Python 3.8+**
- **Flask**
- **Pandas**
- **Google API Client**
- **SerpAPI Key**
- **Groq API Key**

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/DataVerse.git
   cd DataVerse
2. Install required Python packages:
      ```bash
   pip install -r requirements.txt
3. Add your Google Sheets API credentials:
     - Enable the Sheets API in your Google Cloud Console.
     - Download credentials.json and place it in the project directory.
4. Configure .env file:
  - Create a .env file in the root directory and add the following:
     ```bash
      SERP_API_KEY=your_serpapi_key
      GROQ_API_KEY=your_groqapi_key
  - Use the dotenv library in your app.py to load these keys.
5. Run the application:
     ```bash
   python app.py
6. Go to http://127.0.0.1:5000 in your web browser.     
          
## Usage Guide
1. Upload Data: Start by uploading a CSV file or linking to a Google Sheet.
2. Define Your Query: Enter a query like "Find the email address of {company}" using {} for placeholders to represent the variable data points.
3. Choose Columns and Run Query: Select the column you want to search, then click "Run Query" to extract information.
4. Download Results: When ready, download the extracted results as a CSV file.

## API Keys and Environment Variables
Ensure the following environment variables are set in your .env file:
1. Google Sheets API: Store your credentials.json file in the project directory.
2. SerpAPI and Groq API Keys: Insert your API keys as SERP_API_KEY and GROQ_API_KEY in the .env file.
These keys enable the search and AI features of the app.

## Optional Features
1. Advanced Query Templates: Extract multiple fields in a single prompt, such as “Get the email and address for {company}.”
2. Google Sheets Output Integration: Write back the extracted data directly to the Google Sheet.
3. Column Selection: Choose specific columns from your data source for more targeted searches.
4. Downloadable Results: Easily export your results to a CSV for further analysis.
5. Customizable Query Templates: Use placeholders like {company} for dynamic data querying.

## Technologies
1. Flask for the web interface
2. Pandas for handling data
3. Google Sheets API for Google Sheets integration
4. SerpAPI for search capabilities
5. Groq API for AI-based information extraction

## Project Layout   
   ```bash
DataVerse/
├── static/
│   └── style.css      # CSS for the UI
├── templates/
│   └── index.html     # Main HTML page
├── app.py             # Main application logic
└── README.md          # This file
