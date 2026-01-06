"""CSV output writer."""

import csv
from pathlib import Path
from typing import Dict, Any, List

from ..logging_ import get_logger
from ..models import ParsedData


class CSVWriter:
    """Writes parsed data to CSV format."""
    
    def __init__(self, output_dir: Path):
        """Initialize CSV writer.
        
        Args:
            output_dir: Output directory for CSV files
        """
        self.logger = get_logger()
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def write(self, data: ParsedData, filename: str = None) -> Path:
        """Write parsed data to CSV.
        
        Args:
            data: Parsed data to write
            filename: Optional custom filename
            
        Returns:
            Path to written CSV file
        """
        if not filename:
            filename = f"{data.dataset}_{data.period_ym}.csv"
        
        output_path = self.output_dir / filename
        
        try:
            self.logger.info(f"Writing CSV: {output_path}")
            
            if not data.data:
                self.logger.warning("No data to write")
                return output_path
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data.columns or list(data.data[0].keys()))
                writer.writeheader()
                writer.writerows(data.data)
            
            self.logger.info(f"CSV written: {len(data.data)} rows")
            return output_path
        
        except Exception as e:
            self.logger.error(f"CSV write failed: {e}")
            raise
