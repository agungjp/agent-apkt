"""Command-line interface for APKT Agent."""

import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple

import requests

from . import __version__
from .config import Config, load_config
from .logging_ import setup_logger, get_logger
from .workspace import create_run
from .datasets.se004.multi_download import load_units_selection, run_multi_unit_download


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


def print_menu() -> None:
    """Print main CLI menu."""
    print("\n" + "-" * 60)
    print("MENU UTAMA")
    print("-" * 60)
    print("\n  1. Laporan SAIDI SAIFI SE004 [stub]")
    print("  2. Laporan SAIDI SAIFI Kumulatif SE004")
    print("  3. Laporan Detail Kode Gangguan SE004 [stub]")
    print("\n  0. Keluar")
    print("\n" + "-" * 60)


def get_period_input() -> str | None:
    """Get period input from user.
    
    Returns:
        Period in YYYYMM format, or None if cancelled
    """
    print("\n" + "-" * 60)
    print("FORMAT PERIODE: YYYYMM")
    print("-" * 60)
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


def run_se004_kumulatif(config: Config) -> None:
    """Run SE004 Kumulatif extraction.
    
    Args:
        config: Configuration object
    """
    logger = get_logger()
    logger.info("Selected: Laporan SAIDI SAIFI Kumulatif SE004")
    
    print("\n" + "=" * 60)
    print("  LAPORAN SAIDI SAIFI KUMULATIF SE004")
    print("=" * 60)
    
    # Step 1: Load units
    units_file = Path("units_selection.yaml")
    if not units_file.exists():
        print(f"\n✗ File tidak ditemukan: {units_file}")
        print("  Buat file units_selection.yaml terlebih dahulu.")
        input("\nTekan Enter untuk kembali ke menu...")
        return
    
    try:
        units = load_units_selection(units_file)
    except Exception as e:
        print(f"\n✗ Error loading units: {e}")
        input("\nTekan Enter untuk kembali ke menu...")
        return
    
    if not units:
        print("\n✗ Tidak ada unit yang dipilih di units_selection.yaml")
        input("\nTekan Enter untuk kembali ke menu...")
        return
    
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
        return
    
    year = period_ym[:4]
    month = period_ym[4:6]
    month_name = BULAN_INDONESIA.get(month, month)
    
    # Step 4: Get headless option
    headless = get_headless_option()
    
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
        return
    
    # Step 6: Update config with headless option
    config.data['runtime'] = config.data.get('runtime', {})
    config.data['runtime']['headless'] = headless
    
    # Step 7: Create run context
    snapshot_date = datetime.now().strftime('%Y%m%d')
    ctx = create_run("se004_kumulatif", period_ym, snapshot_date, config)
    
    # Re-setup logger
    logger = setup_logger(ctx=ctx)
    logger.info(f"Starting SE004 Kumulatif extraction")
    logger.info(f"Period: {period_ym}, Units: {len(units)}, Headless: {headless}")
    
    # Step 8: Run extraction
    print("\n" + "=" * 60)
    print("MEMULAI PROSES EKSTRAKSI")
    print("=" * 60)
    print(f"  Run ID     : {ctx.run_id}")
    print(f"  Direktori  : {ctx.run_dir}")
    print("=" * 60)
    
    try:
        results = run_multi_unit_download(config, ctx, units, period_ym)
        
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


def handle_menu_choice(choice: str, config: Config) -> bool:
    """Handle menu choice.
    
    Returns:
        False if exit, True otherwise
    """
    if choice == "1":
        run_stub("Laporan SAIDI SAIFI SE004")
        return True
    
    elif choice == "2":
        run_se004_kumulatif(config)
        return True
    
    elif choice == "3":
        run_stub("Laporan Detail Kode Gangguan SE004")
        return True
    
    elif choice == "0":
        get_logger().info("Exiting application")
        print("\n👋 Terima kasih telah menggunakan APKT Agent!")
        return False
    
    else:
        print("\n⚠ Pilihan tidak valid. Silakan coba lagi.")
        return True


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
        
        # Interactive menu
        while True:
            print_menu()
            choice = input("Pilih menu (0-3): ").strip()
            
            if not handle_menu_choice(choice, config):
                break
        
        return 0
    
    except KeyboardInterrupt:
        print("\n\n⚠ Aplikasi dihentikan oleh pengguna.")
        return 1
    
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
