# debug_matching.py
"""
Debug script to test the matching process and identify issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_data_conversion():
    """Test converting WorkOrder objects to dict format"""
    print("🔍 Testing data conversion...")
    
    try:
        from data.sheets_client import SheetsClient
        
        # Load work orders
        sheets_client = SheetsClient()
        sheets_client.authenticate()
        work_orders = sheets_client.load_alpha_numeric_work_orders()[:5]  # Just first 5
        
        print(f"✅ Loaded {len(work_orders)} work orders for testing")
        
        # Test conversion to dict format
        wo_dicts = []
        for wo in work_orders:
            wo_dict = {
                'WO #': wo.wo_id,
                'Total': wo.total,
                'Location': wo.location,
                'Description': wo.description
            }
            wo_dicts.append(wo_dict)
            print(f"   WO {wo.wo_id}: {wo.total} | {wo.location[:30]}...")
        
        return wo_dicts
        
    except Exception as e:
        print(f"❌ Data conversion failed: {e}")
        return []

def test_simple_matching():
    """Test matching with simple email and few work orders"""
    print("\n🤖 Testing simple matching...")
    
    try:
        # Get work orders
        wo_dicts = test_data_conversion()
        if not wo_dicts:
            return False
        
        from llm.anthropic_client import AnthropicClient
        
        # Simple test email
        email_text = """Unit 5966: Concrete repair work completed
Materials and Labor: $450.00"""
        
        print(f"📧 Test email: {email_text[:50]}...")
        print(f"📊 Using {len(wo_dicts)} work orders")
        
        # Run matching
        client = AnthropicClient()
        result = client.find_matches(
            email_text=email_text,
            work_orders=wo_dicts,
            expected_count=1
        )
        
        print(f"✅ API call successful: {result.get('success', False)}")
        
        if result.get('success'):
            matches = result.get('matches', [])
            unmatched = result.get('unmatched_items', [])
            print(f"   Matches found: {len(matches)}")
            print(f"   Unmatched items: {len(unmatched)}")
            
            for match in matches:
                print(f"   → {match.get('work_order_id', 'N/A')}: {match.get('confidence', 0)}%")
        else:
            print(f"❌ API call failed: {result.get('error', 'Unknown error')}")
            if result.get('raw_response'):
                print(f"Raw response: {result['raw_response'][:200]}...")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Simple matching failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_response_validation():
    """Test response validation with sample JSON"""
    print("\n🔍 Testing response validation...")
    
    try:
        from llm.prompt_builder import PromptBuilder
        
        # Test with valid JSON
        valid_json = """{
  "matches": [
    {
      "email_item": "Unit 5966: Concrete repair $450",
      "work_order_id": "A5966",
      "confidence": 85,
      "evidence": {
        "score_breakdown": "50 (unit) + 30 (amount) + 5 (job) = 85%",
        "primary_signals": ["unit match"],
        "supporting_signals": ["amount match"]
      },
      "amount_comparison": {
        "email_amount": 450.0,
        "wo_amount": 450.0,
        "difference": 0.0
      }
    }
  ],
  "unmatched_items": [],
  "summary": "1 match found"
}"""
        
        print("Testing valid JSON...")
        result = PromptBuilder.validate_response(valid_json)
        print(f"✅ Validation result: {result.get('success', False)}")
        
        if not result.get('success'):
            print(f"❌ Validation error: {result.get('error')}")
        
        # Test with invalid JSON
        invalid_json = """{"matches": [], "summary": "no matches"}"""  # Missing unmatched_items
        
        print("\nTesting invalid JSON...")
        result = PromptBuilder.validate_response(invalid_json)
        print(f"❌ Expected failure: {not result.get('success', True)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Response validation test failed: {e}")
        return False

def main():
    """Run all debug tests"""
    print("🚀 Work Order Matcher - Debug Tests")
    print("=" * 50)
    
    tests = [
        ("Data Conversion", test_data_conversion),
        ("Response Validation", test_response_validation), 
        ("Simple Matching", test_simple_matching)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            if test_name == "Data Conversion":
                results[test_name] = bool(test_func())
            else:
                results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("🎯 Debug Test Results:")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {test_name}")

if __name__ == "__main__":
    main() 