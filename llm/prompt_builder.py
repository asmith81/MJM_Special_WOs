# llm/prompt_builder.py
"""
Prompt construction for Work Order Matcher
Implements blended confidence scoring system for intelligent matching
"""

import json
import re
from typing import List, Dict, Any


class PromptBuilder:
    """Constructs prompts for Anthropic Claude with blended confidence scoring"""
    
    # Confidence scoring weights
    EXACT_MATCH_WEIGHTS = {
        'exact_unit': 50,           # "Unit 5996" = "Unit 5996"
        'exact_address': 50,        # "5878 Southern Ave" = "5878 Southern Ave"
        'building_identifier': 45,  # "Building A" = "Building A"
        'property_name': 45         # "New Endeavor" = "New Endeavor Women's Shelter"
    }
    
    AMOUNT_WEIGHTS = {
        'exact_amount': 30,         # $450.00 = $450.00
        'close_amount': 20,         # $450 ≈ $425-475 (10-15% diff)
        'rough_amount': 10          # $450 ≈ $350-550 (20-30% diff)
    }
    
    JOB_TYPE_WEIGHTS = {
        'exact_job': 15,            # "drain backup" = "back up in the unit"
        'job_category': 10,         # "plumbing" = "Plumbing There is a back up"
        'general_work': 5           # "repair" = "repaired, plastered and painted"
    }
    
    LOCATION_WEIGHTS = {
        'address_fragment': 15,     # "56th St" ≈ "5878 Southern Ave"
        'general_area': 5           # "SE DC" = "Washington DC 20019"
    }

    @staticmethod
    def build_matching_prompt(email_text: str, work_orders: List[Dict], expected_count: int = 5) -> str:
        """
        Build the main prompt for work order matching with blended confidence scoring
        
        Args:
            email_text: Raw email text from user
            work_orders: List of filtered alpha-numeric work orders from Google Sheets
            expected_count: Expected number of matches to find
            
        Returns:
            Complete prompt string for Claude
        """
        
        # Format work orders for the prompt
        wo_summary = PromptBuilder._format_work_orders(work_orders)
        
        prompt = f"""You are an expert at matching construction billing emails to work order data for a general contractor.

TASK: Analyze the email billing text and find the best matches from the available work orders using a blended confidence scoring system.

EMAIL BILLING TEXT:
{email_text}

AVAILABLE WORK ORDERS ({len(work_orders)} alpha-numeric work orders for special clients):
{wo_summary}

CONFIDENCE SCORING SYSTEM:
Use these weighted signals to calculate blended confidence scores:

EXACT MATCH SIGNALS (Max 50 points, only highest applies):
• Exact unit match: 50 points → "Unit 5996" matches "Unit 5996"
• Exact address match: 50 points → "5878 Southern Ave" matches "5878 Southern Ave" 
• Building identifier: 45 points → "Building A" matches "Building A"
• Property name match: 45 points → "New Endeavor" matches "New Endeavor Women's Shelter"

AMOUNT SIGNALS (Additive):
• Exact amount: +30 points → $450.00 = $450.00
• Close amount (10-15% diff): +20 points → $450 ≈ $425-475  
• Rough amount (20-30% diff): +10 points → $450 ≈ $350-550

JOB TYPE SIGNALS (Additive):
• Exact job description: +15 points → "drain backup" matches "back up in the unit"
• Job category match: +10 points → "plumbing" matches "Plumbing There is a back up"  
• General work type: +5 points → "repair" matches "repaired, plastered and painted"

LOCATION SIGNALS (Additive):
• Address fragment: +15 points → "56th St" partially matches "5878 Southern Ave"
• General area: +5 points → "SE DC" matches "Washington DC 20019"

CONFIDENCE BANDS:
• 85-100%: Very high confidence (auto-accept quality)
• 70-84%: High confidence (likely correct)
• 50-69%: Medium confidence (review recommended)
• Below 50%: Low confidence (manual review required)

EXAMPLE SCORING:
Email: "Unit 5996: plumbing repair $450"  
Work Order: Unit "5996", "Plumbing backup", "$450.00"
Score: 50 (exact unit) + 30 (exact amount) + 15 (exact job) = 95%

Expected matches to find: {expected_count}

OUTPUT FORMAT:
Return a JSON object with this exact structure:

{{
  "matches": [
    {{
      "email_item": "extracted billing line item from email",
      "work_order_id": "WO123",
      "confidence": 85,
      "evidence": {{
        "primary_signals": ["exact unit match: 5996"],
        "supporting_signals": ["exact amount: $450", "job type: plumbing"],
        "score_breakdown": "50 (unit) + 30 (amount) + 15 (job) = 95%"
      }},
      "amount_comparison": {{
        "email_amount": 450.00,
        "wo_amount": 450.00,
        "difference": 0.00
      }}
    }}
  ],
  "unmatched_items": ["billing items that couldn't be matched with sufficient confidence"],
  "summary": "X high-confidence matches found, Y items need manual review"
}}

IMPORTANT INSTRUCTIONS:
1. Extract ALL billing line items from the email (look for amounts, unit numbers, job descriptions)
2. Calculate blended confidence scores by combining multiple signals
3. Only return matches with confidence ≥ 50%
4. Show your scoring logic in the evidence.score_breakdown field
5. If no good matches exist, include items in unmatched_items
6. Be thorough but realistic with confidence scoring

Begin analysis:"""

        return prompt

    @staticmethod
    def _format_work_orders(work_orders: List[Dict]) -> str:
        """Format work orders for inclusion in prompt"""
        if not work_orders:
            return "No work orders available"
        
        formatted = []
        for i, wo in enumerate(work_orders[:100]):  # Limit to first 100 to stay within token limits
            wo_str = f"WO#{wo.get('WO #', 'N/A')} | ${wo.get('Total', 'N/A')} | {wo.get('Location', 'N/A')[:50]} | {wo.get('Description', 'N/A')[:80]}"
            formatted.append(wo_str)
        
        result = "\n".join(formatted)
        
        if len(work_orders) > 100:
            result += f"\n... and {len(work_orders) - 100} more work orders available"
            
        return result

    @staticmethod
    def validate_response(response_text: str) -> Dict[str, Any]:
        """
        Validate and parse the Claude response
        
        Args:
            response_text: Raw response from Claude
            
        Returns:
            Parsed response dict or error info
        """
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                return {"error": "No JSON found in response", "raw_response": response_text}
            
            parsed = json.loads(json_match.group())
            
            # Validate required fields
            required_fields = ['matches', 'unmatched_items', 'summary']
            for field in required_fields:
                if field not in parsed:
                    return {"error": f"Missing required field: {field}", "parsed": parsed}
            
            # Validate match structure
            for match in parsed.get('matches', []):
                required_match_fields = ['email_item', 'work_order_id', 'confidence', 'evidence']
                for field in required_match_fields:
                    if field not in match:
                        return {"error": f"Missing required match field: {field}", "parsed": parsed}
                
                # Validate confidence score
                if not isinstance(match['confidence'], (int, float)) or not (0 <= match['confidence'] <= 100):
                    return {"error": f"Invalid confidence score: {match['confidence']}", "parsed": parsed}
            
            return {"success": True, "parsed": parsed}
            
        except json.JSONDecodeError as e:
            return {"error": f"JSON parsing failed: {str(e)}", "raw_response": response_text}
        except Exception as e:
            return {"error": f"Validation failed: {str(e)}", "raw_response": response_text}

    @staticmethod
    def create_simple_prompt(email_items: List[str], work_orders: List[Dict]) -> str:
        """
        Create a simpler prompt for testing or fallback scenarios
        
        Args:
            email_items: Pre-extracted billing items
            work_orders: Available work orders
            
        Returns:
            Simplified prompt string
        """
        wo_summary = PromptBuilder._format_work_orders(work_orders)
        items_text = "\n".join([f"- {item}" for item in email_items])
        
        return f"""Match these billing items to work orders:

BILLING ITEMS:
{items_text}

WORK ORDERS:
{wo_summary}

Return JSON with matches array. Use confidence 0-100 based on how well unit numbers, addresses, amounts, and job types align.""" 