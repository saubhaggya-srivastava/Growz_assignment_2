"""JSON report generator"""

import json
from decimal import Decimal
from typing import Any, Dict
from .base import ReportGenerator
from ..models import ComparisonResult


class JSONReportGenerator(ReportGenerator):
    """Generate reports in JSON format"""
    
    def generate(self, comparison: ComparisonResult, output_path: str) -> None:
        """Generate JSON report
        
        Args:
            comparison: ComparisonResult with discrepancies and summary
            output_path: Path where JSON file should be saved
        """
        report_data = self._build_report_data(comparison)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=self._json_serializer)
    
    def _build_report_data(self, comparison: ComparisonResult) -> Dict[str, Any]:
        """Build report data structure
        
        Args:
            comparison: ComparisonResult
            
        Returns:
            Dictionary with report data
        """
        report = {}
        
        # Summary
        if self.config.include_summary:
            report['summary'] = {
                'total_quantity_ordered': comparison.summary.total_quantity_ordered,
                'total_quantity_invoiced': comparison.summary.total_quantity_invoiced,
                'quantity_difference': comparison.summary.quantity_difference,
                'total_value_ordered': str(comparison.summary.total_value_ordered),
                'total_value_invoiced': str(comparison.summary.total_value_invoiced),
                'value_difference': str(comparison.summary.value_difference),
                'items_with_discrepancies': comparison.summary.items_with_discrepancies,
                'total_items_compared': len(comparison.discrepancies)
            }
        
        # Discrepancies
        if self.config.include_matched_items:
            report['discrepancies'] = []
            for disc in comparison.discrepancies:
                # Calculate alert severity
                alert_severity = None
                if disc.has_discrepancy and disc.po_item.total_value and disc.total_value_diff:
                    percent_diff = abs(float(disc.total_value_diff / disc.po_item.total_value)) * 100
                    if percent_diff >= 5.0:
                        alert_severity = 'high'
                    else:
                        alert_severity = 'low'
                
                item_data = {
                    'po_item': {
                        'sku': disc.po_item.sku,
                        'description': disc.po_item.description,
                        'quantity': disc.po_item.quantity,
                        'unit_price': str(disc.po_item.unit_price) if disc.po_item.unit_price else None,
                        'total_value': str(disc.po_item.total_value) if disc.po_item.total_value else None,
                    },
                    'pi_item': {
                        'sku': disc.pi_item.sku,
                        'description': disc.pi_item.description,
                        'quantity': disc.pi_item.quantity,
                        'unit_price': str(disc.pi_item.unit_price) if disc.pi_item.unit_price else None,
                        'total_value': str(disc.pi_item.total_value) if disc.pi_item.total_value else None,
                    },
                    'differences': {
                        'quantity_diff': disc.quantity_diff,
                        'unit_price_diff': str(disc.unit_price_diff) if disc.unit_price_diff else None,
                        'total_value_diff': str(disc.total_value_diff) if disc.total_value_diff else None,
                    },
                    'has_discrepancy': disc.has_discrepancy,
                    'has_quantity_mismatch': disc.has_quantity_mismatch,
                    'has_price_mismatch': disc.has_price_mismatch,
                    'alert_severity': alert_severity
                }
                
                if self.config.highlight_discrepancies:
                    if disc.has_discrepancy:
                        item_data['flagged'] = True
                
                report['discrepancies'].append(item_data)
        
        # Alerts
        if self.config.include_alerts:
            report['alerts'] = [
                {
                    'severity': alert.severity,
                    'message': alert.message,
                    'suggested_action': alert.suggested_action,
                    'related_item': alert.related_item
                }
                for alert in comparison.alerts
            ]
        
        return report
    
    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for special types
        
        Args:
            obj: Object to serialize
            
        Returns:
            Serializable representation
        """
        if isinstance(obj, Decimal):
            return str(obj)
        raise TypeError(f"Type {type(obj)} not serializable")
