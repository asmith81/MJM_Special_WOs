# utils/config.py
"""
Enhanced configuration management for Work Order Matcher
Handles environment variables and application settings with comprehensive options
"""

import os
from typing import Optional

# Try to load environment variables from .env file
# Handle case where python-dotenv is not installed or .env file doesn't exist
try:
    from dotenv import load_dotenv
    # Try to load .env file, but don't fail if it doesn't exist
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"Loaded environment variables from {env_file}")
    else:
        print(f"No .env file found at {env_file} - using system environment variables only")
        print("To create .env file: copy env.example to .env and fill in your values")
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")
    print("Using system environment variables only")
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")
    print("Using system environment variables only")

def _get_bool(key: str, default: bool = False) -> bool:
    """Helper to parse boolean environment variables"""
    return os.getenv(key, str(default)).lower() in ('true', '1', 'yes', 'on')

def _get_int(key: str, default: int) -> int:
    """Helper to parse integer environment variables"""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default

def _get_float(key: str, default: float) -> float:
    """Helper to parse float environment variables"""
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default

class Config:
    """Enhanced configuration settings loaded from environment variables"""
    
    # ============================================================================
    # REQUIRED CONFIGURATION
    # ============================================================================
    
    # Anthropic API
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    
    # Google OAuth2 (NEW: Support for environment-based credentials)
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    
    # Google Sheets
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
    GOOGLE_SHEET_RANGE = os.getenv('GOOGLE_SHEET_RANGE', 'Estimates/Invoices Status!A:R')
    
    # ============================================================================
    # APPLICATION BEHAVIOR
    # ============================================================================
    
    # Application defaults
    EXPECTED_WORK_ORDER_COUNT_DEFAULT = _get_int('EXPECTED_WORK_ORDER_COUNT_DEFAULT', 5)
    CONFIDENCE_THRESHOLD_DEFAULT = _get_int('CONFIDENCE_THRESHOLD_DEFAULT', 50)
    
    # Text processing limits
    MAX_EMAIL_TEXT_LENGTH = _get_int('MAX_EMAIL_TEXT_LENGTH', 10000)
    MIN_EMAIL_TEXT_LENGTH = _get_int('MIN_EMAIL_TEXT_LENGTH', 20)
    
    # ============================================================================
    # AI MODEL CONFIGURATION
    # ============================================================================
    
    # Claude Model Settings
    CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20240620')
    CLAUDE_MAX_TOKENS = _get_int('CLAUDE_MAX_TOKENS', 4000)
    CLAUDE_TEMPERATURE = _get_float('CLAUDE_TEMPERATURE', 0.1)
    CLAUDE_MAX_PROMPT_TOKENS = _get_int('CLAUDE_MAX_PROMPT_TOKENS', 50000)
    
    # ============================================================================
    # LOGGING CONFIGURATION
    # ============================================================================
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    ENABLE_FILE_LOGGING = _get_bool('ENABLE_FILE_LOGGING', True)
    ENABLE_CONSOLE_LOGGING = _get_bool('ENABLE_CONSOLE_LOGGING', True)
    MAX_LOG_FILE_SIZE = _get_int('MAX_LOG_FILE_SIZE', 10485760)  # 10MB
    LOG_BACKUP_COUNT = _get_int('LOG_BACKUP_COUNT', 5)
    
    # ============================================================================
    # SECURITY SETTINGS
    # ============================================================================
    
    # Input sanitization
    STRICT_INPUT_VALIDATION = _get_bool('STRICT_INPUT_VALIDATION', True)
    
    # API settings
    MAX_API_RETRIES = _get_int('MAX_API_RETRIES', 3)
    API_TIMEOUT_SECONDS = _get_int('API_TIMEOUT_SECONDS', 30)
    
    # ============================================================================
    # DEVELOPMENT/DEBUG SETTINGS
    # ============================================================================
    
    # Debug settings
    DEBUG_MODE = _get_bool('DEBUG_MODE', False)
    SAVE_API_DEBUG_DATA = _get_bool('SAVE_API_DEBUG_DATA', False)
    ENABLE_PERFORMANCE_LOGGING = _get_bool('ENABLE_PERFORMANCE_LOGGING', False)
    MOCK_API_RESPONSES = _get_bool('MOCK_API_RESPONSES', False)
    
    # ============================================================================
    # UI/UX SETTINGS
    # ============================================================================
    
    # Window settings
    DEFAULT_WINDOW_WIDTH = _get_int('DEFAULT_WINDOW_WIDTH', 1400)
    DEFAULT_WINDOW_HEIGHT = _get_int('DEFAULT_WINDOW_HEIGHT', 900)
    MIN_WINDOW_WIDTH = _get_int('MIN_WINDOW_WIDTH', 1200)
    MIN_WINDOW_HEIGHT = _get_int('MIN_WINDOW_HEIGHT', 700)
    
    # User preferences
    AUTO_SAVE_PREFERENCES = _get_bool('AUTO_SAVE_PREFERENCES', True)
    UI_THEME = os.getenv('UI_THEME', 'system')
    
    # ============================================================================
    # DATA PROCESSING SETTINGS
    # ============================================================================
    
    # Work order processing
    MAX_WORK_ORDERS_PER_REQUEST = _get_int('MAX_WORK_ORDERS_PER_REQUEST', 100)
    CACHE_WORK_ORDERS = _get_bool('CACHE_WORK_ORDERS', True)
    WORK_ORDER_CACHE_TIMEOUT = _get_int('WORK_ORDER_CACHE_TIMEOUT', 15)
    AUTO_REFRESH_INTERVAL = _get_int('AUTO_REFRESH_INTERVAL', 0)
    
    # ============================================================================
    # EXPORT SETTINGS
    # ============================================================================
    
    # Export options
    DEFAULT_EXPORT_FORMAT = os.getenv('DEFAULT_EXPORT_FORMAT', 'csv')
    INCLUDE_DEBUG_IN_EXPORTS = _get_bool('INCLUDE_DEBUG_IN_EXPORTS', False)
    EXPORT_FILENAME_PATTERN = os.getenv('EXPORT_FILENAME_PATTERN', 'wo_matching_results_{date}_{time}')
    
    # ============================================================================
    # NETWORK SETTINGS
    # ============================================================================
    
    # Proxy settings
    HTTP_PROXY = os.getenv('HTTP_PROXY', '')
    HTTPS_PROXY = os.getenv('HTTPS_PROXY', '')
    
    # Timeout settings
    CONNECTION_TIMEOUT = _get_int('CONNECTION_TIMEOUT', 10)
    READ_TIMEOUT = _get_int('READ_TIMEOUT', 30)
    
    # ============================================================================
    # BACKUP/RECOVERY SETTINGS
    # ============================================================================
    
    # Backup settings
    BACKUP_AUTH_TOKENS = _get_bool('BACKUP_AUTH_TOKENS', True)
    BACKUP_DIRECTORY = os.getenv('BACKUP_DIRECTORY', 'backups')
    TOKEN_BACKUP_COUNT = _get_int('TOKEN_BACKUP_COUNT', 3)

def validate_config():
    """Validate that required configuration values are present and valid"""
    errors = []
    warnings = []
    
    # Required configuration validation
    if not Config.ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY not found in environment variables")
    elif not Config.ANTHROPIC_API_KEY.startswith('sk-ant-'):
        errors.append("ANTHROPIC_API_KEY appears to be invalid (should start with 'sk-ant-')")
    
    if not Config.GOOGLE_SHEET_ID:
        errors.append("GOOGLE_SHEET_ID not found in environment variables")
    
    if not Config.GOOGLE_SHEET_RANGE:
        errors.append("GOOGLE_SHEET_RANGE not found in environment variables")
    
    # OAuth credentials validation (NEW)
    if Config.GOOGLE_CLIENT_ID and Config.GOOGLE_CLIENT_SECRET:
        # OAuth credentials are provided - validate format
        if not Config.GOOGLE_CLIENT_ID.endswith('.apps.googleusercontent.com'):
            warnings.append("GOOGLE_CLIENT_ID format looks incorrect (should end with .apps.googleusercontent.com)")
        if not Config.GOOGLE_CLIENT_SECRET.startswith('GOCSPX-'):
            warnings.append("GOOGLE_CLIENT_SECRET format looks incorrect (should start with GOCSPX-)")
    else:
        warnings.append("OAuth credentials not provided - will use hardcoded credentials from config/credentials.py")
    
    # Range validation
    if Config.EXPECTED_WORK_ORDER_COUNT_DEFAULT < 1 or Config.EXPECTED_WORK_ORDER_COUNT_DEFAULT > 50:
        warnings.append(f"EXPECTED_WORK_ORDER_COUNT_DEFAULT ({Config.EXPECTED_WORK_ORDER_COUNT_DEFAULT}) seems unusual (1-50 recommended)")
    
    if Config.CONFIDENCE_THRESHOLD_DEFAULT < 0 or Config.CONFIDENCE_THRESHOLD_DEFAULT > 100:
        errors.append(f"CONFIDENCE_THRESHOLD_DEFAULT ({Config.CONFIDENCE_THRESHOLD_DEFAULT}) must be between 0-100")
    
    # Model configuration validation
    valid_models = ['claude-3-5-sonnet-20240620', 'claude-3-haiku-20240307', 'claude-3-sonnet-20240229']
    if Config.CLAUDE_MODEL not in valid_models:
        warnings.append(f"CLAUDE_MODEL ({Config.CLAUDE_MODEL}) not in known models: {valid_models}")
    
    if Config.CLAUDE_MAX_TOKENS < 100 or Config.CLAUDE_MAX_TOKENS > 8192:
        warnings.append(f"CLAUDE_MAX_TOKENS ({Config.CLAUDE_MAX_TOKENS}) outside recommended range (100-8192)")
    
    if Config.CLAUDE_TEMPERATURE < 0.0 or Config.CLAUDE_TEMPERATURE > 1.0:
        errors.append(f"CLAUDE_TEMPERATURE ({Config.CLAUDE_TEMPERATURE}) must be between 0.0-1.0")
    
    # Text limits validation
    if Config.MAX_EMAIL_TEXT_LENGTH < Config.MIN_EMAIL_TEXT_LENGTH:
        errors.append("MAX_EMAIL_TEXT_LENGTH must be greater than MIN_EMAIL_TEXT_LENGTH")
    
    if Config.MIN_EMAIL_TEXT_LENGTH < 10:
        warnings.append(f"MIN_EMAIL_TEXT_LENGTH ({Config.MIN_EMAIL_TEXT_LENGTH}) is very low (10+ recommended)")
    
    # Logging validation
    valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if Config.LOG_LEVEL not in valid_log_levels:
        errors.append(f"LOG_LEVEL ({Config.LOG_LEVEL}) must be one of: {valid_log_levels}")
    
    # File size validation
    if Config.MAX_LOG_FILE_SIZE < 1024 * 1024:  # 1MB
        warnings.append(f"MAX_LOG_FILE_SIZE ({Config.MAX_LOG_FILE_SIZE}) is very small (1MB+ recommended)")
    
    # Return combined results
    all_issues = errors + warnings
    return all_issues if all_issues else []

def get_validation_details():
    """Get detailed validation results with categorization"""
    errors = []
    warnings = []
    
    # Required configuration validation
    if not Config.ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY not found in environment variables")
    elif not Config.ANTHROPIC_API_KEY.startswith('sk-ant-'):
        errors.append("ANTHROPIC_API_KEY appears to be invalid (should start with 'sk-ant-')")
    
    if not Config.GOOGLE_SHEET_ID:
        errors.append("GOOGLE_SHEET_ID not found in environment variables")
    
    if not Config.GOOGLE_SHEET_RANGE:
        errors.append("GOOGLE_SHEET_RANGE not found in environment variables")
    
    # OAuth credentials validation
    if Config.GOOGLE_CLIENT_ID and Config.GOOGLE_CLIENT_SECRET:
        if not Config.GOOGLE_CLIENT_ID.endswith('.apps.googleusercontent.com'):
            warnings.append("GOOGLE_CLIENT_ID format looks incorrect")
        if not Config.GOOGLE_CLIENT_SECRET.startswith('GOCSPX-'):
            warnings.append("GOOGLE_CLIENT_SECRET format looks incorrect")
    else:
        warnings.append("OAuth credentials not provided - using fallback")
    
    # Add other validations...
    
    return {
        'errors': errors,
        'warnings': warnings,
        'has_errors': len(errors) > 0,
        'has_warnings': len(warnings) > 0,
        'is_valid': len(errors) == 0
    }

def get_config_summary():
    """Get a comprehensive summary of current configuration (without sensitive values)"""
    return {
        # Core settings
        'anthropic_configured': bool(Config.ANTHROPIC_API_KEY and Config.ANTHROPIC_API_KEY.startswith('sk-ant-')),
        'google_sheet_id': Config.GOOGLE_SHEET_ID[:10] + '...' if Config.GOOGLE_SHEET_ID else None,
        'google_sheet_range': Config.GOOGLE_SHEET_RANGE,
        'oauth_credentials_provided': bool(Config.GOOGLE_CLIENT_ID and Config.GOOGLE_CLIENT_SECRET),
        
        # Application behavior
        'expected_wo_count': Config.EXPECTED_WORK_ORDER_COUNT_DEFAULT,
        'confidence_threshold': Config.CONFIDENCE_THRESHOLD_DEFAULT,
        'max_text_length': Config.MAX_EMAIL_TEXT_LENGTH,
        'min_text_length': Config.MIN_EMAIL_TEXT_LENGTH,
        
        # AI Model settings
        'claude_model': Config.CLAUDE_MODEL,
        'claude_max_tokens': Config.CLAUDE_MAX_TOKENS,
        'claude_temperature': Config.CLAUDE_TEMPERATURE,
        
        # Logging settings
        'log_level': Config.LOG_LEVEL,
        'file_logging': Config.ENABLE_FILE_LOGGING,
        'console_logging': Config.ENABLE_CONSOLE_LOGGING,
        
        # Security settings
        'strict_validation': Config.STRICT_INPUT_VALIDATION,
        'max_api_retries': Config.MAX_API_RETRIES,
        
        # Debug settings
        'debug_mode': Config.DEBUG_MODE,
        'performance_logging': Config.ENABLE_PERFORMANCE_LOGGING,
        'mock_responses': Config.MOCK_API_RESPONSES,
        
        # UI settings
        'window_size': f"{Config.DEFAULT_WINDOW_WIDTH}x{Config.DEFAULT_WINDOW_HEIGHT}",
        'ui_theme': Config.UI_THEME,
        
        # Data processing
        'work_order_caching': Config.CACHE_WORK_ORDERS,
        'cache_timeout_minutes': Config.WORK_ORDER_CACHE_TIMEOUT,
        
        # Export settings
        'default_export_format': Config.DEFAULT_EXPORT_FORMAT,
        'include_debug_in_exports': Config.INCLUDE_DEBUG_IN_EXPORTS
    }

def initialize_logging():
    """Initialize logging system with current configuration"""
    from utils.logging_config import WorkOrderMatcherLogger
    
    WorkOrderMatcherLogger.setup_logging(
        log_level=Config.LOG_LEVEL,
        enable_file_logging=Config.ENABLE_FILE_LOGGING,
        enable_console_logging=Config.ENABLE_CONSOLE_LOGGING,
        max_file_size=Config.MAX_LOG_FILE_SIZE,
        backup_count=Config.LOG_BACKUP_COUNT
    ) 