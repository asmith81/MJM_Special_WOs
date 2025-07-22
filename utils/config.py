# utils/config.py
"""
Configuration management for Work Order Matcher
Handles environment variables and application settings
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration settings loaded from environment variables"""
    
    # Anthropic API
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    
    # Google Sheets
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
    GOOGLE_SHEET_RANGE = os.getenv('GOOGLE_SHEET_RANGE')
    
    # Application defaults
    EXPECTED_WORK_ORDER_COUNT_DEFAULT = int(os.getenv('EXPECTED_WORK_ORDER_COUNT_DEFAULT', 5))
    CONFIDENCE_THRESHOLD_DEFAULT = int(os.getenv('CONFIDENCE_THRESHOLD_DEFAULT', 50))
    
    # Debug settings
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

def validate_config():
    """Validate that required configuration values are present"""
    errors = []
    
    if not Config.ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY not found in environment variables")
    elif not Config.ANTHROPIC_API_KEY.startswith('sk-ant-'):
        errors.append("ANTHROPIC_API_KEY appears to be invalid (should start with 'sk-ant-')")
    
    if not Config.GOOGLE_SHEET_ID:
        errors.append("GOOGLE_SHEET_ID not found in environment variables")
    
    if not Config.GOOGLE_SHEET_RANGE:
        errors.append("GOOGLE_SHEET_RANGE not found in environment variables")
    
    return errors

def get_config_summary():
    """Get a summary of current configuration (without sensitive values)"""
    return {
        'anthropic_configured': bool(Config.ANTHROPIC_API_KEY and Config.ANTHROPIC_API_KEY.startswith('sk-ant-')),
        'google_sheet_id': Config.GOOGLE_SHEET_ID[:10] + '...' if Config.GOOGLE_SHEET_ID else None,
        'google_sheet_range': Config.GOOGLE_SHEET_RANGE,
        'expected_wo_count': Config.EXPECTED_WORK_ORDER_COUNT_DEFAULT,
        'confidence_threshold': Config.CONFIDENCE_THRESHOLD_DEFAULT,
        'debug_mode': Config.DEBUG_MODE
    } 