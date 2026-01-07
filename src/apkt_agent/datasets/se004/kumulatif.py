"""SE004 Kumulatif dataset implementation."""

import json
from pathlib import Path
from typing import List, Optional

from ...browser.auth import login_apkt
from ...browser.download import download_excel
from ...browser.driver import open_browser, close_browser
from ...models import DownloadedFile, ParsedData
from ...workspace import RunContext
from ..base import BaseDataset, RunResult
from .parser import list_excel_files, parse_all_excel_files, save_csv_indonesian_format
from ...transform.validate import validate_se004_kumulatif


# Indonesian month names for period conversion
BULAN_INDONESIA = {
    "01": "Januari",
    "02": "Februari",
    "03": "Maret",
    "04": "April",
    "05": "Mei",
    "06": "Juni",
    "07": "Juli",
    "08": "Agustus",
    "09": "September",
    "10": "Oktober",
    "11": "November",
    "12": "Desember",
}


def parse_period_ym(period_ym: str) -> tuple[str, str]:
    """Parse YYYYMM period to Indonesian month name and year.
    
    Args:
        period_ym: Period in YYYYMM format (e.g., "202512")
        
    Returns:
        Tuple of (month_name, year) e.g., ("Desember", "2025")
    """
    year = period_ym[:4]
    month = period_ym[4:6]
    month_name = BULAN_INDONESIA.get(month, "Desember")
    return month_name, year


class SE004KumulatifDataset(BaseDataset):
    """SE004 Kumulatif dataset handler."""
    
    name = "se004_kumulatif"
    description = "SAIDI/SAIFI Kumulatif Report"
    
    def run(self, ctx: RunContext) -> RunResult:
        """Run SE004 Kumulatif extraction.
        
        Args:
            ctx: Run context
            
        Returns:
            RunResult with status
        """
        self.logger.info(f"Running SE004 Kumulatif for period {ctx.period_ym}")
        
        # Get config values
        unit_text = self.config.get(
            'datasets.se004_kumulatif.unit_text_default',
            '11 - WILAYAH ACEH'
        )
        dataset_url = self.config.get(
            'datasets.se004_kumulatif.url',
            'https://new-apktss.pln.co.id/home/laporan-saidi-saifi-kumulatif-se004'
        )
        
        # Parse period to month name and year
        month_name, year = parse_period_ym(ctx.period_ym)
        
        self.logger.info(f"Unit: {unit_text}")
        self.logger.info(f"Period: {month_name} {year}")
        
        playwright = None
        browser = None
        context = None
        
        try:
            # Step 1: Open browser
            playwright, browser, context, page = open_browser(ctx, self.config)
            self.logger.info("Browser opened, starting authentication...")
            
            # Step 2: Login to APKT via SSO/IAM
            login_apkt(page, ctx, self.config)
            self.logger.info("Authentication successful")
            
            # Step 3: Navigate to APKT-SS subdomain
            # After login, we're at https://new-apkt.pln.co.id/
            # Need to click APKT-SS to go to https://new-apktss.pln.co.id/
            self.logger.info("Step 3: Looking for APKT-SS menu...")
            self._navigate_to_apktss(page)
            
            # Step 4: Navigate to dataset page
            self.logger.info(f"Step 4: Navigating to SE004 Kumulatif page: {dataset_url}")
            page.goto(dataset_url)
            page.wait_for_load_state("networkidle")
            
            # Wait for main content to be ready
            self.logger.info("Waiting for page to be ready...")
            page.wait_for_timeout(3000)  # Give time for Angular/React to render
            
            self.logger.info(f"Current URL: {page.url}")
            
            # Step 5: Set Unit filter
            self.logger.info(f"Step 5: Setting Unit filter to: {unit_text}")
            self._set_unit_filter(page, unit_text)
            
            # Step 6: Set Period filter (month and year)
            self.logger.info(f"Step 6: Setting Period filter to: {month_name} {year}")
            self._set_period_filter(page, month_name, year)
            
            # Step 7: Click Export and download Excel
            self.logger.info("Step 7: Exporting data to Excel...")
            
            # Generate target filename
            unit_code = "WIL_ACEH"  # Hardcoded for now
            target_filename = f"se004_kumulatif_{ctx.period_ym}_{unit_code}.xlsx"
            
            # Define click export function
            def click_export():
                self._click_export_excel(page)
            
            # Download the Excel file
            downloaded_path = download_excel(
                page=page,
                ctx=ctx,
                click_export_fn=click_export,
                target_filename=target_filename,
                max_attempts=3,
            )
            
            self.logger.info(f"Excel downloaded: {downloaded_path}")
            
            # === PARSING PHASE ===
            self.logger.info("Starting parsing phase...")
            
            # Find all Excel files in raw/excel directory
            excel_files = list_excel_files(ctx.excel_dir)
            self.logger.info(f"Found {len(excel_files)} Excel files to parse")
            
            parsed_csv_path = None
            rows_parsed = 0
            validation_warnings = []
            
            if excel_files:
                # Parse all files into combined DataFrame
                combined_df = parse_all_excel_files(ctx.excel_dir)
                rows_parsed = len(combined_df)
                
                # Validate
                validation = validate_se004_kumulatif(combined_df)
                validation_warnings = validation.warnings
                
                if validation.warnings:
                    self.logger.warning(f"Validation warnings: {len(validation.warnings)}")
                    for w in validation.warnings[:5]:
                        self.logger.warning(f"  - {w}")
                
                # Ensure parsed directory exists
                ctx.parsed_dir.mkdir(parents=True, exist_ok=True)
                
                # Generate CSV filename
                csv_filename = f"se004_kumulatif_{ctx.period_ym}_{ctx.run_id}.csv"
                csv_path = ctx.parsed_dir / csv_filename
                
                # Save with Indonesian format (semicolon delimiter, . ribuan, , desimal)
                save_csv_indonesian_format(combined_df, csv_path)
                parsed_csv_path = str(csv_path)
                
                self.logger.info(f"Parsed {rows_parsed} rows from {len(excel_files)} files")
                self.logger.info(f"CSV saved: {csv_path}")
            
            # Update manifest.json
            manifest = {
                "run_id": ctx.run_id,
                "period_ym": ctx.period_ym,
                "timestamp": str(ctx.snapshot_date),
                "downloaded_files": [downloaded_path.name],
                "parsed_csv_path": parsed_csv_path,
                "row_count": rows_parsed,
                "files_parsed": len(excel_files),
                "validation": {
                    "is_valid": len(validation_warnings) == 0,
                    "warnings": validation_warnings,
                },
            }
            
            manifest_path = ctx.run_dir / "manifest.json"
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Manifest saved: {manifest_path}")
            
            return RunResult(
                success=True,
                message=f"Download+Parse OK - {month_name} {year} - {rows_parsed} rows",
                files_downloaded=[str(downloaded_path)],
                rows_parsed=rows_parsed,
                parsed_csv_path=parsed_csv_path,
                validation_warnings=validation_warnings,
            )
            
        except Exception as e:
            self.logger.error(f"Extraction failed: {e}")
            return RunResult(
                success=False,
                message=f"Extraction failed: {e}",
                files_downloaded=[],
                rows_parsed=0,
            )
            
        finally:
            # Always close browser
            if playwright or browser or context:
                close_browser(playwright, browser, context)
    
    def _navigate_to_apktss(self, page) -> None:
        """Navigate from APKT home to APKT-SS subdomain.
        
        After login, user lands on https://new-apkt.pln.co.id/
        Need to click APKT-SS tile/card to go to https://new-apktss.pln.co.id/
        
        Args:
            page: Playwright page object
        """
        self.logger.info(f"Current URL before APKT-SS navigation: {page.url}")
        
        # Check if already on APKT-SS
        if "new-apktss.pln.co.id" in page.url:
            self.logger.info("Already on APKT-SS subdomain")
            return
        
        # Wait for home page to fully load
        page.wait_for_timeout(2000)
        
        # Based on analysis: there's a <p> element with text "APKT-SS" inside a clickable div
        # Try to find and click the APKT-SS card/tile
        apktss_selectors = [
            # The <p> tag with APKT-SS text - click its parent div
            "p:has-text('APKT-SS')",
            "div:has-text('APKT-SS'):not(:has(div:has-text('APKT-SS')))",  # Most specific div
            "*:has-text('APKT-SS') >> nth=0",
            "text=APKT-SS",
        ]
        
        apktss_element = None
        for selector in apktss_selectors:
            try:
                locator = page.locator(selector)
                if locator.count() > 0:
                    apktss_element = locator.first
                    self.logger.info(f"Found APKT-SS element with selector: {selector}")
                    break
            except Exception as e:
                self.logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        if apktss_element:
            self.logger.info("Clicking APKT-SS card...")
            apktss_element.click()
            
            # Wait for navigation to APKT-SS subdomain
            try:
                page.wait_for_url("**/new-apktss.pln.co.id/**", timeout=15000)
                self.logger.info(f"Successfully navigated to APKT-SS: {page.url}")
            except Exception:
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(2000)
                self.logger.info(f"After APKT-SS click, URL: {page.url}")
        else:
            self.logger.error("Could not find APKT-SS card/tile on home page")
            raise Exception("APKT-SS card not found on home page")
        
        # Verify we're on APKT-SS
        if "new-apktss.pln.co.id" not in page.url:
            self.logger.error(f"Failed to navigate to APKT-SS. Current URL: {page.url}")
            raise Exception(f"Failed to navigate to APKT-SS. Current URL: {page.url}")
    
    def _set_unit_filter(self, page, unit_text: str) -> None:
        """Set the Unit Induk/Regional/Pusat filter.
        
        Args:
            page: Playwright page object
            unit_text: Unit text to select (e.g., "11 - WILAYAH ACEH")
        """
        # Based on analysis: select#unitInduk with name='unitInduk'
        try:
            unit_select = page.locator("select#unitInduk, select[name='unitInduk']").first
            unit_select.select_option(label=unit_text)
            self.logger.info(f"Selected unit: {unit_text}")
            page.wait_for_timeout(1000)  # Wait for cascading dropdowns to update
        except Exception as e:
            self.logger.error(f"Failed to set unit filter: {e}")
            raise
    
    def _set_period_filter(self, page, month_name: str, year: str) -> None:
        """Set the Period filter (month and year).
        
        Args:
            page: Playwright page object
            month_name: Indonesian month name (e.g., "Desember")
            year: Year string (e.g., "2025")
        """
        # Based on analysis:
        # - Month: select[name='vc-component-4'] with options Januari, Februari, etc.
        # - Year: select[name='vc-component-6'] with options 2026, 2025, etc.
        
        # Set month
        try:
            month_select = page.locator("select[name='vc-component-4']").first
            month_select.select_option(label=month_name)
            self.logger.info(f"Selected month: {month_name}")
            page.wait_for_timeout(500)
        except Exception as e:
            self.logger.error(f"Failed to set month filter: {e}")
            raise
        
        # Set year
        try:
            year_select = page.locator("select[name='vc-component-6']").first
            year_select.select_option(label=year)
            self.logger.info(f"Selected year: {year}")
            page.wait_for_timeout(500)
        except Exception as e:
            self.logger.error(f"Failed to set year filter: {e}")
            raise
    
    def _click_export_excel(self, page) -> None:
        """Click Export button and select Excel format.
        
        The page has an "Eksport" dropdown button with Excel option.
        
        Args:
            page: Playwright page object
        """
        self.logger.info("Looking for Export button...")
        
        # Based on analysis: Button 26 has text='Eksport' (Indonesian spelling)
        export_selectors = [
            "button:has-text('Eksport')",  # Indonesian spelling
            "button:has-text('Export')",
            "button:has-text('Excel')",
            "button:has-text('Download')",
            "button:has-text('Unduh')",
        ]
        
        export_button = None
        for selector in export_selectors:
            try:
                locator = page.locator(selector)
                if locator.count() > 0:
                    btn = locator.first
                    if btn.is_visible():
                        export_button = btn
                        self.logger.info(f"Found export button with selector: {selector}")
                        break
            except Exception as e:
                self.logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        if not export_button:
            raise Exception("Could not find Export button")
        
        # Click export button to open dropdown
        self.logger.info("Clicking Eksport button...")
        export_button.click()
        page.wait_for_timeout(1000)
        
        # Look for Excel option in dropdown menu
        excel_selectors = [
            "button:has-text('Excel')",
            "a:has-text('Excel')",
            "li:has-text('Excel')",
            ".dropdown-item:has-text('Excel')",
            "[role='menuitem']:has-text('Excel')",
            "div:has-text('Excel'):visible",
        ]
        
        excel_option = None
        for selector in excel_selectors:
            try:
                locator = page.locator(selector)
                if locator.count() > 0:
                    opt = locator.first
                    if opt.is_visible():
                        excel_option = opt
                        self.logger.info(f"Found Excel option with selector: {selector}")
                        break
            except Exception as e:
                self.logger.debug(f"Excel selector {selector} failed: {e}")
                continue
        
        if excel_option:
            self.logger.info("Clicking Excel option...")
            excel_option.click()
        else:
            # Maybe the button directly triggers download without dropdown
            self.logger.info("No Excel dropdown option found, export might trigger directly")
    
    async def extract(
        self,
        ctx: RunContext,
        period_ym: str,
        unit_text: Optional[str] = None,
    ) -> List[DownloadedFile]:
        """Extract SE004 Kumulatif data.
        
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
        """Parse SE004 Kumulatif files.
        
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
