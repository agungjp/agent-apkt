# 🎯 QUICK START - Panduan Cepat Distribusi

Dokumen singkat ini adalah panduan SUPER cepat untuk Anda (Administrator) dalam mendistribusikan APKT Agent ke tim.

---

## 📋 Yang Sudah Siap

✅ **Source Code** → GitHub (https://github.com/agungjp/agent-apkt)
✅ **Dokumentasi untuk User** → `docs/README_INSTALL.md` (Indonesian, step-by-step)
✅ **Dokumentasi untuk Admin** → `docs/CREDENTIAL_DISTRIBUTION.md`
✅ **Checklist Admin** → `docs/SETUP_CHECKLIST.md`
✅ **File Credential ZIP** → `RAHASIA_SETUP.zip` (4.5 KB, dengan struktur folder)

---

## 🚀 Langkah Distribusi (Super Cepat)

### 1️⃣ Siapkan File (Copy-Paste)

```bash
# Buka terminal di folder agent-apkt
cd /Users/agungperkasa/Documents/02\ Dev/sandbox/ods-apkt

# Buat encrypted ZIP (opsional, tapi RECOMMENDED)
# atau gunakan RAHASIA_SETUP.zip yang sudah ada
ls -lh RAHASIA_SETUP.zip
```

### 2️⃣ Kirim Email ke Team Member

Gunakan template ini (COPY-PASTE):

---

**Email Template:**

```
Subject: APKT Agent Setup - Ikuti langkah mudah ini 📋

Hi [Nama],

Setup APKT Agent super mudah. Ikuti 3 langkah:

1. Clone GitHub:
   https://github.com/agungjp/agent-apkt

2. Extract file RAHASIA_SETUP.zip yang saya kirim ke folder project
   (PENTING: extract ke root folder, folder-folder akan otomatis terbuat)

3. Buka file docs/README_INSTALL.md dan ikuti step-by-step

Email attachment atau kirim via [Telegram/WhatsApp/Drive]:
   - File: RAHASIA_SETUP.zip

Password kirim terpisah via [Telegram/WhatsApp]

Kalau ada masalah, baca troubleshooting section di
docs/README_INSTALL.md atau hubungi saya.

Makasih!
```

---

### 3️⃣ Kirim File Credential

Pilih salah satu:

| Method    | Cara Kirim                  | Keamanan                 |
| --------- | --------------------------- | ------------------------ |
| **Email** | Attachment ZIP              | 🔒🔒🔒 (dengan password) |
| **USB**   | Flashdisk langsung          | 🔒🔒🔒                   |
| **Drive** | Google Drive link (limited) | 🔒🔒                     |

**⚠️ PENTING:** Password dikirim TERPISAH!

---

## ✅ User akan menerima:

| File               | Sumber    | Cara dapat            |
| ------------------ | --------- | --------------------- |
| Source code + docs | GitHub    | Download              |
| RAHASIA_SETUP.zip  | Dari Anda | Email/USB/Drive       |
| Password           | Dari Anda | Telegram/WhatsApp/SMS |

---

## 🎯 Expected Result

User akan bisa jalankan:

```bash
apkt-agent
```

Program akan:

1. Tanya pilih laporan
2. Tanya periode & headless mode
3. Login otomatis (pakai credential di file rahasia)
4. Tanya OTP (user lihat di authenticator app & ketik)
5. Download 9 file Excel
6. Parse ke CSV (1,512 rows)
7. Upload ke Google Sheets otomatis ✅

---

## 🔐 Security Checklist

- [ ] RAHASIA_SETUP.zip TIDAK ada di GitHub ✓
- [ ] Password protection di ZIP (jika via email)
- [ ] Password dikirim terpisah dari file
- [ ] Hanya authorized people yang terima file

---

## 📞 Support untuk User

Jika user error:

1. Check README_INSTALL.md → Troubleshooting section
2. Hubungi Anda

Jika Anda perlu bantuan:

1. Lihat SETUP_CHECKLIST.md (lengkap & detail)
2. Lihat CREDENTIAL_DISTRIBUTION.md (security & update)

---

## 📊 File Reference

| File                            | Untuk            | Link                   |
| ------------------------------- | ---------------- | ---------------------- |
| README.md                       | Overview         | 📖 GitHub              |
| docs/README_INSTALL.md          | Installation     | 📖 GitHub (untuk user) |
| docs/CREDENTIAL_DISTRIBUTION.md | Admin security   | 📖 GitHub              |
| docs/SETUP_CHECKLIST.md         | Admin full guide | 📖 GitHub              |
| RAHASIA_SETUP.zip               | Credentials      | 💾 Laptop Anda         |

---

## 💡 Pro Tips

1. **Test dulu dengan 1 orang** sebelum kirim ke semua
2. **Simpan backup** RAHASIA_SETUP.zip di tempat aman
3. **Document** siapa aja yang terima credential
4. **Jika credential expired**, bikin ZIP baru & kirim lagi
5. **Ekstrak ZIP ke root folder** agar struktur folder otomatis terbentuk

---

**Yang Perlu Dilakukan Hari Ini:**

- [ ] Baca file `docs/SETUP_CHECKLIST.md` (untuk pemahaman penuh)
- [ ] Kirim GitHub link ke team member
- [ ] Kirim RAHASIA_SETUP.zip via email (dengan password)
- [ ] Kirim password via Telegram/WhatsApp
- [ ] Follow up sampai mereka berhasil setup

**Total waktu:** ~15 menit komunikasi + ~45 menit per user untuk instalasi

---

**Siap untuk go live? Mulai sekarang! 🚀**
