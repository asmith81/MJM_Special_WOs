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
    print("🚀 Starting Work Order Matcher...")
    print("=" * 50)
    
    try:
        # Step 1: Run startup validation
        print("Running startup validation...")
        from gui.startup_validation import run_all_validations
        
        if not run_all_validations():
            print("❌ Startup validation failed. Please fix the issues above.")
            input("Press Enter to exit...")
            return 1
        
        print("\n🎉 Validation successful! Launching application...")
        
        # Step 2: Launch main application
        from gui.main_window import create_application
        
        app, root = create_application()
        
        print("✅ Work Order Matcher started successfully!")
        print("💡 Paste your email billing text and click 'Find Matches' to begin.")
        print("📖 Use the sample text to test the system.")
        print("")
        
        # Run the GUI main loop
        root.mainloop()
        
        print("Work Order Matcher closed.")
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