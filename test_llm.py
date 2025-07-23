# test_llm.py
"""
Test script for LLM integration with blended confidence scoring
Tests the complete flow: email text → prompt building → Claude API → response parsing
"""

import sys
import os

# Add project directories to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_anthropic_connection():
    """Test basic Anthropic API connection"""
    print("🔗 Testing Anthropic Connection...")
    
    try:
        from llm.anthropic_client import AnthropicClient
        
        client = AnthropicClient()
        
        # Test connection
        result = client.test_connection()
        
        if result.get("success"):
            print(f"✅ {result['status']}")
            print(f"   Model: {result['model']}")
            print(f"   Response: {result['response']}")
            return True
        else:
            print(f"❌ Connection failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        return False

def test_prompt_building():
    """Test prompt construction with sample data"""
    print("\n📝 Testing Prompt Building...")
    
    try:
        from llm.prompt_builder import PromptBuilder
        
        # Sample email text (based on PRD examples)
        email_text = """Our invoice for the work is as follows:
Unit 5966: The concrete sidewalk and drain area was cracked and needed repair
Materials and Labor: $ 3,987.00
Unit 5804: Drywall was repaired, plastered and painted due to a roof leak 
Materials and Labor: $ 350.00
Grand Total: $ 4,337.00"""
        
        # Sample work orders (simplified format)
        sample_work_orders = [
            {
                "WO #": "A5966",
                "Total": "$3,987.00",
                "Location": "Unit 5966 - 5966 Southern Ave SE",
                "Description": "Concrete sidewalk repair and drainage issues"
            },
            {
                "WO #": "B5804", 
                "Total": "$350.00",
                "Location": "Unit 5804 - Building A",
                "Description": "Drywall repair due to roof leak damage"
            },
            {
                "WO #": "C1234",
                "Total": "$450.00", 
                "Location": "5878 Southern Ave SE",
                "Description": "Plumbing backup repair"
            }
        ]
        
        # Build prompt
        prompt = PromptBuilder.build_matching_prompt(
            email_text=email_text,
            work_orders=sample_work_orders,
            expected_count=2
        )
        
        print("✅ Prompt built successfully")
        print(f"   Length: {len(prompt)} characters")
        print(f"   Work orders included: {len(sample_work_orders)}")
        
        # Show prompt preview
        print("\n📋 Prompt preview (first 300 chars):")
        print(prompt[:300] + "...")
        
        return True, prompt, sample_work_orders
        
    except Exception as e:
        print(f"❌ Prompt building failed: {str(e)}")
        return False, None, None

def test_full_matching():
    """Test complete matching flow with Claude"""
    print("\n🤖 Testing Full LLM Matching...")
    
    try:
        from llm.anthropic_client import AnthropicClient
        
        # Get sample data from prompt building test
        success, prompt, work_orders = test_prompt_building()
        if not success:
            print("❌ Cannot test matching - prompt building failed")
            return False
        
        # Sample email text
        email_text = """Our invoice for the work is as follows:
Unit 5966: The concrete sidewalk and drain area was cracked and needed repair
Materials and Labor: $ 3,987.00
Unit 5804: Drywall was repaired, plastered and painted due to a roof leak 
Materials and Labor: $ 350.00"""
        
        # Initialize client and run matching
        client = AnthropicClient()
        result = client.find_matches(
            email_text=email_text,
            work_orders=work_orders,
            expected_count=2
        )
        
        if result.get("success"):
            print("✅ LLM matching completed successfully")
            
            matches = result.get("matches", [])
            unmatched = result.get("unmatched_items", [])
            
            print(f"\n📊 Results Summary:")
            print(f"   {len(matches)} matches found")
            print(f"   {len(unmatched)} unmatched items")
            print(f"   Summary: {result.get('summary', 'N/A')}")
            
            # Show matches with confidence scores
            for i, match in enumerate(matches, 1):
                print(f"\n🎯 Match {i}:")
                print(f"   Email Item: {match.get('email_item', 'N/A')}")
                print(f"   Work Order: {match.get('work_order_id', 'N/A')}")
                print(f"   Confidence: {match.get('confidence', 0)}%")
                
                evidence = match.get('evidence', {})
                if evidence.get('score_breakdown'):
                    print(f"   Scoring: {evidence['score_breakdown']}")
                
                amount_comp = match.get('amount_comparison', {})
                if amount_comp:
                    email_amt = amount_comp.get('email_amount', 0)
                    wo_amt = amount_comp.get('wo_amount', 0)
                    diff = amount_comp.get('difference', 0)
                    print(f"   Amounts: Email ${email_amt} vs WO ${wo_amt} (diff: ${diff})")
            
            # Show unmatched items
            if unmatched:
                print(f"\n⚠️ Unmatched items:")
                for item in unmatched:
                    print(f"   - {item}")
            
            return True
            
        else:
            print(f"❌ LLM matching failed: {result.get('error', 'Unknown error')}")
            if result.get('raw_response'):
                print(f"   Raw response preview: {result['raw_response'][:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Full matching test failed: {str(e)}")
        return False

def test_with_live_data():
    """Test with actual Google Sheets data"""
    print("\n🔗 Testing with Live Google Sheets Data...")
    
    try:
        from auth.google_auth import GoogleAuth
        from llm.anthropic_client import AnthropicClient
        
        # Load real work order data
        print("📊 Loading work orders from Google Sheets...")
        auth = GoogleAuth()
        auth.authenticate()
        work_orders = auth.load_work_orders()
        
        if not work_orders:
            print("❌ No work orders loaded")
            return False
        
        print(f"✅ Loaded {len(work_orders)} alpha-numeric work orders")
        
        # Test email based on your sheet data
        email_text = """New Endeavor for Women: 
Our invoice for the work at 56th St NE is as follows: 
Two (2) stoves were repaired, 
One needed new hooks for the oven door. 
Materials and Labor: $ 477.00"""
        
        # Run matching with live data
        client = AnthropicClient()
        result = client.find_matches(
            email_text=email_text,
            work_orders=work_orders[:50],  # Limit to first 50 for testing
            expected_count=1
        )
        
        if result.get("success"):
            print("✅ Live data matching successful")
            
            matches = result.get("matches", [])
            print(f"   Found {len(matches)} potential matches")
            
            for match in matches:
                print(f"\n🎯 Live Match:")
                print(f"   Confidence: {match.get('confidence', 0)}%")
                print(f"   Work Order: {match.get('work_order_id', 'N/A')}")
                print(f"   Email Item: {match.get('email_item', 'N/A')}")
            
            return True
        else:
            print(f"❌ Live data matching failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Live data test failed: {str(e)}")
        return False

def main():
    """Run all LLM tests"""
    print("🚀 Work Order Matcher - LLM Integration Test")
    print("=" * 60)
    
    # Test sequence
    tests = [
        ("Anthropic Connection", test_anthropic_connection),
        ("Prompt Building", lambda: test_prompt_building()[0]),
        ("Full LLM Matching", test_full_matching),
        ("Live Data Integration", test_with_live_data)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 Test Results Summary:")
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All LLM tests passed! The matching system is ready.")
        print("\nNext steps:")
        print("1. Build the main GUI application")  
        print("2. Integrate this LLM system with user interface")
        print("3. Add export/results display functionality")
    else:
        print(f"\n⚠️ {sum(not r for r in results.values())} tests failed - check errors above")

if __name__ == "__main__":
    main() 