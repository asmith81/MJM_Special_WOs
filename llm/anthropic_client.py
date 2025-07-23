# llm/anthropic_client.py
"""
Anthropic Claude API client for Work Order Matcher
Handles API calls and response processing using blended confidence scoring
"""

import anthropic
import time
from typing import List, Dict, Any, Optional
from utils.config import Config
from utils.logging_config import get_logger
from utils.input_sanitizer import EmailTextSanitizer
from llm.prompt_builder import PromptBuilder

logger = get_logger('anthropic_client')

class AnthropicClient:
    """Enhanced client for interacting with Anthropic Claude API with proper logging and input sanitization"""
    
    def __init__(self):
        """Initialize the Anthropic client with configuration-based settings"""
        if not Config.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.prompt_builder = PromptBuilder()
        self.input_sanitizer = EmailTextSanitizer()
        
        # API settings from configuration
        self.model = Config.CLAUDE_MODEL
        self.max_tokens = Config.CLAUDE_MAX_TOKENS
        self.temperature = Config.CLAUDE_TEMPERATURE
        self.max_retries = Config.MAX_API_RETRIES
        self.timeout = Config.API_TIMEOUT_SECONDS
        
        logger.info(f"AnthropicClient initialized - Model: {self.model}, Max tokens: {self.max_tokens}, Temperature: {self.temperature}")
        
        # Performance tracking
        self._api_calls_count = 0
        self._total_tokens_used = 0
        self._total_api_time = 0.0
    
    def find_matches(self, email_text: str, work_orders: List[Dict], expected_count: int = 5) -> Dict[str, Any]:
        """
        Find work order matches for email billing text using blended confidence scoring with input sanitization
        
        Args:
            email_text: Raw email text from user input
            work_orders: List of alpha-numeric work orders from Google Sheets
            expected_count: Expected number of matches to find
            
        Returns:
            Dict with matches, unmatched items, and processing info
        """
        start_time = time.time()
        self._api_calls_count += 1
        
        try:
            logger.info(f"Starting match analysis - WO count: {len(work_orders)}, Expected matches: {expected_count}")
            
            # Step 1: Sanitize input text
            sanitization_result = self.input_sanitizer.sanitize_email_text(
                email_text, 
                strict_mode=Config.STRICT_INPUT_VALIDATION
            )
            
            if not sanitization_result['is_valid']:
                error_msg = f"Input validation failed: {'; '.join(sanitization_result['errors'])}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "matches": [],
                    "unmatched_items": [],
                    "summary": "Input validation failed",
                    "sanitization_warnings": sanitization_result['warnings']
                }
            
            # Log sanitization results
            if sanitization_result['warnings']:
                logger.warning(f"Input sanitization warnings: {'; '.join(sanitization_result['warnings'])}")
            
            logger.debug(f"Text sanitized: {sanitization_result['original_length']} -> {sanitization_result['sanitized_length']} chars")
            
            # Step 2: Build the prompt
            sanitized_text = sanitization_result['sanitized_text']
            prompt = self.prompt_builder.build_matching_prompt(
                email_text=sanitized_text,
                work_orders=work_orders,
                expected_count=expected_count
            )
            
            # Log prompt info (without sensitive data)
            logger.info(f"🤖 Sending to Claude: {len(work_orders)} work orders, expecting {expected_count} matches")
            
            # Step 3: Make API call with retry logic
            api_start_time = time.time()
            response = self._make_api_call(prompt)
            api_duration = time.time() - api_start_time
            
            self._total_api_time += api_duration
            
            if not response:
                error_msg = "Failed to get response from Claude API"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "matches": [],
                    "unmatched_items": [],
                    "summary": "API call failed"
                }
            
            # Step 4: Validate and parse response
            validation = self.prompt_builder.validate_response(response)
            
            if validation.get("success"):
                result = validation["parsed"]
                result["success"] = True
                
                # Include debugging info if enabled
                if Config.SAVE_API_DEBUG_DATA:
                    result["raw_response"] = response
                    result["sanitization_result"] = sanitization_result
                
                # Log results
                match_count = len(result.get("matches", []))
                unmatched_count = len(result.get("unmatched_items", []))
                total_duration = time.time() - start_time
                
                logger.info(f"✅ Claude analysis complete: {match_count} matches, {unmatched_count} unmatched items in {total_duration:.2f}s")
                
                # Performance logging if enabled
                if Config.ENABLE_PERFORMANCE_LOGGING:
                    logger.info(f"Performance - API: {api_duration:.2f}s, Total: {total_duration:.2f}s, Tokens estimate: {len(prompt)//4}")
                
                return result
            else:
                error_msg = validation.get("error", "Unknown validation error")
                logger.error(f"Response validation failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "raw_response": validation.get("raw_response", response) if Config.SAVE_API_DEBUG_DATA else None,
                    "matches": [],
                    "unmatched_items": [],
                    "summary": "Response validation failed"
                }
                
        except Exception as e:
            total_duration = time.time() - start_time
            logger.error(f"Anthropic client error after {total_duration:.2f}s: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Anthropic client error: {str(e)}",
                "matches": [],
                "unmatched_items": [],
                "summary": "Processing failed"
            }
    
    def _make_api_call(self, prompt: str) -> Optional[str]:
        """
        Make API call to Claude with enhanced retry logic and logging
        
        Args:
            prompt: Complete prompt to send
            
        Returns:
            Response text or None if all retries fail
        """
        for attempt in range(self.max_retries):
            try:
                call_start_time = time.time()
                
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
                
                call_duration = time.time() - call_start_time
                
                # Extract text from response
                if response.content and len(response.content) > 0:
                    response_text = response.content[0].text
                    
                    # Track token usage if available
                    if hasattr(response, 'usage'):
                        input_tokens = getattr(response.usage, 'input_tokens', 0)
                        output_tokens = getattr(response.usage, 'output_tokens', 0)
                        self._total_tokens_used += input_tokens + output_tokens
                        
                        logger.debug(f"API call successful - Duration: {call_duration:.2f}s, Input tokens: {input_tokens}, Output tokens: {output_tokens}")
                    else:
                        logger.debug(f"API call successful - Duration: {call_duration:.2f}s")
                    
                    return response_text
                else:
                    raise ValueError("Empty response from Claude")
                    
            except anthropic.RateLimitError as e:
                wait_time = min((attempt + 1) * 2, 30)  # Cap at 30 seconds
                logger.warning(f"Rate limit hit on attempt {attempt + 1}/{self.max_retries}, waiting {wait_time}s")
                if attempt < self.max_retries - 1:
                    time.sleep(wait_time)
                else:
                    logger.error("Max retries exceeded for rate limit")
                    raise e
                    
            except anthropic.APIError as e:
                logger.error(f"Anthropic API error on attempt {attempt + 1}/{self.max_retries}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(min(attempt + 1, 5))  # Progressive backoff, cap at 5s
                else:
                    raise e
                    
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}/{self.max_retries}: {str(e)}")
                if attempt < self.max_retries - 1:
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