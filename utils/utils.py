import requests
import time
import sqlite3

def search_web(query, api_key):
    """Function to interact with the SerpAPI to get search results."""
    endpoint = "https://serpapi.com/search"
    params = {
        "q": query,
        "api_key": api_key,
        "engine": "google",
        "num": 10,
    }
    retries = 3
    for attempt in range(retries):
        try:
            print(f"Sending query: {query}")  # Log the query being sent
            response = requests.get(endpoint, params=params)
            if response.status_code == 200:
                data = response.json()
                print(f"Full API response for '{query}': {data}")  # Log the full response
                
                # Ensure the expected 'organic_results' field is present
                if 'organic_results' in data and data['organic_results']:
                    return data
                else:
                    print(f"No organic results found for '{query}'")
            else:
                print(f"Error: {response.status_code}. Retrying...")
                time.sleep(5)
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}. Retrying...")
            time.sleep(5)
    return None

def save_results_to_db(query, results):
    """Function to save search results to the database."""
    # Ensure the table exists
    conn = sqlite3.connect('search_results.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            url TEXT NOT NULL,
            snippet TEXT NOT NULL
            extracted_data TEXT
        )
    ''')
    
    # Insert the results into the database
    for result in results.get('organic_results', []):
        url = result.get('link', '')
        snippet = result.get('snippet', '')
        print(f"Inserting: {query}, {url}, {snippet}")  # Log the insertion
        c.execute('''INSERT INTO results (query, url, snippet,extracted_data) VALUES (?, ?, ?,?)''', (query, url, snippet,''))
    
    conn.commit()
    conn.close()
