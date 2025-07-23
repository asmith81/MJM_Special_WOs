# main.py
"""
Work Order Matcher - Main Entry Point
Runs startup validation then launches the GUI application
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def main():
    """Main entry point for Work Order Matcher"""
    try:
        # Step 1: Initialize configuration and logging
        try:
            from utils.config import initialize_logging
            initialize_logging()
            
            # Get logger after initialization
            from utils.logging_config import get_logger
            logger = get_logger('main')
        except ImportError as e:
            print(f"❌ Failed to import configuration modules: {e}")
            print("Please ensure all dependencies are installed: pip install -r requirements.txt")
            input("Press Enter to exit...")
            return 1
        except Exception as e:
            print(f"❌ Failed to initialize logging: {e}")
            print("Continuing without structured logging...")
            logger = None
        
        def log_or_print(message):
            """Log message if logger available, otherwise print"""
            if logger:
                logger.info(message)
            else:
                print(message)
        
        log_or_print("=" * 60)
        log_or_print("🚀 Starting Work Order Matcher...")
        log_or_print("=" * 60)
        
        # Step 2: Run startup validation
        log_or_print("Running startup validation...")
        from gui.startup_validation import run_all_validations
        
        if not run_all_validations():
            error_msg = "❌ Startup validation failed. Please fix the issues above."
            if logger:
                logger.error(error_msg)
            else:
                print(error_msg)
            input("Press Enter to exit...")
            return 1
        
        log_or_print("🎉 Validation successful! Launching application...")
        
        # Step 3: Initialize thread manager
        from utils.thread_manager import get_thread_manager
        thread_manager = get_thread_manager()
        log_or_print(f"Thread manager initialized with {thread_manager.max_workers} workers")
        
        # Step 4: Launch main application
        from gui.main_window import create_application
        
        app, root = create_application()
        
        log_or_print("✅ Work Order Matcher started successfully!")
        log_or_print("💡 Paste your email billing text and click 'Find Matches' to begin.")
        log_or_print("📖 Use the sample text to test the system.")
        
        # Run the GUI main loop
        root.mainloop()
        
        log_or_print("Work Order Matcher closed.")
        
        # Cleanup
        from utils.thread_manager import shutdown_thread_manager
        shutdown_thread_manager()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n❌ Application cancelled by user.")
        return 1
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\nPlease ensure all dependencies are installed:")
        print("pip install -r requirements.txt")
        input("Press Enter to exit...")
        return 1
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("\nPlease check your configuration and try again.")
        input("Press Enter to exit...")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 