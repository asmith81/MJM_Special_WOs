# config/credentials.py
"""
OAuth credentials and configuration for Work Order Matcher
Based on proven pattern from reference project
"""

import os

# Get the directory where this script is located (config directory)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory (project root)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# OAuth2 Client Credentials (same as reference project - these work!)
OAUTH_CLIENT_CREDENTIALS = {
    "client_id": "1042497359356-d1sgm12rerfdlc3v1vvsutnnrs2d0him.apps.googleusercontent.com",
    "client_secret": "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",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "redirect_uris": ["http://localhost"]
}

# Google Sheets configuration
SHEET_ID = "1gdjS8gaGFaQs6J09yv7SeiYKy6ZdOLnXoZfIrQQpGoY"
SHEET_NAME = "Estimates/Invoices Status"

# OAuth scopes required (read-only access)
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'  # For future image access if needed
]

# Token storage file (will be created automatically during OAuth flow)
TOKEN_FILE = os.path.join(PROJECT_ROOT, "auth", "token.json")

# Work Order filtering criteria (alpha-numeric WO# pattern from PRD)
WORK_ORDER_FILTER_PATTERN = r'^[A-Za-z]'  # Starts with letter (special clients)

# Default application settings
DEFAULT_EXPECTED_WO_COUNT = 5
DEFAULT_CONFIDENCE_THRESHOLD = 50

# Anthropic API configuration
# NOTE: Anthropic API key should be set in environment variables, not hardcoded here!
# Create .env file with: ANTHROPIC_API_KEY=sk-ant-your_key_here 