# AI Agent Project

## Project Description

The AI Agent project is designed to provide an interactive dashboard interface for managing and visualizing data retrieved from Google Sheets. This application connects to Google Sheets using the Google Sheets API and allows users to set up search queries, extract results, and view them on a web dashboard. With a user-friendly interface, this project is ideal for anyone looking to leverage automated data extraction and visualization from Google Sheets.

## Setup Instructions

### Prerequisites

- Python 3.7 or higher
- [Pip](https://pip.pypa.io/en/stable/installation/) package manager

### Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/AI_AGENT.git
   cd AI_AGENT
   ```

2. **Set Up a Virtual Environment (Optional but Recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate    # On Windows, use `venv\Scripts\activate`
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Database (Optional):**
   This project uses an SQLite database (`search_results.db`) by default to store search results. The database file will be created automatically when you run the application.

### Run the Application

Once the dependencies are installed and the environment variable is configured (see below), start the application with:

```bash
python app.py
```

The app will run on `http://localhost:5000` by default.

## Usage Guide

### Connecting Google Sheets

To enable data extraction from Google Sheets:

1. **Set Up Google Cloud Credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project, enable the Google Sheets API, and download the credentials JSON file.
   - Rename this JSON file to `.google_credentials.json` and place it in the project root.

2. **Add Google Sheets ID**:
   - To extract data from a specific Google Sheet, provide the Google Sheets ID in your search queries on the dashboard. The Sheets ID is found in the sheet’s URL: `https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit`.

### Setting Up Search Queries

Use the dashboard interface to enter and customize search queries for extracting relevant data from the connected Google Sheets. The queries will pull specific columns and rows based on your search terms, which are displayed in a structured format on the dashboard.

### Accessing the Dashboard

Open `http://localhost:5000` in your browser to access the dashboard. This will allow you to view, update, and interact with data in real time.

## API Key and Environment Variable

To secure your application, use an environment variable for your API key. Here’s how to configure it:

1. **Create a `.env` File** in the project root with the following variable:

   ```plaintext
   SERP_API_KEY=<Your SERP API Key>
   ```

   - `SERP_API_KEY`: The API key for accessing the SERP (Search Engine Results Page) API.

2. **Google Credentials File**:
   Place the `.google_credentials.json` file in the project root. This file authorizes the app to connect with Google Sheets.

## Features

This project includes the following optional features to enhance functionality:

- **End Project Trigger**: Allows you to mark a project as “ended” when you no longer need to use it, which removes it from the active dashboard view.
- **Search Query Customization**: Add and customize search queries in real-time without needing to modify the code.
- **Dynamic Database Updates**: Database is automatically updated with each new query result, maintaining an organized view of search outcomes.

---

[Watch the AI-AGENT Intro Video](https://drive.google.com/file/d/1OykPDchDwwox_k-gyn9iYJTp3t-laob_/view?usp=sharing)
