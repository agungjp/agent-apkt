# APKT Agent - Overview

**Dokumen dibuat:** 7 Januari 2026  
**Versi:** 1.0

## Deskripsi

APKT Agent adalah tool CLI untuk mengekstrak data dari sistem APKT (Aplikasi Pemantauan Kinerja Teknis) PLN. Tool ini mengotomasi proses download laporan Excel dari portal APKT, parsing data ke format CSV, dan upload ke Google Sheets.

## Fitur Utama

1. **Ekstraksi Data SE004 Kumulatif**

   - Download laporan SAIDI/SAIFI kumulatif dari portal APKT
   - Support multi-unit download (9 unit sekaligus)
   - Support pemilihan periode (YYYYMM)

2. **Parsing Excel ke CSV**

   - Parse file Excel hasil download ke format CSV terstruktur
   - Ekstrak header (unit induk, periode, tanggal cetak)
   - Ekstrak data group dan detail per kode gangguan
   - Validasi data hasil parsing

3. **Upload ke Google Sheets**
   - Upload otomatis hasil parsing ke Google Sheets
   - Support mode `replace` (ganti semua) dan `append` (tambah di bawah)
   - Konversi format angka Indonesia ke internasional
   - Auto-resize worksheet jika kurang baris

## Teknologi

- **Python 3.10+**
- **Playwright** - Browser automation
- **Pandas** - Data processing
- **OpenPyXL** - Excel parsing
- **gspread** - Google Sheets API
- **PyYAML** - Configuration

## Struktur Project

```
ods-apkt/
├── src/apkt_agent/
│   ├── browser/           # Browser automation
│   │   ├── auth.py        # Login/authentication
│   │   ├── driver.py      # Playwright driver
│   │   ├── download.py    # Excel download
│   │   └── nav.py         # Navigation helpers
│   ├── datasets/
│   │   └── se004/         # SE004 dataset handlers
│   │       ├── parser.py  # Excel parser
│   │       ├── schema.py  # Data schema
│   │       └── multi_download.py
│   ├── sinks/
│   │   └── sheets.py      # Google Sheets upload
│   ├── transform/
│   │   └── validate.py    # Data validation
│   ├── cli.py             # CLI interface
│   ├── config.py          # Configuration
│   └── workspace.py       # Workspace/run management
├── workspace/             # Output directory
│   └── runs/              # Per-run directories
├── config.yaml            # Configuration
├── credentials.yaml       # APKT login credentials
├── units_selection.yaml   # Selected units for download
└── apkt-agent-*.json      # Google Service Account
```

## Konfigurasi

### config.yaml

```yaml
apkt:
  login_url: "https://new-apkt.pln.co.id/login"
  iam_login_url: "https://iam.pln.co.id/auth/..."
  iam_totp_url_prefix: "https://iam.pln.co.id/auth/mfa/..."

datasets:
  se004_kumulatif:
    url: "https://new-apktss.pln.co.id/home/laporan-saidi-saifi-kumulatif-se004"

workspace:
  root: "./workspace"

runtime:
  headless: false # true untuk headless mode

google_sheets:
  enabled: true
  spreadsheet_id: "YOUR_SPREADSHEET_ID"
  worksheet_name: "se004_kumulatif"
  credentials_json_path: "./service-account.json"
  mode: "append" # atau "replace"
```

### credentials.yaml

```yaml
username: "your_username"
password: "your_password"
```

### units_selection.yaml

```yaml
selected_units:
  - value: "110"
    text: "11 - WILAYAH ACEH"
    code: "WIL_ACEH"
  # ... unit lainnya
```

## Instalasi

```bash
# Clone repository
git clone <repo-url>
cd ods-apkt

# Create virtual environment
python -m venv venv
source venv/bin/activate  # atau venv\Scripts\activate di Windows

# Install dependencies
pip install -e .

# Install Playwright browsers
playwright install chromium
```

## Penggunaan

```bash
# Jalankan CLI
apkt-agent

# Atau dengan Python langsung
python -m apkt_agent
```

## Output

Setiap run menghasilkan:

- `workspace/runs/{run_id}/excel/` - File Excel hasil download
- `workspace/runs/{run_id}/parsed/` - File CSV hasil parsing
- `workspace/runs/{run_id}/manifest.json` - Metadata run
- Upload ke Google Sheets (jika enabled)
