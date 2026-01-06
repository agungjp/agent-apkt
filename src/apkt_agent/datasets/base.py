"""Base dataset class."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from ..errors import DatasetError
from ..logging_ import get_logger
from ..models import DownloadedFile, ParsedData
from ..workspace import RunContext


@dataclass
class RunResult:
    """Result from a dataset run."""
    success: bool
    message: str
    files_downloaded: List[str] = None
    rows_parsed: int = 0
    parsed_csv_path: Optional[str] = None
    validation_warnings: List[str] = None
    
    def __post_init__(self):
        if self.files_downloaded is None:
            self.files_downloaded = []
        if self.validation_warnings is None:
            self.validation_warnings = []


class BaseDataset(ABC):
    """Base class for all datasets."""
    
    name: str = ""
    description: str = ""
    
    def __init__(self, config):
        """Initialize dataset.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = get_logger()
    
    def run(self, ctx: RunContext) -> RunResult:
        """Run the dataset extraction and parsing.
        
        Args:
            ctx: Run context
            
        Returns:
            RunResult with status and details
        """
        self.logger.info(f"Running dataset: {self.name}")
        self.logger.info(f"Period: {ctx.period_ym}, Snapshot: {ctx.snapshot_date}")
        
        # Stub implementation - to be overridden or extended
        return RunResult(
            success=True,
            message=f"Dataset {self.name} run completed (stub)",
            files_downloaded=[],
            rows_parsed=0,
        )
    
    @abstractmethod
    async def extract(
        self,
        ctx: RunContext,
        period_ym: str,
        unit_text: Optional[str] = None,
    ) -> List[DownloadedFile]:
        """Extract data for the dataset.
        
        Args:
            ctx: Run context
            period_ym: Period in YYYYMM format
            unit_text: Optional unit text
            
        Returns:
            List of downloaded files
        """
        pass
    
    @abstractmethod
    async def parse(
        self,
        files: List[DownloadedFile],
        ctx: RunContext,
    ) -> ParsedData:
        """Parse downloaded files.
        
        Args:
            files: List of files to parse
            ctx: Run context
            
        Returns:
            Parsed data
        """
        pass
