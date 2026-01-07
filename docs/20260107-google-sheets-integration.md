# APKT Agent - Google Sheets Integration

**Dokumen dibuat:** 7 Januari 2026  
**Versi:** 1.0

## Overview

Fitur Google Sheets memungkinkan upload otomatis hasil parsing CSV ke Google Sheets menggunakan Service Account authentication.

## Setup

### 1. Buat Google Cloud Project

1. Buka [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project atau pilih existing
3. Enable **Google Sheets API**

### 2. Buat Service Account

1. Go to **IAM & Admin** > **Service Accounts**
2. Click **Create Service Account**
3. Isi nama (e.g., `sheets-agent`)
4. Click **Create and Continue**
5. Skip role assignment
6. Click **Done**

### 3. Generate JSON Key

1. Click service account yang baru dibuat
2. Go to **Keys** tab
3. Click **Add Key** > **Create new key**
4. Pilih **JSON**
5. Download file, simpan di project root
6. Rename jika perlu (e.g., `apkt-agent-xxxxx.json`)

### 4. Share Spreadsheet

1. Buka Google Spreadsheet target
2. Click **Share**
3. Add email service account: `xxx@yyy.iam.gserviceaccount.com`
   - Email ada di JSON file field `client_email`
4. Set permission: **Editor**
5. Click **Send** (uncheck notify)

### 5. Konfigurasi

Edit `config.yaml`:

```yaml
google_sheets:
  enabled: true
  spreadsheet_id: "1Ve4vlRQtVr2dTw5KehoJvm2OKcq3Zn4_hFR7oQ3bFyU"
  worksheet_name: "se004_kumulatif"
  credentials_json_path: "./apkt-agent-af84fa7cde8f.json"
  mode: "append" # atau "replace"
```

| Field                   | Deskripsi                                                 |
| ----------------------- | --------------------------------------------------------- |
| `enabled`               | `true` untuk enable upload, `false` untuk skip            |
| `spreadsheet_id`        | ID dari URL spreadsheet (bagian antara `/d/` dan `/edit`) |
| `worksheet_name`        | Nama sheet/tab untuk upload                               |
| `credentials_json_path` | Path ke Service Account JSON                              |
| `mode`                  | `replace` = clear dulu, `append` = tambah di bawah        |

## Mode Upload

### Replace Mode

```yaml
mode: "replace"
```

- Clear semua data di worksheet
- Upload dari A1
- Cocok untuk: refresh data lengkap, testing

### Append Mode

```yaml
mode: "append"
```

- Cari baris terakhir dengan data
- Tambah data baru di bawah (tanpa header)
- Auto-resize worksheet jika kurang baris
- Cocok untuk: akumulasi data multi-periode

## Format Konversi

Data dikonversi dari format Indonesia ke internasional:

| Kolom              | Indonesia     | Internasional |
| ------------------ | ------------- | ------------- |
| `jumlah_pelanggan` | `2.828.036,0` | `2828036.0`   |
| `saidi_total`      | `5,7905`      | `5.7905`      |
| `saifi_total`      | `3,7555`      | `3.7555`      |
| dst...             |               |               |

Kolom yang dikonversi:

- `jumlah_pelanggan`
- `saidi_total`
- `saidi_total_menit`
- `saifi_total`
- `jml_plg_padam`
- `jam_x_jml_plg_padam`
- `saidi_jam`
- `saifi_kali`
- `jumlah_gangguan_kali`
- `lama_padam_jam`
- `kwh_tak_tersalurkan`

## Troubleshooting

### Error: Permission Denied (403)

**Penyebab:** Service account belum di-share ke spreadsheet

**Solusi:**

1. Buka spreadsheet
2. Share ke email service account
3. Set permission Editor

### Error: Spreadsheet Not Found (404)

**Penyebab:** Spreadsheet ID salah atau tidak ada akses

**Solusi:**

1. Cek spreadsheet_id di config
2. Pastikan ID benar (dari URL)
3. Pastikan sudah di-share

### Error: Credentials File Not Found

**Penyebab:** Path ke JSON salah

**Solusi:**

1. Cek `credentials_json_path` di config
2. Gunakan path relatif dari project root
3. Pastikan file JSON ada

### Error: Exceeds Grid Limits

**Penyebab:** Worksheet terlalu kecil untuk data

**Solusi:**

- Sudah di-handle otomatis dengan auto-resize
- Jika masih error, resize manual di Google Sheets

## API Usage

### Manual Upload

```python
from apkt_agent.sinks.sheets import upload_csv_to_worksheet

result = upload_csv_to_worksheet(
    csv_path="path/to/file.csv",
    spreadsheet_id="YOUR_SPREADSHEET_ID",
    worksheet_name="sheet_name",
    credentials_json_path="./service-account.json",
    mode="append"  # atau "replace"
)

print(result)
# {
#     "success": True,
#     "row_count": 1512,
#     "col_count": 19,
#     "worksheet_name": "sheet_name",
#     "spreadsheet_id": "..."
# }
```

### Cek Data di Sheet

```python
import gspread
from google.oauth2.service_account import Credentials

creds = Credentials.from_service_account_file(
    './apkt-agent-xxx.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
client = gspread.authorize(creds)
sheet = client.open_by_key('SPREADSHEET_ID')
ws = sheet.worksheet('sheet_name')

# Get all data
data = ws.get_all_values()
print(f"Total rows: {len(data)}")

# Get specific range
range_data = ws.get('A1:C10')
```

## Security

### .gitignore

Pastikan file sensitif tidak ter-commit:

```gitignore
# Service Account credentials
secrets/
*-service-account.json
apkt-agent-*.json
```

### Environment Variables (Optional)

Untuk production, bisa gunakan environment variables:

```python
import os
credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', './default.json')
```
