# data/data_models.py
"""
Data models for Work Order Matcher
Clean data structures for matches, work orders, and email processing
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import re


@dataclass
class WorkOrder:
    """Represents a work order from Google Sheets"""
    wo_id: str
    total: str
    location: str
    description: str
    raw_data: Dict[str, Any]  # Original row data
    
    @classmethod
    def from_sheets_row(cls, row_data: Dict[str, Any]) -> 'WorkOrder':
        """Create WorkOrder from Google Sheets row data"""
        return cls(
            wo_id=str(row_data.get('WO #', '')).strip(),
            total=str(row_data.get('Total', '')).strip(), 
            location=str(row_data.get('Location', '')).strip(),
            description=str(row_data.get('Description', '')).strip(),
            raw_data=row_data
        )
    
    def get_clean_amount(self) -> float:
        """Extract numeric amount from total string"""
        try:
            if not self.total or not isinstance(self.total, str):
                return 0.0
            
            # Remove currency symbols and commas
            clean_total = re.sub(r'[^\d.-]', '', str(self.total).strip())
            if not clean_total or clean_total in ['-', '.']:
                return 0.0
            
            return float(clean_total)
        except (ValueError, TypeError, AttributeError):
            return 0.0
    
    def is_alpha_numeric(self) -> bool:
        """Check if work order ID starts with a letter (special clients)"""
        return bool(self.wo_id and re.match(r'^[A-Za-z]', self.wo_id))


@dataclass  
class EmailItem:
    """Represents a billing item extracted from email"""
    description: str
    amount: float
    unit_number: Optional[str] = None
    location_hints: List[str] = None
    
    def __post_init__(self):
        if self.location_hints is None:
            self.location_hints = []


@dataclass
class MatchEvidence:
    """Evidence supporting a work order match"""
    primary_signals: List[str]
    supporting_signals: List[str] 
    score_breakdown: str
    concerns: List[str] = None
    
    def __post_init__(self):
        if self.concerns is None:
            self.concerns = []


@dataclass
class AmountComparison:
    """Comparison between email and work order amounts"""
    email_amount: float
    wo_amount: float
    difference: float
    
    @property
    def percentage_difference(self) -> float:
        """Calculate percentage difference"""
        if self.wo_amount == 0:
            return float('inf') if self.email_amount != 0 else 0.0
        return abs(self.difference / self.wo_amount) * 100
    
    @property
    def is_exact_match(self) -> bool:
        """Check if amounts match exactly"""
        return abs(self.difference) < 0.01
    
    @property
    def is_close_match(self) -> bool:
        """Check if amounts are within 15%"""
        return self.percentage_difference <= 15.0


@dataclass
class Match:
    """Represents a matched email item to work order"""
    email_item: str
    work_order_id: str
    confidence: int
    evidence: MatchEvidence
    amount_comparison: AmountComparison
    work_order: Optional[WorkOrder] = None
    
    @property
    def confidence_level(self) -> str:
        """Get confidence level description"""
        if self.confidence >= 85:
            return "Very High"
        elif self.confidence >= 70:
            return "High"  
        elif self.confidence >= 50:
            return "Medium"
        else:
            return "Low"
    
    @property
    def color_code(self) -> str:
        """Get color code for GUI display"""
        if self.confidence >= 85:
            return "green"
        elif self.confidence >= 70:
            return "lightgreen"
        elif self.confidence >= 50:
            return "yellow"
        else:
            return "lightcoral"


@dataclass
class MatchingResult:
    """Complete result from the matching process"""
    matches: List[Match]
    unmatched_items: List[str]
    summary: str
    success: bool
    error: Optional[str] = None
    raw_response: Optional[str] = None
    
    @property
    def high_confidence_matches(self) -> List[Match]:
        """Get matches with high confidence (≥70%)"""
        return [m for m in self.matches if m.confidence >= 70]
    
    @property
    def medium_confidence_matches(self) -> List[Match]:
        """Get matches requiring review (50-69%)"""  
        return [m for m in self.matches if 50 <= m.confidence < 70]
    
    @property
    def total_match_count(self) -> int:
        """Total number of matches found"""
        return len(self.matches)
    
    @property
    def unmatched_count(self) -> int:
        """Number of unmatched items"""
        return len(self.unmatched_items)
    
    @classmethod
    def from_api_response(cls, api_result: Dict[str, Any], work_orders: List[WorkOrder]) -> 'MatchingResult':
        """Create MatchingResult from API response"""
        if not api_result.get('success', False):
            return cls(
                matches=[],
                unmatched_items=[],
                summary="Matching failed",
                success=False,
                error=api_result.get('error', 'Unknown error'),
                raw_response=api_result.get('raw_response')
            )
        
        # Create WorkOrder lookup
        wo_lookup = {wo.wo_id: wo for wo in work_orders}
        
        # Convert API matches to Match objects
        matches = []
        for match_data in api_result.get('matches', []):
            try:
                # Validate match_data structure
                if not isinstance(match_data, dict):
                    continue
                
                # Build evidence with type checking
                evidence_data = match_data.get('evidence', {})
                if not isinstance(evidence_data, dict):
                    evidence_data = {}
                
                evidence = MatchEvidence(
                    primary_signals=evidence_data.get('primary_signals', []) if isinstance(evidence_data.get('primary_signals'), list) else [],
                    supporting_signals=evidence_data.get('supporting_signals', []) if isinstance(evidence_data.get('supporting_signals'), list) else [],
                    score_breakdown=str(evidence_data.get('score_breakdown', '')),
                    concerns=evidence_data.get('concerns', []) if isinstance(evidence_data.get('concerns'), list) else []
                )
                
                # Build amount comparison with type checking
                amount_comp_data = match_data.get('amount_comparison', {})
                if not isinstance(amount_comp_data, dict):
                    amount_comp_data = {}
                
                def safe_float(value, default=0.0):
                    try:
                        return float(value) if value is not None else default
                    except (ValueError, TypeError):
                        return default
                
                amount_comparison = AmountComparison(
                    email_amount=safe_float(amount_comp_data.get('email_amount')),
                    wo_amount=safe_float(amount_comp_data.get('wo_amount')), 
                    difference=safe_float(amount_comp_data.get('difference'))
                )
                
                # Clean work order ID
                wo_id_raw = match_data.get('work_order_id', '')
                wo_id = str(wo_id_raw).replace('WO#', '').strip() if wo_id_raw else ''
                
                # Validate confidence score
                confidence_raw = match_data.get('confidence', 0)
                try:
                    confidence = int(float(confidence_raw))
                    confidence = max(0, min(100, confidence))  # Clamp to 0-100
                except (ValueError, TypeError):
                    confidence = 0
                
                match = Match(
                    email_item=str(match_data.get('email_item', '')),
                    work_order_id=wo_id,
                    confidence=confidence,
                    evidence=evidence,
                    amount_comparison=amount_comparison,
                    work_order=wo_lookup.get(wo_id)
                )
                matches.append(match)
                
            except Exception as e:
                # Skip malformed matches but log the issue if logging is available
                # Don't fail entire result
                continue
        
        return cls(
            matches=matches,
            unmatched_items=api_result.get('unmatched_items', []),
            summary=api_result.get('summary', 'Analysis complete'),
            success=True,
            raw_response=api_result.get('raw_response')
        ) 