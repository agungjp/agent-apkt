"""Command-line interface for APKT Agent."""

import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional

import requests
from playwright.sync_api import sync_playwright, Page, Browser

from . import __version__
from .config import Config, load_config
from .logging_ import setup_logger, get_logger
from .workspace import create_run
from .datasets.se004.multi_download import load_units_selection, run_multi_unit_download
from .datasets.se004.bulanan import run_se004_bulanan as run_se004_bulanan_extraction
from .browser.auth import login_apkt


# Indonesian month names
BULAN_INDONESIA = {
    "01": "Januari", "02": "Februari", "03": "Maret",
    "04": "April", "05": "Mei", "06": "Juni",
    "07": "Juli", "08": "Agustus", "09": "September",
    "10": "Oktober", "11": "November", "12": "Desember",
}


def check_url(url: str, timeout: int = 10) -> Tuple[bool, str]:
    """Check connectivity to a URL."""
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
    """Check connectivity to APKT services."""
    logger = get_logger()
    
    print("\n" + "-" * 60)
    print("Memeriksa koneksi...")
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
        
        print("\n⚠ Koneksi bermasalah!")
        
        while True:
            choice = input("\nLanjutkan? (y/n): ").strip().lower()
            if choice == 'y':
                return True
            elif choice == 'n':
                return False
            else:
                print("Masukkan 'y' atau 'n'")


def print_header() -> None:
    """Print CLI header with version info."""
    print("\n" + "=" * 60)
    print("APKT Agent - Data Extraction Tool")
    print(f"Version {__version__} | Python {sys.version.split()[0]}")
    print("=" * 60)


def print_login_status(is_logged_in: bool, username: Optional[str] = None) -> None:
    """Print login status info."""
    print("\n" + "-" * 60)
    if is_logged_in and username:
        print(f"✓ Status Login: BERHASIL")
        print(f"  User: {username}")
    else:
        print(f"✗ Status Login: BELUM LOGIN")
    print("-" * 60)


def print_menu(is_logged_in: bool = False, username: Optional[str] = None, config: Optional[Config] = None) -> None:
    """Print main CLI menu with login status and settings."""
    print_login_status(is_logged_in, username)
    
    print("\n" + "-" * 60)
    print("MENU UTAMA")
    print("-" * 60)
    print("\n  1. Laporan SAIDI SAIFI SE004 (Bulanan)")
    print("  2. Laporan SAIDI SAIFI Kumulatif SE004")
    print("  3. Laporan Detail Kode Gangguan SE004 [stub]")
    print("\n  0. Keluar")
    print("\n" + "-" * 60)


def perform_login(config: Config) -> Tuple[Optional[Page], Optional[str]]:
    """Perform login to APKT system.
    
    Returns:
        Tuple of (page instance, username) or (None, None) if login failed
    """
    from .browser.driver import open_browser
    from .workspace import create_run
    
    logger = get_logger()
    
    print("\n" + "=" * 60)
    print("PROSES LOGIN")
    print("=" * 60)
    
    # Ask user for headless option during login (will be used for entire session)
    headless = get_headless_option()
    config.data['runtime'] = config.data.get('runtime', {})
    config.data['runtime']['headless'] = headless
    
    page = None
    try:
        # Create temporary context for login without creating run folder
        # We only need the excel_dir for browser download settings
        from .workspace import RunContext
        
        temp_excel_dir = Path.home() / ".cache" / "apkt-agent" / "downloads"
        temp_excel_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a minimal RunContext just for browser initialization
        ctx = RunContext(
            run_id="login_temp",
            dataset="login",
            period_ym="login",
            snapshot_date=datetime.now().strftime('%Y%m%d'),
            run_dir=temp_excel_dir,
            raw_dir=temp_excel_dir,
            excel_dir=temp_excel_dir,
            parsed_dir=temp_excel_dir,
            logs_dir=temp_excel_dir,
            manifest_path=temp_excel_dir / "manifest.json",
        )
        
        # Open browser with user's headless preference
        playwright, browser, context, page = open_browser(ctx, config)
        
        # Perform login
        login_apkt(page, ctx, config)
        
        print("\n✓ Login berhasil!")
        
        # Extract username from session or config
        username = "user"  # Default
        try:
            # Try to get username from credentials
            username = page.evaluate("() => window.localStorage.getItem('username') || 'user'")
        except:
            pass
        
        logger.info("User logged in successfully")
        # Return page but keep browser alive for session reuse
        return page, username
        
    except Exception as e:
        logger.error(f"Login failed: {e}")
        print(f"\n✗ Login gagal: {e}")
        # Close browser if login failed
        if page:
            try:
                page.context.browser.close()
            except:
                pass
        return None, None


def check_session_valid(page: Optional[Page]) -> bool:
    """Check if current session is still valid."""
    if not page:
        return False
    
    try:
        # Try a simple page operation to check if session is alive
        page.context  # Access context to verify page is still active
        return True
    except:
        return False


def get_period_input() -> str | None:
    """Get period input from user (interactive prompt).
    
    Returns:
        Period in YYYYMM format, or None if cancelled
    """
    print("\n" + "-" * 60)
    print("MASUKKAN PERIODE")
    print("-" * 60)
    print("  Format: YYYYMM")
    print("  YYYY = Tahun (4 digit)")
    print("  MM   = Bulan (01-12)")
    print("")
    print("  Contoh:")
    print("    202512 = Desember 2025")
    print("    202501 = Januari 2025")
    print("-" * 60)
    
    default_period = datetime.now().strftime('%Y%m')
    period_input = input(f"\nMasukkan periode (default: {default_period}): ").strip()
    
    if not period_input:
        period_input = default_period
    
    # Validate format
    if not (len(period_input) == 6 and period_input.isdigit()):
        print(f"\n✗ Format periode tidak valid: {period_input}")
        return None
    
    # Validate month
    month = period_input[4:6]
    if not (1 <= int(month) <= 12):
        print(f"\n✗ Bulan tidak valid: {month}")
        return None
    
    return period_input


def get_headless_option() -> bool:
    """Get headless option from user.
    
    Returns:
        True if headless (browser tidak tampil), False if visible
    """
    print("\n" + "-" * 60)
    print("OPSI TAMPILAN BROWSER")
    print("-" * 60)
    print("  y = Tidak tampil (headless) - lebih cepat")
    print("  n = Tampil di layar - untuk debugging")
    print("-" * 60)
    
    choice = input("\nJalankan tanpa tampilan browser? (Y/n): ").strip().lower()
    
    # Default is headless (y)
    if choice == '' or choice == 'y':
        return True
    elif choice == 'n':
        return False
    else:
        return True  # Default headless


def run_stub(menu_name: str) -> None:
    """Run stub for unimplemented menu."""
    logger = get_logger()
    logger.info(f"Selected: {menu_name} (stub)")
    
    print("\n" + "=" * 60)
    print(f"  {menu_name}")
    print("=" * 60)
    print("\n  ⚠ Fitur ini belum diimplementasi.")
    print("  Akan dikembangkan pada versi selanjutnya.")
    print("\n" + "=" * 60)
    
    input("\nTekan Enter untuk kembali ke menu...")


def run_se004_bulanan(config: Config, page: Optional[Page] = None) -> Optional[Page]:
    """Run SE004 monthly report extraction.
    
    Args:
        config: Configuration object
        page: Optional existing Playwright page instance
        
    Returns:
        Playwright page instance (new or reused)
    """
    logger = get_logger()
    logger.info("Selected: Laporan SAIDI SAIFI SE004 Bulanan")
    
    print("\n" + "=" * 60)
    print("  LAPORAN SAIDI SAIFI SE004 (BULANAN)")
    print("=" * 60)
    
    # Step 1: Get period
    period_ym = get_period_input()
    if not period_ym:
        input("\nTekan Enter untuk kembali ke menu...")
        return page
    
    year = period_ym[:4]
    month = period_ym[4:6]
    month_name = BULAN_INDONESIA.get(month, month)
    
    # Step 2: Get browser mode from config (set during login)
    headless = config.data.get('runtime', {}).get('headless', True)
    
    # Step 3: Confirm
    print("\n" + "=" * 60)
    print("KONFIRMASI")
    print("=" * 60)
    print(f"  Periode    : {month_name} {year}")
    print(f"  Browser    : {'Tidak tampil (headless)' if headless else 'Tampil di layar'}")
    print("=" * 60)
    
    confirm = input("\nLanjutkan download? (y/n): ").strip().lower()
    if confirm != 'y':
        print("\n✗ Download dibatalkan.")
        input("\nTekan Enter untuk kembali ke menu...")
        return page
    
    # Step 4: Load units
    search_paths = [
        Path("credentials/units_selection.yaml"),
        Path("units_selection.yaml")
    ]
    
    units_file = None
    for path in search_paths:
        if path.exists():
            units_file = path
            break
    
    if not units_file:
        print(f"\n✗ File tidak ditemukan: units_selection.yaml")
        input("\nTekan Enter untuk kembali ke menu...")
        return page
    
    try:
        units = load_units_selection(units_file)
    except Exception as e:
        print(f"\n✗ Error loading units: {e}")
        input("\nTekan Enter untuk kembali ke menu...")
        return page
    
    if not units:
        print("\n✗ Tidak ada unit yang dipilih di units_selection.yaml")
        input("\nTekan Enter untuk kembali ke menu...")
        return page
    
    # Step 5: Show selected units
    print("\n" + "-" * 60)
    print("UNIT YANG AKAN DIDOWNLOAD")
    print("-" * 60)
    for i, unit in enumerate(units, 1):
        print(f"  {i:2}. {unit['text']}")
    print(f"\n  Total: {len(units)} unit")
    
    # Step 6: Create run context
    snapshot_date = datetime.now().strftime('%Y%m%d')
    ctx = create_run("se004_bulanan", period_ym, snapshot_date, config)
    
    # Re-setup logger
    logger = setup_logger(ctx=ctx)
    logger.info(f"Starting SE004 Bulanan extraction")
    logger.info(f"Period: {period_ym}, Units: {len(units)}, Headless: {headless}")
    
    # Step 7: Run extraction
    print("\n" + "=" * 60)
    print("MEMULAI PROSES EKSTRAKSI")
    print("=" * 60)
    print(f"  Run ID     : {ctx.run_id}")
    print(f"  Direktori  : {ctx.run_dir}")
    print("=" * 60)
    
    try:
        results, page = run_se004_bulanan_extraction(config, ctx, period_ym, units, page=page)
        
        # Step 6: Print final summary
        print("\n" + "=" * 60)
        print("HASIL EKSTRAKSI")
        print("=" * 60)
        print(f"\n  📊 RINGKASAN")
        print(f"  " + "-" * 40)
        print(f"  Total unit      : {results.get('total', 0)}")
        print(f"  ✓ Berhasil      : {results.get('success', 0)}")
        print(f"  ✗ Gagal         : {results.get('failed', 0)}")
        
        # Show failed units with errors
        if results.get('errors'):
            print(f"\n  ❌ DAFTAR ERROR: {len(results['errors'])} unit gagal")
            for error in results['errors'][:5]:
                print(f"     - {error}")
            if len(results['errors']) > 5:
                print(f"     ... dan {len(results['errors']) - 5} lainnya")
        
        if results.get('rows_parsed'):
            print(f"\n  📄 HASIL PARSING")
            print(f"  " + "-" * 40)
            print(f"  Total baris     : {results['rows_parsed']:,}")
            print(f"  File CSV        : {Path(results.get('parsed_csv_path', '')).name}")
        
        # Google Sheets upload status
        if results.get('sheet_uploaded') is not None:
            print(f"\n  📤 GOOGLE SHEETS")
            print(f"  " + "-" * 40)
            if results.get('sheet_uploaded'):
                print(f"  Status          : ✓ Berhasil diupload")
                print(f"  Worksheet       : {results.get('sheet_worksheet', '-')}")
                print(f"  Baris diupload  : {results.get('sheet_row_count', 0):,}")
            else:
                print(f"  Status          : ✗ Gagal")
                print(f"  Error           : {results.get('sheet_error', 'Unknown')[:50]}")
                print(f"  (Lihat manifest.json untuk detail)")
        
        print(f"\n  📁 LOKASI FILE")
        print(f"  " + "-" * 40)
        print(f"  Run directory   : {ctx.run_dir}")
        print(f"  Excel files     : {ctx.excel_dir}")
        print(f"  Parsed CSV      : {ctx.parsed_dir}")
        
        print("\n" + "=" * 60)
        logger.info(f"Extraction completed")
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        print(f"\n✗ Ekstraksi gagal: {e}")
    
    input("\nTekan Enter untuk kembali ke menu...")
    return page


def run_se004_kumulatif(config: Config, page: Optional[Page] = None) -> Optional[Page]:
    """Run SE004 Kumulatif extraction.
    
    Args:
        config: Configuration object
        page: Optional existing Playwright page instance
        
    Returns:
        Playwright page instance (new or reused)
    """
    logger = get_logger()
    logger.info("Selected: Laporan SAIDI SAIFI Kumulatif SE004")
    
    print("\n" + "=" * 60)
    print("  LAPORAN SAIDI SAIFI KUMULATIF SE004")
    print("=" * 60)
    
    # Step 1: Load units - search in credentials folder first, then root
    search_paths = [
        Path("credentials/units_selection.yaml"),
        Path("units_selection.yaml")
    ]
    
    units_file = None
    for path in search_paths:
        if path.exists():
            units_file = path
            break
    
    if not units_file:
        print(f"\n✗ File tidak ditemukan: units_selection.yaml")
        print(f"  Cari di: {' atau '.join(str(p) for p in search_paths)}")
        input("\nTekan Enter untuk kembali ke menu...")
        return page
    
    try:
        units = load_units_selection(units_file)
    except Exception as e:
        print(f"\n✗ Error loading units: {e}")
        input("\nTekan Enter untuk kembali ke menu...")
        return page
    
    if not units:
        print("\n✗ Tidak ada unit yang dipilih di units_selection.yaml")
        input("\nTekan Enter untuk kembali ke menu...")
        return page
    
    # Step 2: Show selected units
    print("\n" + "-" * 60)
    print("UNIT YANG AKAN DIDOWNLOAD")
    print("-" * 60)
    for i, unit in enumerate(units, 1):
        print(f"  {i:2}. {unit['text']}")
    print(f"\n  Total: {len(units)} unit")
    
    # Step 3: Get period
    period_ym = get_period_input()
    if not period_ym:
        input("\nTekan Enter untuk kembali ke menu...")
        return page
    
    year = period_ym[:4]
    month = period_ym[4:6]
    month_name = BULAN_INDONESIA.get(month, month)
    
    # Step 4: Get browser mode from config (set during login)
    headless = config.data.get('runtime', {}).get('headless', True)
    
    # Step 5: Confirm
    print("\n" + "=" * 60)
    print("KONFIRMASI")
    print("=" * 60)
    print(f"  Periode    : {month_name} {year}")
    print(f"  Total Unit : {len(units)}")
    print(f"  Browser    : {'Tidak tampil (headless)' if headless else 'Tampil di layar'}")
    print("=" * 60)
    
    confirm = input("\nLanjutkan download? (y/n): ").strip().lower()
    if confirm != 'y':
        print("\n✗ Download dibatalkan.")
        input("\nTekan Enter untuk kembali ke menu...")
        return page
    
    # Step 6: Create run context
    snapshot_date = datetime.now().strftime('%Y%m%d')
    ctx = create_run("se004_kumulatif", period_ym, snapshot_date, config)
    
    # Re-setup logger
    logger = setup_logger(ctx=ctx)
    logger.info(f"Starting SE004 Kumulatif extraction")
    logger.info(f"Period: {period_ym}, Units: {len(units)}, Headless: {headless}")
    
    # Step 7: Run extraction
    print("\n" + "=" * 60)
    print("MEMULAI PROSES EKSTRAKSI")
    print("=" * 60)
    print(f"  Run ID     : {ctx.run_id}")
    print(f"  Direktori  : {ctx.run_dir}")
    print("=" * 60)
    
    try:
        results, page = run_multi_unit_download(config, ctx, units, period_ym, page=page)
        
        # Step 9: Print final summary
        print("\n" + "=" * 60)
        print("HASIL EKSTRAKSI")
        print("=" * 60)
        print(f"\n  📊 RINGKASAN")
        print(f"  " + "-" * 40)
        print(f"  Total unit      : {results['total']}")
        print(f"  ✓ Berhasil      : {results['success']}")
        print(f"  ✗ Gagal         : {results['failed']}")
        
        if results.get('rows_parsed'):
            print(f"\n  📄 HASIL PARSING")
            print(f"  " + "-" * 40)
            print(f"  Total baris     : {results['rows_parsed']:,}")
            print(f"  File CSV        : {Path(results.get('parsed_csv_path', '')).name}")
        
        # Google Sheets upload status
        if results.get('sheet_uploaded') is not None:
            print(f"\n  📤 GOOGLE SHEETS")
            print(f"  " + "-" * 40)
            if results.get('sheet_uploaded'):
                print(f"  Status          : ✓ Berhasil diupload")
                print(f"  Worksheet       : {results.get('sheet_worksheet', '-')}")
                print(f"  Baris diupload  : {results.get('sheet_row_count', 0):,}")
            else:
                print(f"  Status          : ✗ Gagal")
                print(f"  Error           : {results.get('sheet_error', 'Unknown')[:50]}")
                print(f"  (Lihat manifest.json untuk detail)")
        
        if results.get('validation_warnings'):
            print(f"\n  ⚠ PERINGATAN VALIDASI: {len(results['validation_warnings'])}")
            for w in results['validation_warnings'][:3]:
                print(f"     - {w}")
        
        print(f"\n  📁 LOKASI FILE")
        print(f"  " + "-" * 40)
        print(f"  Run directory   : {ctx.run_dir}")
        print(f"  Excel files     : {ctx.excel_dir}")
        print(f"  Parsed CSV      : {ctx.parsed_dir}")
        
        if results['errors']:
            print(f"\n  ❌ DAFTAR ERROR")
            print(f"  " + "-" * 40)
            for err in results['errors']:
                print(f"     - {err['unit']}: {err['error']}")
        
        print("\n" + "=" * 60)
        logger.info(f"Extraction completed: {results['success']}/{results['total']} success")
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        print(f"\n✗ Ekstraksi gagal: {e}")
    
    input("\nTekan Enter untuk kembali ke menu...")
    return page


def handle_menu_choice(choice: str, config: Config, page: Optional[Page] = None) -> Tuple[bool, Optional[Page]]:
    """Handle menu choice.
    
    Args:
        choice: Menu choice
        config: Configuration object
        page: Playwright page instance (optional)
    
    Returns:
        Tuple of (continue_menu, page) - False if exit, True otherwise
    """
    if choice == "1":
        page = run_se004_bulanan(config, page)
        return True, page
    
    elif choice == "2":
        page = run_se004_kumulatif(config, page)
        return True, page
    
    elif choice == "3":
        run_stub("Laporan Detail Kode Gangguan SE004")
        return True, page
    
    elif choice == "0":
        get_logger().info("Exiting application")
        print("\n👋 Terima kasih telah menggunakan APKT Agent!")
        return False, page
    
    else:
        print("\n⚠ Pilihan tidak valid. Silakan coba lagi.")
        return True, page

def main() -> int:
    """Main CLI entry point."""
    try:
        config = load_config()
        logger = setup_logger()
        
        logger.info("APKT Agent CLI started")
        
        print_header()
        
        # Show configuration info
        print("\n📋 INFORMASI KONFIGURASI:")
        print("-" * 60)
        login_url = config.get('apkt.login_url', 'Not configured')
        print(f"  APKT URL        : {login_url}")
        print(f"  Config file     : {config.config_path}")
        print("-" * 60)
        
        # Check connectivity
        if not check_connectivity(config):
            print("\n✗ Keluar karena masalah koneksi.")
            return 1
        
        # === PERFORM LOGIN BEFORE SHOWING MENU ===
        page, username = perform_login(config)
        
        if not page or not username:
            print("\n✗ Tidak dapat melanjutkan tanpa login.")
            return 1
        
        is_logged_in = True
        
        try:
            # Interactive menu loop with session reuse
            while True:
                # Check session validity before showing menu
                if not check_session_valid(page):
                    print("\n⚠ Sesi login telah hangus. Login ulang diperlukan.")
                    is_logged_in = False
                    
                    retry = input("\nLogin ulang? (y/n): ").strip().lower()
                    if retry == 'y':
                        page, username = perform_login(config)
                        if page and username:
                            is_logged_in = True
                        else:
                            print("\n✗ Login ulang gagal. Keluar.")
                            return 1
                    else:
                        print("\n✗ Keluar karena sesi tidak valid.")
                        return 1
                
                # Show menu with login status
                print_menu(is_logged_in, username, config)
                choice = input("Pilih menu (0-3): ").strip()
                
                continue_loop, page = handle_menu_choice(choice, config, page)
                if not continue_loop:
                    break
            
            return 0
        
        finally:
            # Cleanup: close browser if it was opened
            if page:
                try:
                    page.context.browser.close()
                    logger.info("Browser session closed")
                except Exception as e:
                    logger.warning(f"Error closing browser: {e}")
    
    except KeyboardInterrupt:
        print("\n\n⚠ Aplikasi dihentikan oleh pengguna.")
        return 1
    
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
