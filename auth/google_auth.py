# auth/google_auth.py
"""
Google OAuth2 authentication for Work Order Matcher
Based on proven pattern from reference project
"""

import os
import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config.credentials import (
    OAUTH_CLIENT_CREDENTIALS, SCOPES, TOKEN_FILE,
    SHEET_ID, SHEET_NAME, WORK_ORDER_FILTER_PATTERN
)


class GoogleAuth:
    """Google authentication and API client manager"""
    
    def __init__(self):
        self.credentials = None
        self.sheets_client = None
        self.drive_client = None
    
    def authenticate(self):
        """Authenticate with Google APIs using OAuth flow"""
        try:
            creds = None
            
            # Check if token file exists (stored credentials)
            if os.path.exists(TOKEN_FILE):
                try:
                    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                except Exception as e:
                    print(f"Warning: Could not load existing token: {e}")
                    # Continue without existing credentials
            
            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    print("Refreshing expired Google credentials...")
                    try:
                        creds.refresh(Request())
                        print("✅ Google credentials refreshed successfully!")
                    except Exception as e:
                        print(f"Failed to refresh credentials: {e}")
                        creds = None
                
                if not creds or not creds.valid:
                    print("Starting Google OAuth2 login flow...")
                    
                    # Create OAuth flow from client configuration
                    client_config = {
                        "installed": OAUTH_CLIENT_CREDENTIALS
                    }
                    flow = InstalledAppFlow.from_client_config(
                        client_config, SCOPES
                    )
                    
                    # Run local server for OAuth flow
                    creds = flow.run_local_server(port=0)
                    print("✅ Google authentication successful!")
                
                # Save the credentials for the next run
                try:
                    # Create auth directory if it doesn't exist
                    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
                    
                    with open(TOKEN_FILE, 'w') as token:
                        token.write(creds.to_json())
                    print(f"✅ Credentials saved to {TOKEN_FILE}")
                except Exception as e:
                    print(f"Warning: Could not save credentials: {e}")
            
            self.credentials = creds
            
            # Initialize API clients
            self.sheets_client = gspread.authorize(self.credentials)
            self.drive_client = build('drive', 'v3', credentials=self.credentials)
            
            return True
            
        except Exception as e:
            raise Exception(f"Google authentication failed: {str(e)}")
    
    def test_connection(self):
        """Test the Google Sheets connection"""
        try:
            if not self.sheets_client:
                raise Exception("Not authenticated - call authenticate() first")
            
            # Try to open the configured sheet
            sheet = self.sheets_client.open_by_key(SHEET_ID)
            worksheet = sheet.worksheet(SHEET_NAME)
            
            # Get basic info about the sheet
            row_count = worksheet.row_count
            col_count = worksheet.col_count
            
            print(f"✅ Successfully connected to Google Sheet:")
            print(f"   Sheet ID: {SHEET_ID}")
            print(f"   Sheet Name: '{SHEET_NAME}'")
            print(f"   Dimensions: {row_count} rows × {col_count} columns")
            
            return True
            
        except Exception as e:
            raise Exception(f"Google Sheets connection test failed: {str(e)}")
    
    def load_work_orders(self):
        """Load and filter work order data from Google Sheets"""
        try:
            if not self.sheets_client:
                raise Exception("Not authenticated - call authenticate() first")
            
            # Open the sheet
            sheet = self.sheets_client.open_by_key(SHEET_ID)
            worksheet = sheet.worksheet(SHEET_NAME)
            
            # Get all records
            all_data = worksheet.get_all_records()
            print(f"📊 Loaded {len(all_data)} total rows from Google Sheets")
            
            # Filter to alpha-numeric work orders (special clients)
            import re
            alpha_numeric_data = []
            
            for row in all_data:
                wo_number = str(row.get('WO #', '')).strip()
                if wo_number and re.match(WORK_ORDER_FILTER_PATTERN, wo_number):
                    alpha_numeric_data.append(row)
            
            print(f"🔍 Filtered to {len(alpha_numeric_data)} alpha-numeric work orders (special clients)")
            return alpha_numeric_data
            
        except Exception as e:
            raise Exception(f"Failed to load work orders: {str(e)}")
    
    def get_credentials_status(self):
        """Get current authentication status"""
        if not self.credentials:
            return "Not authenticated"
        elif not self.credentials.valid:
            return "Expired credentials"
        else:
            return "Authenticated and valid"


# Convenience function for simple authentication
def authenticate_google():
    """Simple function to authenticate and return GoogleAuth instance"""
    auth = GoogleAuth()
    auth.authenticate()
    return auth 