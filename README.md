# 🔐 LoginTabSystem - Cybersecurity Modal 0

**Modern login system with tab-based authentication** - Optimized for Termux (Android Terminal)

## ✨ Fitur Utama

- ✅ **Tab-Based Authentication** - Multiple login options
- ✅ **Password Hashing** - PBKDF2-SHA256 dengan salt 32 byte
- ✅ **Session Management** - Token-based sessions dengan 24 jam expiry
- ✅ **Rate Limiting** - Max 5 login attempts per 15 menit (auto-lock)
- ✅ **Audit Logging** - Tracking semua aktivitas login
- ✅ **2FA Ready** - Siap untuk two-factor authentication
- ✅ **SQL Injection Protection** - Prepared statements di semua query
- ✅ **Password Policy** - Strong password requirements (uppercase, lowercase, angka, spesial)
- ✅ **Zero Dependencies** - Hanya Python standard library (SQLite3, hashlib, secrets, etc)
- ✅ **Termux Compatible** - Berjalan sempurna di Android Termux

## 📋 Persyaratan

- **Python 3.8+** (atau lebih baru)
- **Git** (untuk clone repository)
- **Termux** (untuk Android) atau Linux/Mac Terminal
- ~50MB storage space

## 🚀 Quick Start di Termux

### 1️⃣ Update Termux
```bash
pkg update && pkg upgrade -y
```

### 2️⃣ Install Python & Git
```bash
pkg install python3 git -y
```

### 3️⃣ Clone Repository
```bash
git clone https://github.com/leodirgantarad-blip/LoginTabSystem.git
cd LoginTabSystem
```

### 4️⃣ Setup Database
```bash
python3 setup.py
```

### 5️⃣ Jalankan Sistem
```bash
python3 main.py
```

## 💻 Penggunaan

### Mode CLI (Default)
```bash
python3 main.py
```

### Pilihan Menu

**Jika belum login:**
- [1] Login
- [2] Register
- [3] Audit Log
- [4] Exit

**Jika sudah login:**
- [1] Dashboard
- [2] Change Password
- [3] View Profile
- [4] Logout
- [5] Admin Panel (jika role admin)
- [6] Exit

## 👤 Default Credentials

Setelah menjalankan `setup.py`, Anda akan mendapat:

| User | Username | Password |
|------|----------|----------|
| Admin | `admin` | `Admin@123456` |
| Demo | `demo` | `Demo@123456` |

⚠️ **PENTING**: Ubah password ini immediately setelah first login!

## 📁 Struktur Direktori

```
LoginTabSystem/
├── main.py                 # Entry point utama
├── setup.py               # Script setup database
├── requirements.txt       # Optional dependencies
├── README.md             # Dokumentasi ini
├── LICENSE               # MIT License
├── db/                   # Database directory
│   └── users.db         # SQLite database (dibuat otomatis)
└── logs/                # Logging directory
    └── audit.log        # Audit log file (dibuat otomatis)
```

## 🔐 Fitur Keamanan

### Password Security
- ✅ PBKDF2-SHA256 hashing dengan 100,000 iterations
- ✅ Random salt 32 byte per user
- ✅ Password policy enforcement:
  - Minimum 8 karakter
  - Harus ada huruf besar (A-Z)
  - Harus ada huruf kecil (a-z)
  - Harus ada angka (0-9)
  - Harus ada karakter spesial (!@#$%^&*)

### Login Security
- ✅ Rate limiting: Max 5 failed attempts
- ✅ Auto-lock akun selama 15 menit setelah 5 failed attempts
- ✅ Session timeout: 24 jam
- ✅ IP address logging

### Data Protection
- ✅ SQL injection protection via prepared statements
- ✅ Email validation
- ✅ Username validation (3-20 karakter, alphanumeric + underscore/dash)
- ✅ Comprehensive audit trail

## 📊 Contoh Output

```
╔══════════════════════════════════════════╗
║   CYBERSECURITY LOGIN SYSTEM             ║
║   Modal 0 Edition - Termux Compatible    ║
╚══════════════════════════════════════════╝

Status: Not logged in

[1] Login
[2] Register
[3] Audit Log
[4] Exit

Pilih menu [1-4]: _
```

## 🛠️ Troubleshooting

### Error: "ModuleNotFoundError: No module named 'main'"
```bash
# Pastikan Anda di direktori LoginTabSystem
cd LoginTabSystem
python3 main.py
```

### Error: "database is locked"
```bash
# Reset database
rm db/users.db
python3 setup.py
```

### Error: "Permission denied"
```bash
# Beri permission executable
chmod +x main.py setup.py
python3 main.py
```

### Termux: Keyboard tidak berfungsi
```bash
# Install external keyboard support
apt install termux-api -y
```

### ImportError untuk library tertentu
```bash
# Install optional dependencies
pip install -r requirements.txt
```

## 🔄 Update Repository

```bash
cd LoginTabSystem
git pull origin main
python3 setup.py
```

## 📝 Database Schema

### users table
```sql
- id: INTEGER PRIMARY KEY
- username: TEXT UNIQUE
- email: TEXT UNIQUE
- password_hash: TEXT
- salt: TEXT
- role: TEXT (admin/user)
- is_active: BOOLEAN
- created_at: TIMESTAMP
- last_login: TIMESTAMP
- failed_attempts: INTEGER
- locked_until: TIMESTAMP
```

### sessions table
```sql
- id: INTEGER PRIMARY KEY
- user_id: INTEGER FOREIGN KEY
- token: TEXT UNIQUE
- ip_address: TEXT
- created_at: TIMESTAMP
- expires_at: TIMESTAMP
```

### audit_log table
```sql
- id: INTEGER PRIMARY KEY
- user_id: INTEGER FOREIGN KEY (nullable)
- action: TEXT
- details: TEXT
- ip_address: TEXT
- timestamp: TIMESTAMP
```

## 🎯 Fitur yang Akan Datang

- [ ] 2FA (Two-Factor Authentication)
- [ ] OAuth2 integration (Google, GitHub)
- [ ] Email verification
- [ ] Password reset via email
- [ ] API REST
- [ ] Web dashboard (HTML/CSS/JS)
- [ ] Biometric authentication
- [ ] Session management interface

## 📄 Lisensi

MIT License - Bebas digunakan untuk tujuan komersial dan personal

## 🤝 Kontribusi

Kontribusi terbuka! Silakan:
1. Fork repository
2. Buat branch fitur (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## ⚠️ Disclaimer

Sistem ini dibuat untuk tujuan **edukatif**. Gunakan secara bertanggung jawab dan sesuai hukum yang berlaku. Pengembang tidak bertanggung jawab atas penyalahgunaan.

## 📞 Support

Buat issue di repository untuk pertanyaan atau laporan bug.

---

**Made with ❤️ by leodirgantarad-blip**

**Last Updated: 2026-10-09**
