
import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from functools import cache
from typing import List, Optional

import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

CREDENTIALS_PATH = os.getenv('GOOG_OAUTH_CONFIG_PATH')
TOKEN_PATH = 'token.json'

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


@dataclass
class Sheet:
    
    spreadsheet_id: str = None
    rows: List[List[str]] = None
    range: str = 'A:K'

    def __post_init__(self):
        if self.rows:
            self._process_rows()


    def _process_rows(self):
        self.header = self.rows[0]
        self.header_dict = {h:i for i, h in enumerate(self.header)}

        header_len = len(self.header)

        for i, row in enumerate(self.rows):
            missing_col_count = header_len - len(row)
            if missing_col_count > 0:

                row += ([''] * missing_col_count)

            self.rows[i] = row


    def fetch(self):
        print(f"Fetching sheet {self.spreadsheet_id}", file=sys.stderr)
        # https://googleapis.github.io/google-api-python-client/docs/dyn/sheets_v4.spreadsheets.values.html
        result = get_sheets_service().spreadsheets().values().get(
        spreadsheetId=self.spreadsheet_id, range=self.range).execute(num_retries=1)
        self.rows = result['values']
        print(f"Successfully fetched sheet", file=sys.stderr)
        self._process_rows()

    def save(self):
        print(f"Saving sheet {self.spreadsheet_id}", file=sys.stderr)
        get_sheets_service().spreadsheets().values().update(        
        spreadsheetId=self.spreadsheet_id, range=self.range, valueInputOption='RAW', body={"values":self.rows}).execute()


    def fail_on_invalid_cell(self, row_num: int):
        if row_num <= 1:
            raise Exception("Sheets are indexed from 1")


    def get_cell(self, row_num: int, col: str):

        self.fail_on_invalid_cell(row_num)

        row_index = self.header_dict.get(col)
        if row_index is None:
            return None

        try:
            row = self.rows[row_num - 1] 
        except IndexError:
            return None

        return row[row_index]

    def set_cell(self, row_num, col: str, val: str):
        self.fail_on_invalid_cell(row_num)

        row_index = self.header_dict.get(col)

        self.rows[row_num - 1][row_index] = val

    def __len__(self):
        return len(self.rows)


    def __str__(self):
        return str(self.rows)



# Deprecated: here for historical purposes
@cache
def _get_creds_with_oauth():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    
    return creds

@cache
def get_creds():
    creds, _ = google.auth.default()
    return creds

def get_sheets_service():
    creds = get_creds()
    # pylint: disable=maybe-no-member
    service = build('sheets', 'v4', credentials=creds)
    return service


@contextmanager
def autosaving_sheet(movie_speadsheet_id):

    sheet = Sheet(movie_speadsheet_id)
    sheet.fetch()
    try:
        yield sheet
    finally:
        sheet.save()

