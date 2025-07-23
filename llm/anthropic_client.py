# llm/anthropic_client.py
"""
Anthropic Claude API client for Work Order Matcher
Handles API calls and response processing using blended confidence scoring
"""

import anthropic
import time
from typing import List, Dict, Any, Optional
from utils.config import Config
from llm.prompt_builder import PromptBuilder


class AnthropicClient:
    """Client for interacting with Anthropic Claude API"""
    
    def __init__(self):
        """Initialize the Anthropic client"""
        if not Config.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.prompt_builder = PromptBuilder()
        
        # API settings
        self.model = "claude-3-5-sonnet-20240620"  # Claude 3.5 Sonnet (widely available)
        self.max_tokens = 4000
        self.temperature = 0.1  # Low temperature for consistent, focused responses
    
    def find_matches(self, email_text: str, work_orders: List[Dict], expected_count: int = 5) -> Dict[str, Any]:
        """
        Find work order matches for email billing text using blended confidence scoring
        
        Args:
            email_text: Raw email text from user input
            work_orders: List of alpha-numeric work orders from Google Sheets
            expected_count: Expected number of matches to find
            
        Returns:
            Dict with matches, unmatched items, and processing info
        """
        try:
            # Build the prompt
            prompt = self.prompt_builder.build_matching_prompt(
                email_text=email_text,
                work_orders=work_orders,
                expected_count=expected_count
            )
            
            # Log prompt info (without sensitive data)
            print(f"🤖 Sending to Claude: {len(work_orders)} work orders, expecting {expected_count} matches")
            
            # Make API call with retry logic
            response = self._make_api_call(prompt)
            
            if not response:
                return {
                    "success": False,
                    "error": "Failed to get response from Claude API",
                    "matches": [],
                    "unmatched_items": [],
                    "summary": "API call failed"
                }
            
            # Validate and parse response
            validation = self.prompt_builder.validate_response(response)
            
            if validation.get("success"):
                result = validation["parsed"]
                result["success"] = True
                result["raw_response"] = response  # Include for debugging
                
                # Log results
                match_count = len(result.get("matches", []))
                unmatched_count = len(result.get("unmatched_items", []))
                print(f"✅ Claude analysis complete: {match_count} matches, {unmatched_count} unmatched items")
                
                return result
            else:
                return {
                    "success": False,
                    "error": validation.get("error", "Unknown validation error"),
                    "raw_response": validation.get("raw_response", response),
                    "matches": [],
                    "unmatched_items": [],
                    "summary": "Response validation failed"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Anthropic client error: {str(e)}",
                "matches": [],
                "unmatched_items": [],
                "summary": "Processing failed"
            }
    
    def _make_api_call(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """
        Make API call to Claude with retry logic
        
        Args:
            prompt: Complete prompt to send
            max_retries: Maximum number of retry attempts
            
        Returns:
            Response text or None if all retries fail
        """
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                
                # Extract text from response
                if response.content and len(response.content) > 0:
                    return response.content[0].text
                else:
                    raise ValueError("Empty response from Claude")
                    
            except anthropic.RateLimitError as e:
                wait_time = (attempt + 1) * 2  # Exponential backoff: 2, 4, 6 seconds
                print(f"⚠️ Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                else:
                    print("❌ Max retries exceeded for rate limit")
                    raise e
                    
            except anthropic.APIError as e:
                print(f"❌ Anthropic API error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    raise e
                    
            except Exception as e:
                print(f"❌ Unexpected error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    raise e
        
        return None
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to Anthropic API
        
        Returns:
            Test results with connection status
        """
        try:
            test_prompt = "Respond with just 'OK' if you can process this message."
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                temperature=0,
                messages=[{"role": "user", "content": test_prompt}]
            )
            
            if response.content and len(response.content) > 0:
                response_text = response.content[0].text.strip()
                return {
                    "success": True,
                    "response": response_text,
                    "model": self.model,
                    "status": "Connected to Anthropic Claude API"
                }
            else:
                return {
                    "success": False,
                    "error": "Empty response from Claude",
                    "status": "Connection test failed"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status": "Connection test failed"
            }
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get current API client status and configuration"""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "api_key_configured": bool(Config.ANTHROPIC_API_KEY and Config.ANTHROPIC_API_KEY.startswith('sk-ant-')),
            "client_initialized": bool(self.client)
        }
    
    def simple_match(self, email_items: List[str], work_orders: List[Dict]) -> Dict[str, Any]:
        """
        Simplified matching for testing or fallback scenarios
        
        Args:
            email_items: Pre-extracted billing items
            work_orders: Available work orders
            
        Returns:
            Simplified matching results
        """
        try:
            prompt = self.prompt_builder.create_simple_prompt(email_items, work_orders)
            response = self._make_api_call(prompt)
            
            if response:
                return {
                    "success": True,
                    "response": response,
                    "prompt": prompt
                }
            else:
                return {
                    "success": False,
                    "error": "No response from API",
                    "prompt": prompt
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            } 