#!/usr/bin/env python3
"""Quick test for parsing and J/P filter on existing run."""
import sys
from pathlib import Path

# Use existing parsed CSV (skip parsing)
RUN_DIR = "workspace/runs/20260109_162513_se004_detail_gangguan_202502_BKOX"
CSV_PATH = f"{RUN_DIR}/parsed/se004_detail_gangguan_202502_combined.csv"

def test_with_pandas():
    import pandas as pd
    
    csv_path = Path(CSV_PATH)
    if not csv_path.exists():
        print(f"CSV not found: {csv_path}")
        return
    
    print(f"Reading: {csv_path}")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"Original: {len(df):,} rows")
    
    # Filter J or P
    df_filtered = df[df['no_laporan'].astype(str).str.upper().str.match(r'^[JP]')]
    print(f"Filtered (J/P only): {len(df_filtered):,} rows")
    
    # Show breakdown
    j_count = len(df[df['no_laporan'].astype(str).str.upper().str.startswith('J')])
    p_count = len(df[df['no_laporan'].astype(str).str.upper().str.startswith('P')])
    print(f"  J: {j_count:,}, P: {p_count:,}")

if __name__ == "__main__":
    test_with_pandas()
