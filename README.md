# APKT Agent 🤖

Automated data extraction tool for PLN APKT (Aplikasi Pelayanan dan Keluhan Terpusat) system. Downloads SAIDI/SAIFI reports, parses Excel files, and uploads to Google Sheets.

## ✨ Features

- 🌐 **Browser Automation** - Playwright-based headless browser for reliable data extraction
- 📊 **Multi-Unit Download** - Download reports from multiple PLN units in one run
- 📁 **Excel Parsing** - Parse downloaded Excel files to clean CSV format
- ☁️ **Google Sheets Integration** - Auto-upload parsed data to Google Sheets
- 🔐 **SSO Authentication** - Supports PLN IAM SSO with TOTP/OTP
- 📋 **Organized Output** - Each run creates timestamped directory with manifest

## 📋 Requirements

- Python 3.11 or higher
- Google Cloud Service Account (for Sheets integration)
- PLN IAM credentials

---

## 🚀 Quick Start (New Machine Setup)

### 1. Clone Repository

```bash
git clone https://github.com/agungjp/agent-apkt.git
cd agent-apkt
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

### 3. Install Dependencies

```bash
pip install -e .
playwright install chromium
```

### 4. Configure Credentials

#### a. Copy example configs

```bash
cp config.example.yaml config.yaml
cp credentials.example.yaml credentials.yaml
```

#### b. Edit credentials.yaml

```yaml
iam:
  username: "your_pln_username"
  password: "your_pln_password"
```

#### c. Setup Google Sheets (Required)

1. Get the Service Account JSON file (ask project owner)
2. Create secrets directory:
   ```bash
   mkdir -p src/apkt_agent/secrets
   ```
3. Copy the JSON file:
   ```bash
   cp /path/to/service-account.json src/apkt_agent/secrets/apkt-agent.json
   ```
4. Update `config.yaml`:
   ```yaml
   google_sheets:
     enabled: true
     spreadsheet_id: "1Ve4vlRQtVr2dTw5KehoJvm2OKcq3Zn4_hFR7oQ3bFyU"
     credentials_json_path: "src/apkt_agent/secrets/apkt-agent.json"
   ```

### 5. Run the Agent

```bash
apkt-agent
```

---

## 📁 Project Structure

```
agent-apkt/
├── src/apkt_agent/
│   ├── browser/          # Playwright automation
│   │   ├── auth.py       # SSO authentication
│   │   ├── driver.py     # Browser management
│   │   └── download.py   # File download helpers
│   ├── datasets/
│   │   └── se004/        # SE004 report handlers
│   │       ├── kumulatif.py
│   │       ├── multi_download.py
│   │       └── parser.py
│   ├── sinks/
│   │   └── sheets.py     # Google Sheets integration
│   ├── secrets/          # Credentials (gitignored)
│   ├── cli.py            # Command-line interface
│   └── config.py         # Configuration management
├── workspace/
│   └── runs/             # Output directories (gitignored)
├── docs/                 # Documentation
├── config.yaml           # Your configuration (gitignored)
├── credentials.yaml      # Your credentials (gitignored)
├── config.example.yaml   # Example config (committed)
├── credentials.example.yaml  # Example credentials (committed)
└── pyproject.toml        # Package configuration
```

---

## ⚙️ Configuration Files

### config.yaml

```yaml
apkt:
  login_url: "https://new-apkt.pln.co.id/login"
  base_url: "https://new-apkt.pln.co.id"
  timeout: 30000

runtime:
  headless: true          # Run browser without visible window
  viewport:
    width: 1920
    height: 1080

google_sheets:
  enabled: true
  spreadsheet_id: "your-spreadsheet-id"
  credentials_json_path: "src/apkt_agent/secrets/your-service-account.json"
  default_mode: "append"  # "append" or "replace"

datasets:
  se004_kumulatif:
    worksheet_name: "se004_kumulatif"
    units:
      - code: "11"
        name: "WILAYAH ACEH"
      # ... more units
```

### credentials.yaml

```yaml
iam:
  username: "your_pln_username"
  password: "your_pln_password"
```

---

## 📖 Usage

### Interactive Mode

```bash
apkt-agent
```

Follow the menu prompts:
1. Select **2** for "Laporan SAIDI SAIFI Kumulatif SE004"
2. Enter period (YYYYMM format, e.g., `202503` for March 2025)
3. Choose headless mode: `y` (faster) or `n` (for debugging)
4. Confirm with `y` to start download
5. Enter OTP when prompted (from your authenticator app)

### Output

Each run creates a directory in `workspace/runs/`:

```
20260108_084715_se004_kumulatif_202503_PAHF/
├── raw/
│   └── excel/           # Downloaded Excel files (9 files)
├── parsed/
│   └── se004_kumulatif_202503_PAHF.csv  # Combined CSV
└── manifest.json        # Run metadata and results
```

### Results Summary

After successful run:
```
📊 RINGKASAN
----------------------------------------
Total unit      : 9
✓ Berhasil      : 9
✗ Gagal         : 0

📄 HASIL PARSING
----------------------------------------
Total baris     : 1,512
File CSV        : se004_kumulatif_202503_PAHF.csv

📤 GOOGLE SHEETS
----------------------------------------
Status          : ✓ Berhasil diupload
Worksheet       : se004_kumulatif
Baris diupload  : 1,512
```

---

## 🔧 Troubleshooting

### Browser Timeout Issues

If you experience timeouts in headless mode:
- Ensure viewport is configured (1920x1080 recommended)
- Check network connectivity
- Try running with headless: `n` for debugging

### Google Sheets Upload Fails

1. Verify service account JSON path is correct
2. Check that the spreadsheet is shared with the service account email:
   - Open your Google Sheet
   - Click Share → Add the service account email as Editor
   - Service account email looks like: `xxx@project-id.iam.gserviceaccount.com`
3. Ensure Google Sheets API is enabled in Google Cloud Console

### OTP/TOTP Issues

- Make sure your authenticator app time is synced
- OTP codes are valid for 30 seconds
- You have 3 attempts before the process fails

### Playwright Not Installed

```bash
playwright install chromium
```

---

## 📊 Supported Reports

| Report | Status | Description |
|--------|--------|-------------|
| SE004 Kumulatif | ✅ Ready | SAIDI/SAIFI cumulative monthly report |
| SE004 Detail | 🚧 Stub | SAIDI/SAIFI detail report |
| SE004 Gangguan | 🚧 Stub | Disturbance code detail report |

---

## 🛡️ Security Notes

**Never commit these files:**
- `credentials.yaml` - Contains PLN IAM password
- `src/apkt_agent/secrets/*.json` - Google Service Account keys
- `config.yaml` - May contain sensitive IDs

These files are gitignored by default.

---

## 📝 Files You Need to Create on New Machine

| File | Template | Description |
|------|----------|-------------|
| `config.yaml` | `config.example.yaml` | App configuration |
| `credentials.yaml` | `credentials.example.yaml` | PLN IAM credentials |
| `src/apkt_agent/secrets/apkt-agent.json` | (get from owner) | Google Service Account |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Made with ❤️ for PLN data automation**
