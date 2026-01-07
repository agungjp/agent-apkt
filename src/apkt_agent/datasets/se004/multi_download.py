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
    if "new-apktss.pln.co.id" in page.url:
        return
    
    page.wait_for_timeout(2000)
    
    apktss = page.locator("p:has-text('APKT-SS')").first
    if apktss:
        apktss.click()
        try:
            page.wait_for_url("**/new-apktss.pln.co.id/**", timeout=15000)
        except Exception:
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
    
    if "new-apktss.pln.co.id" not in page.url:
        raise Exception(f"Failed to navigate to APKT-SS. Current URL: {page.url}")


def _set_unit_filter(page, unit_text: str) -> None:
    """Set the Unit Induk filter."""
    unit_select = page.locator("select#unitInduk, select[name='unitInduk']").first
    unit_select.select_option(label=unit_text)
    page.wait_for_timeout(1000)


def _set_period_filter(page, month_name: str, year: str) -> None:
    """Set the Period filter (month and year)."""
    # Set Month
    month_select = page.locator("select[name='vc-component-4']").first
    month_select.select_option(label=month_name)
    page.wait_for_timeout(500)
    
    # Set Year
    year_select = page.locator("select[name='vc-component-6']").first
    year_select.select_option(label=year)
    page.wait_for_timeout(500)


def _click_export_excel(page) -> None:
    """Click Export button and select Excel."""
    # Click Eksport button
    export_btn = page.locator("button:has-text('Eksport')").first
    export_btn.click()
    page.wait_for_timeout(500)
    
    # Click Excel option
    excel_btn = page.locator("button:has-text('Excel')").first
    excel_btn.click()
