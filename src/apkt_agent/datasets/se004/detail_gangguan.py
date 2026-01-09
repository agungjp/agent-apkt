"""SE004 Detail Kode Gangguan data download (all selected units, all kelompok).

Includes: Download, Parsing, and Google Sheets upload.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, TYPE_CHECKING

from ...browser.download import download_excel
from ...browser.driver import open_browser
from ...browser.auth import login_apkt
from ...workspace import RunContext
from ...config import Config
from ...logging_ import get_logger
from ...errors import NoDataFoundError
from ...sinks.sheets import upload_dataframe_to_worksheet

# Lazy import to avoid loading pandas at startup
# from .parser_detail_gangguan import parse_run_directory

if TYPE_CHECKING:
    from playwright.sync_api import Page


# Kelompok options for Detail Gangguan
KELOMPOK_OPTIONS = [
    {"value": "DISTRIBUSI", "text": "DISTRIBUSI"},
    {"value": "TRANSMISI", "text": "TRANSMISI"},
    {"value": "PEMBANGKIT", "text": "PEMBANGKIT"},
]

# Units to exclude from Menu 3 (Detail Gangguan)
# Regional Sumkal doesn't have per-kelompok data
EXCLUDED_UNIT_CODES = ["REG_SUMKAL"]


def load_units_selection(filepath: Optional[Path] = None, exclude_regional: bool = False) -> List[Dict[str, Any]]:
    """Load selected units from YAML file.
    
    Args:
        filepath: Path to units_selection.yaml
        exclude_regional: If True, exclude units in EXCLUDED_UNIT_CODES (for Menu 3)
    """
    if filepath is None:
        filepath = Path("units_selection.yaml")
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    units = data.get("selected_units", [])
    
    if exclude_regional:
        units = [u for u in units if u.get("code") not in EXCLUDED_UNIT_CODES]
    
    return units


def _navigate_to_apktss(page: "Page") -> None:
    """Navigate from APKT home to APKT-SS subdomain.
    
    Same as bulanan.py - click APKT-SS link to transfer session/token.
    After clicking, wait for auth redirect to complete.
    """
    logger = get_logger()
    
    # Check if already on APKT-SS (not on login page)
    if "new-apktss.pln.co.id" in page.url and "/login" not in page.url and "/auth" not in page.url:
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
            logger.info(f"✓ After click, current URL: {page.url}")
            
            # Wait for auth redirect to complete (may go through /auth?token=... first)
            max_wait = 10
            for i in range(max_wait):
                current_url = page.url
                if "new-apktss.pln.co.id/home" in current_url:
                    logger.info(f"✓ Successfully on APKT-SS home")
                    break
                elif "/login" in current_url:
                    logger.warning(f"⚠ On login page, waiting for redirect... ({i+1}/{max_wait})")
                    page.wait_for_timeout(1000)
                elif "/auth" in current_url:
                    logger.info(f"Auth redirect in progress... ({i+1}/{max_wait})")
                    page.wait_for_timeout(1000)
                else:
                    # Some other page on APKT-SS
                    logger.info(f"✓ On APKT-SS page: {current_url[:60]}...")
                    break
            
            # Final check
            if "/login" in page.url:
                logger.error("⚠ Still on login page after waiting - session may have expired")
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
    """Set the Unit Induk filter using vanilla-rich-select.
    
    Menu 3 uses vanilla-rich-select, need to click dropdown then select option.
    """
    logger = get_logger()
    
    logger.info(f"🔍 Setting unit filter: {unit_text}")
    
    try:
        # First try the hidden select element directly
        unit_select = page.locator("select#unitInduk, select[name='unitInduk']").first
        if unit_select.count() > 0:
            try:
                # Force select on hidden element
                unit_select.select_option(label=unit_text, timeout=3000)
                logger.info(f"✓ Unit selected via hidden select: {unit_text}")
                page.wait_for_timeout(1500)
                return
            except Exception:
                logger.info("Hidden select failed, trying dropdown click...")
        
        # Click the dropdown trigger for unitInduk
        dropdown_trigger = page.locator("label[for='unitInduk']").locator("..").locator("div[data-rich-select-focusable]").first
        if dropdown_trigger.count() == 0:
            # Try alternative: find by placeholder text
            dropdown_trigger = page.locator("span:has-text('Pilih Unit Induk')").first
        
        dropdown_trigger.wait_for(state="visible", timeout=10000)
        dropdown_trigger.click()
        page.wait_for_timeout(500)
        
        # Click the option
        option = page.locator(f"text='{unit_text}'").first
        option.wait_for(state="visible", timeout=5000)
        option.click()
        logger.info(f"✓ Unit selected via dropdown: {unit_text}")
        
    except Exception as e:
        logger.error(f"✗ Failed to select unit: {e}")
        raise
    
    page.wait_for_timeout(1500)


def _set_kelompok_filter(page: "Page", kelompok_text: str) -> None:
    """Set the Kelompok filter (DISTRIBUSI/TRANSMISI/PEMBANGKIT).
    
    Menu 3 uses vanilla-rich-select with id='kelompok'.
    """
    logger = get_logger()
    
    logger.info(f"🔍 Setting kelompok filter: {kelompok_text}")
    
    try:
        # First try the hidden select element directly
        kelompok_select = page.locator("select#kelompok, select[name='kelompok']").first
        if kelompok_select.count() > 0:
            try:
                kelompok_select.select_option(label=kelompok_text, timeout=3000)
                logger.info(f"✓ Kelompok selected via hidden select: {kelompok_text}")
                page.wait_for_timeout(1000)
                return
            except Exception:
                logger.info("Hidden select failed, trying dropdown click...")
        
        # Click the dropdown trigger for kelompok
        dropdown_trigger = page.locator("label[for='kelompok']").locator("..").locator("div[data-rich-select-focusable]").first
        if dropdown_trigger.count() == 0:
            # Try alternative: find by placeholder text
            dropdown_trigger = page.locator("span:has-text('Pilih Kelompok'), span:has-text('-- Pilih Kelompok')").first
        
        if dropdown_trigger.count() > 0:
            dropdown_trigger.wait_for(state="visible", timeout=5000)
            dropdown_trigger.click()
            page.wait_for_timeout(500)
            
            # Click the option
            option = page.locator(f"text='{kelompok_text}'").first
            option.wait_for(state="visible", timeout=5000)
            option.click()
            logger.info(f"✓ Kelompok selected via dropdown: {kelompok_text}")
            page.wait_for_timeout(1000)
            return
        
        logger.warning(f"⚠ Could not find kelompok dropdown")
        
    except Exception as e:
        logger.warning(f"⚠ Could not set kelompok filter: {e}")


def _set_period_filter(page: "Page", month_name: str, year: str) -> None:
    """Set period filter (month and year) on Detail Gangguan page.
    
    Menu 3 uses:
    - Month: vc-component-9 (Januari-Desember)
    - Year: vc-component-11 (2018-2026)
    """
    logger = get_logger()
    
    try:
        # Extra wait for page rendering
        page.wait_for_timeout(2000)
        
        # Set Month - Menu 3 uses vc-component-9
        logger.info(f"🔍 Setting month: {month_name}")
        month_select = page.locator("select[name='vc-component-9'], select#vc-component-9").first
        if month_select.count() > 0:
            try:
                month_select.select_option(label=month_name, timeout=5000)
                logger.info(f"✓ Month selected via hidden select: {month_name}")
            except Exception:
                logger.info("Month hidden select failed, trying dropdown...")
                # Click dropdown and select
                page.locator("h3:has-text('Periode')").locator("..").locator("div[data-rich-select-focusable]").first.click()
                page.wait_for_timeout(300)
                page.locator(f"text='{month_name}'").first.click()
        else:
            logger.warning("Month selector not found")
        
        page.wait_for_timeout(500)
        
        # Set Year - Menu 3 uses vc-component-11
        logger.info(f"🔍 Setting year: {year}")
        year_select = page.locator("select[name='vc-component-11'], select#vc-component-11").first
        if year_select.count() > 0:
            try:
                year_select.select_option(label=year, timeout=5000)
                logger.info(f"✓ Year selected via hidden select: {year}")
            except Exception:
                logger.info("Year hidden select failed, trying dropdown...")
                # Click dropdown and select
                page.locator("h3:has-text('Periode')").locator("..").locator("div[data-rich-select-focusable]").nth(1).click()
                page.wait_for_timeout(300)
                page.locator(f"text='{year}'").first.click()
        else:
            logger.warning("Year selector not found")
        
        page.wait_for_timeout(2000)  # Wait for data to reload
        logger.info(f"✓ Period set: {month_name} {year}")
        
    except Exception as e:
        logger.error(f"Error setting period filter: {e}")
        raise


def _click_export_excel(page: "Page") -> None:
    """Click the export to Excel button using Headless UI menu."""
    logger = get_logger()
    try:
        # Click Eksport button (Headless UI menu button)
        logger.info("🔍 Looking for Eksport button...")
        export_btn = page.locator("#headlessui-menu-button-v-2, button:has-text('Eksport')").first
        export_btn.wait_for(state="visible", timeout=5000)
        logger.info("✓ Eksport button found, clicking...")
        export_btn.click()
        
        # Wait for menu to open
        page.wait_for_timeout(500)
        
        # Try multiple selectors for Excel option in Headless UI menu
        logger.info("🔍 Looking for Excel option in dropdown...")
        
        # Headless UI uses role="menuitem" or button inside menu
        selectors = [
            "[role='menuitem']:has-text('Excel')",
            "button:has-text('Excel')",
            "a:has-text('Excel')",
            "div[role='menu'] >> text=Excel",
            "text='Excel'",
        ]
        
        excel_found = False
        for selector in selectors:
            try:
                excel_option = page.locator(selector).first
                excel_option.wait_for(state="visible", timeout=2000)
                logger.info(f"✓ Excel option found with selector: {selector}")
                excel_option.click()
                excel_found = True
                break
            except Exception:
                continue
        
        if not excel_found:
            # Debug: log what's visible in the menu
            logger.warning("Excel option not found, checking menu content...")
            menu_items = page.locator("[role='menu'], [role='menuitem'], [data-headlessui-state]").all()
            logger.info(f"Found {len(menu_items)} menu elements")
            for item in menu_items[:5]:  # Log first 5
                try:
                    text = item.inner_text(timeout=500)
                    logger.info(f"  Menu item: {text[:50] if text else '(empty)'}")
                except:
                    pass
            raise Exception("Excel option not found in dropdown menu")
        
    except Exception as e:
        logger.error(f"Error during export: {e}")
        raise


def parse_period_ym(period_ym: str) -> Tuple[str, str]:
    """Parse period_ym string to month_name and year."""
    from ...datasets.se004.schema import BULAN_INDONESIA
    
    month_num = period_ym[4:6]
    year = period_ym[0:4]
    
    month_name = None
    for bulan, num in BULAN_INDONESIA.items():
        if num == month_num:
            month_name = bulan.capitalize()
            break
    
    if not month_name:
        raise ValueError(f"Invalid period: {period_ym}")
    
    return month_name, year


def run_se004_detail_gangguan(
    config: Config,
    ctx: RunContext,
    period_ym: str,
    units: List[Dict[str, Any]],
    page: Optional["Page"] = None,
) -> Tuple[Dict[str, Any], "Page"]:
    """Download SE004 Detail Kode Gangguan data for single period, all selected units, all kelompok.
    
    For each unit, downloads 3 files (DISTRIBUSI, TRANSMISI, PEMBANGKIT).
    Total files = units × 3
    
    Focus on download only - parsing and Google Sheets to be added later.
    
    Args:
        config: Configuration object
        ctx: Run context
        period_ym: Period in YYYYMM format (e.g., '202501')
        units: List of unit dictionaries to download
        page: Existing browser page (optional, will create if not provided)
        
    Returns:
        Tuple of (results dict, page)
    """
    logger = get_logger()
    dataset_url = "https://new-apktss.pln.co.id/home/laporan-detil-kode-gangguan-se004"
    
    # Parse period
    month_name, year = parse_period_ym(period_ym)
    
    # Total downloads = units × kelompok (3)
    total_downloads = len(units) * len(KELOMPOK_OPTIONS)
    
    # Initialize results
    results = {
        "total": total_downloads,
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
    }
    
    playwright = None
    browser = None
    context = None
    page_from_browser = None
    should_close_browser = False
    
    try:
        print("\n" + "=" * 60)
        print(f"SE004 Detail Kode Gangguan: {month_name} {year} ({period_ym})")
        print("=" * 60)
        print(f"Units: {len(units)} | Kelompok: {len(KELOMPOK_OPTIONS)} | Total: {total_downloads} files")
        
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
        
        # Navigate to APKT-SS (click link to transfer token/session)
        print("Navigating to APKT-SS...")
        _navigate_to_apktss(page)
        
        # Navigate to Detail Gangguan page with retry
        print(f"Navigating to SE004 Detail Kode Gangguan report...")
        logger.info(f"Current URL before navigation: {page.url}")
        logger.info(f"Target URL: {dataset_url}")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Navigation attempt {attempt+1}/{max_retries}...")
                page.goto(dataset_url, timeout=60000, wait_until="domcontentloaded")  # Less strict wait
                logger.info(f"Page loaded (domcontentloaded), waiting for networkidle...")
                try:
                    page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    logger.warning("networkidle timeout, continuing anyway...")
                page.wait_for_timeout(3000)  # Extra wait for page rendering
                logger.info(f"After navigation, URL: {page.url}")
                break
            except Exception as e:
                logger.warning(f"⚠ Navigation attempt {attempt+1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    logger.info("Retrying navigation...")
                    page.wait_for_timeout(2000)
                else:
                    raise
        
        # Ensure page is truly ready - Menu 3 uses vc-component-9 for month
        try:
            page.wait_for_function("document.querySelector('select[name=\"vc-component-9\"]') !== null", timeout=20000)
            logger.info("✓ Page fully ready, selectors available")
        except Exception as e:
            logger.warning(f"⚠ Page readiness check timeout (may still work): {e}")
        
        # Verify page loaded with correct selector for Menu 3
        logger.info(f"🔍 Verifying page loaded...")
        try:
            page.wait_for_selector("select[name='vc-component-9']", timeout=5000)
            logger.info(f"✓ Page verified, month selector found")
        except Exception as e:
            logger.warning(f"⚠ Selector not immediately visible, trying reload...")
            page.reload()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(3000)
        
        # Set period filter once for all units
        print(f"Setting period: {month_name} {year}...")
        _set_period_filter(page, month_name, year)
        
        # Track download counter
        download_counter = 0
        
        # Download for each unit
        for i, unit in enumerate(units, 1):
            unit_text = unit["text"]
            unit_code = unit.get("code", unit_text.replace(" ", "_").upper()[:20])
            
            print("\n" + "=" * 60)
            print(f"[Unit {i}/{len(units)}] {unit_text}")
            print("=" * 60)
            
            # Set unit filter once per unit
            try:
                _set_unit_filter(page, unit_text)
                page.wait_for_timeout(1500)
            except Exception as e:
                print(f"✗ Failed to set unit filter: {e}")
                # Mark all 3 kelompok as failed
                for kelompok in KELOMPOK_OPTIONS:
                    results["failed"] += 1
                    results["errors"].append({
                        "unit": unit_text,
                        "kelompok": kelompok["text"],
                        "error": f"Unit filter failed: {str(e)}",
                    })
                continue
            
            # Download for each kelompok
            for j, kelompok in enumerate(KELOMPOK_OPTIONS, 1):
                kelompok_text = kelompok["text"]
                download_counter += 1
                
                print(f"\n  [{download_counter}/{total_downloads}] {kelompok_text}")
                print(f"  " + "-" * 40)
                
                try:
                    # Set kelompok filter
                    _set_kelompok_filter(page, kelompok_text)
                    
                    # Wait for data to load
                    page.wait_for_timeout(2000)
                    
                    # Generate filename with kelompok
                    safe_kelompok = kelompok_text.lower()
                    target_filename = f"se004_detail_{period_ym}_{unit_code}_{safe_kelompok}.xlsx"
                    
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
                    
                    print(f"  ✓ Downloaded: {target_filename}")
                    results["success"] += 1
                    results["files"].append(str(downloaded_path))
                
                except NoDataFoundError as e:
                    # No data for this filter - skip without retry
                    print(f"  ⚠ Skipped (no data): {kelompok_text}")
                    results["failed"] += 1
                    results["errors"].append({
                        "unit": unit_text,
                        "kelompok": kelompok_text,
                        "error": "Data tidak ditemukan",
                    })
                    
                except Exception as e:
                    print(f"  ✗ Failed: {e}")
                    results["failed"] += 1
                    results["errors"].append({
                        "unit": unit_text,
                        "kelompok": kelompok_text,
                        "error": str(e),
                    })
        
        # Print download summary
        print("\n" + "=" * 60)
        print("DOWNLOAD SUMMARY")
        print("=" * 60)
        print(f"  Total      : {results['total']} files")
        print(f"  ✓ Success  : {results['success']}")
        print(f"  ✗ Failed   : {results['failed']}")
        print(f"  Directory  : {ctx.excel_dir}")
        
        if results['errors']:
            print(f"\n  Errors:")
            for err in results['errors'][:5]:
                print(f"    - {err['unit']} / {err['kelompok']}: {err['error'][:50]}")
        
        # Save manifest
        manifest = {
            "type": "se004_detail_gangguan",
            "period": period_ym,
            "month": month_name,
            "year": year,
            "url": dataset_url,
            "download_date": ctx.snapshot_date,
            "units_count": len(units),
            "kelompok_count": len(KELOMPOK_OPTIONS),
            "files_downloaded": len(results["files"]),
            "files_expected": total_downloads,
            "files": results["files"],
            "errors": results["errors"],
        }
        
        manifest_path = ctx.run_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Manifest saved: {manifest_path}")
        
        # Step 2: Parse all downloaded Excel files
        print("\n" + "=" * 60)
        print("PARSING EXCEL FILES")
        print("=" * 60)
        
        from .parser_detail_gangguan import parse_run_directory  # Lazy import
        parse_results = parse_run_directory(ctx.run_dir)
        
        if parse_results.get('success'):
            results['rows_parsed'] = parse_results.get('total_rows', 0)
            results['parsed_csv_path'] = parse_results.get('output_path')
            print(f"  ✓ Parsed: {results['rows_parsed']:,} rows")
            print(f"  ✓ Output: {results['parsed_csv_path']}")
            
            # Update manifest with parsing info
            manifest['parsed'] = {
                'rows': results['rows_parsed'],
                'csv_path': results['parsed_csv_path'],
                'summary': parse_results.get('summary', []),
            }
        else:
            print(f"  ✗ Parsing failed: {parse_results.get('error')}")
        
        # Step 3: Upload to Google Sheets if enabled
        gs_config = config.data.get('google_sheets', {})
        if gs_config.get('enabled') and results.get('parsed_csv_path'):
            print("\n" + "=" * 60)
            print("UPLOAD TO GOOGLE SHEETS")
            print("=" * 60)
            
            try:
                import pandas as pd
                
                spreadsheet_id = gs_config.get('spreadsheet_id')
                worksheet_name = 'detilTM_komulatif'  # Fixed worksheet name for Menu 3
                credentials_path = gs_config.get('credentials_json_path')
                
                print(f"  Spreadsheet: {spreadsheet_id}")
                print(f"  Worksheet : {worksheet_name}")
                
                # Read CSV and upload
                parsed_csv = results.get('parsed_csv_path')
                if not parsed_csv:
                    raise ValueError("No parsed CSV path available")
                
                csv_path = Path(parsed_csv)
                if not csv_path.exists():
                    raise FileNotFoundError(f"Parsed CSV not found: {csv_path}")
                
                df = pd.read_csv(csv_path, low_memory=False)
                df = df.fillna('')
                
                # Filter: Only keep rows where no_laporan starts with J or P
                original_count = len(df)
                df = df[df['no_laporan'].astype(str).str.upper().str.match(r'^[JP]')]
                filtered_count = len(df)
                print(f"  Filter: {filtered_count:,} rows (J/P only) from {original_count:,} total")
                
                upload_result = upload_dataframe_to_worksheet(
                    df=df,
                    spreadsheet_id=spreadsheet_id,
                    worksheet_name=worksheet_name,
                    credentials_json_path=credentials_path,
                    mode=gs_config.get('sheets_mode', 'smart'),  # From config: 'smart', 'update', 'append', or 'replace'
                    period_column='period',  # Column to match for smart/update modes
                    period_value=period_ym,
                )
                
                if upload_result.get('success'):
                    results['sheet_uploaded'] = True
                    results['sheet_worksheet'] = worksheet_name
                    results['sheet_row_count'] = upload_result.get('row_count', 0)
                    print(f"  ✓ Uploaded: {results['sheet_row_count']:,} rows to '{worksheet_name}'")
                    
                    manifest['google_sheets'] = {
                        'uploaded': True,
                        'worksheet': worksheet_name,
                        'rows': results['sheet_row_count'],
                    }
                else:
                    print(f"  ✗ Upload failed")
                    
            except Exception as e:
                logger.error(f"Google Sheets upload failed: {e}")
                print(f"  ✗ Upload failed: {e}")
        else:
            if not gs_config.get('enabled'):
                print("\n  ℹ Google Sheets upload disabled in config")
        
        # Save updated manifest
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        return results, page
    
    except Exception as e:
        logger.error(f"SE004 Detail Gangguan extraction failed: {e}")
        raise
