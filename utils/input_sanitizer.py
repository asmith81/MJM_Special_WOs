"""
Input sanitization for Work Order Matcher
Provides security and data quality checks for email text input
"""

import re
import html
from typing import Dict, List, Optional, Any
from utils.logging_config import get_logger

logger = get_logger('input_sanitizer')

class EmailTextSanitizer:
    """Sanitizes and validates email text input for security and quality"""
    
    # Maximum allowed text length (to prevent token overload)
    MAX_TEXT_LENGTH = 10000
    
    # Minimum meaningful text length
    MIN_TEXT_LENGTH = 20
    
    # Patterns for potential security issues
    SUSPICIOUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',                # JavaScript URLs
        r'data:.*base64',             # Base64 data URLs
        r'<!--.*?-->',                # HTML comments
        r'<iframe[^>]*>.*?</iframe>', # Iframe tags
    ]
    
    # Patterns for cleaning common formatting issues
    CLEANING_PATTERNS = [
        (r'\r\n', '\n'),              # Normalize line endings
        (r'\r', '\n'),                # Convert Mac line endings
        (r'\n{3,}', '\n\n'),          # Reduce excessive newlines
        (r'[ \t]{2,}', ' '),          # Reduce multiple spaces/tabs
        (r'^\s+|\s+$', ''),           # Trim whitespace (per line)
    ]
    
    @classmethod
    def sanitize_email_text(cls, text: str, strict_mode: bool = True) -> Dict[str, Any]:
        """
        Sanitize and validate email text input
        
        Args:
            text: Raw email text from user input
            strict_mode: Whether to apply strict validation rules
            
        Returns:
            Dict with sanitized text and validation results
        """
        result = {
            'sanitized_text': '',
            'is_valid': False,
            'warnings': [],
            'errors': [],
            'original_length': len(text) if text else 0,
            'sanitized_length': 0
        }
        
        try:
            if not text or not isinstance(text, str):
                result['errors'].append("Input text is empty or not a string")
                return result
            
            logger.debug(f"Sanitizing email text: {len(text)} characters")
            
            # Step 1: Check length limits
            if len(text) > cls.MAX_TEXT_LENGTH:
                result['errors'].append(f"Text too long ({len(text)} chars). Maximum allowed: {cls.MAX_TEXT_LENGTH}")
                if strict_mode:
                    return result
                else:
                    text = text[:cls.MAX_TEXT_LENGTH]
                    result['warnings'].append("Text truncated to maximum length")
            
            if len(text) < cls.MIN_TEXT_LENGTH:
                result['errors'].append(f"Text too short ({len(text)} chars). Minimum required: {cls.MIN_TEXT_LENGTH}")
                return result
            
            # Step 2: Security checks
            security_issues = cls._check_security_patterns(text)
            if security_issues:
                result['errors'].extend(security_issues)
                if strict_mode:
                    return result
            
            # Step 3: HTML entity decoding (in case text was HTML encoded)
            text = html.unescape(text)
            
            # Step 4: Remove potential HTML/XML tags
            text = cls._remove_html_tags(text)
            
            # Step 5: Clean formatting
            text = cls._clean_formatting(text)
            
            # Step 6: Validate content structure
            validation_warnings = cls._validate_content_structure(text)
            result['warnings'].extend(validation_warnings)
            
            # Step 7: Final validation
            if len(text.strip()) < cls.MIN_TEXT_LENGTH:
                result['errors'].append("Text became too short after sanitization")
                return result
            
            result['sanitized_text'] = text.strip()
            result['sanitized_length'] = len(result['sanitized_text'])
            result['is_valid'] = True
            
            logger.info(f"Email text sanitized successfully: {result['original_length']} -> {result['sanitized_length']} chars, {len(result['warnings'])} warnings")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sanitizing email text: {str(e)}")
            result['errors'].append(f"Sanitization failed: {str(e)}")
            return result
    
    @classmethod
    def _check_security_patterns(cls, text: str) -> List[str]:
        """Check for suspicious patterns that might indicate security issues"""
        issues = []
        
        for pattern in cls.SUSPICIOUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                issues.append(f"Suspicious pattern detected: {pattern}")
        
        # Check for excessive special characters (might indicate injection attempt)
        special_char_ratio = len(re.findall(r'[<>{}[\]();\'"`]', text)) / len(text)
        if special_char_ratio > 0.1:  # More than 10% special characters
            issues.append(f"High ratio of special characters: {special_char_ratio:.2%}")
        
        return issues
    
    @classmethod
    def _remove_html_tags(cls, text: str) -> str:
        """Remove HTML/XML tags from text"""
        # Remove HTML tags but preserve content
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove HTML entities that might have been missed
        text = re.sub(r'&[a-zA-Z0-9#]+;', '', text)
        
        return text
    
    @classmethod
    def _clean_formatting(cls, text: str) -> str:
        """Clean common formatting issues"""
        for pattern, replacement in cls.CLEANING_PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
        
        return text
    
    @classmethod
    def _validate_content_structure(cls, text: str) -> List[str]:
        """Validate that the text has reasonable structure for billing content"""
        warnings = []
        
        # Check for currency amounts (should have at least one)
        currency_patterns = [
            r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?',  # $1,234.56
            r'\d+(?:,\d{3})*(?:\.\d{2})?\s*dollars?',  # 1234.56 dollars
        ]
        
        has_currency = any(re.search(pattern, text, re.IGNORECASE) for pattern in currency_patterns)
        if not has_currency:
            warnings.append("No currency amounts detected - this may not be billing text")
        
        # Check for common billing keywords
        billing_keywords = [
            'invoice', 'bill', 'charge', 'cost', 'price', 'total', 'amount',
            'materials', 'labor', 'work', 'repair', 'service', 'unit'
        ]
        
        keyword_count = sum(1 for keyword in billing_keywords 
                          if re.search(r'\b' + keyword + r'\b', text, re.IGNORECASE))
        
        if keyword_count < 2:
            warnings.append("Few billing-related keywords detected")
        
        # Check line structure (should have multiple lines for typical billing)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if len(lines) < 3:
            warnings.append("Text has very few lines - typical billing emails have multiple line items")
        
        # Check for extremely long lines (might indicate formatting issues)
        long_lines = [line for line in lines if len(line) > 200]
        if long_lines:
            warnings.append(f"{len(long_lines)} extremely long lines detected - might have formatting issues")
        
        return warnings
    
    @classmethod
    def extract_billing_items(cls, sanitized_text: str) -> List[Dict[str, Any]]:
        """
        Extract structured billing items from sanitized text
        
        Args:
            sanitized_text: Clean email text
            
        Returns:
            List of extracted billing items with metadata
        """
        items = []
        
        try:
            # Pattern to match common billing line formats
            billing_patterns = [
                # "Unit 1234: Description $amount"
                r'(?:unit\s+(\w+)\s*:?\s*)?([^$\n]+?)\s*\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                # "Description: $amount"
                r'([^$\n:]+?)\s*:?\s*\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                # "Description - $amount"
                r'([^$\n-]+?)\s*-\s*\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            ]
            
            for line in sanitized_text.split('\n'):
                line = line.strip()
                if not line or len(line) < 10:
                    continue
                
                for pattern in billing_patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        groups = match.groups()
                        
                        if len(groups) == 3:  # Unit number pattern
                            unit_num, description, amount = groups
                            item = {
                                'full_text': line,
                                'unit_number': unit_num.strip() if unit_num else None,
                                'description': description.strip(),
                                'amount_text': amount,
                                'amount_value': cls._parse_currency(amount)
                            }
                        elif len(groups) == 2:  # No unit number
                            description, amount = groups
                            item = {
                                'full_text': line,
                                'unit_number': None,
                                'description': description.strip(),
                                'amount_text': amount,
                                'amount_value': cls._parse_currency(amount)
                            }
                        else:
                            continue
                        
                        # Validate item quality
                        if (len(item['description']) > 5 and 
                            item['amount_value'] > 0 and
                            not cls._is_total_line(item['description'])):
                            items.append(item)
                        
                        break  # Found a match for this line, move to next line
            
            logger.info(f"Extracted {len(items)} billing items from sanitized text")
            return items
            
        except Exception as e:
            logger.error(f"Error extracting billing items: {str(e)}")
            return []
    
    @classmethod
    def _parse_currency(cls, amount_str: str) -> float:
        """Parse currency string to float value"""
        try:
            if not amount_str or not isinstance(amount_str, str):
                return 0.0
            
            # Remove commas, dollar signs, and whitespace
            clean_amount = re.sub(r'[,$\s]', '', str(amount_str).strip())
            if not clean_amount or clean_amount in ['-', '.']:
                return 0.0
            
            return float(clean_amount)
        except (ValueError, TypeError, AttributeError):
            return 0.0
    
    @classmethod
    def _is_total_line(cls, description: str) -> bool:
        """Check if a line appears to be a total/summary line"""
        total_keywords = ['total', 'grand total', 'subtotal', 'sum', 'amount due']
        return any(keyword in description.lower() for keyword in total_keywords)
    
    @classmethod
    def get_sanitization_stats(cls, text: str) -> Dict[str, Any]:
        """Get detailed statistics about text content for debugging"""
        if not text:
            return {"error": "No text provided"}
        
        lines = text.split('\n')
        words = text.split()
        
        return {
            'total_length': len(text),
            'line_count': len(lines),
            'word_count': len(words),
            'non_empty_lines': len([line for line in lines if line.strip()]),
            'avg_line_length': sum(len(line) for line in lines) / len(lines) if lines else 0,
            'currency_mentions': len(re.findall(r'\$\s*\d+', text)),
            'number_mentions': len(re.findall(r'\b\d+\b', text)),
            'special_char_ratio': len(re.findall(r'[^\w\s]', text)) / len(text) if text else 0,
            'whitespace_ratio': len(re.findall(r'\s', text)) / len(text) if text else 0
        } 