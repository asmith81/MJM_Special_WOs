# test_auth.py
"""
Simple test script for Work Order Matcher authentication
Run this to verify your setup is working correctly
"""

import sys
import os

# Add project directories to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_configuration():
    """Test environment configuration"""
    print("🔧 Testing Configuration...")
    
    try:
        from utils.config import validate_config, get_config_summary
        
        # Validate configuration
        errors = validate_config()
        if errors:
            print("❌ Configuration errors:")
            for error in errors:
                print(f"   - {error}")
            return False
        
        # Show config summary
        summary = get_config_summary()
        print("✅ Configuration valid!")
        print(f"   Anthropic configured: {summary['anthropic_configured']}")
        print(f"   Google Sheet ID: {summary['google_sheet_id']}")
        print(f"   Google Sheet Range: {summary['google_sheet_range']}")
        print(f"   Expected WO count: {summary['expected_wo_count']}")
        print(f"   Confidence threshold: {summary['confidence_threshold']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_google_auth():
    """Test Google authentication"""
    print("\n🔐 Testing Google Authentication...")
    
    try:
        from auth.google_auth import GoogleAuth
        
        # Create auth instance
        auth = GoogleAuth()
        
        # Authenticate (this will open browser if needed)
        auth.authenticate()
        print("✅ Google authentication successful!")
        
        # Test connection
        auth.test_connection()
        
        # Try loading work orders
        print("\n📊 Testing work order data loading...")
        work_orders = auth.load_work_orders()
        
        if work_orders:
            print(f"✅ Successfully loaded {len(work_orders)} work orders")
            
            # Show sample work order
            if len(work_orders) > 0:
                sample = work_orders[0]
                print("\n📝 Sample work order:")
                print(f"   WO #: {sample.get('WO #', 'N/A')}")
                print(f"   Description: {sample.get('Description', 'N/A')[:50]}...")
                print(f"   Total: {sample.get('Total', 'N/A')}")
                print(f"   Location: {sample.get('Location', 'N/A')[:50]}...")
        else:
            print("⚠️ No alpha-numeric work orders found in sheet")
        
        return True
        
    except Exception as e:
        print(f"❌ Google authentication test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Work Order Matcher - Authentication Test")
    print("=" * 50)
    
    # Test configuration
    config_ok = test_configuration()
    
    if not config_ok:
        print("\n❌ Fix configuration issues before proceeding")
        return
    
    # Test Google authentication
    auth_ok = test_google_auth()
    
    print("\n" + "=" * 50)
    if config_ok and auth_ok:
        print("🎉 All tests passed! Your setup is working correctly.")
        print("\nNext steps:")
        print("1. You can now start building the main application")
        print("2. The authentication will work automatically in the main app")
        print("3. Your token is saved for future use (no re-authentication needed)")
    else:
        print("❌ Some tests failed. Please fix the issues above.")

if __name__ == "__main__":
    main() 