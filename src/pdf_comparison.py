"""Main PDF comparison orchestration"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from .extractors import ExtractionStrategy
from .normalizers import DataNormalizer
from .matchers import ItemMatcher
from .comparators import ComparisonEngine
from .reporters import JSONReportGenerator, CSVReportGenerator, ExcelReportGenerator
from .models import ComparisonResult, ReportConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PDFComparison:
    """Main class for orchestrating PDF comparison"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize PDF comparison system
        
        Args:
            config: Configuration dictionary with optional settings:
                - fuzzy_threshold: Threshold for fuzzy matching (default: 80.0)
                - report_config: ReportConfig instance
        """
        self.config = config or {}
        
        # Initialize components
        self.extractor = ExtractionStrategy()
        self.normalizer = DataNormalizer()
        self.matcher = ItemMatcher(
            fuzzy_threshold=self.config.get('fuzzy_threshold', 80.0)
        )
        self.comparator = ComparisonEngine()
        
        # Report configuration
        self.report_config = self.config.get('report_config', ReportConfig())
    
    def compare_documents(
        self,
        po_path: str,
        pi_path: str
    ) -> ComparisonResult:
        """Compare a purchase order with a proforma invoice
        
        Args:
            po_path: Path to purchase order PDF
            pi_path: Path to proforma invoice PDF
            
        Returns:
            ComparisonResult with discrepancies and summary
        """
        logger.info(f"Starting comparison: PO={po_path}, PI={pi_path}")
        
        try:
            # Extract data from PDFs
            logger.info("Extracting data from purchase order...")
            po_extracted = self.extractor.extract(po_path)
            logger.info(f"Extracted {len(po_extracted.line_items)} items from PO using {po_extracted.extraction_method}")
            
            logger.info("Extracting data from proforma invoice...")
            pi_extracted = self.extractor.extract(pi_path)
            logger.info(f"Extracted {len(pi_extracted.line_items)} items from PI using {pi_extracted.extraction_method}")
            
            # Normalize data
            logger.info("Normalizing extracted data...")
            po_normalized = self.normalizer.normalize_document(po_extracted)
            pi_normalized = self.normalizer.normalize_document(pi_extracted)
            
            # Log validation errors
            if po_normalized.validation_errors:
                logger.warning(f"PO validation errors: {len(po_normalized.validation_errors)}")
            if pi_normalized.validation_errors:
                logger.warning(f"PI validation errors: {len(pi_normalized.validation_errors)}")
            
            # Match items
            logger.info("Matching line items...")
            match_result = self.matcher.match_items(
                po_normalized.line_items,
                pi_normalized.line_items
            )
            logger.info(f"Matched {match_result.match_statistics.matched_count} items")
            logger.info(f"Unmatched PO items: {match_result.match_statistics.unmatched_po_count}")
            logger.info(f"Unmatched PI items: {match_result.match_statistics.unmatched_pi_count}")
            
            # Compare and generate results
            logger.info("Calculating discrepancies...")
            comparison_result = self.comparator.compare(match_result)
            logger.info(f"Found {comparison_result.summary.items_with_discrepancies} items with discrepancies")
            logger.info(f"Generated {len(comparison_result.alerts)} alerts")
            
            logger.info("Comparison completed successfully")
            return comparison_result
        
        except Exception as e:
            logger.error(f"Error during comparison: {str(e)}", exc_info=True)
            raise
    
    def generate_reports(
        self,
        comparison: ComparisonResult,
        output_dir: str,
        base_filename: str = "comparison_report"
    ) -> Dict[str, str]:
        """Generate reports in multiple formats
        
        Args:
            comparison: ComparisonResult to report
            output_dir: Directory where reports should be saved
            base_filename: Base name for report files
            
        Returns:
            Dictionary mapping format to file path
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        generated_files = {}
        
        try:
            # Generate JSON report
            json_path = output_path / f"{base_filename}.json"
            logger.info(f"Generating JSON report: {json_path}")
            json_reporter = JSONReportGenerator(self.report_config)
            json_reporter.generate(comparison, str(json_path))
            generated_files['json'] = str(json_path)
            logger.info("JSON report generated successfully")
        except Exception as e:
            logger.error(f"Failed to generate JSON report: {e}")
        
        try:
            # Generate CSV report
            csv_path = output_path / f"{base_filename}.csv"
            logger.info(f"Generating CSV report: {csv_path}")
            csv_reporter = CSVReportGenerator(self.report_config)
            csv_reporter.generate(comparison, str(csv_path))
            generated_files['csv'] = str(csv_path)
            logger.info("CSV report generated successfully")
        except Exception as e:
            logger.error(f"Failed to generate CSV report: {e}")
        
        try:
            # Generate Excel report
            excel_path = output_path / f"{base_filename}.xlsx"
            logger.info(f"Generating Excel report: {excel_path}")
            excel_reporter = ExcelReportGenerator(self.report_config)
            excel_reporter.generate(comparison, str(excel_path))
            generated_files['excel'] = str(excel_path)
            logger.info("Excel report generated successfully")
        except Exception as e:
            logger.error(f"Failed to generate Excel report: {e}")
        
        return generated_files
    
    def compare_and_report(
        self,
        po_path: str,
        pi_path: str,
        output_dir: str,
        base_filename: str = "comparison_report"
    ) -> Dict[str, Any]:
        """Complete workflow: compare documents and generate reports
        
        Args:
            po_path: Path to purchase order PDF
            pi_path: Path to proforma invoice PDF
            output_dir: Directory where reports should be saved
            base_filename: Base name for report files
            
        Returns:
            Dictionary with comparison results and generated file paths
        """
        # Compare documents
        comparison = self.compare_documents(po_path, pi_path)
        
        # Generate reports
        report_files = self.generate_reports(comparison, output_dir, base_filename)
        
        return {
            'comparison': comparison,
            'reports': report_files
        }
    
    def batch_compare(
        self,
        document_pairs: list[tuple[str, str]],
        output_dir: str
    ) -> list[Dict[str, Any]]:
        """Process multiple document pairs in batch
        
        Args:
            document_pairs: List of (po_path, pi_path) tuples
            output_dir: Directory where reports should be saved
            
        Returns:
            List of results for each pair
        """
        results = []
        
        for idx, (po_path, pi_path) in enumerate(document_pairs, 1):
            logger.info(f"Processing pair {idx}/{len(document_pairs)}")
            
            try:
                base_filename = f"comparison_report_{idx}"
                result = self.compare_and_report(po_path, pi_path, output_dir, base_filename)
                result['status'] = 'success'
                result['pair_index'] = idx
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process pair {idx}: {e}")
                results.append({
                    'status': 'failed',
                    'pair_index': idx,
                    'po_path': po_path,
                    'pi_path': pi_path,
                    'error': str(e)
                })
        
        logger.info(f"Batch processing complete: {len([r for r in results if r['status'] == 'success'])}/{len(document_pairs)} successful")
        return results
