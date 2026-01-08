# 🔐 RAHASIA_SETUP.zip - Panduan Distribusi File Credential

**Dokumen ini HANYA untuk Administrator/Developer. Jangan bagikan ke publik.**

---

## 📦 Isi File RAHASIA_SETUP.zip

File ZIP ini berisi 3 file credential yang **SANGAT SENSITIF** dan diperlukan agar program APKT Agent bisa berjalan:

### 1. **config.yaml** (767 bytes)

- **Apa itu:** File konfigurasi aplikasi dengan setting PLN IAM
- **Berisi:** Username/password PLN IAM asli dan ID Google Spreadsheet
- **Bahaya jika bocor:** Orang lain bisa login ke akun PLN Anda dan akses data sensitif
- **Aksi:** Jalankan `pip install -e . && playwright install chromium`

### 2. **units_selection.yaml** (1.3 KB)

- **Apa itu:** Daftar unit/wilayah PLN yang akan didownload
- **Berisi:** Kode dan nama 9 wilayah PLN
- **Bahaya jika bocor:** Rendah, informasi bersifat publik
- **Aksi:** Menentukan unit mana saja yang didownload dalam setiap run

### 3. **apkt-agent-af84fa7cde8f.json** (2.3 KB)

- **Apa itu:** Private key dari Google Service Account
- **Berisi:** Kunci autentikasi untuk mengakses Google Sheets API
- **Bahaya jika bocor:** Orang lain bisa mengubah/menghapus data di Google Sheets Anda
- **Fungsi:** Memungkinkan bot auto-upload hasil parsing ke Google Sheets

---

## 👥 Distribusi File

### Siapa Yang Boleh Mendapat File Ini?

✅ **BOLEH:**

- Team member yang bekerja resmi dengan Anda
- Laptop/komputer yang under your control
- Melalui channel komunikasi aman (email internal, USB internal, etc)

❌ **JANGAN PERNAH:**

- Upload ke GitHub atau public repository
- Bagikan via email publik atau messaging app tidak aman
- Simpan di cloud storage yang tidak ter-enkripsi
- Bagikan ke orang yang tidak authorized

---

## 📤 Cara Mengirim File ke Team Member

### Opsi 1: Email dengan Password Protection ⭐ (Recommended)

1. Kirim file `RAHASIA_SETUP.zip` sebagai attachment
2. **Buat ZIP password** (gunakan tool seperti 7-Zip atau WinRAR):
   - Klik kanan ZIP → 7-Zip → Add to archive
   - Set password enkripsi (jangan password yang mudah)
3. Kirim password terpisah melalui channel lain (misalnya Telegram/WhatsApp)

### Opsi 2: USB Flashdisk Internal

1. Copy `RAHASIA_SETUP.zip` ke USB flashdisk
2. Serahkan langsung kepada team member
3. Minta konfirmasi mereka sudah copy file

### Opsi 3: Google Drive/OneDrive Dengan Limited Access

1. Upload ke folder private
2. Share folder dengan "Restricted" access ke team member saja
3. Beri tau mereka download dan delete file di laptop mereka setelah extracted

---

## 📋 Instruksi untuk Team Member

Kirimkan pesan berikut kepada setiap orang yang akan menggunakan program:

---

### 📖 **INSTRUKSI UNTUK TEAM MEMBER**

Berikut adalah langkah untuk setup APKT Agent di laptop Anda:

#### **PENTING: File Rahasia**

Anda akan menerima file `RAHASIA_SETUP.zip` dari Developer/Administrator. File ini berisi konfigurasi dan kunci yang diperlukan program.

**⚠️ KEAMANAN:**

- Jangan bagikan file ini ke siapapun
- Jangan upload ke cloud storage publik
- Jangan commit ke GitHub
- Simpan dengan aman di laptop Anda

#### **Langkah Setup:**

1. **Baca panduan instalasi:** `README_INSTALL.md` di GitHub
2. **Clone repository:**

   ```bash
   git clone https://github.com/agungjp/agent-apkt.git
   cd agent-apkt
   ```

3. **Ekstrak file rahasia (WAJIB dilakukan sebelum langkah lainnya):**

   - Tempatkan file `RAHASIA_SETUP.zip` di folder `agent-apkt`
   - Klik kanan → Extract All
   - Pastikan ketiga file sudah ada:
     - `config.yaml`
     - `units_selection.yaml`
     - `apkt-agent-af84fa7cde8f.json`

4. **Lanjutkan dengan README_INSTALL.md untuk langkah instalasi selanjutnya**

#### **Jika Ada Masalah:**

- Baca troubleshooting section di `README_INSTALL.md`
- Hubungi Developer/Administrator

---

## 🔄 Update Credential

Jika credential perlu diupdate (misalnya password PLN diubah):

1. **Developer melakukan update:**

   ```bash
   zip -j RAHASIA_SETUP.zip config.yaml units_selection.yaml src/apkt_agent/secrets/apkt-agent-af84fa7cde8f.json
   ```

2. **Kirim file baru ke team member**

3. **Team member melakukan:**
   - Delete ketiga file lama dari folder `agent-apkt`
   - Extract file ZIP baru
   - Restart program

---

## 🛡️ Best Practices

### Checklist Keamanan:

- [ ] Sebelum membuat ZIP, verifikasi file-file sudah benar
- [ ] Gunakan password untuk ZIP saat distribute
- [ ] Kirim password terpisah dari file ZIP
- [ ] Inform team member untuk menjaga keamanan file
- [ ] Jika ada yang resign, regenerate credential (khususnya service account)
- [ ] Backup file credential di tempat aman
- [ ] Jangan commit ke git (sudah di .gitignore, tapi verify)

---

## 📞 Emergency: Jika File Kebocoran

Jika Anda curiga file credential telah bocor:

1. **Segera lakukan regenerasi:**

   - Ubah password PLN IAM
   - Regenerate Google Service Account key di Google Cloud Console
   - Update `config.yaml` dan `apkt-agent-af84fa7cde8f.json`
   - Buat ZIP baru dan kirim ke team member

2. **Komunikasikan ke team:**

   - Beri tahu ada security incident
   - Minta mereka update file credential dengan yang baru

3. **Review logs:**
   - Cek Google Sheets history untuk melihat ada aktivitas mencurigakan

---

## 📊 File Size & Checksum

Untuk verifikasi file tidak corrupted:

```
RAHASIA_SETUP.zip: 3.1 KB (compressed)

Isi:
  config.yaml ........................... 767 bytes
  units_selection.yaml ................. 1,319 bytes
  apkt-agent-af84fa7cde8f.json ......... 2,352 bytes

Total uncompressed size ............... 4,438 bytes
```

---

**Versi Dokumen:** 1.0  
**Tanggal:** Januari 2026  
**Status:** Internal Use Only 🔐
