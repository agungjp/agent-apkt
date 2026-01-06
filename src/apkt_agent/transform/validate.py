"""Data validation utilities."""

from typing import Dict, Any, List, Optional
import pandas as pd

from ..errors import ValidationError
from ..logging_ import get_logger


class ValidationResult:
    """Result of validation check."""
    
    def __init__(self):
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.is_valid: bool = True
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
    
    def add_error(self, message: str):
        """Add an error message and mark as invalid."""
        self.errors.append(message)
        self.is_valid = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for manifest."""
        return {
            "is_valid": self.is_valid,
            "warnings": self.warnings,
            "errors": self.errors,
            "warning_count": len(self.warnings),
            "error_count": len(self.errors),
        }


def validate_se004_kumulatif(df: pd.DataFrame) -> ValidationResult:
    """Validate SE004 Kumulatif DataFrame.
    
    Rules:
    1. period_ym should be consistent across all files
    2. TOTAL KESELURUHAN row should have non-null saidi_jam and saifi_kali
    3. jml_plg_padam should not be negative
    4. kode (if present) should be numeric or convertible to numeric
    
    Args:
        df: DataFrame to validate
        
    Returns:
        ValidationResult with warnings and errors
    """
    logger = get_logger()
    result = ValidationResult()
    
    if df.empty:
        result.add_warning("DataFrame is empty")
        return result
    
    # Rule 1: period_ym consistency
    unique_periods = df["period_ym"].dropna().unique()
    if len(unique_periods) > 1:
        result.add_warning(
            f"Multiple period_ym values found: {list(unique_periods)}. "
            "Expected all files to have the same period."
        )
    
    # Rule 2: Check TOTAL KESELURUHAN row
    total_mask = df["penyebab_gangguan"].fillna("").str.upper().str.contains("TOTAL KESELURUHAN")
    total_rows = df[total_mask]
    if len(total_rows) == 0:
        result.add_warning("No 'TOTAL KESELURUHAN' row found in data")
    else:
        for idx, row in total_rows.iterrows():
            if pd.isna(row["saidi_jam"]):
                result.add_warning(
                    f"TOTAL KESELURUHAN row (source: {row['source_file']}) has null saidi_jam"
                )
            if pd.isna(row["saifi_kali"]):
                result.add_warning(
                    f"TOTAL KESELURUHAN row (source: {row['source_file']}) has null saifi_kali"
                )
    
    # Rule 3: jml_plg_padam not negative
    negative_mask = df["jml_plg_padam"].fillna(0) < 0
    negative_rows = df[negative_mask]
    if len(negative_rows) > 0:
        result.add_warning(
            f"Found {len(negative_rows)} rows with negative jml_plg_padam"
        )
    
    # Rule 4: kode should be numeric (for detail rows)
    detail_rows = df[df["row_type"] == "detail"]
    non_numeric_kode_found = False
    for idx, row in detail_rows.iterrows():
        kode = row["kode"]
        if kode is not None and str(kode).strip() != "":
            try:
                float(str(kode).replace(" ", ""))
            except (ValueError, TypeError):
                if not non_numeric_kode_found:
                    result.add_warning(
                        f"Non-numeric kode '{kode}' in file {row['source_file']}"
                    )
                    non_numeric_kode_found = True
    
    # Summary logging
    logger.info(f"Validation complete: {len(result.warnings)} warnings, {len(result.errors)} errors")
    
    return result


def validate_and_report(df: pd.DataFrame, run_dir: Optional[str] = None) -> ValidationResult:
    """Validate DataFrame and optionally save report.
    
    Args:
        df: DataFrame to validate
        run_dir: Optional run directory to save validation report
        
    Returns:
        ValidationResult
    """
    result = validate_se004_kumulatif(df)
    
    if run_dir:
        import json
        from pathlib import Path
        
        report_path = Path(run_dir) / "validation_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2)
    
    return result


class Validator:
    """Data validation utilities (legacy)."""
    
    def __init__(self):
        """Initialize validator."""
        self.logger = get_logger()
        self.errors: List[str] = []
    
    def validate_record(self, record: Dict[str, Any], schema: Dict[str, type]) -> bool:
        """Validate a single record against schema."""
        self.errors = []
        
        for field, expected_type in schema.items():
            if field not in record:
                self.errors.append(f"Missing required field: {field}")
                continue
            
            if not isinstance(record[field], expected_type):
                self.errors.append(
                    f"Field {field}: expected {expected_type}, got {type(record[field])}"
                )
        
        return len(self.errors) == 0
    
    def validate_records(self, records: List[Dict[str, Any]], schema: Dict[str, type]) -> Dict[str, Any]:
        """Validate multiple records."""
        valid_records = []
        invalid_records = []
        
        for i, record in enumerate(records):
            if self.validate_record(record, schema):
                valid_records.append(record)
            else:
                invalid_records.append({
                    'record_index': i,
                    'record': record,
                    'errors': self.errors.copy()
                })
        
        self.logger.info(f"Validation: {len(valid_records)} valid, {len(invalid_records)} invalid")
        
        return {
            'valid': valid_records,
            'invalid': invalid_records,
        }
