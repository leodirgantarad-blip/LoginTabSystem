# 📥 Panduan Instalasi LoginTabSystem

## 🤖 Untuk Termux (Android)

### Step 1: Download dan Install Termux
1. Buka Google Play Store di Android
2. Cari "Termux"
3. Klik Install (by Fredrik Fornwall)
4. Tunggu sampai selesai
5. Buka aplikasi Termux

### Step 2: Update Termux
```bash
pkg update
pkg upgrade -y
```

### Step 3: Install Required Tools
```bash
pkg install python3 git curl wget -y
```

### Step 4: Clone Repository
```bash
git clone https://github.com/leodirgantarad-blip/LoginTabSystem.git
cd LoginTabSystem
```

### Step 5: Setup Database
```bash
python3 setup.py
```

### Step 6: Run Application
```bash
python3 main.py
```

---

## 💻 Untuk Linux/Mac

### Debian/Ubuntu
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3 python3-pip git -y

# Clone repository
git clone https://github.com/leodirgantarad-blip/LoginTabSystem.git
cd LoginTabSystem

# Setup
python3 setup.py

# Run
python3 main.py
```

### macOS
```bash
# Install Homebrew (jika belum ada)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python3 git

# Clone repository
git clone https://github.com/leodirgantarad-blip/LoginTabSystem.git
cd LoginTabSystem

# Setup
python3 setup.py

# Run
python3 main.py
```

### Windows (PowerShell)
```powershell
# Install Python dari https://www.python.org/ atau:
choco install python git

# Clone repository
git clone https://github.com/leodirgantarad-blip/LoginTabSystem.git
cd LoginTabSystem

# Setup
python setup.py

# Run
python main.py
```

---

## 🐳 Docker Installation (Optional)

### Create Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["python3", "main.py"]
```

### Build & Run
```bash
docker build -t logintabsystem .
docker run -it logintabsystem
```

---

## 📱 Mobile Setup (Pydroid 3)

1. Install **Pydroid 3** dari Play Store
2. Buka aplikasi
3. Klik "New" → "New project"
4. Download `main.py` dari GitHub
5. Paste ke project
6. Klik Run

---

## ✅ Verification

Setelah instalasi, cek dengan:
```bash
python3 main.py
```

Jika melihat menu login, instalasi berhasil! ✓

---

## 🆘 Common Issues

### "python3: command not found"
**Solution:**
```bash
pkg install python3  # For Termux
sudo apt install python3  # For Linux
```

### "git: command not found"
**Solution:**
```bash
pkg install git  # For Termux
sudo apt install git  # For Linux
```

### "Permission denied"
**Solution:**
```bash
chmod +x main.py setup.py
```

### Database locked error
**Solution:**
```bash
rm db/users.db
python3 setup.py
```

### Module import errors
**Solution:**
```bash
pip3 install -r requirements.txt
```

---

**Need more help?** Buat issue di GitHub repository.
