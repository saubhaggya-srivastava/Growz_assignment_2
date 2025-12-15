"""Core data models for PDF comparison system"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, List, Any


@dataclass
class DocumentMetadata:
    """Metadata extracted from a PDF document"""
    document_number: Optional[str] = None
    date: Optional[str] = None
    vendor_name: Optional[str] = None
    total_amount: Optional[float] = None


@dataclass
class RawLineItem:
    """Raw line item extracted from PDF before normalization"""
    sku: Optional[str] = None
    description: str = ""
    quantity: Any = None
    unit_price: Any = None
    total_value: Any = None
    row_number: int = 0


@dataclass
class NormalizedLineItem:
    """Normalized line item with validated and typed fields"""
    sku: Optional[str] = None
    description: str = ""
    quantity: Optional[float] = None
    unit_price: Optional[Decimal] = None
    total_value: Optional[Decimal] = None
    row_number: int = 0
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class ExtractedDocument:
    """Document with extracted raw data"""
    metadata: DocumentMetadata
    line_items: List[RawLineItem]
    extraction_method: str = ""
    errors: List[str] = field(default_factory=list)


@dataclass
class NormalizedDocument:
    """Document with normalized and validated data"""
    metadata: DocumentMetadata
    line_items: List[NormalizedLineItem]
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class MatchedPair:
    """A pair of matched line items from PO and PI"""
    po_item: NormalizedLineItem
    pi_item: NormalizedLineItem
    match_type: str  # "sku", "exact_description", or "fuzzy"
    match_score: float = 1.0


@dataclass
class MatchStatistics:
    """Statistics about the matching process"""
    total_po_items: int = 0
    total_pi_items: int = 0
    matched_count: int = 0
    unmatched_po_count: int = 0
    unmatched_pi_count: int = 0


@dataclass
class MatchResult:
    """Result of matching line items between two documents"""
    matched_pairs: List[MatchedPair] = field(default_factory=list)
    unmatched_po_items: List[NormalizedLineItem] = field(default_factory=list)
    unmatched_pi_items: List[NormalizedLineItem] = field(default_factory=list)
    match_statistics: MatchStatistics = field(default_factory=MatchStatistics)


@dataclass
class Discrepancy:
    """Discrepancy between matched PO and PI line items"""
    po_item: NormalizedLineItem
    pi_item: NormalizedLineItem
    quantity_diff: Optional[float] = None
    unit_price_diff: Optional[Decimal] = None
    total_value_diff: Optional[Decimal] = None
    has_quantity_mismatch: bool = False
    has_price_mismatch: bool = False
    has_discrepancy: bool = False  # True if ANY financial difference exists (>$0.01)


@dataclass
class ComparisonSummary:
    """Summary statistics for the comparison"""
    total_quantity_ordered: float = 0.0
    total_quantity_invoiced: float = 0.0
    total_value_ordered: Decimal = Decimal("0.00")
    total_value_invoiced: Decimal = Decimal("0.00")
    quantity_difference: float = 0.0
    value_difference: Decimal = Decimal("0.00")
    items_with_discrepancies: int = 0


@dataclass
class Alert:
    """Alert generated for a discrepancy"""
    severity: str  # "low", "medium", "high", "critical"
    message: str = ""
    suggested_action: str = ""
    related_item: str = ""


@dataclass
class ComparisonResult:
    """Complete result of comparing two documents"""
    discrepancies: List[Discrepancy] = field(default_factory=list)
    summary: ComparisonSummary = field(default_factory=ComparisonSummary)
    alerts: List[Alert] = field(default_factory=list)


@dataclass
class ReportConfig:
    """Configuration for report generation"""
    include_matched_items: bool = True
    include_unmatched_items: bool = True
    include_summary: bool = True
    include_alerts: bool = True
    highlight_discrepancies: bool = True
