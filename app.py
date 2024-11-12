from flask import Flask, render_template, request, redirect, url_for, flash,make_response
from utils.utils import search_web, save_results_to_db
from transformers import pipeline
from io import StringIO
import csv
import pandas as pd
import gspread
import os
import re
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
import sqlite3

# Load environment variables
load_dotenv()
api_key = os.getenv("SERP_API_KEY")

app = Flask(__name__)

# Google Sheets API setup (replace with your JSON key file path)
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('google_credentails.json', scopes=SCOPES)
client = gspread.authorize(creds)

# Global variables for data
sheet_data = None

qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2")

# Helper function to get a database connection
def get_db_connection():
    conn = sqlite3.connect('search_results.db')
    conn.row_factory = sqlite3.Row  # To fetch rows as dictionaries
    return conn

@app.route('/end_project', methods=['POST'])
def end_project():
    # Clear the results table to end the project 
    clear_results_table()

    # Optionally, display a message that the project has ended
    flash("The project has been successfully ended and all data has been cleared.")

    # Redirect to the home page or a separate "ended project" page
    return redirect(url_for('index'))  # Or you can use a different route for the "ended" status page

# Define the clear_results_table function
def clear_results_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM results')  # Clears all previous data in the results table
    conn.commit()
    conn.close()

# Route for displaying the dashboard
@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT query, url, snippet,extracted_data FROM results')
    results = cursor.fetchall()  # Retrieve all results
    conn.close()

    # Pass the data to the HTML template
    return render_template('dashboard.html', results=results)

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    global sheet_data  # Use the global variable to store the CSV data
    if 'file' not in request.files:
        flash("No file selected")
        return redirect(url_for("index"))

    file = request.files['file']
    if file.filename == '':
        flash("No selected file")
        return redirect(url_for("index"))

    if file:
        data = pd.read_csv(file)
        sheet_data = data  # Store the CSV data globally
        columns = data.columns.tolist()
        preview_data = data.head().to_html(classes='table table-striped')
        return render_template("dashboard.html", columns=columns, preview_data=preview_data)

    return redirect(url_for("index"))

@app.route('/connect_sheets', methods=['POST'])
def connect_sheets():
    global sheet_data  # Use the global variable to store the sheet data
    sheet_url = request.form.get('sheet_url')  # Get sheet URL from form
    if not sheet_url:
        flash("Please provide a valid Google Sheet URL!")
        return redirect(url_for('index'))

    try:
        # Open the Google Sheet using gspread
        sheet = client.open_by_url(sheet_url).sheet1
        data = pd.DataFrame(sheet.get_all_records())  # Fetch data into a DataFrame
        sheet_data = data  # Store the sheet data globally

        # Debug: print the data to check
        print(data.head().to_html(classes='table table-striped'))

        flash("Connected to Google Sheet successfully!")
        return render_template('dashboard.html', columns=data.columns.tolist(), preview_data=data.head().to_html(classes='table table-striped'))

    except Exception as e:
        flash(f"Error connecting to Google Sheet: {e}")
        return redirect(url_for('index'))

@app.route('/process_query', methods=['POST'])
def process_query():
    global sheet_data
    column_name = request.form.get('column_name')
    query_template = request.form.get('query_template')    

    if not column_name or not query_template:
        flash("Please select a column and provide a query template.")
        return redirect(url_for('index'))
    if sheet_data is None:
        flash("No data available. Please upload a CSV or connect to a Google Sheet.")
        return redirect(url_for('index'))
    # Ensure the column exists in the data
    if column_name not in sheet_data.columns:
        flash(f"Column '{column_name}' not found in the data.")
        return redirect(url_for('index'))
    
    # Process new queries
    entities = sheet_data[column_name].tolist()
    queries = [query_template.format(Column=entity) for entity in entities]

    conn = get_db_connection()
    cursor = conn.cursor()

    for query in queries:
        try:
            # Step 1: Get search results from the web
            results = search_web(query, api_key)
            
            if results and 'organic_results' in results and results['organic_results']:
                # Step 2: Combine the first two snippets (if available) from the search results
                snippets = [result.get('snippet', '') for result in results['organic_results']]

                # Combine the first two snippets (if they exist)
                if len(snippets) >= 2:
                 context = snippets[0] + " " + snippets[1]  # Combine first two snippets
                else:
                 context = " ".join(snippets)  # Fallback if less than two snippets are available
                # Step 3: Get the answer from the QA model
                result = qa_pipeline(question=query, context=context)

                # Extract the answer from the model's result
                extracted_data = result.get('answer', 'No relevant answer found.')

                # Clean the extracted data to ensure it's in a single line
                extracted_data = re.sub(r'\n+', ' ', extracted_data).strip()  # Remove any extra newlines and spaces

                if not extracted_data:
                    extracted_data = "No relevant data found."





                # Step 4: Save the original query, prompt response, and extracted data to the database
                for result in results['organic_results']:
                    url = result.get('link', '')
                    snippet = result.get('snippet', '')

                    # Check if this query-url combination already exists in the database
                    cursor.execute('''
                        SELECT * FROM results WHERE query = ?
                    ''', (query,))
                    existing_result = cursor.fetchone()

                    if not existing_result:  # Only insert if no duplicate found
                      cursor.execute('''
                        INSERT INTO results (query, url, snippet, extracted_data)
                        VALUES (?, ?, ?, ?)
                        ''', (query, url, snippet, extracted_data))
            else:
                print(f"No results for query: {query}")
                flash(f'No results found for query: {query}')
        except Exception as e:
            flash(f"Error occurred during query processing: {e}")
            continue

    conn.commit()
    conn.close()
    flash('Queries processed and results stored!')
    return redirect('/')

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    results = search_web(query, api_key)  # Call the search function from utils.py
    if results:
        save_results_to_db(query, results)  # Call the save function from utils.py
        flash('Search completed and results saved!')
    else:
        flash('Failed to fetch search results.')
    return redirect('/')

@app.route('/download_csv')
def download_csv():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT query, url, snippet, extracted_data FROM results')
    results = cursor.fetchall()
    conn.close()

    # Create a StringIO object to write CSV data to
    output = StringIO()
    writer = csv.writer(output)
    
    # Write headers to CSV
    writer.writerow(["Query", "URL", "Snippet", "Extracted Data"])
    
    # Write rows to CSV
    for result in results:
        writer.writerow([result["query"], result["url"], result["snippet"], result["extracted_data"]])

    # Generate response with CSV data
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=results.csv'
    response.mimetype = 'text/csv'
    
    return response

@app.route('/update_google_sheet', methods=['POST'])
def update_google_sheet():
    sheet_url = request.form.get('sheet_url')
    print(f"Received sheet_url: {sheet_url}")  # Debugging line

    try:
        # Check if the URL is valid and provided
        if not sheet_url:
            raise ValueError("No URL provided.")
        
        # Attempt to open the Google Sheet by URL
        sheet = client.open_by_url(sheet_url).sheet1

        # Sample data to update (replace with actual data retrieval)
        data = [["Query", "URL", "Snippet", "Extracted Data"]]  # Header row
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT query, url, snippet, extracted_data FROM results')
        for result in cursor.fetchall():
            data.append([result["query"], result["url"], result["snippet"], result["extracted_data"]])
        conn.close()

        # Get the current sheet data
        existing_data = sheet.get_all_values()
        
        # Find the last column index (to append new data to the right)
        last_column = len(existing_data[0]) if existing_data else 0
        
        # Append new data as new columns (the length of new data determines the number of columns added)
        for i, row in enumerate(data):
            for j, cell in enumerate(row):
                # Update the appropriate cell (starting from the last column index)
                sheet.update_cell(i + 1, last_column + j + 1, cell)  # `i + 1` for 1-based index

        flash("Google Sheet updated successfully!")
        return redirect(url_for('index'))

    except gspread.exceptions.NoValidUrlKeyFound:
        flash("Invalid Google Sheets URL. Please ensure it follows the correct format.")
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"An error occurred: {str(e)}")
        return redirect(url_for('index'))
    
if __name__ == "__main__":
    clear_results_table()
    try:
        app.run(debug=True)
    except Exception as e:
        print(f"Error: {e}")
