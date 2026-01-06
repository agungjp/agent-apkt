"""SE004 Rolling dataset implementation."""

from typing import List, Optional

from ...models import DownloadedFile, ParsedData
from ...workspace import RunContext
from ..base import BaseDataset, RunResult


class SE004RollingDataset(BaseDataset):
    """SE004 Rolling dataset handler."""
    
    name = "se004_rolling"
    description = "SAIDI/SAIFI Rolling Report"
    
    def run(self, ctx: RunContext) -> RunResult:
        """Run SE004 Rolling extraction (stub)."""
        self.logger.info(f"Running SE004 Rolling for period {ctx.period_ym} (stub)")
        return RunResult(
            success=True,
            message=f"SE004 Rolling extraction completed (stub) - period {ctx.period_ym}",
            files_downloaded=[],
            rows_parsed=0,
        )
    
    async def extract(
        self,
        ctx: RunContext,
        period_ym: str,
        unit_text: Optional[str] = None,
    ) -> List[DownloadedFile]:
        """Extract SE004 Rolling data.
        
        Args:
            ctx: Run context
            period_ym: Period in YYYYMM format
            unit_text: Optional unit text
            
        Returns:
            List of downloaded files
        """
        # TODO: Implement extraction logic
        return []
    
    async def parse(
        self,
        files: List[DownloadedFile],
        ctx: RunContext,
    ) -> ParsedData:
        """Parse SE004 Rolling files.
        
        Args:
            files: List of files to parse
            ctx: Run context
            
        Returns:
            Parsed data
        """
        # TODO: Implement parsing logic
        return ParsedData(
            dataset=self.name,
            period_ym=ctx.period_ym,
            data=[],
            row_count=0,
        )
