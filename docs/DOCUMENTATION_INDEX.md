# 📚 DOCUMENTATION INDEX - APKT Agent

Master index untuk semua dokumentasi yang tersedia.

---

## 🎯 Mulai Dari Mana?

### Saya adalah **USER/TEAM MEMBER** 👨‍💻

Saya perlu setup program di laptop Windows saya.

**Start here:** [📖 README_INSTALL.md](README_INSTALL.md)

Dokumentasi lengkap step-by-step dalam Bahasa Indonesia yang mudah diikuti.

---

### Saya adalah **ADMINISTRATOR/DEVELOPER** 👨‍💼

Saya perlu share program ini ke team member saya.

**Start here:** [⚡ QUICK_START_ADMIN.md](QUICK_START_ADMIN.md) (5 menit)

Lalu lanjut ke: [📋 SETUP_CHECKLIST.md](SETUP_CHECKLIST.md) (detail)

---

## 📋 Daftar Lengkap Dokumentasi

### 👥 Untuk Team Member (User)

| Dokumen                                | Konten                                                                                                                                                  | Waktu  |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| [README_INSTALL.md](README_INSTALL.md) | **Step-by-step installation guide** - Python setup, Git setup, clone repo, virtual env, install dependencies, cara menjalankan program, troubleshooting | 45 min |
| [README.md](README.md)                 | Overview program, fitur, konfigurasi dasar                                                                                                              | 10 min |

### 👨‍💼 Untuk Administrator

| Dokumen                                                  | Konten                                                                                                                          | Waktu  |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ------ |
| [QUICK_START_ADMIN.md](QUICK_START_ADMIN.md)             | **SUPER CEPAT** - Langkah distribusi, email template, file reference                                                            | 5 min  |
| [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md)                 | **LENGKAP** - Fase persiapan, pembuatan credential ZIP, distribution methods, email template, support guide, security checklist | 30 min |
| [CREDENTIAL_DISTRIBUTION.md](CREDENTIAL_DISTRIBUTION.md) | **SECURITY GUIDE** - Apa isi file rahasia, siapa yang boleh dapat, cara distribute aman, update procedure, emergency response   | 15 min |

### 📖 Program Documentation

| File                     | Tujuan                        |
| ------------------------ | ----------------------------- |
| README.md                | Pengenalan & feature overview |
| config.example.yaml      | Template konfigurasi          |
| credentials.example.yaml | Template credentials          |

---

## 🚀 Scenario-Based Guide

### Scenario 1: "Aku user baru, mau setup di Windows"

1. Clone GitHub repo
2. Baca **[README_INSTALL.md](README_INSTALL.md)** ← **START HERE**
3. Follow step-by-step
4. Done! Jalankan `apkt-agent`

**Time:** 45 minutes

---

### Scenario 2: "Aku admin, mau kirim ke 1 orang dulu"

1. Baca **[QUICK_START_ADMIN.md](QUICK_START_ADMIN.md)** ← **START HERE** (5 min)
2. Buat RAHASIA_SETUP.zip (sudah ada)
3. Kirim GitHub link + ZIP file + password (via email template)
4. Follow up sampai mereka install sukses

**Time:** ~20 minutes + user installation time

---

### Scenario 3: "Aku admin, mau share ke 10+ orang"

1. Baca **[QUICK_START_ADMIN.md](QUICK_START_ADMIN.md)** (5 min) ← **MULAI SINI**
2. Baca **[SETUP_CHECKLIST.md](SETUP_CHECKLIST.md)** (30 min) ← **DETAIL**
3. Baca **[CREDENTIAL_DISTRIBUTION.md](CREDENTIAL_DISTRIBUTION.md)** (15 min) ← **SECURITY**
4. Plan distribusi (method, timeline, support)
5. Test dengan 1 orang dulu
6. Roll out ke semua

**Time:** ~1 hour planning + distribution time

---

### Scenario 4: "Credential kami expired, mau update"

1. Generate credential baru (password, service account, etc)
2. Update file locally
3. Buat RAHASIA_SETUP.zip baru
4. Baca **[CREDENTIAL_DISTRIBUTION.md](CREDENTIAL_DISTRIBUTION.md)** → "Update Credential" section
5. Kirim ke semua team member yang punya akses

---

### Scenario 5: "Ada masalah saat setup"

**Jika Anda adalah USER:**

1. Baca **[README_INSTALL.md](README_INSTALL.md)** → Troubleshooting section
2. Jika masih stuck, hubungi admin

**Jika Anda adalah ADMIN:**

1. Baca **[SETUP_CHECKLIST.md](SETUP_CHECKLIST.md)** → "Support & Troubleshooting" section
2. Cek apakah user sudah ekstrak RAHASIA_SETUP.zip
3. Cek apakah Python installation benar
4. Remote debugging jika perlu

---

## 🔑 File Credential (TIDAK di GitHub)

### Apa itu File Rahasia?

File ini TIDAK ada di GitHub karena sensitive:

```
RAHASIA_SETUP.zip (3.1 KB)
├── config.yaml (password PLN IAM asli)
├── units_selection.yaml (daftar unit)
└── apkt-agent-af84fa7cde8f.json (Google Service Account key)
```

### Kamu sebagai USER:

Anda akan **menerima** file ini dari admin.

Instruksi: Ekstrak ke folder root project SEBELUM menjalankan instalasi.

### Kamu sebagai ADMIN:

Anda yang **membuat dan mendistribusikan** file ini.

Instruksi: Baca [CREDENTIAL_DISTRIBUTION.md](CREDENTIAL_DISTRIBUTION.md)

---

## 📊 Documentation Map

```
README.md (Program overview)
│
├─→ USER INSTALLATION PATH:
│   └─→ README_INSTALL.md ⭐ (START HERE for users)
│       ├─ Step 1-7: Installation
│       ├─ Usage guide
│       └─ Troubleshooting
│
└─→ ADMIN DISTRIBUTION PATH:
    ├─→ QUICK_START_ADMIN.md ⭐ (START HERE for fast distribution)
    │   ├─ 3 langkah distribusi cepat
    │   ├─ Email template
    │   └─ Security checklist
    │
    ├─→ SETUP_CHECKLIST.md (Full admin guide)
    │   ├─ Phase 1-5: Complete distribution
    │   ├─ Email template
    │   ├─ Support guide
    │   └─ Success criteria
    │
    └─→ CREDENTIAL_DISTRIBUTION.md (Security guide)
        ├─ File contents & security warnings
        ├─ Distribution methods
        ├─ Update procedures
        └─ Emergency response
```

---

## ✅ Reading Checklist

### For New Users (Windows, non-technical):

- [ ] Read README_INSTALL.md completely
- [ ] Follow Langkah 1-7 step-by-step
- [ ] Test dengan jalankan `apkt-agent`
- [ ] Contact admin jika ada error

### For New Administrators:

- [ ] Read QUICK_START_ADMIN.md (untuk pemahaman cepat)
- [ ] Read SETUP_CHECKLIST.md (untuk planning)
- [ ] Read CREDENTIAL_DISTRIBUTION.md (untuk security)
- [ ] Create distribution plan
- [ ] Prepare RAHASIA_SETUP.zip
- [ ] Test dengan 1 user
- [ ] Roll out ke semua

---

## 🎯 Key Takeaways

| Role         | Action             | Doc                        |
| ------------ | ------------------ | -------------------------- |
| **User**     | Install program    | README_INSTALL.md          |
| **Admin**    | Quick distribution | QUICK_START_ADMIN.md       |
| **Admin**    | Full planning      | SETUP_CHECKLIST.md         |
| **Admin**    | Security & update  | CREDENTIAL_DISTRIBUTION.md |
| **Everyone** | Program overview   | README.md                  |

---

## 🔗 Quick Links

- **GitHub Repository:** https://github.com/agungjp/agent-apkt
- **Installation Guide (User):** [README_INSTALL.md](README_INSTALL.md)
- **Admin Quick Start:** [QUICK_START_ADMIN.md](QUICK_START_ADMIN.md)
- **Admin Full Guide:** [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md)
- **Security Guide:** [CREDENTIAL_DISTRIBUTION.md](CREDENTIAL_DISTRIBUTION.md)

---

## 📞 Support

**Untuk User:** Hubungi Administrator Anda

**Untuk Administrator:**

1. Cek relevant documentation di atas
2. Jika masih stuck, review implementation details di relevant markdown files
3. Ensure RAHASIA_SETUP.zip sudah properly configured

---

**Version:** 1.0  
**Last Updated:** Januari 2026  
**Status:** Ready for Production ✅
