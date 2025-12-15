"""Extraction strategy that tries pdfplumber first, then falls back to PyPDF2"""

from typing import List
from ..models import ExtractedDocument, DocumentMetadata, RawLineItem
from .pdfplumber_extractor import PdfPlumberExtractor
from .pypdf2_extractor import PyPDF2Extractor


class ExtractionStrategy:
    """Strategy for extracting data from PDFs with fallback"""
    
    def __init__(self):
        self.primary_extractor = PdfPlumberExtractor()
        self.fallback_extractor = PyPDF2Extractor()
    
    def extract(self, pdf_path: str) -> ExtractedDocument:
        """Extract data from PDF using primary method with fallback
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            ExtractedDocument with data and metadata
        """
        errors = []
        extraction_method = "pdfplumber"
        
        # Try primary extractor (pdfplumber)
        try:
            metadata_dict = self.primary_extractor.extract_metadata(pdf_path)
            line_items_dict = self.primary_extractor.extract_line_items(pdf_path)
            
            # If we got no line items, try fallback
            if not line_items_dict:
                errors.append("pdfplumber: No line items extracted, trying fallback")
                extraction_method = "PyPDF2"
                line_items_dict = self.fallback_extractor.extract_line_items(pdf_path)
                
                # If fallback also fails for metadata, try it
                if not metadata_dict.get("document_number"):
                    metadata_dict = self.fallback_extractor.extract_metadata(pdf_path)
        
        except Exception as e:
            errors.append(f"pdfplumber failed: {str(e)}, trying fallback")
            extraction_method = "PyPDF2"
            
            # Try fallback extractor
            try:
                metadata_dict = self.fallback_extractor.extract_metadata(pdf_path)
                line_items_dict = self.fallback_extractor.extract_line_items(pdf_path)
            except Exception as fallback_error:
                errors.append(f"PyPDF2 also failed: {str(fallback_error)}")
                metadata_dict = {
                    "document_number": None,
                    "date": None,
                    "vendor_name": None,
                    "total_amount": None
                }
                line_items_dict = []
        
        # Convert to data models
        metadata = DocumentMetadata(
            document_number=metadata_dict.get("document_number"),
            date=metadata_dict.get("date"),
            vendor_name=metadata_dict.get("vendor_name"),
            total_amount=metadata_dict.get("total_amount")
        )
        
        line_items = [
            RawLineItem(
                sku=item.get("sku"),
                description=item.get("description", ""),
                quantity=item.get("quantity"),
                unit_price=item.get("unit_price"),
                total_value=item.get("total_value"),
                row_number=item.get("row_number", 0)
            )
            for item in line_items_dict
        ]
        
        return ExtractedDocument(
            metadata=metadata,
            line_items=line_items,
            extraction_method=extraction_method,
            errors=errors
        )
