"""Extract filter options from SE004 Kumulatif page."""

import json
from pathlib import Path
from typing import Any

from ...browser.auth import login_apkt
from ...browser.driver import open_browser, close_browser
from ...workspace import RunContext
from ...config import Config


def extract_select_options(page, selector: str) -> list[dict[str, str]]:
    """Extract all options from a select element.
    
    Args:
        page: Playwright page object
        selector: CSS selector for the select element
        
    Returns:
        List of dicts with 'value' and 'text' keys
    """
    options = []
    try:
        select_elem = page.locator(selector).first
        if select_elem.count() == 0:
            return options
            
        # Get all option elements
        option_elems = select_elem.locator("option")
        count = option_elems.count()
        
        for i in range(count):
            opt = option_elems.nth(i)
            value = opt.get_attribute("value") or ""
            text = opt.inner_text().strip()
            if text:  # Skip empty options
                options.append({
                    "value": value,
                    "text": text,
                })
    except Exception as e:
        print(f"Error extracting options from {selector}: {e}")
    
    return options


def extract_se004_filters(config: Config, ctx: RunContext) -> dict[str, Any]:
    """Extract all filter options from SE004 Kumulatif page.
    
    Args:
        config: Configuration object
        ctx: Run context
        
    Returns:
        Dict with all filter options
    """
    dataset_url = config.get(
        'datasets.se004_kumulatif.url',
        'https://new-apktss.pln.co.id/home/laporan-saidi-saifi-kumulatif-se004'
    )
    
    playwright = None
    browser = None
    context = None
    
    filters = {
        "unit_induk": [],
        "bulan": [],
        "tahun": [],
    }
    
    try:
        # Step 1: Open browser
        playwright, browser, context, page = open_browser(ctx, config)
        print("Browser opened, starting authentication...")
        
        # Step 2: Login to APKT via SSO/IAM
        login_apkt(page, ctx, config)
        print("Authentication successful")
        
        # Step 3: Navigate to APKT-SS
        print("Navigating to APKT-SS...")
        _navigate_to_apktss(page)
        
        # Step 4: Navigate to SE004 Kumulatif page
        print(f"Navigating to: {dataset_url}")
        page.goto(dataset_url)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)  # Wait for Angular/React to render
        
        print(f"Current URL: {page.url}")
        
        # Step 5: Extract filter options
        print("\n=== EXTRACTING FILTER OPTIONS ===\n")
        
        # Unit Induk dropdown
        print("Extracting Unit Induk options...")
        filters["unit_induk"] = extract_select_options(page, "select#unitInduk")
        print(f"Found {len(filters['unit_induk'])} unit options")
        
        # Bulan (Month) dropdown
        print("Extracting Bulan (Month) options...")
        filters["bulan"] = extract_select_options(page, "select[name='vc-component-4']")
        print(f"Found {len(filters['bulan'])} month options")
        
        # Tahun (Year) dropdown
        print("Extracting Tahun (Year) options...")
        filters["tahun"] = extract_select_options(page, "select[name='vc-component-6']")
        print(f"Found {len(filters['tahun'])} year options")
        
        return filters
        
    except Exception as e:
        print(f"Error extracting filters: {e}")
        raise
        
    finally:
        if playwright or browser or context:
            close_browser(playwright, browser, context)


def _navigate_to_apktss(page) -> None:
    """Navigate from APKT home to APKT-SS subdomain."""
    if "new-apktss.pln.co.id" in page.url:
        return
    
    page.wait_for_timeout(2000)
    
    # Click APKT-SS card
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


def save_filters_to_json(filters: dict, output_path: Path) -> None:
    """Save filter options to JSON file.
    
    Args:
        filters: Filter options dict
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(filters, f, ensure_ascii=False, indent=2)
    print(f"Filters saved to: {output_path}")


def print_filters(filters: dict) -> None:
    """Print filter options in readable format."""
    print("\n" + "="*60)
    print("UNIT INDUK OPTIONS")
    print("="*60)
    for i, unit in enumerate(filters["unit_induk"], 1):
        print(f"  {i:2}. [{unit['value']:3}] {unit['text']}")
    
    print("\n" + "="*60)
    print("BULAN (MONTH) OPTIONS")
    print("="*60)
    for i, bulan in enumerate(filters["bulan"], 1):
        print(f"  {i:2}. {bulan['text']}")
    
    print("\n" + "="*60)
    print("TAHUN (YEAR) OPTIONS")
    print("="*60)
    for i, tahun in enumerate(filters["tahun"], 1):
        print(f"  {i:2}. {tahun['text']}")
    
    print("\n")
