# auth/google_auth.py
"""
Google OAuth2 authentication for Work Order Matcher
Based on proven pattern from reference project
"""

import os
import time
import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from utils.config import Config
from utils.logging_config import get_logger
from config.credentials import (
    OAUTH_CLIENT_CREDENTIALS, SCOPES, TOKEN_FILE,
    SHEET_ID, SHEET_NAME, WORK_ORDER_FILTER_PATTERN
)

logger = get_logger('google_auth')


class GoogleAuth:
    """Enhanced Google authentication and API client manager with environment variable support"""
    
    def __init__(self):
        self.credentials = None
        self.sheets_client = None
        self.drive_client = None
        
        # Determine OAuth credentials source
        self.oauth_credentials = self._get_oauth_credentials()
        logger.debug(f"OAuth credentials source: {'Environment variables' if self._using_env_credentials() else 'Hardcoded config'}")
    
    def _using_env_credentials(self) -> bool:
        """Check if we're using environment-based OAuth credentials"""
        return bool(Config.GOOGLE_CLIENT_ID and Config.GOOGLE_CLIENT_SECRET)
    
    def _get_oauth_credentials(self) -> dict:
        """Get OAuth credentials from environment or fallback to hardcoded"""
        if self._using_env_credentials():
            logger.info("Using OAuth credentials from environment variables")
            return {
                "client_id": Config.GOOGLE_CLIENT_ID,
                "client_secret": Config.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["http://localhost"]
            }
        else:
            logger.info("Using hardcoded OAuth credentials from config/credentials.py")
            return OAUTH_CLIENT_CREDENTIALS
    
    def authenticate(self):
        """Authenticate with Google APIs using OAuth flow with enhanced logging"""
        try:
            logger.info("Starting Google authentication process")
            creds = None
            
            # Check if token file exists (stored credentials)
            if os.path.exists(TOKEN_FILE):
                try:
                    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                    logger.debug("Loaded existing credentials from token file")
                except Exception as e:
                    logger.warning(f"Could not load existing token: {e}")
                    # Continue without existing credentials
            
            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("Attempting to refresh expired Google credentials...")
                    try:
                        creds.refresh(Request())
                        logger.info("✅ Google credentials refreshed successfully!")
                    except Exception as e:
                        logger.error(f"Failed to refresh credentials: {e}")
                        creds = None
                
                if not creds or not creds.valid:
                    logger.info("Starting Google OAuth2 login flow...")
                    
                    # Create OAuth flow from selected client configuration
                    client_config = {
                        "installed": self.oauth_credentials
                    }
                    flow = InstalledAppFlow.from_client_config(
                        client_config, SCOPES
                    )
                    
                    # Run local server for OAuth flow
                    logger.info("Opening browser for Google authentication...")
                    creds = flow.run_local_server(port=0)
                    logger.info("✅ Google authentication successful!")
                
                # Save the credentials for the next run
                try:
                    # Create auth directory if it doesn't exist
                    token_dir = os.path.dirname(TOKEN_FILE)
                    if token_dir:  # Only create if directory path is not empty
                        os.makedirs(token_dir, exist_ok=True)
                    
                    with open(TOKEN_FILE, 'w') as token:
                        token.write(creds.to_json())
                    logger.info(f"✅ Credentials saved to {TOKEN_FILE}")
                except OSError as e:
                    logger.warning(f"Could not create directory for token file: {e}")
                    logger.warning("Authentication will work but tokens won't persist between sessions")
                except Exception as e:
                    logger.warning(f"Could not save credentials: {e}")
                    logger.warning("Authentication will work but tokens won't persist between sessions")
            
            self.credentials = creds
            
            # Initialize API clients
            logger.debug("Initializing Google API clients...")
            self.sheets_client = gspread.authorize(self.credentials)
            self.drive_client = build('drive', 'v3', credentials=self.credentials)
            
            logger.info("Google authentication completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Google authentication failed: {str(e)}")
            raise Exception(f"Google authentication failed: {str(e)}")
    
    def test_connection(self):
        """Test the Google Sheets connection with configuration-based settings"""
        try:
            if not self.sheets_client:
                raise Exception("Not authenticated - call authenticate() first")
            
            logger.info("Testing Google Sheets connection...")
            
            # Use configuration-based sheet settings
            sheet_id = Config.GOOGLE_SHEET_ID or SHEET_ID
            
            # Extract sheet name from range, with fallback
            if Config.GOOGLE_SHEET_RANGE and isinstance(Config.GOOGLE_SHEET_RANGE, str) and '!' in Config.GOOGLE_SHEET_RANGE:
                sheet_name = Config.GOOGLE_SHEET_RANGE.split('!')[0]
            else:
                sheet_name = SHEET_NAME
            
            # Try to open the configured sheet
            sheet = self.sheets_client.open_by_key(sheet_id)
            worksheet = sheet.worksheet(sheet_name)
            
            # Get basic info about the sheet
            row_count = worksheet.row_count
            col_count = worksheet.col_count
            
            logger.info(f"✅ Successfully connected to Google Sheet:")
            logger.info(f"   Sheet ID: {sheet_id}")
            logger.info(f"   Sheet Name: '{sheet_name}'")
            logger.info(f"   Dimensions: {row_count} rows × {col_count} columns")
            
            return True
            
        except Exception as e:
            logger.error(f"Google Sheets connection test failed: {str(e)}")
            raise Exception(f"Google Sheets connection test failed: {str(e)}")
    
    def load_work_orders(self):
        """Load and filter work order data from Google Sheets using configuration"""
        try:
            if not self.sheets_client:
                raise Exception("Not authenticated - call authenticate() first")
            
            logger.info("Loading work orders from Google Sheets...")
            
            # Use configuration-based sheet settings
            sheet_id = Config.GOOGLE_SHEET_ID or SHEET_ID
            
            # Extract sheet name from range, with fallback
            if Config.GOOGLE_SHEET_RANGE and isinstance(Config.GOOGLE_SHEET_RANGE, str) and '!' in Config.GOOGLE_SHEET_RANGE:
                sheet_name = Config.GOOGLE_SHEET_RANGE.split('!')[0]
            else:
                sheet_name = SHEET_NAME
            
            # Open the sheet
            sheet = self.sheets_client.open_by_key(sheet_id)
            worksheet = sheet.worksheet(sheet_name)
            
            # Get all records with performance tracking
            start_time = time.time()
            all_data = worksheet.get_all_records()
            load_duration = time.time() - start_time
            
            logger.info(f"📊 Loaded {len(all_data)} total rows from Google Sheets in {load_duration:.2f}s")
            
            # Filter to alpha-numeric work orders (special clients)
            import re
            alpha_numeric_data = []
            
            filter_pattern = WORK_ORDER_FILTER_PATTERN
            filter_start_time = time.time()
            
            for row in all_data:
                wo_number = str(row.get('WO #', '')).strip()
                if wo_number and re.match(filter_pattern, wo_number):
                    alpha_numeric_data.append(row)
            
            filter_duration = time.time() - filter_start_time
            logger.info(f"🔍 Filtered to {len(alpha_numeric_data)} alpha-numeric work orders (special clients) in {filter_duration:.2f}s")
            
            # Performance logging if enabled
            if Config.ENABLE_PERFORMANCE_LOGGING:
                logger.info(f"Work orders performance - Load: {load_duration:.2f}s, Filter: {filter_duration:.2f}s, Total: {load_duration + filter_duration:.2f}s")
            
            return alpha_numeric_data
            
        except Exception as e:
            logger.error(f"Failed to load work orders: {str(e)}")
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