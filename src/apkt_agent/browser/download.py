"""File download handling for APKT data."""

import time
from pathlib import Path
from typing import Callable, Optional, Tuple

from playwright.sync_api import Page, Download, TimeoutError as PlaywrightTimeout

from ..errors import ApktDownloadError, BrowserError, NoDataFoundError
from ..logging_ import get_logger
from ..workspace import RunContext


def _check_and_dismiss_popup(page: Page) -> Tuple[bool, bool]:
    """Check and dismiss any popup/modal that blocks download.
    
    Handles "Data tidak ditemukan" popup and similar SweetAlert2 modals.
    
    Returns:
        Tuple of (popup_found, is_no_data_error)
        - popup_found: True if popup was found and dismissed
        - is_no_data_error: True if it was "Data tidak ditemukan" popup
    """
    logger = get_logger()
    
    # Check for "Data tidak ditemukan" popup text first
    is_no_data = False
    try:
        popup_text_loc = page.locator("text='Data tidak ditemukan'")
        if popup_text_loc.is_visible(timeout=500):
            logger.warning("📢 Popup: 'Data tidak ditemukan' - no data available for this filter")
            is_no_data = True
    except:
        pass
    
    # SweetAlert2 and common modal selectors - very specific to avoid false positives
    # The popup has a yellow "Ok" button
    popup_selectors = [
        # SweetAlert2 specific selectors
        ".swal2-confirm",
        "button.swal2-confirm", 
        ".swal2-popup button",
        # Generic modal with Ok button - but within a modal container
        ".swal2-actions button:has-text('Ok')",
        ".swal2-actions button:has-text('OK')",
        # Fallback: Any modal overlay with Ok button
        "[class*='swal'] button:has-text('Ok')",
        # Very generic but scoped to modal
        "div[role='dialog'] button:has-text('Ok')",
        "div[role='dialog'] button:has-text('OK')",
    ]
    
    for selector in popup_selectors:
        try:
            popup_btn = page.locator(selector).first
            if popup_btn.is_visible(timeout=500):
                text = ""
                try:
                    text = popup_btn.inner_text(timeout=300)
                except:
                    text = "button"
                logger.info(f"✓ Popup dismissed: clicked '{text}' button")
                popup_btn.click()
                page.wait_for_timeout(500)
                return (True, is_no_data)
        except Exception:
            continue
    
    return (False, is_no_data)


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
        NoDataFoundError: If no data available for filter
    """
    logger = get_logger()
    
    # Backoff delays in seconds
    backoff_delays = [2, 5, 10]
    
    target_path = ctx.excel_dir / target_filename
    
    for attempt in range(1, max_attempts + 1):
        logger.info(f"Download attempt {attempt}/{max_attempts} for {target_filename}")
        
        try:
            # Setup download capture with reasonable timeout (60s for large files)
            # and check for popup periodically during the wait
            download = None
            download_started = False
            
            def on_download(d):
                nonlocal download, download_started
                download = d
                download_started = True
            
            # Register download event listener
            page.on("download", on_download)
            
            try:
                # Trigger the export click
                click_export_fn()
                
                # Poll for download or popup (check every 2 seconds, max 60 seconds)
                max_wait = 30  # 30 iterations * 2 seconds = 60 seconds max
                for i in range(max_wait):
                    # Check if download started
                    if download_started:
                        break
                    
                    # Check for popup every iteration
                    popup_found, is_no_data = _check_and_dismiss_popup(page)
                    if is_no_data:
                        raise NoDataFoundError("No data found for this filter combination")
                    if popup_found:
                        raise ApktDownloadError("Download blocked by popup")
                    
                    # Wait 2 seconds before next check
                    page.wait_for_timeout(2000)
                
                if not download_started:
                    raise ApktDownloadError("Download timeout - no file received after 60s")
                    
            finally:
                # Remove event listener
                page.remove_listener("download", on_download)
            
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
            
        except NoDataFoundError:
            # No data found - propagate immediately without retry
            raise
            
        except Exception as e:
            logger.warning(f"Download attempt {attempt} failed: {e}")
            
            # Check for popup that might have appeared
            popup_found, is_no_data = _check_and_dismiss_popup(page)
            if is_no_data:
                raise NoDataFoundError("No data found for this filter combination")
            
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
