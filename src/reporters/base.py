"""Abstract base class for report generators"""

from abc import ABC, abstractmethod
from ..models import ComparisonResult, ReportConfig


class ReportGenerator(ABC):
    """Abstract base class for generating reports"""
    
    def __init__(self, config: ReportConfig = None):
        """Initialize report generator
        
        Args:
            config: Report configuration
        """
        self.config = config or ReportConfig()
    
    @abstractmethod
    def generate(self, comparison: ComparisonResult, output_path: str) -> None:
        """Generate report from comparison results
        
        Args:
            comparison: ComparisonResult with discrepancies and summary
            output_path: Path where report should be saved
        """
        pass
