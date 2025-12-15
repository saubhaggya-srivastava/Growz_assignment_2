"""Item matching engine for comparing PO and PI line items"""

from typing import List, Optional
from rapidfuzz import fuzz
from ..models import (
    NormalizedLineItem,
    MatchResult,
    MatchedPair,
    MatchStatistics,
)


class ItemMatcher:
    """Match line items between purchase orders and proforma invoices"""
    
    def __init__(self, fuzzy_threshold: float = 80.0):
        """Initialize matcher
        
        Args:
            fuzzy_threshold: Minimum similarity score (0-100) for fuzzy matching
        """
        self.fuzzy_threshold = fuzzy_threshold
    
    def match_items(
        self,
        po_items: List[NormalizedLineItem],
        pi_items: List[NormalizedLineItem]
    ) -> MatchResult:
        """Match line items using SKU, description, and fuzzy matching
        
        Matching priority:
        1. SKU matching (if both items have SKUs)
        2. Exact description matching
        3. Fuzzy description matching
        
        Args:
            po_items: List of normalized PO line items
            pi_items: List of normalized PI line items
            
        Returns:
            MatchResult with matched pairs and unmatched items
        """
        matched_pairs = []
        unmatched_po = list(po_items)  # Copy to track unmatched
        unmatched_pi = list(pi_items)  # Copy to track unmatched
        
        # Phase 1: SKU matching (primary)
        po_remaining = []
        for po_item in unmatched_po:
            pi_match = self.sku_match(po_item, unmatched_pi)
            if pi_match:
                matched_pairs.append(MatchedPair(
                    po_item=po_item,
                    pi_item=pi_match,
                    match_type="sku",
                    match_score=1.0
                ))
                unmatched_pi.remove(pi_match)
            else:
                po_remaining.append(po_item)
        
        unmatched_po = po_remaining
        
        # Phase 2: Exact description matching (secondary)
        po_remaining = []
        for po_item in unmatched_po:
            pi_match = self.exact_description_match(po_item, unmatched_pi)
            if pi_match:
                matched_pairs.append(MatchedPair(
                    po_item=po_item,
                    pi_item=pi_match,
                    match_type="exact_description",
                    match_score=1.0
                ))
                unmatched_pi.remove(pi_match)
            else:
                po_remaining.append(po_item)
        
        unmatched_po = po_remaining
        
        # Phase 3: Fuzzy matching (fallback)
        po_remaining = []
        for po_item in unmatched_po:
            pi_match, score = self.fuzzy_match(po_item, unmatched_pi, self.fuzzy_threshold)
            if pi_match:
                matched_pairs.append(MatchedPair(
                    po_item=po_item,
                    pi_item=pi_match,
                    match_type="fuzzy",
                    match_score=score / 100.0  # Normalize to 0-1
                ))
                unmatched_pi.remove(pi_match)
            else:
                po_remaining.append(po_item)
        
        unmatched_po = po_remaining
        
        # Calculate statistics
        statistics = MatchStatistics(
            total_po_items=len(po_items),
            total_pi_items=len(pi_items),
            matched_count=len(matched_pairs),
            unmatched_po_count=len(unmatched_po),
            unmatched_pi_count=len(unmatched_pi)
        )
        
        return MatchResult(
            matched_pairs=matched_pairs,
            unmatched_po_items=unmatched_po,
            unmatched_pi_items=unmatched_pi,
            match_statistics=statistics
        )
    
    def sku_match(
        self,
        po_item: NormalizedLineItem,
        pi_items: List[NormalizedLineItem]
    ) -> Optional[NormalizedLineItem]:
        """Match by SKU (primary matching method)
        
        Args:
            po_item: PO line item
            pi_items: List of PI line items to search
            
        Returns:
            Matched PI item or None
        """
        if not po_item.sku:
            return None
        
        po_sku = po_item.sku.strip().upper()
        
        for pi_item in pi_items:
            if pi_item.sku:
                pi_sku = pi_item.sku.strip().upper()
                if po_sku == pi_sku:
                    return pi_item
        
        return None
    
    def exact_description_match(
        self,
        po_item: NormalizedLineItem,
        pi_items: List[NormalizedLineItem]
    ) -> Optional[NormalizedLineItem]:
        """Match by exact description (secondary matching method)
        
        Args:
            po_item: PO line item
            pi_items: List of PI line items to search
            
        Returns:
            Matched PI item or None
        """
        if not po_item.description:
            return None
        
        po_desc = po_item.description.strip().lower()
        
        for pi_item in pi_items:
            if pi_item.description:
                pi_desc = pi_item.description.strip().lower()
                if po_desc == pi_desc:
                    return pi_item
        
        return None
    
    def fuzzy_match(
        self,
        po_item: NormalizedLineItem,
        pi_items: List[NormalizedLineItem],
        threshold: float
    ) -> tuple[Optional[NormalizedLineItem], float]:
        """Match by fuzzy description similarity (fallback matching method)
        
        Args:
            po_item: PO line item
            pi_items: List of PI line items to search
            threshold: Minimum similarity score (0-100)
            
        Returns:
            Tuple of (matched PI item or None, similarity score)
        """
        if not po_item.description:
            return None, 0.0
        
        po_desc = po_item.description.strip().lower()
        best_match = None
        best_score = 0.0
        
        for pi_item in pi_items:
            if pi_item.description:
                pi_desc = pi_item.description.strip().lower()
                
                # Use token_sort_ratio for better matching with word order variations
                score = fuzz.token_sort_ratio(po_desc, pi_desc)
                
                if score > best_score and score >= threshold:
                    best_score = score
                    best_match = pi_item
        
        return best_match, best_score
