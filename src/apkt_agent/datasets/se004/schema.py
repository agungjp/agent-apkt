"""Schema definition for SE004 Kumulatif CSV output."""

import re
from dataclasses import dataclass
from typing import List, Optional

# CSV column names for SE004 Kumulatif output
SE004_KUMULATIF_COLUMNS: List[str] = [
    # Metadata columns (from header/file info)
    "unit_induk",
    "period_ym",
    "period_label",
    "jumlah_pelanggan",
    "saidi_total",
    "saifi_total",
    "tanggal_cetak",
    
    # Table data columns
    "kode",
    "penyebab_gangguan",
    "jml_plg_padam",
    "jam_x_jml_plg_padam",
    "saidi_jam",
    "saifi_kali",
    "jumlah_gangguan_kali",
    "lama_padam_jam",
    "kwh_tak_tersalurkan",
    
    # Classification and tracking
    "row_type",       # detail, subtotal, total, group
    "source_file",    # original Excel filename
]

# Indonesian month names for period parsing
BULAN_INDONESIA = {
    "januari": "01",
    "februari": "02",
    "maret": "03",
    "april": "04",
    "mei": "05",
    "juni": "06",
    "juli": "07",
    "agustus": "08",
    "september": "09",
    "oktober": "10",
    "november": "11",
    "desember": "12",
}

# Reverse mapping
BULAN_INDONESIA_REVERSE = {v: k.capitalize() for k, v in BULAN_INDONESIA.items()}


def parse_indonesian_number(value: str) -> Optional[float]:
    """Parse Indonesian number format to float.
    
    Indonesian format uses:
    - Dot (.) as thousand separator
    - Comma (,) as decimal separator
    
    Examples:
        "95.874.596" -> 95874596.0
        "8,4367" -> 8.4367
        "1.234,56" -> 1234.56
    
    Args:
        value: String number in Indonesian format
        
    Returns:
        Float value or None
    """
    if not value or not isinstance(value, str):
        return None
    
    value = value.strip()
    if not value or value == "-":
        return None
    
    try:
        # Check if it has comma (decimal separator)
        if "," in value:
            # Remove thousand separators (dots before comma)
            parts = value.split(",")
            integer_part = parts[0].replace(".", "")
            decimal_part = parts[1] if len(parts) > 1 else "0"
            return float(f"{integer_part}.{decimal_part}")
        else:
            # No decimal, just remove thousand separators
            return float(value.replace(".", ""))
    except ValueError:
        return None


def parse_period_label_to_ym(period_label: str) -> Optional[str]:
    """Convert Indonesian period label to YYYYMM format.
    
    Args:
        period_label: Period label like "Desember 2025"
        
    Returns:
        Period in YYYYMM format like "202512"
    """
    if not period_label:
        return None
    
    period_label = period_label.strip().lower()
    
    for month_name, month_num in BULAN_INDONESIA.items():
        if month_name in period_label:
            # Extract year (4 digits)
            year_match = re.search(r'(\d{4})', period_label)
            if year_match:
                year = year_match.group(1)
                return f"{year}{month_num}"
    
    return None


# Legacy dataclasses for backward compatibility
@dataclass
class SE004Record:
    """Base record for SE004 data."""
    unit_name: str
    period: str
    snapshot_date: str


@dataclass
class SE004KumulatifRecord(SE004Record):
    """SE004 Kumulatif record."""
    saidi_value: float
    saifi_value: float
    caidi_value: Optional[float] = None
    asai_value: Optional[float] = None
