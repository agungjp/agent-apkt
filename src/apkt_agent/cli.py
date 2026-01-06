"""Command-line interface for APKT Agent."""

import sys
from datetime import datetime
from typing import Optional, Tuple

import requests

from .config import Config, load_config
from .logging_ import setup_logger, get_logger
from .workspace import RunContext, create_run
from .datasets.registry import DatasetRegistry
from .datasets.se004.extract_filters import extract_se004_filters, print_filters, save_filters_to_json
from .datasets.se004.multi_download import load_units_selection, run_multi_unit_download


def check_url(url: str, timeout: int = 10) -> Tuple[bool, str]:
    """Check connectivity to a URL.
    
    Args:
        url: URL to check
        timeout: Timeout in seconds (default: 10)
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return True, f"OK (HTTP {response.status_code})"
    except requests.exceptions.Timeout:
        return False, f"Timeout after {timeout}s"
    except requests.exceptions.ConnectionError as e:
        return False, f"Connection error: {e}"
    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {e}"


def check_connectivity(config: Config) -> bool:
    """Check connectivity to APKT services.
    
    Args:
        config: Configuration object
        
    Returns:
        True if should continue, False if should exit
    """
    logger = get_logger()
    
    print("\n" + "-" * 60)
    print("Checking connectivity...")
    print("-" * 60)
    
    login_url = config.get('apkt.login_url')
    
    if not login_url:
        logger.warning("No login_url configured, skipping connectivity check")
        return True
    
    print(f"  → {login_url} ... ", end="", flush=True)
    success, message = check_url(login_url)
    
    if success:
        print(f"✓ {message}")
        logger.info(f"Connectivity check passed: {login_url} - {message}")
        return True
    else:
        print(f"✗ {message}")
        logger.warning(f"Connectivity check failed: {login_url} - {message}")
        
        print("\n⚠ Network connectivity issue detected!")
        print("  You may experience problems during automation.")
        
        while True:
            choice = input("\nContinue anyway? (y/n): ").strip().lower()
            if choice == 'y':
                logger.info("User chose to continue despite connectivity issue")
                return True
            elif choice == 'n':
                logger.info("User chose to exit due to connectivity issue")
                return False
            else:
                print("Please enter 'y' or 'n'")


def print_menu() -> None:
    """Print main CLI menu."""
    print("\n" + "=" * 60)
    print("APKT Agent - Data Extraction Tool")
    print("=" * 60)
    print("\n1. Run extraction (SE004 Rolling) [stub]")
    print("2. Run extraction (SE004 Kumulatif) - Single Unit")
    print("3. Run extraction (SE004 Kumulatif) - Multi Unit")
    print("4. Run extraction (SE004 Gangguan) [stub]")
    print("5. Extract filter options (SE004 Kumulatif)")
    print("6. View latest run")
    print("7. Settings")
    print("8. Exit")
    print("\n" + "-" * 60)


def handle_menu_choice(choice: str, config: Config) -> bool:
    """Handle menu choice.
    
    Args:
        choice: User choice
        config: Configuration object
        
    Returns:
        False if exit, True otherwise
    """
    logger = get_logger()
    
    if choice == "1":
        logger.info("Selected: SE004 Rolling")
        run_extraction("se004_rolling", config)
        return True
    
    elif choice == "2":
        logger.info("Selected: SE004 Kumulatif - Single Unit")
        run_extraction_with_prompt("se004_kumulatif", config)
        return True
    
    elif choice == "3":
        logger.info("Selected: SE004 Kumulatif - Multi Unit")
        run_multi_unit_extraction(config)
        return True
    
    elif choice == "4":
        logger.info("Selected: SE004 Gangguan")
        run_extraction("se004_gangguan", config)
        return True
    
    elif choice == "5":
        logger.info("Selected: Extract filter options")
        run_extract_filters(config)
        return True
    
    elif choice == "6":
        logger.info("Selected: View latest run")
        # TODO: Implement latest run viewer
        return True
    
    elif choice == "7":
        logger.info("Selected: Settings")
        # TODO: Implement settings menu
        return True
    
    elif choice == "8":
        logger.info("Exiting application")
        return False
    
    else:
        print("Invalid choice. Please try again.")
        return True


def run_extraction_with_prompt(dataset: str, config: Config) -> None:
    """Run extraction with period input prompt.
    
    Args:
        dataset: Dataset name
        config: Configuration object
    """
    logger = get_logger()
    
    # Get default period from config
    default_period = config.get(f'datasets.{dataset}.period_default')
    if not default_period:
        default_period = datetime.now().strftime('%Y%m')
    
    # Prompt for period
    print(f"\nDefault period: {default_period}")
    period_input = input(f"Enter period (YYYYMM) or press Enter for default: ").strip()
    
    if period_input:
        period_ym = period_input
    else:
        period_ym = default_period
    
    # Validate format
    if not (len(period_ym) == 6 and period_ym.isdigit()):
        print(f"✗ Invalid period format: {period_ym}. Expected YYYYMM.")
        return
    
    logger.info(f"Using period: {period_ym}")
    
    # Snapshot date is today
    snapshot_date = datetime.now().strftime('%Y%m%d')
    
    try:
        # Create run context
        ctx = create_run(dataset, period_ym, snapshot_date, config)
        
        # Re-setup logger with file handler
        logger = setup_logger(ctx=ctx)
        
        logger.info(f"Created run: {ctx.run_id}")
        logger.info(f"Run directory: {ctx.run_dir}")
        
        # Get handler from registry and run
        handler = DatasetRegistry.get_handler(dataset, config)
        result = handler.run(ctx)
        
        # Display result summary
        print("\n" + "-" * 60)
        print("Run Summary")
        print("-" * 60)
        
        if result.success:
            print(f"  Status: ✓ {result.message}")
        else:
            print(f"  Status: ✗ {result.message}")
        
        print(f"  Run ID: {ctx.run_id}")
        print(f"  Directory: {ctx.run_dir}")
        print(f"  Files downloaded: {len(result.files_downloaded)}")
        if result.files_downloaded:
            for f in result.files_downloaded:
                print(f"    - {f}")
        print(f"  Rows parsed: {result.rows_parsed}")
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        print(f"\n✗ Extraction failed: {e}")


def run_extraction(dataset: str, config: Config) -> None:
    """Run extraction for a dataset.
    
    Args:
        dataset: Dataset name
        config: Configuration object
    """
    logger = get_logger()
    
    # Get period from config or use current month
    period_ym = config.get(f'datasets.{dataset}.period_default')
    if not period_ym:
        period_ym = datetime.now().strftime('%Y%m')
    
    # Snapshot date is today
    snapshot_date = datetime.now().strftime('%Y%m%d')
    
    try:
        # Create run context
        ctx = create_run(dataset, period_ym, snapshot_date, config)
        
        # Re-setup logger with file handler
        logger = setup_logger(ctx=ctx)
        
        logger.info(f"Created run: {ctx.run_id}")
        logger.info(f"Run directory: {ctx.run_dir}")
        logger.info(f"Dataset: {dataset}, Period: {period_ym}, Snapshot: {snapshot_date}")
        
        # TODO: Implement actual extraction
        logger.info("Extraction not yet implemented (stub)")
        
        print(f"\n✓ Run created: {ctx.run_id}")
        print(f"  Directory: {ctx.run_dir}")
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        print(f"\n✗ Extraction failed: {e}")


def run_extract_filters(config: Config) -> None:
    """Extract and display filter options from SE004 Kumulatif.
    
    Args:
        config: Configuration object
    """
    logger = get_logger()
    
    print("\n" + "=" * 60)
    print("Extracting filter options from SE004 Kumulatif...")
    print("=" * 60)
    
    # Create a minimal run context for browser operations
    snapshot_date = datetime.now().strftime('%Y%m%d')
    period_ym = datetime.now().strftime('%Y%m')
    
    try:
        ctx = create_run("se004_filters", period_ym, snapshot_date, config)
        
        # Extract filters
        filters = extract_se004_filters(config, ctx)
        
        # Print to console
        print_filters(filters)
        
        # Save to JSON in workspace
        from pathlib import Path
        output_path = Path(config.get('workspace.base_dir', 'workspace')) / "se004_filters.json"
        save_filters_to_json(filters, output_path)
        
        print(f"\n✓ Filter options extracted successfully!")
        print(f"  Total Unit Induk: {len(filters['unit_induk'])}")
        print(f"  Total Bulan: {len(filters['bulan'])}")
        print(f"  Total Tahun: {len(filters['tahun'])}")
        
    except Exception as e:
        logger.error(f"Failed to extract filters: {e}")
        print(f"\n✗ Failed to extract filters: {e}")


def run_multi_unit_extraction(config: Config) -> None:
    """Run multi-unit extraction for SE004 Kumulatif.
    
    Args:
        config: Configuration object
    """
    from pathlib import Path
    
    logger = get_logger()
    
    # Load units from selection file
    units_file = Path("units_selection.yaml")
    if not units_file.exists():
        print(f"\n✗ File tidak ditemukan: {units_file}")
        print("  Buat file units_selection.yaml terlebih dahulu.")
        return
    
    try:
        units = load_units_selection(units_file)
    except Exception as e:
        print(f"\n✗ Error loading units: {e}")
        return
    
    if not units:
        print("\n✗ Tidak ada unit yang dipilih di units_selection.yaml")
        return
    
    # Show selected units
    print("\n" + "=" * 60)
    print("Unit yang akan didownload:")
    print("=" * 60)
    for i, unit in enumerate(units, 1):
        print(f"  {i:2}. {unit['text']} [{unit['code']}]")
    
    # Get period input
    print("\n" + "-" * 60)
    print("FORMAT PERIODE: YYYYMM")
    print("-" * 60)
    print("  YYYY = Tahun (4 digit)")
    print("  MM   = Bulan (2 digit: 01-12)")
    print("")
    print("  Contoh:")
    print("    202512 = Desember 2025")
    print("    202501 = Januari 2025")
    print("    202406 = Juni 2024")
    print("-" * 60)
    
    default_period = datetime.now().strftime('%Y%m')
    period_input = input(f"\nMasukkan periode (default: {default_period}): ").strip()
    
    if period_input:
        period_ym = period_input
    else:
        period_ym = default_period
    
    # Validate format
    if not (len(period_ym) == 6 and period_ym.isdigit()):
        print(f"\n✗ Format periode tidak valid: {period_ym}")
        print("  Format yang benar: YYYYMM (contoh: 202512)")
        return
    
    # Validate month
    month = period_ym[4:6]
    if not (1 <= int(month) <= 12):
        print(f"\n✗ Bulan tidak valid: {month}")
        print("  Bulan harus antara 01-12")
        return
    
    # Confirm
    year = period_ym[:4]
    month_names = {
        "01": "Januari", "02": "Februari", "03": "Maret",
        "04": "April", "05": "Mei", "06": "Juni",
        "07": "Juli", "08": "Agustus", "09": "September",
        "10": "Oktober", "11": "November", "12": "Desember",
    }
    month_name = month_names.get(month, month)
    
    print(f"\n→ Periode: {month_name} {year}")
    print(f"→ Total unit: {len(units)}")
    
    confirm = input("\nLanjutkan download? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Download dibatalkan.")
        return
    
    # Create run context
    snapshot_date = datetime.now().strftime('%Y%m%d')
    ctx = create_run("se004_multi", period_ym, snapshot_date, config)
    
    # Re-setup logger
    logger = setup_logger(ctx=ctx)
    logger.info(f"Multi-unit download started: {len(units)} units, period {period_ym}")
    
    # Run multi-unit download
    results = run_multi_unit_download(config, ctx, units, period_ym)
    
    # Print summary
    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"  Total units: {results['total']}")
    print(f"  ✓ Success: {results['success']}")
    print(f"  ✗ Failed: {results['failed']}")
    print(f"  Run directory: {ctx.run_dir}")
    
    if results['files']:
        print("\nFiles downloaded:")
        for f in results['files']:
            print(f"  → {Path(f).name}")
    
    if results['errors']:
        print("\nErrors:")
        for err in results['errors']:
            print(f"  ✗ {err['unit']}: {err['error']}")
    
    # Show parsing results
    if results.get('parsed_csv_path'):
        print("\n" + "-" * 60)
        print("PARSING RESULT")
        print("-" * 60)
        print(f"  ✓ Rows parsed: {results.get('rows_parsed', 0)}")
        print(f"  ✓ CSV file: {Path(results['parsed_csv_path']).name}")
        
        if results.get('validation_warnings'):
            print(f"\n  ⚠ Validation warnings: {len(results['validation_warnings'])}")
            for w in results['validation_warnings'][:5]:
                print(f"    - {w}")


def main() -> int:
    """Main CLI entry point."""
    try:
        config = load_config()
        logger = setup_logger()
        
        logger.info("APKT Agent CLI started")
        
        # Check connectivity before showing menu
        if not check_connectivity(config):
            print("\nExiting due to connectivity issue.")
            return 1
        
        # Interactive menu
        while True:
            print_menu()
            choice = input("Enter your choice (1-8): ").strip()
            
            if not handle_menu_choice(choice, config):
                break
        
        return 0
    
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user.")
        return 1
    
    except Exception as e:
        print(f"\nFatal error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
