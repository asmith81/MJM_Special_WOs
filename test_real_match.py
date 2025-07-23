# test_real_match.py
"""
Test matching with realistic email that should match actual work orders
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_realistic_test_email():
    """Create an email that should match the work orders we saw in debug"""
    
    # From debug output, we have P1003 at 5878 Southern Ave SE for $525
    email_text = """Our invoice for work completed:

5878 Southern Ave: Plumbing repair work completed. 
Fixed backup in kitchen sink and drain line.
Materials and Labor: $525.00

Thank you for your business."""
    
    return email_text

def test_realistic_matching():
    """Test with realistic email"""
    print("🧪 Testing with realistic email that should match actual work orders...")
    
    try:
        from data.sheets_client import SheetsClient
        from llm.anthropic_client import AnthropicClient
        from data.data_models import MatchingResult
        
        # Load work orders
        sheets_client = SheetsClient()
        sheets_client.authenticate()
        work_orders = sheets_client.load_alpha_numeric_work_orders()
        
        print(f"✅ Loaded {len(work_orders)} work orders")
        
        # Show some sample work orders for reference
        print("\n📋 Sample work orders:")
        for i, wo in enumerate(work_orders[:5]):
            print(f"   {wo.wo_id}: ${wo.get_clean_amount():.2f} | {wo.location[:40]}...")
        
        # Create realistic email
        email_text = create_realistic_test_email()
        print(f"\n📧 Test email:")
        print(email_text)
        
        # Convert work orders to dict format
        work_orders_dict = []
        for wo in work_orders[:20]:  # Use first 20 for faster testing
            wo_dict = {
                'WO #': wo.wo_id,
                'Total': wo.total,
                'Location': wo.location,
                'Description': wo.description
            }
            work_orders_dict.append(wo_dict)
        
        # Run matching
        client = AnthropicClient()
        result = client.find_matches(
            email_text=email_text,
            work_orders=work_orders_dict,
            expected_count=1
        )
        
        print(f"\n🤖 Claude Analysis Result:")
        print(f"   Success: {result.get('success', False)}")
        
        if result.get('success'):
            # Convert to MatchingResult object
            matching_result = MatchingResult.from_api_response(result, work_orders[:20])
            
            print(f"   Matches: {matching_result.total_match_count}")
            print(f"   Unmatched: {matching_result.unmatched_count}")
            print(f"   Summary: {matching_result.summary}")
            
            for match in matching_result.matches:
                print(f"\n🎯 Match Found:")
                print(f"   WO ID: {match.work_order_id}")
                print(f"   Confidence: {match.confidence}% ({match.confidence_level})")
                print(f"   Evidence: {match.evidence.score_breakdown}")
                print(f"   Amounts: ${match.amount_comparison.email_amount} vs ${match.amount_comparison.wo_amount}")
        else:
            print(f"   Error: {result.get('error')}")
            if result.get('raw_response'):
                print(f"   Raw: {result['raw_response'][:200]}...")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Realistic Work Order Matching Test")
    print("=" * 50)
    
    success = test_realistic_matching()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Realistic matching test completed!")
    else:
        print("❌ Test failed - check errors above") 