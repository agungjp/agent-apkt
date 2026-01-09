"""Single-month SE004 data download and extraction (all selected units)."""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, TYPE_CHECKING

from ...browser.auth import login_apkt
from ...browser.download import download_excel
from ...browser.driver import open_browser, close_browser
from ...workspace import RunContext
from ...config import Config
from ...logging_ import get_logger
from .parser import list_excel_files, parse_all_excel_files, save_csv_indonesian_format
from ...transform.validate import validate_se004_kumulatif

if TYPE_CHECKING:
    from playwright.sync_api import Page


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
    """Parse YYYYMM period to Indonesian month name and year."""
    year = period_ym[:4]
    month = period_ym[4:6]
    month_name = BULAN_INDONESIA.get(month, "Desember")
    return month_name, year


def load_units_selection(filepath: Path = None) -> List[Dict[str, str]]:
    """Load selected units from YAML file.
    
    Args:
        filepath: Path to units_selection.yaml
        
    Returns:
        List of unit dicts with value, text, code
    """
    if filepath is None:
        filepath = Path("units_selection.yaml")
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    return data.get("selected_units", [])


def _navigate_to_apktss(page: "Page") -> None:
    """Navigate from APKT home to APKT-SS subdomain."""
    logger = get_logger()
    
    if "new-apktss.pln.co.id" in page.url:
        logger.info("✓ Already on APKT-SS, skipping navigation")
        return
    
    page.wait_for_timeout(2000)
    
    logger.info("🔍 Looking for APKT-SS link...")
    apktss_link = page.locator("p:has-text('APKT-SS')").first
    try:
        if apktss_link.count() > 0:
            logger.info("✓ Found APKT-SS link, clicking...")
            apktss_link.click()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)
            logger.info(f"✓ Navigated, current URL: {page.url}")
            
            # Check if redirected to login (session issue)
            if "/login" in page.url:
                logger.warning("⚠ Redirected to login page - session may have expired")
                raise Exception("Session expired during navigation to APKT-SS")
        else:
            logger.warning("APKT-SS link not found, trying direct navigation...")
            page.goto("https://new-apktss.pln.co.id/home")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
    except Exception as e:
        logger.error(f"✗ Navigation to APKT-SS failed: {e}")
        raise


def _set_unit_filter(page: "Page", unit_text: str) -> None:
    """Set the Unit Induk filter."""
    logger = get_logger()
    
    logger.info(f"🔍 Waiting for unit selector to be visible...")
    unit_select = page.locator("select#unitInduk, select[name='unitInduk']").first
    try:
        # Wait for element to be visible and enabled before selecting
        unit_select.wait_for(state="visible", timeout=10000)
        logger.info(f"✓ Unit selector visible, selecting: {unit_text}")
        unit_select.select_option(label=unit_text)
        logger.info(f"✓ Unit selected: {unit_text}")
    except Exception as e:
        logger.error(f"✗ Failed to select unit: {e}")
        raise
    
    page.wait_for_timeout(1000)


def _set_period_filter(page: "Page", month_name: str, year: str) -> None:
    """Set period filter (month and year) on SE004 page."""
    logger = get_logger()
    
    try:
        # Pre-check: Ensure page is fully loaded
        page.wait_for_load_state("networkidle", timeout=10000)
        page.wait_for_timeout(1000)  # Extra stability wait
        
        # Set Month - using the same selector as kumulatif
        logger.info(f"🔍 Waiting for month selector to be visible...")
        month_select = page.locator("select[name='vc-component-4']").first
        
        # Retry logic if selector not found
        max_retries = 3
        for attempt in range(max_retries):
            try:
                month_select.wait_for(state="visible", timeout=5000)
                logger.info(f"✓ Month selector visible, selecting: {month_name}")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠ Attempt {attempt + 1}/{max_retries}: Selector not visible, retrying...")
                    page.wait_for_timeout(2000)
                    # Try to reload page
                    try:
                        page.reload()
                        page.wait_for_load_state("networkidle", timeout=5000)
                    except Exception:
                        pass  # Reload might fail, that's ok
                else:
                    raise Exception(f"Month selector not found after {max_retries} attempts: {e}")
        
        month_select.select_option(label=month_name)
        logger.info(f"✓ Month selected: {month_name}")
        page.wait_for_timeout(500)
        
        # Set Year - using the same selector as kumulatif
        logger.info(f"🔍 Waiting for year selector to be visible...")
        year_select = page.locator("select[name='vc-component-6']").first
        year_select.wait_for(state="visible", timeout=10000)
        logger.info(f"✓ Year selector visible, selecting: {year}")
        year_select.select_option(label=year)
        logger.info(f"✓ Year selected: {year}")
        
        page.wait_for_timeout(2000)  # Wait for data to reload
        
    except Exception as e:
        logger.error(f"Error setting period filter: {e}")
        raise


def _click_export_excel(page: "Page") -> None:
    """Click the export to Excel button on the SE004 page."""
    logger = get_logger()
    try:
        # Click Eksport button
        logger.info("🔍 Looking for Eksport button...")
        export_btn = page.locator("button:has-text('Eksport')").first
        export_btn.wait_for(state="visible", timeout=5000)
        logger.info("✓ Eksport button found, clicking...")
        export_btn.click()
        
        page.wait_for_timeout(500)
        
        # Click Excel option
        logger.info("🔍 Looking for Excel option...")
        excel_btn = page.locator("button:has-text('Excel')").first
        excel_btn.wait_for(state="visible", timeout=5000)
        logger.info("✓ Excel option found, clicking...")
        excel_btn.click()
        
    except Exception as e:
        logger.error(f"Error clicking export button: {e}")
        raise


def run_se004_bulanan(
    config: Config,
    ctx: RunContext,
    period_ym: str,
    units: List[Dict[str, str]],
    page: Optional["Page"] = None,
) -> Tuple[Dict[str, Any], Optional["Page"]]:
    """Download and extract SE004 monthly data for a single month across multiple units.
    
    Args:
        config: Configuration object
        ctx: Run context
        period_ym: Period in YYYYMM format
        units: List of unit dicts with value, text, code
        page: Optional existing Playwright page instance
        
    Returns:
        Tuple of (results dict, page instance) for session reuse
    """
    dataset_url = config.get(
        'datasets.se004_bulanan.url',
        'https://new-apktss.pln.co.id/home/laporan-saidi-saifi-se004'
    )
    
    month_name, year = parse_period_ym(period_ym)
    
    results = {
        "total": len(units),
        "success": 0,
        "failed": 0,
        "period": period_ym,
        "month_name": month_name,
        "year": year,
        "files": [],
        "errors": [],
        "rows_parsed": 0,
        "parsed_csv_path": None,
        "sheet_uploaded": False,
        "sheet_worksheet": None,
        "sheet_row_count": 0,
        "sheet_error": None,
    }
    
    playwright = None
    browser = None
    context = None
    page_from_browser = None
    should_close_browser = False
    logger = get_logger()
    
    try:
        print("\n" + "=" * 60)
        print(f"SE004 Monthly Report: {month_name} {year} ({period_ym})")
        print("=" * 60)
        
        if page is None:
            # New session: open browser
            playwright, browser, context, page = open_browser(ctx, config)
            page_from_browser = page
            should_close_browser = True
            print("Browser opened, starting authentication...")
            
            # Login
            login_apkt(page, ctx, config)
            print("✓ Authentication successful\n")
        else:
            # Reuse existing session
            print("Using existing browser session...\n")
            should_close_browser = False
        
        # Navigate to APKT-SS
        print("Navigating to APKT-SS...")
        _navigate_to_apktss(page)
        
        # Navigate to SE004 page
        print(f"Navigating to SE004 monthly report...")
        page.goto(dataset_url)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)
        
        # Verify page loaded with explicit check
        logger.info(f"🔍 Verifying SE004 page loaded...")
        try:
            page.wait_for_selector("select[name='vc-component-4']", timeout=5000)
            logger.info(f"✓ Page verified, selector found")
        except Exception as e:
            logger.warning(f"⚠ Selector not immediately visible, trying reload...")
            page.reload()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
        
        # Set period filter once for all units
        print(f"Setting period: {month_name} {year}...")
        _set_period_filter(page, month_name, year)
        
        # Loop through each unit to download
        for i, unit in enumerate(units, 1):
            unit_text = unit["text"]
            unit_code = unit["code"]
            unit_value = unit["value"]
            
            print("\n" + "-" * 60)
            print(f"[{i}/{len(units)}] Downloading: {unit_text}")
            print("-" * 60)
            
            try:
                # Set unit filter
                _set_unit_filter(page, unit_text)
                
                # Wait for data to load
                page.wait_for_timeout(2000)
                
                # Generate filename
                target_filename = f"se004_bulanan_{period_ym}_{unit_code}.xlsx"
                
                # Download Excel
                def click_export():
                    _click_export_excel(page)
                
                downloaded_path = download_excel(
                    page=page,
                    ctx=ctx,
                    click_export_fn=click_export,
                    target_filename=target_filename,
                    max_attempts=3,
                )
                
                print(f"✓ Downloaded: {target_filename}")
                results["success"] += 1
                results["files"].append(str(downloaded_path))
                
            except Exception as e:
                print(f"✗ Failed: {e}")
                results["failed"] += 1
                results["errors"].append({
                    "unit": unit_text,
                    "error": str(e),
                })
        
        # Parse all downloaded files
        print("\n" + "=" * 60)
        print("PARSING DOWNLOADED FILES")
        print("=" * 60)
        
        excel_files = list_excel_files(ctx.excel_dir)
        print(f"Found {len(excel_files)} Excel files to parse")
        
        if excel_files:
            try:
                parsed_data = parse_all_excel_files(ctx.excel_dir)
                
                # Check if dataframe is empty using len()
                import pandas as pd
                if isinstance(parsed_data, pd.DataFrame) and len(parsed_data) > 0:
                    results["rows_parsed"] = len(parsed_data)
                    print(f"✓ Parsed {results['rows_parsed']} rows from {len(excel_files)} files")
                    
                    # Save as CSV
                    csv_path = save_csv_indonesian_format(
                        parsed_data,
                        ctx.parsed_dir / f"se004_bulanan_{period_ym}.csv"
                    )
                    results["parsed_csv_path"] = str(csv_path)
                    print(f"✓ Saved CSV: {Path(csv_path).name}")
                    
                    # Validate data
                    validation = validate_se004_kumulatif(parsed_data)
                    if validation.warnings:
                        logger.warning(f"Validation warnings: {len(validation.warnings)} issues found")
                    
                    # === GOOGLE SHEETS UPLOAD ===
                    gs_config = config.data.get('google_sheets', {})
                    
                    if gs_config.get('enabled', False) and csv_path:
                        print("\n" + "=" * 60)
                        print("UPLOADING TO GOOGLE SHEETS")
                        print("=" * 60)
                        
                        try:
                            from ...sinks.sheets import upload_csv_to_worksheet
                            
                            sheet_upload_result = upload_csv_to_worksheet(
                                csv_path=csv_path,
                                spreadsheet_id=gs_config['spreadsheet_id'],
                                worksheet_name=gs_config.get('worksheet_name_bulanan', 'se004_bulanan'),
                                credentials_json_path=gs_config['credentials_json_path'],
                                mode=gs_config.get('mode', 'replace'),
                            )
                            
                            results["sheet_uploaded"] = True
                            results["sheet_worksheet"] = sheet_upload_result['worksheet_name']
                            results["sheet_row_count"] = sheet_upload_result['row_count']
                            
                            print(f"✓ Uploaded to Google Sheets: {sheet_upload_result['worksheet_name']}")
                            print(f"  Rows: {sheet_upload_result['row_count']}, Cols: {sheet_upload_result['col_count']}")
                            logger.info(f"Google Sheets upload successful: {results['sheet_worksheet']}")
                            
                        except Exception as e:
                            logger.warning(f"Google Sheets upload failed: {e}")
                            results["sheet_error"] = str(e)
                            results["sheet_uploaded"] = False
                else:
                    print("✗ No data parsed from Excel files")
            
            except Exception as e:
                logger.error(f"Parsing failed: {e}")
                print(f"✗ Parsing error: {e}")
        else:
            print("✗ No Excel files found in download directory")
        
        # Save manifest
        manifest = {
            "type": "se004_bulanan",
            "period": period_ym,
            "month": month_name,
            "year": year,
            "url": dataset_url,
            "download_date": ctx.snapshot_date,
            "files_downloaded": len(results["files"]),
            "rows_parsed": results["rows_parsed"],
            "parsed_csv": results.get("parsed_csv_path"),
            "google_sheets": {
                "uploaded": results["sheet_uploaded"],
                "worksheet_name": results.get("sheet_worksheet"),
                "row_count": results.get("sheet_row_count", 0),
            }
        }
        
        manifest_path = ctx.run_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Manifest saved: {manifest_path}")
        
        return results, page
    
    except Exception as e:
        logger.error(f"SE004 Bulanan extraction failed: {e}")
        raise
    
    finally:
        # Cleanup: close browser only if we opened it
        if should_close_browser and browser and context and playwright:
            close_browser(playwright, browser, context)
            logger.info("Browser session closed")
