"""File download handling for APKT data."""

import time
from pathlib import Path
from typing import Callable, Optional

from playwright.sync_api import Page, Download

from ..errors import ApktDownloadError, BrowserError
from ..logging_ import get_logger
from ..workspace import RunContext


def download_excel(
    page: Page,
    ctx: RunContext,
    click_export_fn: Callable[[], None],
    target_filename: str,
    max_attempts: int = 3,
) -> Path:
    """Download an Excel file with retry logic.
    
    Args:
        page: Playwright page instance
        ctx: Run context with download directory info
        click_export_fn: Function to click export button (will be called to trigger download)
        target_filename: Target filename to save as (e.g., "se004_kumulatif_202512_WIL_ACEH.xlsx")
        max_attempts: Maximum number of download attempts
        
    Returns:
        Path to the downloaded file
        
    Raises:
        ApktDownloadError: If download fails after all attempts
    """
    logger = get_logger()
    
    # Backoff delays in seconds
    backoff_delays = [2, 5, 10]
    
    target_path = ctx.excel_dir / target_filename
    
    for attempt in range(1, max_attempts + 1):
        logger.info(f"Download attempt {attempt}/{max_attempts} for {target_filename}")
        
        try:
            # Use expect_download to capture the download
            with page.expect_download(timeout=60000) as download_info:
                # Trigger the download by clicking export button
                click_export_fn()
            
            download: Download = download_info.value
            
            # Log download info
            logger.info(f"Download started: {download.suggested_filename}")
            
            # Save to target path
            download.save_as(target_path)
            
            # Verify file exists and has content
            if not target_path.exists():
                raise ApktDownloadError(f"Downloaded file not found: {target_path}")
            
            file_size = target_path.stat().st_size
            if file_size == 0:
                raise ApktDownloadError(f"Downloaded file is empty: {target_path}")
            
            logger.info(f"Download successful: {target_path} ({file_size} bytes)")
            return target_path
            
        except Exception as e:
            logger.warning(f"Download attempt {attempt} failed: {e}")
            
            # Take screenshot on failure
            screenshot_path = ctx.logs_dir / f"download_fail_attempt_{attempt}.png"
            try:
                page.screenshot(path=str(screenshot_path))
                logger.info(f"Screenshot saved: {screenshot_path}")
            except Exception as ss_err:
                logger.warning(f"Failed to save screenshot: {ss_err}")
            
            # If not last attempt, wait with backoff
            if attempt < max_attempts:
                delay = backoff_delays[min(attempt - 1, len(backoff_delays) - 1)]
                logger.info(f"Waiting {delay}s before retry...")
                time.sleep(delay)
            else:
                # Last attempt failed
                raise ApktDownloadError(
                    f"Download failed after {max_attempts} attempts: {target_filename}. Last error: {e}"
                ) from e
    
    # Should not reach here
    raise ApktDownloadError(f"Download failed: {target_filename}")


class Downloader:
    """Handles file downloads from APKT (legacy class)."""
    
    def __init__(self, page, download_dir: Path):
        """Initialize downloader.
        
        Args:
            page: Playwright page instance
            download_dir: Directory for downloaded files
        """
        self.logger = get_logger()
        self.page = page
        self.download_dir = download_dir
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    async def download_report(self, filename_pattern: Optional[str] = None) -> Path:
        """Download report file.
        
        Args:
            filename_pattern: Expected filename pattern
            
        Returns:
            Path to downloaded file
            
        Raises:
            BrowserError: If download fails
        """
        try:
            self.logger.info("Starting file download")
            # TODO: Implement download handling
            # 1. Wait for download trigger
            # 2. Handle download dialog
            # 3. Save to download_dir
            # 4. Verify file
            return self.download_dir / "placeholder.xlsx"
        except Exception as e:
            raise BrowserError(f"Download failed: {e}")
    
    async def wait_for_download(self, timeout: int = 30000) -> Path:
        """Wait for file download.
        
        Args:
            timeout: Timeout in milliseconds
            
        Returns:
            Path to downloaded file
        """
        try:
            self.logger.info(f"Waiting for download (timeout={timeout}ms)")
            # TODO: Implement download waiting
            return self.download_dir / "placeholder.xlsx"
        except Exception as e:
            raise BrowserError(f"Download wait failed: {e}")
