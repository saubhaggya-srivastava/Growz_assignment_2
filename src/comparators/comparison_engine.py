"""Comparison engine for calculating discrepancies and generating alerts"""

from decimal import Decimal
from typing import List
from ..models import (
    MatchResult,
    MatchedPair,
    ComparisonResult,
    Discrepancy,
    ComparisonSummary,
    Alert,
)


class ComparisonEngine:
    """Calculate discrepancies and generate alerts for matched items"""
    
    def compare(self, match_result: MatchResult) -> ComparisonResult:
        """Compare matched items and generate comprehensive results
        
        Args:
            match_result: Result from item matching
            
        Returns:
            ComparisonResult with discrepancies, summary, and alerts
        """
        discrepancies = []
        alerts = []
        
        # Calculate discrepancies for each matched pair
        for pair in match_result.matched_pairs:
            discrepancy = self.calculate_discrepancy(pair)
            discrepancies.append(discrepancy)
            
            # Generate alerts for this discrepancy
            item_alerts = self.generate_alerts(discrepancy)
            alerts.extend(item_alerts)
        
        # Calculate summary statistics
        summary = self._calculate_summary(match_result, discrepancies)
        
        return ComparisonResult(
            discrepancies=discrepancies,
            summary=summary,
            alerts=alerts
        )
    
    def calculate_discrepancy(self, pair: MatchedPair) -> Discrepancy:
        """Calculate discrepancies between matched PO and PI items
        
        Args:
            pair: Matched pair of PO and PI items
            
        Returns:
            Discrepancy with calculated differences
        """
        po_item = pair.po_item
        pi_item = pair.pi_item
        
        # Calculate quantity difference
        quantity_diff = None
        if po_item.quantity is not None and pi_item.quantity is not None:
            quantity_diff = pi_item.quantity - po_item.quantity
        
        # Calculate unit price difference
        unit_price_diff = None
        if po_item.unit_price is not None and pi_item.unit_price is not None:
            unit_price_diff = pi_item.unit_price - po_item.unit_price
        
        # Calculate total value difference
        total_value_diff = None
        if po_item.total_value is not None and pi_item.total_value is not None:
            total_value_diff = pi_item.total_value - po_item.total_value
        
        # Flag mismatches
        has_quantity_mismatch = quantity_diff is not None and quantity_diff != 0
        has_price_mismatch = (
            unit_price_diff is not None and 
            abs(unit_price_diff) > Decimal('0.01')
        )
        
        # Flag ANY financial discrepancy (separate from alert thresholds)
        has_discrepancy = (
            total_value_diff is not None and 
            abs(total_value_diff) > Decimal('0.01')
        )
        
        return Discrepancy(
            po_item=po_item,
            pi_item=pi_item,
            quantity_diff=quantity_diff,
            unit_price_diff=unit_price_diff,
            total_value_diff=total_value_diff,
            has_quantity_mismatch=has_quantity_mismatch,
            has_price_mismatch=has_price_mismatch,
            has_discrepancy=has_discrepancy
        )
    
    def generate_alerts(self, discrepancy: Discrepancy) -> List[Alert]:
        """Generate alerts for a discrepancy based on severity rules
        
        Alerts are only generated when differences exceed thresholds.
        Small discrepancies (<5%) are tracked but don't generate alerts.
        
        Args:
            discrepancy: Discrepancy to analyze
            
        Returns:
            List of alerts
        """
        alerts = []
        po_item = discrepancy.po_item
        pi_item = discrepancy.pi_item
        
        item_desc = po_item.description[:50] if po_item.description else "Unknown item"
        
        # High-severity quantity alert (>10% difference)
        if discrepancy.quantity_diff is not None and po_item.quantity:
            qty_percent = abs(discrepancy.quantity_diff / po_item.quantity) * 100
            if qty_percent > 10:
                alerts.append(Alert(
                    severity="high",
                    message=f"Quantity discrepancy of {discrepancy.quantity_diff:.2f} ({qty_percent:.1f}%) for '{item_desc}'",
                    suggested_action="Contact vendor to clarify quantity difference",
                    related_item=item_desc
                ))
        
        # High-severity price alert (>5% difference)
        if discrepancy.unit_price_diff is not None and po_item.unit_price:
            price_percent = abs(float(discrepancy.unit_price_diff / po_item.unit_price)) * 100
            if price_percent > 5:
                alerts.append(Alert(
                    severity="high",
                    message=f"Unit price discrepancy of ${discrepancy.unit_price_diff:.2f} ({price_percent:.1f}%) for '{item_desc}'",
                    suggested_action="Verify pricing with vendor and check for price changes",
                    related_item=item_desc
                ))
        
        # Critical alert for large total value discrepancy (>$1000)
        if discrepancy.total_value_diff is not None:
            if abs(discrepancy.total_value_diff) > Decimal('1000'):
                alerts.append(Alert(
                    severity="critical",
                    message=f"Large total value discrepancy of ${discrepancy.total_value_diff:.2f} for '{item_desc}'",
                    suggested_action="Immediate review required - contact vendor and verify order details",
                    related_item=item_desc
                ))
        
        # Low-severity alert for small total value discrepancies (>$0.01 but <5%)
        # This provides visibility without alert fatigue
        if discrepancy.has_discrepancy and not alerts:
            # Only add low alert if no high/critical alerts were generated
            if po_item.total_value and abs(discrepancy.total_value_diff) > Decimal('0.01'):
                value_percent = abs(float(discrepancy.total_value_diff / po_item.total_value)) * 100
                if value_percent < 5:
                    alerts.append(Alert(
                        severity="low",
                        message=f"Minor total value discrepancy of ${discrepancy.total_value_diff:.2f} ({value_percent:.2f}%) for '{item_desc}'",
                        suggested_action="Review during routine reconciliation",
                        related_item=item_desc
                    ))
        
        return alerts
    
    def _calculate_summary(
        self,
        match_result: MatchResult,
        discrepancies: List[Discrepancy]
    ) -> ComparisonSummary:
        """Calculate summary statistics
        
        Args:
            match_result: Matching results
            discrepancies: List of calculated discrepancies
            
        Returns:
            ComparisonSummary with totals and differences
        """
        total_qty_ordered = 0.0
        total_qty_invoiced = 0.0
        total_value_ordered = Decimal('0.00')
        total_value_invoiced = Decimal('0.00')
        items_with_discrepancies = 0
        
        for disc in discrepancies:
            # Sum quantities
            if disc.po_item.quantity is not None:
                total_qty_ordered += disc.po_item.quantity
            if disc.pi_item.quantity is not None:
                total_qty_invoiced += disc.pi_item.quantity
            
            # Sum values
            if disc.po_item.total_value is not None:
                total_value_ordered += disc.po_item.total_value
            if disc.pi_item.total_value is not None:
                total_value_invoiced += disc.pi_item.total_value
            
            # Count items with ANY financial discrepancy (not just those triggering alerts)
            if disc.has_discrepancy:
                items_with_discrepancies += 1
        
        return ComparisonSummary(
            total_quantity_ordered=total_qty_ordered,
            total_quantity_invoiced=total_qty_invoiced,
            total_value_ordered=total_value_ordered,
            total_value_invoiced=total_value_invoiced,
            quantity_difference=total_qty_invoiced - total_qty_ordered,
            value_difference=total_value_invoiced - total_value_ordered,
            items_with_discrepancies=items_with_discrepancies
        )
