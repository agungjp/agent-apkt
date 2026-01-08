# 📋 Panduan Instalasi APKT Agent untuk Windows

Dokumen ini adalah panduan lengkap dan mudah diikuti untuk menginstal dan menjalankan **APKT Agent** di komputer Windows Anda. Ikuti setiap langkah dengan teliti.

---

## ⚠️ PENTING: Baca Terlebih Dahulu

**Program ini memerlukan 3 file rahasia yang TIDAK ada di GitHub. File-file ini akan dikirimkan oleh Administrator/Developer secara terpisah melalui:**

- Email (attachment ZIP)
- USB Flashdisk
- Cloud storage (Google Drive, OneDrive)

**Anda WAJIB memiliki ketiga file ini sebelum melanjutkan:**

1. `config.yaml` - Konfigurasi aplikasi dengan password PLN IAM asli
2. `service_account.json` - Kunci Google Service Account untuk upload ke Google Sheets
3. `units_selection.yaml` - Daftar unit/wilayah yang akan didownload

> 🚨 **JANGAN PERNAH** upload ketiga file ini ke folder public atau bagikan di tempat umum. File-file ini berisi informasi sensitif dan kunci akses!

---

## 📦 Prasyarat: Software Yang Perlu Diinstal

Sebelum memulai, pastikan komputer Anda memiliki dua software berikut:

### 1. Python 3.11 (atau lebih tinggi)

**Cara Download dan Install:**

1. Buka browser dan kunjungi: **https://www.python.org/downloads/**
2. Klik tombol besar yang bertuliskan **"Download Python 3.11"** (atau versi terbaru)
3. Tunggu file `.exe` selesai diunduh
4. **Buka/Double-click file yang sudah diunduh**
5. **PENTING:** Centang kotak yang bertuliskan **"Add Python to PATH"** (jangan lupa!)

   ![image-alt-text]

   Jika Anda lupa mencentang, install akan bermasalah!

6. Klik **"Install Now"** dan tunggu sampai selesai
7. Klik **"Close"**

**Verifikasi instalasi:**

- Buka **Command Prompt** (tekan `Win + R`, ketik `cmd`, Enter)
- Ketik: `python --version`
- Jika muncul versi Python, instalasi berhasil ✅

---

### 2. Git for Windows

**Cara Download dan Install:**

1. Buka browser dan kunjungi: **https://git-scm.com/download/win**
2. Klik pada file yang sesuai (64-bit atau 32-bit, sesuaikan dengan komputer Anda)
3. **Buka file yang sudah diunduh**
4. Klik **"Next"** untuk semua opsi default (tidak perlu diubah)
5. Tunggu instalasi selesai dan klik **"Close"**

**Verifikasi instalasi:**

- Buka **Command Prompt** (tekan `Win + R`, ketik `cmd`, Enter)
- Ketik: `git --version`
- Jika muncul versi Git, instalasi berhasil ✅

---

## 🚀 Langkah-Langkah Instalasi

### Langkah 1: Buat Folder untuk Proyek

1. Buka **File Explorer** (tekan `Win + E`)
2. Navigasi ke folder yang Anda inginkan (misalnya `C:\Users\NamaAnda\Documents`)
3. Klik kanan → **New Folder** → Beri nama: `agent-apkt`

---

### Langkah 2: Ekstrak File Rahasia (SANGAT PENTING!)

1. **Mintalah file `RAHASIA_SETUP.zip` dari Administrator/Developer**
2. Tempatkan file ZIP tersebut di folder `agent-apkt` yang baru dibuat
3. **Klik kanan pada `RAHASIA_SETUP.zip`** → **Extract All...**
4. Pastikan folder tujuan adalah **`agent-apkt`** (bukan subfolder)
5. Klik **"Extract"**

**Setelah ekstrak, folder Anda harus terlihat seperti ini:**

```
agent-apkt/
├── config.yaml                    ✅ (dari file rahasia)
├── service_account.json           ✅ (dari file rahasia)
├── units_selection.yaml           ✅ (dari file rahasia)
└── [folder dan file lainnya akan ditambah di langkah berikutnya]
```

> ⚠️ **Jika ketiga file ini TIDAK ada, program tidak akan bisa jalan!** Hubungi Administrator/Developer jika file hilang.

---

### Langkah 3: Clone Repository dari GitHub

1. **Buka Command Prompt** di folder `agent-apkt`:

   - Tekan `Win + R`
   - Ketik: `cmd`
   - Ketika Command Prompt terbuka, ketik:

   ```
   cd C:\Users\NamaAnda\Documents\agent-apkt
   ```

   (Sesuaikan path sesuai lokasi folder Anda)

2. **Clone kode dari GitHub dengan perintah:**

   ```bash
   git clone https://github.com/agungjp/agent-apkt.git .
   ```

   (Perhatian: Ada titik `.` di akhir perintah!)

3. Tunggu proses clone selesai (beberapa menit)

**Hasilnya:**

```
agent-apkt/
├── config.yaml                    ✅ (milik Anda dari file rahasia)
├── service_account.json           ✅ (milik Anda dari file rahasia)
├── units_selection.yaml           ✅ (milik Anda dari file rahasia)
├── src/                           ✅ (dari GitHub)
├── workspace/                     ✅ (dari GitHub)
├── README.md                      ✅ (dari GitHub)
└── [file lainnya...]
```

---

### Langkah 4: Membuat Virtual Environment

Virtual environment adalah "ruang kerja" terpisah untuk Python program ini agar tidak mengganggu program Python lainnya.

**Di Command Prompt yang masih terbuka, ketik:**

```bash
python -m venv venv
```

Tunggu beberapa saat hingga proses selesai (muncul prompt baru).

---

### Langkah 5: Mengaktifkan Virtual Environment

**Masih di Command Prompt, ketik perintah berikut (PERLU DIINGAT untuk setiap kali membuka terminal baru):**

```bash
venv\Scripts\activate
```

Jika berhasil, prompt Command Prompt akan berubah menjadi:

```
(venv) C:\Users\NamaAnda\Documents\agent-apkt>
```

> 💡 **PENTING:** Setiap kali Anda membuka Command Prompt baru untuk menjalankan program ini, jangan lupa jalankan perintah ini terlebih dahulu! Jika Anda lupa activate, program tidak akan bisa jalan dengan benar.

---

### Langkah 6: Menginstal Dependencies

Dependencies adalah library/paket Python yang diperlukan program ini untuk berjalan.

**Masih di Command Prompt (dengan venv sudah aktif), ketik:**

```bash
pip install -e .
```

Tunggu proses instalasi selesai (akan ada banyak teks yang muncul dan bisa memakan waktu 2-5 menit).

---

### Langkah 7: Menginstal Chromium Browser

Program ini memerlukan Chromium browser untuk otomasi download data.

**Masih di Command Prompt, ketik:**

```bash
playwright install chromium
```

Tunggu proses instalasi selesai (akan ada output teks).

---

## ✅ Instalasi Selesai!

Jika semua langkah di atas berhasil tanpa error, Anda siap menjalankan program.

---

## 🎯 Cara Menjalankan Program

### Setiap Kali Ingin Menjalankan Program:

1. **Buka Command Prompt** (tekan `Win + R`, ketik `cmd`, Enter)

2. **Navigasi ke folder project:**

   ```bash
   cd C:\Users\NamaAnda\Documents\agent-apkt
   ```

3. **Aktifkan virtual environment:**

   ```bash
   venv\Scripts\activate
   ```

   (Prompt akan berubah menjadi `(venv) C:\...>`)

4. **Jalankan program:**
   ```bash
   apkt-agent
   ```

Program akan menampilkan menu interaktif dengan pilihan laporan yang tersedia.

---

## 📖 Penggunaan Program

### Menu Utama

Program akan menampilkan menu seperti ini:

```
============================================================
APKT Agent - Data Extraction Tool
============================================================

------------------------------------------------------------
MENU UTAMA
------------------------------------------------------------

  1. Laporan SAIDI SAIFI SE004 [stub]
  2. Laporan SAIDI SAIFI Kumulatif SE004
  3. Laporan Detail Kode Gangguan SE004 [stub]

  0. Keluar

------------------------------------------------------------
Pilih menu (0-3):
```

### Cara Menggunakan:

1. **Pilih Menu:** Ketik angka `2` untuk "Laporan SAIDI SAIFI Kumulatif SE004" dan tekan Enter

2. **Masukkan Periode:**

   - Program akan meminta Anda memasukkan periode dalam format `YYYYMM`
   - Contoh: `202503` untuk Maret 2025
   - Tekan Enter

3. **Pilih Mode Tampilan Browser:**

   - Ketik `y` untuk mode headless (tanpa tampilan browser, lebih cepat)
   - Ketik `n` untuk mode dengan tampilan browser (untuk debugging)
   - Tekan Enter

4. **Konfirmasi:**

   - Program akan menampilkan ringkasan pilihan Anda
   - Ketik `y` untuk lanjutkan atau `n` untuk membatalkan
   - Tekan Enter

5. **Browser Akan Terbuka (jika mode non-headless):**

   - Browser akan secara otomatis melakukan login ke APKT
   - Anda TIDAK perlu melakukan apa-apa, biarkan browser bekerja

6. **Masukkan Kode OTP (jika diminta):**
   - Program mungkin meminta Anda untuk memasukkan kode OTP
   - **Buka aplikasi authenticator di HP Anda (Google Authenticator, Authy, dll)**
   - **Ketik kode 6 digit yang ditampilkan di terminal Command Prompt**
   - **Tekan Enter**

---

## 🔐 Login & OTP (Detail)

### Apa itu OTP?

OTP (One-Time Password) adalah kode keamanan 6 digit yang berubah setiap 30 detik. Ini digunakan untuk autentikasi dua faktor pada sistem PLN IAM.

### Cara Mendapatkan Kode OTP:

1. **Buka aplikasi Authenticator di HP Anda**, misalnya:

   - Google Authenticator
   - Microsoft Authenticator
   - Authy
   - Atau aplikasi authenticator lainnya yang Anda gunakan untuk PLN

2. **Cari akun PLN Anda di aplikasi tersebut**

3. **Lihat kode 6 digit yang ditampilkan** (biasanya berubah setiap 30 detik)

### Ketika Program Meminta OTP:

```
------------------------------------------------------------
Two-Factor Authentication Required (Attempt 1/3)
------------------------------------------------------------
Enter OTP code:
```

1. **Buka authenticator di HP Anda**
2. **Lihat kode yang muncul**
3. **Kembali ke terminal Command Prompt**
4. **Ketik kode OTP** (6 digit)
5. **Tekan Enter**

> ⏰ **INGAT:** Kode OTP hanya berlaku 30 detik! Ketik dengan cepat!

> 📍 **Jika OTP salah:** Program memberi Anda 3 kesempatan sebelum proses gagal.

---

## 📊 Hasil Program

Setelah program selesai, Anda akan melihat ringkasan hasil:

```
============================================================
HASIL EKSTRAKSI
============================================================

  📊 RINGKASAN
  ----------------------------------------
  Total unit      : 9
  ✓ Berhasil      : 9
  ✗ Gagal         : 0

  📄 HASIL PARSING
  ----------------------------------------
  Total baris     : 1,512
  File CSV        : se004_kumulatif_202503_XXXXX.csv

  📤 GOOGLE SHEETS
  ----------------------------------------
  Status          : ✓ Berhasil diupload
  Worksheet       : se004_kumulatif
  Baris diupload  : 1,512

  📁 LOKASI FILE
  ----------------------------------------
  Run directory   : workspace/runs/20260108_XXXXX
  Excel files     : workspace/runs/20260108_XXXXX/raw/excel
  Parsed CSV      : workspace/runs/20260108_XXXXX/parsed
```

File hasil download akan tersimpan di folder `workspace/runs/` dengan struktur:

```
workspace/runs/
└── 20260108_084715_se004_kumulatif_202503_PAHF/
    ├── raw/
    │   └── excel/                 # File Excel asli (9 file)
    ├── parsed/
    │   └── se004_kumulatif_202503_PAHF.csv  # Hasil parsing CSV
    └── manifest.json              # Metadata run
```

---

## 🐛 Troubleshooting (Solusi Masalah Umum)

### ❌ Error: "python command not found" atau "pip command not found"

**Penyebab:** Python belum ditambahkan ke PATH saat instalasi

**Solusi:**

1. Buka Control Panel → System → Advanced System Settings
2. Klik "Environment Variables"
3. Pastikan Python path sudah ada (biasanya `C:\Users\NamaAnda\AppData\Local\Programs\Python\Python311\`)
4. Restart Command Prompt

Atau install ulang Python dan **PASTIKAN centang "Add Python to PATH"**

---

### ❌ Error: "No module named 'apkt_agent'"

**Penyebab:** Virtual environment belum diaktifkan

**Solusi:** Pastikan prompt Command Prompt menampilkan `(venv)` di awal:

```
(venv) C:\Users\...>
```

Jika belum, jalankan:

```bash
venv\Scripts\activate
```

---

### ❌ Error: "File config.yaml not found" atau "service_account.json not found"

**Penyebab:** File rahasia belum diektrak ke folder project

**Solusi:**

1. Pastikan Anda sudah menerima file `RAHASIA_SETUP.zip` dari Administrator/Developer
2. Ekstrak file ZIP ke folder `agent-apkt`
3. Verifikasi bahwa `config.yaml`, `service_account.json`, dan `units_selection.yaml` sudah ada di folder root

---

### ❌ Error: Timeout pada saat download atau login gagal

**Penyebab:** Koneksi internet lambat atau sistem APKT sedang maintenance

**Solusi:**

1. Cek koneksi internet Anda
2. Tunggu beberapa menit dan coba lagi
3. Jika menggunakan headless mode, coba dengan mode non-headless untuk debugging:
   - Saat program meminta pilihan headless mode, ketik `n`

---

### ❌ Error: "OTP code invalid" atau OTP terus salah

**Penyebab:**

- Kode OTP sudah expired (lebih dari 30 detik)
- Waktu di HP/komputer tidak sinkron
- Kode OTP yang diketik tidak sesuai

**Solusi:**

1. **Sinkronkan waktu komputer:**

   - Buka Settings → Time & Language → Date & time
   - Pastikan "Sync time" aktif (toggle ON)

2. **Ketik OTP dengan cepat** (dalam 30 detik setelah melihat kode)

3. **Jika masih gagal setelah 3 percobaan:** Program akan restart, jalankan kembali dari awal

---

### ❌ Browser crash atau tidak bisa login

**Penyebab:** Koneksi internet atau sistem APKT bermasalah

**Solusi:**

1. Jalankan program lagi (biasanya langsung berhasil)
2. Jika masih error, coba tunggu 5 menit lalu jalankan lagi
3. Hubungi Administrator/Developer jika masalah terus berlanjut

---

## 📞 Butuh Bantuan?

Jika Anda mengalami masalah yang tidak tercantum di atas, silakan hubungi:

- **Administrator/Developer:** [Nama dan kontak]
- **Email:** [Email support]
- **Telegram/WhatsApp:** [Nomor kontak]

**Saat menghubungi, tuliskan:**

1. Pesan error yang muncul (copy-paste dari Command Prompt)
2. Langkah apa yang sedang Anda lakukan
3. Sistem operasi dan versi Windows Anda

---

## ✨ Selamat!

Anda sudah siap menggunakan **APKT Agent**! 🎉

Program ini akan membantu Anda mengunduh dan memproses data APKT secara otomatis, menghemat waktu dan tenaga.

Jika ada pertanyaan atau masalah, jangan ragu untuk menghubungi Tim Teknis.

---

**Versi Dokumen:** 1.0  
**Tanggal:** Januari 2026  
**Diperbarui oleh:** Administrator
