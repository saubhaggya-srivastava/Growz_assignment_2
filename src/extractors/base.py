"""Abstract base class for PDF extractors"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any


class PDFExtractor(ABC):
    """Abstract base class for PDF extraction"""
    
    @abstractmethod
    def extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing metadata fields
        """
        pass
    
    @abstractmethod
    def extract_line_items(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract line items from PDF
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of dictionaries containing line item data
        """
        pass
