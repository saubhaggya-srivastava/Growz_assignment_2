"""PDF extraction using PyPDF2 library (fallback)"""

import re
from typing import Dict, List, Any
from PyPDF2 import PdfReader
from .base import PDFExtractor


class PyPDF2Extractor(PDFExtractor):
    """Extract data from PDFs using PyPDF2 (fallback method)"""
    
    def extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF using PyPDF2
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with metadata fields
        """
        metadata = {
            "document_number": None,
            "date": None,
            "vendor_name": None,
            "total_amount": None
        }
        
        try:
            reader = PdfReader(pdf_path)
            
            if not reader.pages:
                return metadata
            
            # Extract text from first page
            first_page = reader.pages[0]
            text = first_page.extract_text()
            
            if text:
                # Extract document number
                po_match = re.search(r'(?:PO|Purchase Order|Order)\s*#?\s*:?\s*(\S+)', text, re.IGNORECASE)
                invoice_match = re.search(r'(?:Invoice|Proforma)\s*#?\s*:?\s*(\S+)', text, re.IGNORECASE)
                
                if po_match:
                    metadata["document_number"] = po_match.group(1)
                elif invoice_match:
                    metadata["document_number"] = invoice_match.group(1)
                
                # Extract date
                date_match = re.search(r'Date\s*:?\s*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
                if date_match:
                    metadata["date"] = date_match.group(1)
                
                # Extract vendor name
                vendor_match = re.search(r'(?:Vendor|Supplier|From)\s*:?\s*([^\n]+)', text, re.IGNORECASE)
                if vendor_match:
                    metadata["vendor_name"] = vendor_match.group(1).strip()
                
                # Extract total amount
                total_match = re.search(r'(?:Total|Grand Total)\s*:?\s*\$?\s*([\d,]+\.?\d*)', text, re.IGNORECASE)
                if total_match:
                    try:
                        metadata["total_amount"] = float(total_match.group(1).replace(',', ''))
                    except ValueError:
                        pass
        
        except Exception as e:
            print(f"Error extracting metadata with PyPDF2: {e}")
        
        return metadata
    
    def extract_line_items(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract line items from PDF using text-based extraction
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of dictionaries containing line item data
        """
        line_items = []
        
        try:
            reader = PdfReader(pdf_path)
            row_number = 0
            
            # Process all pages
            for page in reader.pages:
                text = page.extract_text()
                
                if not text:
                    continue
                
                # Try to extract line items using regex patterns
                # This is a simplified approach - looks for patterns like:
                # SKU Description Qty Price Total
                lines = text.split('\n')
                
                for line in lines:
                    # Skip empty lines and likely headers
                    if not line.strip() or any(keyword in line.lower() for keyword in ['description', 'quantity', 'price', 'total', 'item']):
                        continue
                    
                    # Try to parse line item pattern
                    # Pattern: optional SKU, description (text), quantity (number), price (number), total (number)
                    pattern = r'(\S+)?\s+(.+?)\s+(\d+(?:\.\d+)?)\s+\$?([\d,]+\.?\d*)\s+\$?([\d,]+\.?\d*)'
                    match = re.search(pattern, line)
                    
                    if match:
                        row_number += 1
                        sku, desc, qty, price, total = match.groups()
                        
                        item = {
                            "sku": sku if sku and not sku.isdigit() else None,
                            "description": desc.strip(),
                            "quantity": qty,
                            "unit_price": price,
                            "total_value": total,
                            "row_number": row_number
                        }
                        
                        line_items.append(item)
        
        except Exception as e:
            print(f"Error extracting line items with PyPDF2: {e}")
        
        return line_items
