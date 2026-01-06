"""Data models for APKT Agent."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Dict, List


@dataclass
class DownloadedFile:
    """Represents a downloaded file."""
    
    filename: str
    path: str
    size: int
    downloaded_at: datetime = field(default_factory=datetime.now)
    md5: Optional[str] = None


@dataclass
class ParsedData:
    """Represents parsed data."""
    
    dataset: str
    period_ym: str
    data: List[Dict[str, Any]]
    parsed_at: datetime = field(default_factory=datetime.now)
    row_count: int = 0
    columns: List[str] = field(default_factory=list)


@dataclass
class RunReport:
    """Report from a run execution."""
    
    run_id: str
    dataset: str
    period_ym: str
    status: str  # "success", "partial", "failed"
    started_at: datetime
    completed_at: datetime
    downloads: List[DownloadedFile] = field(default_factory=list)
    parsed_data: Optional[ParsedData] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
