"""CSV report generator"""

import pandas as pd
from .base import ReportGenerator
from ..models import ComparisonResult


class CSVReportGenerator(ReportGenerator):
    """Generate reports in CSV format"""
    
    def generate(self, comparison: ComparisonResult, output_path: str) -> None:
        """Generate CSV report
        
        Args:
            comparison: ComparisonResult with discrepancies and summary
            output_path: Path where CSV file should be saved
        """
        # Build rows for discrepancies
        rows = []
        
        for disc in comparison.discrepancies:
            # Calculate alert severity
            alert_severity = ''
            if disc.has_discrepancy and disc.po_item.total_value and disc.total_value_diff:
                percent_diff = abs(float(disc.total_value_diff / disc.po_item.total_value)) * 100
                if percent_diff >= 5.0:
                    alert_severity = 'HIGH'
                else:
                    alert_severity = 'LOW'
            
            row = {
                'PO_SKU': disc.po_item.sku or '',
                'PO_Description': disc.po_item.description,
                'PO_Quantity': disc.po_item.quantity,
                'PO_Unit_Price': float(disc.po_item.unit_price) if disc.po_item.unit_price else None,
                'PO_Total_Value': float(disc.po_item.total_value) if disc.po_item.total_value else None,
                'PI_SKU': disc.pi_item.sku or '',
                'PI_Description': disc.pi_item.description,
                'PI_Quantity': disc.pi_item.quantity,
                'PI_Unit_Price': float(disc.pi_item.unit_price) if disc.pi_item.unit_price else None,
                'PI_Total_Value': float(disc.pi_item.total_value) if disc.pi_item.total_value else None,
                'Quantity_Difference': disc.quantity_diff,
                'Unit_Price_Difference': float(disc.unit_price_diff) if disc.unit_price_diff else None,
                'Total_Value_Difference': float(disc.total_value_diff) if disc.total_value_diff else None,
                'Has_Discrepancy': disc.has_discrepancy,
                'Has_Quantity_Mismatch': disc.has_quantity_mismatch,
                'Has_Price_Mismatch': disc.has_price_mismatch,
                'Alert_Severity': alert_severity
            }
            rows.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(rows)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
