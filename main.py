"""Main entry point for PDF comparison system"""

import sys
import argparse
from pathlib import Path
from src.pdf_comparison import PDFComparison


def main():
    """Main function to run PDF comparison"""
    parser = argparse.ArgumentParser(
        description='PDF Data Extraction and Comparison System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare two PDFs
  python main.py compare po.pdf invoice.pdf -o output/
  
  # Compare with custom fuzzy threshold
  python main.py compare po.pdf invoice.pdf -o output/ --threshold 85
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare a PO with a PI')
    compare_parser.add_argument('po_file', help='Path to Purchase Order PDF')
    compare_parser.add_argument('pi_file', help='Path to Proforma Invoice PDF')
    compare_parser.add_argument('-o', '--output', default='output', help='Output directory for reports')
    compare_parser.add_argument('--threshold', type=float, default=80.0, help='Fuzzy matching threshold (0-100)')
    compare_parser.add_argument('--filename', default='comparison_report', help='Base filename for reports')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'compare':
        print("PDF Data Extraction and Comparison System")
        print("=" * 50)
        print(f"Purchase Order: {args.po_file}")
        print(f"Proforma Invoice: {args.pi_file}")
        print(f"Output Directory: {args.output}")
        print(f"Fuzzy Threshold: {args.threshold}")
        print("=" * 50)
        
        # Initialize comparison system
        config = {
            'fuzzy_threshold': args.threshold
        }
        pdf_comp = PDFComparison(config)
        
        try:
            # Run comparison and generate reports
            result = pdf_comp.compare_and_report(
                args.po_file,
                args.pi_file,
                args.output,
                args.filename
            )
            
            # Print summary
            print("\n" + "=" * 50)
            print("COMPARISON SUMMARY")
            print("=" * 50)
            summary = result['comparison'].summary
            print(f"Total Quantity Ordered: {summary.total_quantity_ordered}")
            print(f"Total Quantity Invoiced: {summary.total_quantity_invoiced}")
            print(f"Quantity Difference: {summary.quantity_difference}")
            print(f"Total Value Ordered: ${summary.total_value_ordered:.2f}")
            print(f"Total Value Invoiced: ${summary.total_value_invoiced:.2f}")
            print(f"Value Difference: ${summary.value_difference:.2f}")
            print(f"Items with Discrepancies: {summary.items_with_discrepancies}")
            
            # Print alerts
            alerts = result['comparison'].alerts
            if alerts:
                print("\n" + "=" * 50)
                print(f"ALERTS ({len(alerts)})")
                print("=" * 50)
                for alert in alerts[:5]:  # Show first 5
                    print(f"[{alert.severity.upper()}] {alert.message}")
                if len(alerts) > 5:
                    print(f"... and {len(alerts) - 5} more alerts")
            
            # Print generated reports
            print("\n" + "=" * 50)
            print("GENERATED REPORTS")
            print("=" * 50)
            for format_type, file_path in result['reports'].items():
                print(f"{format_type.upper()}: {file_path}")
            
            print("\n✓ Comparison completed successfully!")
            
        except Exception as e:
            print(f"\n✗ Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
