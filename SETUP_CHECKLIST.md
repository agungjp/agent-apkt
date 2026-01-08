# 📋 CHECKLIST DISTRIBUSI APKT AGENT KE TEAM

Dokumen ini adalah checklist lengkap untuk didistribusikan kepada tim yang akan menggunakan APKT Agent. Anda (Administrator/Developer) harus mengikuti langkah-langkah ini.

---

## ✅ FASE 1: Persiapan di Laptop Developer

Pastikan semua file sudah siap di repositori GitHub:

- [ ] Semua kode sudah di-commit dan di-push ke GitHub
- [ ] File README_INSTALL.md sudah ada (panduan Windows)
- [ ] File CREDENTIAL_DISTRIBUTION.md sudah ada (panduan untuk admin)
- [ ] File .gitignore sudah include `RAHASIA_SETUP.zip` dan file-file credential lainnya

**Cek GitHub:**
```bash
git log --oneline | head -5
git push origin main  # Push final commits
```

---

## ✅ FASE 2: Membuat File RAHASIA_SETUP.zip

File ini berisi 3 file credential yang diperlukan team member:

```bash
cd /path/to/agent-apkt
zip -j RAHASIA_SETUP.zip config.yaml units_selection.yaml src/apkt_agent/secrets/apkt-agent-af84fa7cde8f.json
```

**Hasil:** File `RAHASIA_SETUP.zip` (ukuran ~3-4 KB) di folder root

**Verifikasi:**
```bash
unzip -l RAHASIA_SETUP.zip
# Pastikan 3 file ada:
# - config.yaml
# - units_selection.yaml
# - apkt-agent-af84fa7cde8f.json
```

---

## ✅ FASE 3: Persiapan File untuk Distribusi

### Opsi A: Email dengan Password Protection (RECOMMENDED) ⭐

1. **Create password-protected ZIP** (menggunakan 7-Zip atau WinRAR):
   - Buka `RAHASIA_SETUP.zip` 
   - Buat archive baru dengan password enkripsi
   - Gunakan password yang kuat (12+ karakter, mix alphanumeric)
   - Contoh password: `APKTAgent2026!SecurePass`

2. **Siapkan file-file yang akan dikirim:**
   ```
   File 1: RAHASIA_SETUP_ENCRYPTED.zip (via email)
   File 2: Password (via SMS/Telegram/WhatsApp terpisah)
   ```

### Opsi B: USB Flashdisk Internal

1. Copy `RAHASIA_SETUP.zip` ke USB flashdisk
2. Serahkan langsung kepada team member
3. Minta konfirmasi sudah copy dan stored dengan aman

### Opsi C: Cloud Storage Dengan Limited Access

1. Upload ke Google Drive/OneDrive folder private
2. Share dengan "Restricted" access ke team member
3. Set expiration date (download hanya valid 7 hari)

---

## 📧 TEMPLATE EMAIL UNTUK TEAM MEMBER

Salin dan modifikasi email berikut untuk dikirim ke team member:

---

**Subject: APKT Agent Setup - Action Required** 📋

Hi [Nama Team Member],

Saya telah siapkan APKT Agent untuk Anda. APKT Agent adalah program otomasi untuk download data APKT dari sistem PLN, parsing ke CSV, dan upload ke Google Sheets secara otomatis.

### 📥 Yang Perlu Anda Lakukan:

#### 1. **Download File Rahasia (CRITICAL)**
File berikut akan dikirim terpisah (JANGAN ubah, JANGAN share):
- ✅ File ZIP dengan password (attached email ini atau via Telegram)
- ✅ Password (via SMS/Telegram - kirim terpisah)

**⚠️ PENTING:** File ini berisi konfigurasi sensitif. Simpan dengan aman dan JANGAN bagikan ke orang lain.

#### 2. **Ikuti Panduan Instalasi**

Buka file **README_INSTALL.md** yang ada di GitHub repository:

**GitHub Link:** https://github.com/agungjp/agent-apkt

Panduan ini berisi:
- ✅ Cara download dan install Python 3.11
- ✅ Cara download dan install Git
- ✅ Cara clone repository
- ✅ Cara setup virtual environment
- ✅ Cara menjalankan program
- ✅ Troubleshooting jika ada error

Dokumen sudah dalam **Bahasa Indonesia** dan sangat mudah diikuti step-by-step.

#### 3. **Ekstrak File Rahasia Sebelum Instalasi**

⚠️ **SANGAT PENTING:**

Sebelum menjalankan perintah instalasi di README_INSTALL.md:

1. Ekstrak file `RAHASIA_SETUP.zip` ke folder `agent-apkt` (folder utama project)
2. Masukkan password yang saya kirim terpisah
3. Verifikasi 3 file sudah ada:
   - `config.yaml`
   - `units_selection.yaml`
   - `apkt-agent-af84fa7cde8f.json`

Jika file ini TIDAK ada, program tidak akan bisa jalan!

#### 4. **Lanjutkan Instalasi**

Setelah file di-ekstrak, ikuti langkah di README_INSTALL.md mulai dari "Langkah 4: Membuat Virtual Environment".

### ❓ Jika Ada Pertanyaan:

1. Baca section **Troubleshooting** di README_INSTALL.md terlebih dahulu
2. Jika masih tidak ketemu solusi, hubungi saya

### 📞 Contact:
- **Email:** [your email]
- **Telegram:** [your telegram]
- **WhatsApp:** [your whatsapp]

---

Sekali lagi, pastikan Anda sudah terima:
- [ ] File `RAHASIA_SETUP.zip` (atau `RAHASIA_SETUP_ENCRYPTED.zip`)
- [ ] Password untuk file ZIP (jika encrypted)
- [ ] Link GitHub repository

Kalau semua sudah ready, mulai dari README_INSTALL.md dan ikuti step-by-step.

Kalau ada yang kurang jelas, hubungi saya!

Terima kasih! 🙏

---

**[Your Name]**  
**[Your Title]**

---

## ✅ FASE 4: Distribusi ke Team Member

Gunakan checklist berikut untuk setiap team member:

| Nama | Method | File Sent | Password Sent | Confirmation |
|------|--------|-----------|---------------|--------------|
| [Nama 1] | Email | ✓ | ✓ | ✓ |
| [Nama 2] | USB | ✓ | ✓ | ✓ |
| [Nama 3] | Drive | ✓ | ✓ | ✓ |

---

## ✅ FASE 5: Support & Troubleshooting

### Hal-hal yang Sering Ditanyakan:

**Q: "Aku lupa password untuk ZIP file"**
A: Kirim password lagi via Telegram/WhatsApp

**Q: "Saya download GitHub, tapi program tidak jalan"**
A: Pastikan Anda sudah ekstrak file `RAHASIA_SETUP.zip` terlebih dahulu

**Q: "Error 'python command not found'"**
A: Lihat section Troubleshooting di README_INSTALL.md, atau minta bantuan untuk reset Python installation

**Q: "Program minta OTP tapi saya tidak tahu caranya"**
A: Baca section "Login & OTP (Detail)" di README_INSTALL.md

### Emergency Support:

Jika ada team member yang mengalami masalah:

1. Minta mereka copy-paste error message yang muncul di terminal
2. Lihat di bagian Troubleshooting README_INSTALL.md
3. Jika masih tidak ketemu solusi, lakukan remote debugging

---

## 🔐 Security Checklist

- [ ] File credential TIDAK ada di GitHub (verify .gitignore)
- [ ] RAHASIA_SETUP.zip sudah ter-proteksi dengan password (jika distribute via email)
- [ ] Password dikirim melalui channel terpisah (BUKAN email yang sama dengan file)
- [ ] Hanya authorized team member yang mendapat file ini
- [ ] Backup credential sudah disimpan di tempat aman (personal laptop/USB internal)

---

## 📝 Dokumentasi Yang Tersedia

File-file dokumentasi yang sudah tersedia di GitHub:

| File | Untuk Siapa | Konten |
|------|-------------|--------|
| **README.md** | Everyone | Overview dan fitur program |
| **README_INSTALL.md** | Team Member (non-technical) | Step-by-step instalasi Windows |
| **CREDENTIAL_DISTRIBUTION.md** | Admin/Developer | Cara distribute credential dengan aman |
| **SETUP_CHECKLIST.md** | Admin/Developer | Checklist ini |

---

## 🎯 Success Criteria

Program dianggap **berhasil di-setup** ketika:

- ✅ Team member bisa jalankan `apkt-agent` di terminal
- ✅ Program menampilkan menu pilihan laporan
- ✅ Team member bisa berhasil login dengan OTP
- ✅ Download selesai tanpa error
- ✅ Data ter-upload ke Google Sheets dengan sukses

---

## 📞 Questions?

Jika ada pertanyaan atau ada yang tidak jelas dalam dokumentasi, hubungi Developer/Administrator.

---

**Versi:** 1.0  
**Tanggal:** Januari 2026  
**Status:** Ready for Distribution ✅
