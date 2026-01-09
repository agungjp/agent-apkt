"""Google Sheets sink for uploading CSV data."""

from pathlib import Path
from typing import Optional, List, Any, Dict

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

from ..logging_ import get_logger

# Google Sheets API scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

# Numeric columns that need format conversion (Indonesian to international)
NUMERIC_COLUMNS = [
    'jumlah_pelanggan',
    'saidi_total',
    'saidi_total_menit',
    'saifi_total',
    'jml_plg_padam',
    'jam_x_jml_plg_padam',
    'saidi_jam',
    'saifi_kali',
    'jumlah_gangguan_kali',
    'lama_padam_jam',
    'kwh_tak_tersalurkan',
]


def convert_indonesian_number(value: str) -> Any:
    """Convert Indonesian number format to international format.
    
    Indonesian: 1.234.567,89 (dot for thousands, comma for decimal)
    International: 1234567.89 (no thousands separator, dot for decimal)
    
    Args:
        value: String value in Indonesian format
        
    Returns:
        Float number if valid, original string if not a number
    """
    if not value or not isinstance(value, str):
        return value
    
    value = value.strip()
    if not value:
        return ""
    
    try:
        # Remove thousand separators (dots) and replace comma with dot for decimal
        # "2.828.036,0" -> "2828036.0"
        # "5,7905" -> "5.7905"
        cleaned = value.replace('.', '').replace(',', '.')
        return float(cleaned)
    except (ValueError, AttributeError):
        return value


def build_client(credentials_json_path: str) -> gspread.Client:
    """Build a gspread client using Service Account credentials.
    
    Args:
        credentials_json_path: Path to Service Account JSON file
        
    Returns:
        Authenticated gspread.Client
        
    Raises:
        FileNotFoundError: If credentials file not found
        Exception: If authentication fails
    """
    logger = get_logger()
    creds_path = Path(credentials_json_path)
    
    if not creds_path.exists():
        raise FileNotFoundError(f"Service Account JSON not found: {creds_path}")
    
    logger.info(f"Loading credentials from: {creds_path}")
    creds = Credentials.from_service_account_file(str(creds_path), scopes=SCOPES)
    client = gspread.authorize(creds)
    
    return client


def open_spreadsheet(client: gspread.Client, spreadsheet_id: str) -> gspread.Spreadsheet:
    """Open a Google Spreadsheet by ID.
    
    Args:
        client: Authenticated gspread client
        spreadsheet_id: The spreadsheet ID from the URL
        
    Returns:
        gspread.Spreadsheet object
        
    Raises:
        gspread.SpreadsheetNotFound: If spreadsheet not found
        gspread.exceptions.APIError: If permission denied (403)
    """
    logger = get_logger()
    logger.info(f"Opening spreadsheet: {spreadsheet_id}")
    
    return client.open_by_key(spreadsheet_id)


def ensure_worksheet(
    spreadsheet: gspread.Spreadsheet,
    worksheet_name: str,
    rows: int = 2000,
    cols: int = 50
) -> gspread.Worksheet:
    """Ensure worksheet exists, create if not.
    
    Args:
        spreadsheet: The spreadsheet object
        worksheet_name: Name of the worksheet/tab
        rows: Default number of rows for new worksheet
        cols: Default number of columns for new worksheet
        
    Returns:
        gspread.Worksheet object
    """
    logger = get_logger()
    
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
        logger.info(f"Found existing worksheet: {worksheet_name}")
    except gspread.WorksheetNotFound:
        logger.info(f"Creating new worksheet: {worksheet_name} ({rows}x{cols})")
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=rows, cols=cols)
    
    return worksheet


def upload_csv_to_worksheet(
    csv_path: Path,
    spreadsheet_id: str,
    worksheet_name: str,
    credentials_json_path: str,
    mode: str = "replace",
    period_column: Optional[str] = None,
    period_value: Optional[str] = None,
) -> Dict[str, Any]:
    """Upload CSV file to Google Sheets worksheet.
    
    Args:
        csv_path: Path to CSV file
        spreadsheet_id: Google Sheets spreadsheet ID
        worksheet_name: Name of worksheet/tab to upload to
        credentials_json_path: Path to Service Account JSON
        mode: Upload mode - "replace" (full replace), "append" (add rows), 
              "smart"/"update" (replace by period column if exists)
        period_column: Column name for period detection (e.g., 'period_ym')
        period_value: Period value to match for smart/update replace (e.g., '202501')
        
    Returns:
        Dict with upload results: {success, row_count, col_count, worksheet_name}
        
    Raises:
        FileNotFoundError: If CSV or credentials not found
        gspread.exceptions.APIError: If permission denied
    """
    logger = get_logger()
    
    # Normalize mode: 'update' is alias for 'smart'
    if mode == 'update':
        mode = 'smart'
    
    # Read CSV
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    logger.info(f"Reading CSV: {csv_path}")
    
    # Read with semicolon delimiter (Indonesian format)
    df = pd.read_csv(csv_path, sep=';', dtype=str)
    df = df.fillna("")
    
    # Convert Indonesian number format to international for numeric columns
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = df[col].apply(convert_indonesian_number)
    
    row_count = len(df)
    col_count = len(df.columns)
    logger.info(f"CSV loaded: {row_count} rows x {col_count} columns (numeric columns converted)")
    
    # Prepare values: header + data rows
    header = df.columns.tolist()
    data_rows = df.values.tolist()
    values = [header] + data_rows
    
    try:
        # Build client and open spreadsheet
        client = build_client(credentials_json_path)
        spreadsheet = open_spreadsheet(client, spreadsheet_id)
        
        # Ensure worksheet exists with enough size
        needed_rows = len(values) + 100  # Extra buffer
        needed_cols = col_count + 5
        worksheet = ensure_worksheet(spreadsheet, worksheet_name, rows=needed_rows, cols=needed_cols)
        
        # Resize worksheet if needed
        if worksheet.row_count < len(values) or worksheet.col_count < col_count:
            logger.info(f"Resizing worksheet to {len(values)} rows x {col_count} cols")
            worksheet.resize(rows=len(values) + 100, cols=col_count + 5)
        
        # Handle mode: replace, append, or smart (period-based replace)
        if mode == "smart" and period_column and period_value:
            # Smart mode: replace only rows matching the period
            logger.info(f"Smart mode: Checking for existing period '{period_value}' in column '{period_column}'")
            existing_data = worksheet.get_all_values()
            
            logger.info(f"Existing sheet data: {len(existing_data)} rows total")
            
            if existing_data and len(existing_data) > 1:
                # Find period column index
                existing_header = existing_data[0]
                logger.info(f"Header columns: {existing_header}")
                
                if period_column in existing_header:
                    period_col_idx = existing_header.index(period_column)
                    logger.info(f"✓ Found period column '{period_column}' at index {period_col_idx}")
                    
                    # Find and remove rows with matching period
                    matching_row_indices = []
                    for i, row in enumerate(existing_data[1:], start=1):  # Start from 1 (skip header)
                        if len(row) > period_col_idx:
                            row_period = row[period_col_idx].strip()
                            if row_period == period_value.strip():
                                matching_row_indices.append(i)
                                if len(matching_row_indices) <= 5:  # Log first 5 matches
                                    logger.info(f"  → Row {i+1} matches period '{row_period}'")
                    
                    logger.info(f"Total matching rows: {len(matching_row_indices)}")
                    
                    if matching_row_indices:
                        logger.info(f"✓ Found {len(matching_row_indices)} rows with period '{period_value}', replacing them...")
                        
                        # Build new data: keep header + rows that don't match + new data
                        kept_rows = []
                        for i, row in enumerate(existing_data[1:], start=1):
                            if i not in matching_row_indices:
                                kept_rows.append(row)
                        
                        # Combine: header + kept rows + new rows
                        combined_values = [existing_header] + kept_rows + data_rows
                        logger.info(f"Combined data: 1 header + {len(kept_rows)} kept rows + {len(data_rows)} new rows = {len(combined_values)} total rows")
                        
                        # Clear and upload combined data
                        new_size = len(combined_values) + 100
                        if worksheet.row_count < new_size:
                            logger.info(f"Resizing worksheet to {new_size} rows")
                            worksheet.resize(rows=new_size, cols=max(worksheet.col_count, col_count + 5))
                        
                        worksheet.clear()
                        logger.info(f"Uploading combined data: {len(combined_values)} rows total")
                        worksheet.update("A1", combined_values, value_input_option="RAW")
                        logger.info(f"✓ Smart replace completed!")
                    else:
                        # No matching period found, append
                        logger.warning(f"⚠ No existing rows with period '{period_value}', appending new data...")
                        existing_data = worksheet.get_all_values()
                        next_row = len(existing_data) + 1
                        total_needed_rows = next_row + len(data_rows)
                        
                        if worksheet.row_count < total_needed_rows:
                            worksheet.resize(rows=total_needed_rows + 500, cols=max(worksheet.col_count, col_count + 5))
                        
                        logger.info(f"Appending {len(data_rows)} rows starting at row {next_row}")
                        worksheet.update(f"A{next_row}", data_rows, value_input_option="RAW")
                else:
                    logger.warning(f"⚠ Period column '{period_column}' NOT found in header!")
                    logger.warning(f"  Available columns: {existing_header}")
                    logger.warning(f"  Falling back to append mode")
                    existing_data = worksheet.get_all_values()
                    next_row = len(existing_data) + 1
                    if worksheet.row_count < next_row + len(data_rows):
                        worksheet.resize(rows=next_row + len(data_rows) + 500, cols=max(worksheet.col_count, col_count + 5))
                    logger.info(f"Appending {len(data_rows)} rows starting at row {next_row}")
                    worksheet.update(f"A{next_row}", data_rows, value_input_option="RAW")
            else:
                # Empty sheet, add with header
                logger.info("Sheet is empty, uploading with header")
                worksheet.update("A1", values, value_input_option="RAW")
        
        elif mode == "replace":
            logger.info("Clearing existing data (mode=replace)")
            worksheet.clear()
            # Upload with header
            logger.info(f"Uploading {len(values)} rows to worksheet: {worksheet_name}")
            worksheet.update("A1", values, value_input_option="RAW")
        elif mode == "append":
            # Find last row with data and append below
            existing_data = worksheet.get_all_values()
            next_row = len(existing_data) + 1
            total_needed_rows = next_row + len(data_rows)
            
            # Resize if needed for append
            if worksheet.row_count < total_needed_rows:
                new_size = total_needed_rows + 500  # Buffer for future appends
                logger.info(f"Resizing worksheet from {worksheet.row_count} to {new_size} rows")
                worksheet.resize(rows=new_size, cols=max(worksheet.col_count, col_count + 5))
            
            # Only add data rows (skip header if appending to existing data)
            if next_row > 1:
                # Append data without header
                logger.info(f"Appending {len(data_rows)} rows starting at row {next_row}")
                worksheet.update(f"A{next_row}", data_rows, value_input_option="RAW")
            else:
                # Empty sheet, add with header
                logger.info(f"Uploading {len(values)} rows to worksheet: {worksheet_name}")
                worksheet.update("A1", values, value_input_option="RAW")
        else:
            # Default: replace behavior
            worksheet.clear()
            logger.info(f"Uploading {len(values)} rows to worksheet: {worksheet_name}")
            worksheet.update("A1", values, value_input_option="RAW")
        
        logger.info(f"✓ Upload successful: {row_count} data rows to '{worksheet_name}'")
        
        return {
            "success": True,
            "row_count": row_count,
            "col_count": col_count,
            "worksheet_name": worksheet_name,
            "spreadsheet_id": spreadsheet_id,
        }
        
    except gspread.exceptions.APIError as e:
        error_msg = str(e)
        if "403" in error_msg or "PERMISSION_DENIED" in error_msg:
            # Extract client_email from credentials for helpful message
            try:
                import json
                with open(credentials_json_path) as f:
                    creds_data = json.load(f)
                client_email = creds_data.get("client_email", "unknown")
                logger.error(
                    f"Permission denied! Please share the spreadsheet with: {client_email}\n"
                    f"Open the spreadsheet and click 'Share' -> add {client_email} as Editor"
                )
            except Exception:
                logger.error(
                    f"Permission denied! Please share the spreadsheet with the Service Account email.\n"
                    f"Check client_email in your credentials JSON file."
                )
        raise


# Keep legacy class for backward compatibility
class GoogleSheetsSink:
    """Writes parsed data to Google Sheets (legacy class)."""
    
    def __init__(self, spreadsheet_id: str, credentials_path: Optional[str] = None):
        """Initialize Google Sheets sink.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            credentials_path: Path to Google credentials JSON file
        """
        self.logger = get_logger()
        self.spreadsheet_id = spreadsheet_id
        self.credentials_path = credentials_path
    
    def write(self, csv_path: Path, worksheet_name: str) -> Dict[str, Any]:
        """Write CSV to Google Sheets.
        
        Args:
            csv_path: Path to CSV file
            worksheet_name: Target worksheet name
            
        Returns:
            Dict with results
        """
        return upload_csv_to_worksheet(
            csv_path=csv_path,
            spreadsheet_id=self.spreadsheet_id,
            worksheet_name=worksheet_name,
            credentials_json_path=self.credentials_path,
            mode="replace"
        )
