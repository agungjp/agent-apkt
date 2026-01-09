"""Parser for SE004 Detail Kode Gangguan Excel files."""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd

from ...logging_ import get_logger


# Column mapping for SE004 Detail Gangguan
# The Excel has merged headers, we'll flatten them
COLUMN_NAMES = [
    "no",
    "no_laporan",
    "ulp",
    "penyulang",
    "lokasi_titik_gangguan",
    "waktu_padam_tanggal",
    "waktu_padam_jam",
    "waktu_nyala_sementara_tanggal",
    "waktu_nyala_sementara_jam",
    "waktu_nyala_tanggal",
    "waktu_nyala_jam",
    "kelompok_gangguan_fasilitas",
    "kelompok_gangguan_sub_fasilitas",
    "kelompok_gangguan_equipment",
    "event_damage",
    "cause",
    "group_cause",
    "weather",
    "jumlah_pelanggan_padam",
    "lama_padam_jam",
    "jam_x_pelanggan_padam",
    "penyebab_padam",
    "ens",
    "ampere",
    "keterangan",
    "lokasi_gangguan",
    "section_gangguan",
    "pembatas_section",
    "no_tiang_gangguan",
    "rele_proteksi",
    "besar_arus_ampere",
]


def extract_metadata_from_filename(filename: str) -> Dict[str, str]:
    """Extract metadata from filename.
    
    Example: se004_detail_202501_WIL_ACEH_distribusi.xlsx
    Returns: {"period": "202501", "unit_code": "WIL_ACEH", "kelompok": "distribusi"}
    """
    # Pattern: se004_detail_{period}_{unit_code}_{kelompok}.xlsx
    pattern = r"se004_detail_(\d{6})_(.+)_(distribusi|transmisi|pembangkit)\.xlsx"
    match = re.match(pattern, filename, re.IGNORECASE)
    
    if match:
        return {
            "period": match.group(1),
            "unit_code": match.group(2),
            "kelompok": match.group(3).lower(),
        }
    return {}


def parse_single_file(filepath: Path) -> pd.DataFrame:
    """Parse a single SE004 Detail Gangguan Excel file.
    
    Args:
        filepath: Path to Excel file
        
    Returns:
        DataFrame with parsed data
    """
    logger = get_logger()
    
    # Extract metadata from filename
    metadata = extract_metadata_from_filename(filepath.name)
    
    # Read Excel, skip header rows (15 rows of metadata + 2 header rows = 17)
    # Data starts at row 17 (0-indexed)
    df = pd.read_excel(filepath, header=None, skiprows=17)
    
    # Check if we have data
    if df.empty:
        logger.warning(f"No data in file: {filepath.name}")
        return pd.DataFrame()
    
    # Assign column names (may have fewer columns)
    if len(df.columns) <= len(COLUMN_NAMES):
        df.columns = COLUMN_NAMES[:len(df.columns)]
    else:
        # More columns than expected, use what we have
        df.columns = COLUMN_NAMES + [f"extra_{i}" for i in range(len(df.columns) - len(COLUMN_NAMES))]
    
    # Drop rows where 'no' is NaN or not a number (footer rows)
    df = df[pd.to_numeric(df['no'], errors='coerce').notna()]
    
    # Add metadata columns
    df['period'] = metadata.get('period', '')
    df['unit_code'] = metadata.get('unit_code', '')
    df['kelompok'] = metadata.get('kelompok', '')
    df['source_file'] = filepath.name
    
    # Convert numeric columns
    numeric_cols = ['no', 'jumlah_pelanggan_padam', 'lama_padam_jam', 
                    'jam_x_pelanggan_padam', 'ens', 'ampere', 'besar_arus_ampere']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    logger.info(f"Parsed {len(df)} rows from {filepath.name}")
    return df


def parse_all_files(excel_dir: Path, output_dir: Path) -> Dict[str, Any]:
    """Parse all SE004 Detail Gangguan Excel files in a directory.
    
    Args:
        excel_dir: Directory containing Excel files
        output_dir: Directory to save parsed CSV
        
    Returns:
        Dictionary with parsing results
    """
    logger = get_logger()
    
    # Find all SE004 detail files
    excel_files = list(excel_dir.glob("se004_detail_*.xlsx"))
    
    if not excel_files:
        logger.warning(f"No SE004 detail files found in {excel_dir}")
        return {"success": False, "error": "No files found", "rows": 0}
    
    logger.info(f"Found {len(excel_files)} SE004 detail files to parse")
    
    # Parse all files
    all_dfs = []
    errors = []
    
    for filepath in sorted(excel_files):
        try:
            df = parse_single_file(filepath)
            if not df.empty:
                all_dfs.append(df)
        except Exception as e:
            logger.error(f"Error parsing {filepath.name}: {e}")
            errors.append({"file": filepath.name, "error": str(e)})
    
    if not all_dfs:
        return {"success": False, "error": "All files failed to parse", "rows": 0}
    
    # Combine all DataFrames
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # Save to CSV
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get period from first file for naming
    period = combined_df['period'].iloc[0] if 'period' in combined_df.columns else 'unknown'
    output_path = output_dir / f"se004_detail_gangguan_{period}_combined.csv"
    
    combined_df.to_csv(output_path, index=False, encoding='utf-8')
    logger.info(f"Saved combined CSV: {output_path} ({len(combined_df)} rows)")
    
    # Summary by unit and kelompok
    summary = combined_df.groupby(['unit_code', 'kelompok']).size().reset_index(name='row_count')
    
    return {
        "success": True,
        "total_files": len(excel_files),
        "files_parsed": len(all_dfs),
        "total_rows": len(combined_df),
        "output_path": str(output_path),
        "summary": summary.to_dict('records'),
        "errors": errors,
    }


def parse_run_directory(run_dir: Path) -> Dict[str, Any]:
    """Parse all Excel files in a run directory.
    
    Args:
        run_dir: Run directory (contains raw/excel and parsed subdirs)
        
    Returns:
        Parsing results dictionary
    """
    excel_dir = run_dir / "raw" / "excel"
    output_dir = run_dir / "parsed"
    
    return parse_all_files(excel_dir, output_dir)


if __name__ == "__main__":
    # Test parsing
    import sys
    
    if len(sys.argv) > 1:
        run_dir = Path(sys.argv[1])
    else:
        # Default test directory
        run_dir = Path("workspace/runs/20260109_153539_se004_detail_gangguan_202501_5E85")
    
    print(f"Parsing run directory: {run_dir}")
    results = parse_run_directory(run_dir)
    
    print("\n" + "=" * 60)
    print("PARSING RESULTS")
    print("=" * 60)
    print(f"  Success: {results.get('success')}")
    print(f"  Files parsed: {results.get('files_parsed', 0)} / {results.get('total_files', 0)}")
    print(f"  Total rows: {results.get('total_rows', 0)}")
    print(f"  Output: {results.get('output_path', 'N/A')}")
    
    if results.get('summary'):
        print("\n  Summary by Unit & Kelompok:")
        for row in results['summary']:
            print(f"    {row['unit_code']:20s} | {row['kelompok']:12s} | {row['row_count']:,} rows")
    
    if results.get('errors'):
        print(f"\n  Errors ({len(results['errors'])}):")
        for err in results['errors'][:5]:
            print(f"    - {err['file']}: {err['error'][:50]}")
