"""Data normalization for extracted PDF data"""

import re
from decimal import Decimal, InvalidOperation
from typing import Optional, Any
from ..models import (
    ExtractedDocument,
    NormalizedDocument,
    RawLineItem,
    NormalizedLineItem,
)


class DataNormalizer:
    """Normalize and validate extracted data"""
    
    def normalize_document(self, extracted: ExtractedDocument) -> NormalizedDocument:
        """Normalize an extracted document
        
        Args:
            extracted: ExtractedDocument with raw data
            
        Returns:
            NormalizedDocument with cleaned and validated data
        """
        normalized_items = []
        validation_errors = []
        
        for raw_item in extracted.line_items:
            try:
                normalized_item = self.normalize_line_item(raw_item)
                normalized_items.append(normalized_item)
                
                # Collect validation errors
                if normalized_item.validation_errors:
                    validation_errors.extend([
                        f"Row {raw_item.row_number}: {error}"
                        for error in normalized_item.validation_errors
                    ])
            except Exception as e:
                validation_errors.append(f"Row {raw_item.row_number}: Failed to normalize - {str(e)}")
        
        return NormalizedDocument(
            metadata=extracted.metadata,
            line_items=normalized_items,
            validation_errors=validation_errors
        )
    
    def normalize_line_item(self, raw_item: RawLineItem) -> NormalizedLineItem:
        """Normalize a single line item
        
        Args:
            raw_item: RawLineItem with raw data
            
        Returns:
            NormalizedLineItem with normalized data
        """
        errors = []
        
        # Normalize description
        description = self.normalize_description(raw_item.description)
        
        # Parse quantity
        quantity = self.parse_quantity(raw_item.quantity)
        if quantity is None and raw_item.quantity is not None:
            errors.append(f"Invalid quantity: {raw_item.quantity}")
        
        # Parse unit price
        unit_price = self.parse_price(raw_item.unit_price)
        if unit_price is None and raw_item.unit_price is not None:
            errors.append(f"Invalid unit price: {raw_item.unit_price}")
        
        # Parse total value
        total_value = self.parse_price(raw_item.total_value)
        if total_value is None and raw_item.total_value is not None:
            errors.append(f"Invalid total value: {raw_item.total_value}")
        
        # Validate required fields
        is_valid = True
        if not description:
            errors.append("Missing description")
            is_valid = False
        if quantity is None:
            errors.append("Missing or invalid quantity")
            is_valid = False
        if unit_price is None:
            errors.append("Missing or invalid unit price")
            is_valid = False
        
        return NormalizedLineItem(
            sku=raw_item.sku,
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            total_value=total_value,
            row_number=raw_item.row_number,
            is_valid=is_valid,
            validation_errors=errors
        )
    
    def parse_quantity(self, value: Any) -> Optional[float]:
        """Convert quantity value to float
        
        Args:
            value: Raw quantity value
            
        Returns:
            Float value or None if parsing fails
        """
        if value is None:
            return None
        
        # If already a number
        if isinstance(value, (int, float)):
            return float(value)
        
        # Convert to string and clean
        value_str = str(value).strip()
        
        if not value_str or value_str.upper() in ['N/A', 'TBD', 'PENDING', '']:
            return None
        
        # Remove common formatting
        value_str = value_str.replace(',', '')
        
        try:
            return float(value_str)
        except (ValueError, TypeError):
            return None
    
    def parse_price(self, value: Any) -> Optional[Decimal]:
        """Convert price value to Decimal with 2 decimal places
        
        Args:
            value: Raw price value
            
        Returns:
            Decimal value with 2 decimal places or None if parsing fails
        """
        if value is None:
            return None
        
        # If already a Decimal
        if isinstance(value, Decimal):
            return value.quantize(Decimal('0.01'))
        
        # If a number
        if isinstance(value, (int, float)):
            return Decimal(str(value)).quantize(Decimal('0.01'))
        
        # Convert to string and clean
        value_str = str(value).strip()
        
        if not value_str or value_str.upper() in ['N/A', 'TBD', 'PENDING', '']:
            return None
        
        # Remove currency symbols and common formatting
        value_str = value_str.replace('$', '').replace('€', '').replace('£', '')
        value_str = value_str.replace(',', '')
        value_str = value_str.strip()
        
        try:
            return Decimal(value_str).quantize(Decimal('0.01'))
        except (ValueError, TypeError, InvalidOperation):
            return None
    
    def normalize_description(self, text: str) -> str:
        """Normalize description text while preserving meaningful characters
        
        Removes leading/trailing whitespace, collapses multiple spaces,
        removes non-semantic formatting artifacts, but preserves meaningful
        characters like hyphens, numbers, and alphanumerics (e.g., "USB-C", "7-in-1", "1080p")
        
        Args:
            text: Raw description text
            
        Returns:
            Normalized description string
        """
        if not text:
            return ""
        
        # Convert to string if not already
        text = str(text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Collapse multiple spaces to single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove non-semantic formatting artifacts (like excessive punctuation)
        # but preserve meaningful characters: letters, numbers, hyphens, spaces, common punctuation
        # This preserves "USB-C", "7-in-1", "1080p", etc.
        text = re.sub(r'[^\w\s\-.,()&/]', '', text)
        
        # Clean up any double spaces that might have been created
        text = re.sub(r'\s+', ' ', text)
        
        # Final trim
        text = text.strip()
        
        return text
