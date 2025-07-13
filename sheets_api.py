# sheets_api.py

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os.path

# Full access to Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Your sheet
SPREADSHEET_ID = '1UC83jw-ZM2YB2rVv587uAwn5qdUAEP3-m6dCcaeecdE'
SHEET_NAME = 'admin_review'  # Rename this if your tab name is different

def get_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('sheets', 'v4', credentials=creds)

def append_to_sheet(values: list):
    service = get_service()
    sheet = service.spreadsheets()
    request = sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1",
        valueInputOption="USER_ENTERED",
        body={"values": [values]}
    )
    return request.execute()
