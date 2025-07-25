# gui/startup_validation.py
"""
Startup validation for Work Order Matcher
Pre-flight checks with user-friendly error dialogs (based on reference project pattern)
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize logging for startup validation with better error handling
logger = None
try:
    from utils.config import initialize_logging
    initialize_logging()
    from utils.logging_config import get_logger
    logger = get_logger('startup_validation')
except ImportError as e:
    # Missing dependencies
    print(f"Warning: Missing dependencies for logging: {e}")
    print("Install with: pip install -r requirements.txt")
except Exception as e:
    # Other logging initialization failures
    print(f"Warning: Could not initialize logging: {e}")
    print("Continuing with console output only")


def validate_configuration():
    """Validate environment configuration with enhanced validation and logging"""
    if logger:
        logger.info("🔧 Starting configuration validation...")
    else:
        print("🔧 Validating configuration...")
    
    try:
        from utils.config import validate_config, get_config_summary, get_validation_details
        
        # Get detailed validation results
        validation_details = get_validation_details()
        
        if validation_details['has_errors']:
            error_msg = "Configuration errors found:\n\n"
            for error in validation_details['errors']:
                error_msg += f"• {error}\n"
            
            error_msg += "\n" + _get_configuration_help()
            
            if logger:
                logger.error(f"Configuration validation failed: {len(validation_details['errors'])} errors")
                for error in validation_details['errors']:
                    logger.error(f"  - {error}")
            
            messagebox.showerror("Configuration Error", error_msg)
            return False
        
        # Log warnings if any
        if validation_details['has_warnings']:
            if logger:
                logger.warning(f"Configuration warnings found: {len(validation_details['warnings'])}")
                for warning in validation_details['warnings']:
                    logger.warning(f"  - {warning}")
        
        # Show config summary for confirmation
        summary = get_config_summary()
        
        if logger:
            logger.info("✅ Configuration validation successful!")
            logger.info(f"   Anthropic configured: {summary['anthropic_configured']}")
            logger.info(f"   OAuth credentials: {'Environment' if summary['oauth_credentials_provided'] else 'Hardcoded'}")
            logger.info(f"   Google Sheet ID: {summary['google_sheet_id']}")
            logger.info(f"   Claude Model: {summary['claude_model']}")
            logger.info(f"   Log Level: {summary['log_level']}")
        else:
            print("✅ Configuration valid!")
            print(f"   Anthropic configured: {summary['anthropic_configured']}")
            print(f"   Google Sheet ID: {summary['google_sheet_id']}")
        
        return True
        
    except ImportError as e:
        error_msg = f"Failed to import configuration modules:\n{str(e)}\n\nPlease ensure all dependencies are installed:\npip install -r requirements.txt"
        if logger:
            logger.error(f"Import error during configuration validation: {str(e)}")
        messagebox.showerror("Import Error", error_msg)
        return False
    except Exception as e:
        error_msg = f"Configuration validation failed:\n{str(e)}"
        if logger:
            logger.error(f"Configuration validation exception: {str(e)}")
        messagebox.showerror("Configuration Error", error_msg)
        return False


def validate_google_sheets_access():
    """Test Google Sheets authentication and access"""
    print("🔐 Testing Google Sheets access...")
    
    try:
        from data.sheets_client import SheetsClient
        
        # Initialize and authenticate
        sheets_client = SheetsClient()
        
        # Test authentication (this will open browser if needed)
        if not sheets_client.authenticate():
            messagebox.showerror(
                "Google Sheets Authentication Failed",
                "Could not authenticate with Google Sheets.\n\n"
                "This will open a browser window for Google login.\n"
                "Please complete the authentication process and try again."
            )
            return False
        
        # Test connection
        if not sheets_client.test_connection():
            messagebox.showerror(
                "Google Sheets Connection Failed",
                "Authentication succeeded but could not connect to your Google Sheet.\n\n"
                "Please verify:\n"
                "• Sheet ID is correct in your .env file\n"
                "• Sheet name 'Estimates/Invoices Status' exists\n"
                "• You have read access to the sheet"
            )
            return False
        
        # Test data loading
        work_orders = sheets_client.load_alpha_numeric_work_orders()
        if not work_orders:
            result = messagebox.askquestion(
                "No Work Orders Found",
                "Connected to Google Sheets but no alpha-numeric work orders found.\n\n"
                "This means no work order IDs start with a letter (special clients).\n\n"
                "Continue anyway for testing purposes?",
                icon='warning'
            )
            return result == 'yes'
        
        print(f"✅ Google Sheets access successful!")
        print(f"   Found {len(work_orders)} alpha-numeric work orders")
        
        return True
        
    except ImportError as e:
        messagebox.showerror(
            "Import Error",
            f"Failed to import Google Sheets modules:\n{str(e)}\n\n"
            "Please ensure all dependencies are installed."
        )
        return False
    except Exception as e:
        messagebox.showerror(
            "Google Sheets Error",
            f"Google Sheets validation failed:\n{str(e)}\n\n"
            "Please check your configuration and network connection."
        )
        return False


def validate_anthropic_access():
    """Test Anthropic API connection"""
    print("🤖 Testing Anthropic API access...")
    
    try:
        from llm.anthropic_client import AnthropicClient
        
        # Initialize client
        client = AnthropicClient()
        
        # Test connection
        result = client.test_connection()
        
        if not result.get('success'):
            error_msg = f"Anthropic API connection failed:\n{result.get('error', 'Unknown error')}\n\n"
            error_msg += "Please verify:\n"
            error_msg += "• ANTHROPIC_API_KEY is set correctly in your .env file\n"
            error_msg += "• API key starts with 'sk-ant-'\n"
            error_msg += "• You have internet connectivity\n"
            error_msg += "• Your API key has sufficient credits"
            
            messagebox.showerror("Anthropic API Error", error_msg)
            return False
        
        print(f"✅ Anthropic API access successful!")
        print(f"   Model: {result.get('model', 'Unknown')}")
        print(f"   Response: {result.get('response', 'OK')}")
        
        return True
        
    except ImportError as e:
        messagebox.showerror(
            "Import Error", 
            f"Failed to import Anthropic modules:\n{str(e)}\n\n"
            "Please ensure all dependencies are installed."
        )
        return False
    except Exception as e:
        messagebox.showerror(
            "Anthropic API Error",
            f"Anthropic API validation failed:\n{str(e)}\n\n"
            "Please check your API key and network connection."
        )
        return False


def run_all_validations():
    """
    Run all startup validations with user-friendly dialogs
    Returns True if all validations pass, False otherwise
    """
    print("🚀 Work Order Matcher - Startup Validation")
    print("=" * 50)
    
    # Hide main window during validation
    root = tk.Tk()
    root.withdraw()
    
    try:
        # Step 1: Configuration validation
        if not validate_configuration():
            return False
        
        # Step 2: Anthropic API validation  
        if not validate_anthropic_access():
            return False
        
        # Step 3: Google Sheets validation
        if not validate_google_sheets_access():
            return False
        
        # All validations passed
        print("\n" + "=" * 50)
        print("🎉 All startup validations passed!")
        print("The Work Order Matcher is ready to use.")
        
        return True
        
    except KeyboardInterrupt:
        print("\n❌ Startup validation cancelled by user")
        return False
    except Exception as e:
        messagebox.showerror(
            "Startup Validation Error",
            f"Unexpected error during startup validation:\n{str(e)}"
        )
        return False
    finally:
        root.destroy()


def _get_configuration_help():
    """Get helpful configuration instructions"""
    return """Configuration Setup:

1. Create a .env file in the project root with:
   ANTHROPIC_API_KEY=sk-ant-your_api_key_here
   GOOGLE_SHEET_ID=your_google_sheet_id
   GOOGLE_SHEET_RANGE=Estimates/Invoices Status!A:R

2. Ensure your Google Sheet is shared with the OAuth application

3. Verify the sheet name 'Estimates/Invoices Status' exists

4. Check that work orders with letter prefixes exist (special clients)"""


if __name__ == "__main__":
    success = run_all_validations()
    if success:
        print("✅ Ready to launch main application")
    else:
        print("❌ Please fix configuration issues before launching")
        sys.exit(1) 