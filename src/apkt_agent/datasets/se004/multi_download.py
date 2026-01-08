"""Multi-unit download for SE004 Kumulatif."""

import json
import yaml
from pathlib import Path
from typing import List, Dict, Any

from ...browser.auth import login_apkt
from ...browser.download import download_excel
from ...browser.driver import open_browser, close_browser
from ...workspace import RunContext
from ...config import Config
from ...logging_ import get_logger
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


def run_multi_unit_download(
    config: Config,
    ctx: RunContext,
    units: List[Dict[str, str]],
    period_ym: str,
) -> Dict[str, Any]:
    """Download SE004 Kumulatif for multiple units.
    
    Args:
        config: Configuration object
        ctx: Run context
        units: List of unit dicts with value, text, code
        period_ym: Period in YYYYMM format
        
    Returns:
        Dict with results summary
    """
    dataset_url = config.get(
        'datasets.se004_kumulatif.url',
        'https://new-apktss.pln.co.id/home/laporan-saidi-saifi-kumulatif-se004'
    )
    
    month_name, year = parse_period_ym(period_ym)
    
    results = {
        "total": len(units),
        "success": 0,
        "failed": 0,
        "files": [],
        "errors": [],
    }
    
    playwright = None
    browser = None
    context = None
    
    try:
        # Step 1: Open browser
        print("\n" + "=" * 60)
        print(f"Multi-Unit Download: {len(units)} units")
        print(f"Period: {month_name} {year} ({period_ym})")
        print("=" * 60)
        
        playwright, browser, context, page = open_browser(ctx, config)
        print("Browser opened, starting authentication...")
        
        # Step 2: Login
        login_apkt(page, ctx, config)
        print("✓ Authentication successful\n")
        
        # Step 3: Navigate to APKT-SS
        print("Navigating to APKT-SS...")
        _navigate_to_apktss(page)
        
        # Step 4: Navigate to SE004 page
        print(f"Navigating to SE004 Kumulatif...")
        page.goto(dataset_url)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)
        
        # Step 5: Set period filter once (same for all units)
        print(f"Setting period: {month_name} {year}...")
        _set_period_filter(page, month_name, year)
        
        # Step 6: Loop through each unit
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
                target_filename = f"se004_kumulatif_{period_ym}_{unit_code}.xlsx"
                
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
        
        # === PARSING PHASE ===
        print("\n" + "=" * 60)
        print("PARSING DOWNLOADED FILES")
        print("=" * 60)
        
        logger = get_logger()
        
        # Find all Excel files (use excel_dir which is raw/excel)
        excel_files = list_excel_files(ctx.excel_dir)
        print(f"Found {len(excel_files)} Excel files to parse")
        
        if excel_files:
            # Parse all files into combined DataFrame
            combined_df = parse_all_excel_files(ctx.excel_dir)
            
            # Validate
            validation = validate_se004_kumulatif(combined_df)
            results["validation_warnings"] = validation.warnings
            
            if validation.warnings:
                print(f"\n⚠ Validation warnings: {len(validation.warnings)}")
                for w in validation.warnings[:5]:  # Show first 5
                    print(f"  - {w}")
            
            # Ensure parsed directory exists
            ctx.parsed_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate short run ID for filename
            run_id_short = ctx.run_id.split("_")[-1] if "_" in ctx.run_id else ctx.run_id[:8]
            csv_filename = f"se004_kumulatif_{period_ym}_{run_id_short}.csv"
            csv_path = ctx.parsed_dir / csv_filename
            
            # Save to CSV with Indonesian format (semicolon delimiter, . ribuan, , desimal)
            save_csv_indonesian_format(combined_df, csv_path)
            
            results["parsed_csv_path"] = str(csv_path)
            results["rows_parsed"] = len(combined_df)
            
            print(f"\n✓ Parsed {len(combined_df)} rows from {len(excel_files)} files")
            print(f"✓ CSV saved: {csv_filename}")
            
            # === GOOGLE SHEETS UPLOAD ===
            gs_config = config.data.get('google_sheets', {})
            sheet_upload_result = None
            
            if gs_config.get('enabled', False):
                print("\n" + "-" * 60)
                print("UPLOADING TO GOOGLE SHEETS")
                print("-" * 60)
                
                try:
                    from ...sinks.sheets import upload_csv_to_worksheet
                    
                    sheet_upload_result = upload_csv_to_worksheet(
                        csv_path=csv_path,
                        spreadsheet_id=gs_config['spreadsheet_id'],
                        worksheet_name=gs_config.get('worksheet_name', 'se004_kumulatif'),
                        credentials_json_path=gs_config['credentials_json_path'],
                        mode=gs_config.get('mode', 'replace'),
                    )
                    
                    print(f"✓ Uploaded to Google Sheets: {sheet_upload_result['worksheet_name']}")
                    print(f"  Rows: {sheet_upload_result['row_count']}, Cols: {sheet_upload_result['col_count']}")
                    
                    results["sheet_uploaded"] = True
                    results["sheet_worksheet"] = sheet_upload_result['worksheet_name']
                    results["sheet_row_count"] = sheet_upload_result['row_count']
                    
                except Exception as e:
                    logger.warning(f"Google Sheets upload failed: {e}")
                    print(f"⚠ Upload failed: {e}")
                    print("  (See logs for details)")
                    
                    results["sheet_uploaded"] = False
                    results["sheet_error"] = str(e)
            
            # Save manifest
            manifest = {
                "run_id": ctx.run_id,
                "period_ym": period_ym,
                "timestamp": str(ctx.snapshot_date),
                "downloaded_files": [Path(f).name for f in results["files"]],
                "parsed_csv_path": str(csv_path),
                "row_count": len(combined_df),
                "files_parsed": len(excel_files),
                "validation": validation.to_dict(),
            }
            
            # Add Google Sheets info to manifest
            if gs_config.get('enabled', False):
                manifest["google_sheets"] = {
                    "enabled": True,
                    "uploaded": results.get("sheet_uploaded", False),
                    "worksheet_name": results.get("sheet_worksheet"),
                    "row_count": results.get("sheet_row_count"),
                    "error": results.get("sheet_error"),
                }
            
            manifest_path = ctx.run_dir / "manifest.json"
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Manifest saved: {manifest_path}")
        
        return results
        
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        results["errors"].append({
            "unit": "GLOBAL",
            "error": str(e),
        })
        return results
        
    finally:
        if playwright or browser or context:
            close_browser(playwright, browser, context)


def _navigate_to_apktss(page) -> None:
    """Navigate from APKT home to APKT-SS subdomain."""
    from ...logging_ import get_logger
    logger = get_logger()
    
    if "new-apktss.pln.co.id" in page.url:
        logger.info("✓ Already on APKT-SS, skipping navigation")
        return
    
    page.wait_for_timeout(2000)
    
    apktss = page.locator("p:has-text('APKT-SS')").first
    if apktss:
        logger.info("🔍 Found APKT-SS link, clicking...")
        apktss.click()
        try:
            page.wait_for_url("**/new-apktss.pln.co.id/**", timeout=15000)
            logger.info("✓ Navigated to APKT-SS")
        except Exception:
            logger.warning("⚠ URL wait timeout, trying alternative waits...")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
    
    # Additional wait for page to be fully interactive
    logger.info("🔍 Waiting for page to be fully interactive...")
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2000)  # Extra buffer for JavaScript to execute
    
    if "new-apktss.pln.co.id" not in page.url:
        raise Exception(f"Failed to navigate to APKT-SS. Current URL: {page.url}")
    
    logger.info("✓ APKT-SS page ready for filtering")


def _set_unit_filter(page, unit_text: str) -> None:
    """Set the Unit Induk filter."""
    from ...logging_ import get_logger
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


def _set_period_filter(page, month_name: str, year: str) -> None:
    """Set the Period filter (month and year)."""
    from ...logging_ import get_logger
    logger = get_logger()
    
    # Set Month
    logger.info(f"🔍 Waiting for month selector [vc-component-4] to be visible...")
    month_select = page.locator("select[name='vc-component-4']").first
    try:
        # Wait for month select to be visible - critical for headless mode
        month_select.wait_for(state="visible", timeout=15000)
        logger.info(f"✓ Month selector visible, selecting: {month_name}")
        month_select.select_option(label=month_name)
        logger.info(f"✓ Month selected: {month_name}")
    except Exception as e:
        logger.error(f"✗ Failed to select month: {e}")
        # Try to debug - take screenshot if headless
        try:
            screenshot_path = f"debug_month_select_error_{page.context.browser.chromium_executable_path if hasattr(page.context, 'browser') else 'unknown'}.png"
            page.screenshot(path=screenshot_path)
            logger.error(f"📸 Screenshot saved to: {screenshot_path}")
        except:
            pass
        raise
    
    page.wait_for_timeout(500)
    
    # Set Year
    logger.info(f"🔍 Waiting for year selector [vc-component-6] to be visible...")
    year_select = page.locator("select[name='vc-component-6']").first
    try:
        year_select.wait_for(state="visible", timeout=10000)
        logger.info(f"✓ Year selector visible, selecting: {year}")
        year_select.select_option(label=year)
        logger.info(f"✓ Year selected: {year}")
    except Exception as e:
        logger.error(f"✗ Failed to select year: {e}")
        raise
    
    page.wait_for_timeout(500)


def _click_export_excel(page) -> None:
    """Click Export button and select Excel."""
    from ...logging_ import get_logger
    logger = get_logger()
    
    # Click Eksport button
    logger.info("🔍 Looking for Eksport button...")
    export_btn = page.locator("button:has-text('Eksport')").first
    try:
        export_btn.wait_for(state="visible", timeout=5000)
        logger.info("✓ Eksport button found, clicking...")
        export_btn.click()
    except Exception as e:
        logger.error(f"✗ Eksport button not found or not clickable: {e}")
        raise
    
    page.wait_for_timeout(500)
    
    # Click Excel option
    logger.info("🔍 Looking for Excel option...")
    excel_btn = page.locator("button:has-text('Excel')").first
    try:
        excel_btn.wait_for(state="visible", timeout=5000)
        logger.info("✓ Excel option found, clicking...")
        excel_btn.click()
    except Exception as e:
        logger.error(f"✗ Excel option not found or not clickable: {e}")
        raise
