"""PDF extraction using pdfplumber library"""

import pdfplumber
import re
from typing import Dict, List, Any, Optional
from .base import PDFExtractor


class PdfPlumberExtractor(PDFExtractor):
    """Extract data from PDFs using pdfplumber (primary method)"""
    
    def extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF using pdfplumber
        
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
            with pdfplumber.open(pdf_path) as pdf:
                if not pdf.pages:
                    return metadata
                
                # Extract text from first page for metadata
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                
                if text:
                    # Extract document number (PO# or Invoice#)
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
            print(f"Error extracting metadata with pdfplumber: {e}")
        
        return metadata
    
    def extract_line_items(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract line items from PDF tables using pdfplumber
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of dictionaries containing line item data
        """
        line_items = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                row_number = 0
                
                # Process all pages
                for page in pdf.pages:
                    tables = page.extract_tables()
                    
                    if not tables:
                        continue
                    
                    for table in tables:
                        if not table or len(table) < 2:  # Need at least header + 1 row
                            continue
                        
                        # Try to identify columns
                        header = [str(cell).lower() if cell else "" for cell in table[0]]
                        
                        # Find column indices
                        sku_idx = self._find_column_index(header, ['sku', 'item', 'code', 'product code'])
                        desc_idx = self._find_column_index(header, ['description', 'item description', 'product'])
                        qty_idx = self._find_column_index(header, ['qty', 'quantity', 'qnty'])
                        price_idx = self._find_column_index(header, ['unit price', 'price', 'rate', 'unit cost'])
                        # Look for "Line Total" specifically (not "Line Subtotal")
                        # Try "line total" first, then fall back to just "total" if not found
                        total_idx = self._find_column_index(header, ['line total'])
                        if total_idx is None:
                            total_idx = self._find_column_index(header, ['total', 'amount'])
                        
                        # Process data rows (skip header)
                        for row in table[1:]:
                            if not row or all(cell is None or str(cell).strip() == '' for cell in row):
                                continue  # Skip empty rows
                            
                            row_number += 1
                            
                            item = {
                                "sku": self._get_cell_value(row, sku_idx),
                                "description": self._get_cell_value(row, desc_idx) or "",
                                "quantity": self._get_cell_value(row, qty_idx),
                                "unit_price": self._get_cell_value(row, price_idx),
                                "total_value": self._get_cell_value(row, total_idx),
                                "row_number": row_number
                            }
                            
                            # Only add if we have at least a description
                            if item["description"]:
                                line_items.append(item)
        
        except Exception as e:
            print(f"Error extracting line items with pdfplumber: {e}")
        
        return line_items
    
    def _find_column_index(self, header: List[str], keywords: List[str]) -> Optional[int]:
        """Find column index by matching keywords
        
        Args:
            header: List of header cell values
            keywords: List of keywords to search for
            
        Returns:
            Index of matching column or None
        """
        for idx, cell in enumerate(header):
            for keyword in keywords:
                if keyword in cell:
                    return idx
        return None
    
    def _get_cell_value(self, row: List[Any], index: Optional[int]) -> Any:
        """Safely get cell value from row
        
        Args:
            row: List of cell values
            index: Column index
            
        Returns:
            Cell value or None
        """
        if index is None or index >= len(row):
            return None
        return row[index]
