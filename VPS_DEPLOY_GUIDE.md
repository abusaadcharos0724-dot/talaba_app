# 🚀 Talaba Bot - VPS Serverga Deploy Qilish Qo'llanmasi

Bu qo'llanma Telegram botingizni VPS serverga qanday qilib 24/7 ishlaydigan qilib o'rnatishni ko'rsatadi.

---

## 📋 Kerakli Narsalar

1. **VPS Server** (Ubuntu 20.04/22.04 tavsiya etiladi)
   - Minimal: 1 CPU, 1GB RAM, 10GB disk
   - Tavsiya: 2 CPU, 2GB RAM, 20GB disk

2. **SSH kirish huquqi** - Server IP, username, password/SSH key

3. **Domain (ixtiyoriy)** - Webhook uchun kerak bo'lsa

---

## 🔧 1-QADAM: VPS Serverga Ulanish

### Windows'dan SSH orqali ulanish:

```bash
ssh root@YOUR_SERVER_IP
# yoki
ssh username@YOUR_SERVER_IP
```

**Misol:**
```bash
ssh root@185.123.45.67
```

Parolni kiriting va servergа kiring.

---

## 📦 2-QADAM: Serverni Tayyorlash

### Sistema yangilanishlarini o'rnatish:

```bash
sudo apt update && sudo apt upgrade -y
```

### Python va kerakli paketlarni o'rnatish:

```bash
# Python 3.10+ o'rnatish
sudo apt install python3 python3-pip python3-venv git -y

# Python versiyasini tekshirish
python3 --version
```

### Tesseract OCR o'rnatish (Foto → Konspekt uchun):

```bash
sudo apt install tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng -y
```

---

## 📁 3-QADAM: Bot Fayllarini Serverga Ko'chirish

### Variant 1: Git orqali (Tavsiya etiladi)

Agar botingiz GitHub'da bo'lsa:

```bash
cd /home
git clone https://github.com/YOUR_USERNAME/talaba_bot.git
cd talaba_bot
```

### Variant 2: SCP orqali (Windows'dan)

Windows PowerShell'da:

```powershell
# Butun papkani ko'chirish
scp -r C:\Users\user\Downloads\talaba_bot root@YOUR_SERVER_IP:/home/

# .env faylini alohida ko'chirish
scp C:\Users\user\Downloads\.env root@YOUR_SERVER_IP:/home/talaba_bot/
```

### Variant 3: FileZilla/WinSCP orqali

1. FileZilla yoki WinSCP dasturini oching
2. Server IP, username, password kiriting
3. `talaba_bot` papkasini serverga drag & drop qiling

---

## 🔐 4-QADAM: .env Faylini Sozlash

Serverda `.env` faylini yarating:

```bash
cd /home/talaba_bot
nano .env
```

Quyidagi ma'lumotlarni kiriting:

```env
BOT_TOKEN=your_bot_token
ADMIN_ID=your_admin_id
OPENAI_API_KEY=your_openai_api_key
HUMO_CARD=9860 1201 1367 9696
PREMIUM_PRICE=25000
```

`Ctrl+O` → Enter → `Ctrl+X` (saqlash va chiqish)

---

## 🐍 5-QADAM: Virtual Environment va Kutubxonalarni O'rnatish

```bash
cd /home/talaba_bot

# Virtual environment yaratish
python3 -m venv venv

# Virtual environment'ni faollashtirish
source venv/bin/activate

# Kutubxonalarni o'rnatish
pip install --upgrade pip
pip install aiogram python-dotenv openai python-docx python-pptx PyPDF2 pytesseract Pillow requests beautifulsoup4
```

---

## ✅ 6-QADAM: Botni Test Qilish

```bash
# Virtual environment ichida
python -m talaba_bot.main
```

Agar bot ishga tushsa, `Ctrl+C` bilan to'xtating. Endi uni doimiy ishlaydigan qilamiz.

---

## 🔄 7-QADAM: Botni Doimiy Ishlaydigan Qilish (Systemd Service)

### Service fayli yaratish:

```bash
sudo nano /etc/systemd/system/talaba-bot.service
```

Quyidagi kodni kiriting:

```ini
[Unit]
Description=Talaba Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/talaba_bot
Environment="PATH=/home/talaba_bot/venv/bin"
ExecStart=/home/talaba_bot/venv/bin/python -m talaba_bot.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

`Ctrl+O` → Enter → `Ctrl+X`

### Service'ni ishga tushirish:

```bash
# Service'ni qayta yuklash
sudo systemctl daemon-reload

# Service'ni yoqish
sudo systemctl enable talaba-bot

# Service'ni ishga tushirish
sudo systemctl start talaba-bot

# Holatni tekshirish
sudo systemctl status talaba-bot
```

---

## 📊 8-QADAM: Bot Loglarini Ko'rish

```bash
# Real-time loglar
sudo journalctl -u talaba-bot -f

# Oxirgi 100 qator
sudo journalctl -u talaba-bot -n 100

# Bugungi loglar
sudo journalctl -u talaba-bot --since today
```

---

## 🛠️ Foydali Buyruqlar

### Botni boshqarish:

```bash
# Botni to'xtatish
sudo systemctl stop talaba-bot

# Botni qayta ishga tushirish
sudo systemctl restart talaba-bot

# Bot holatini ko'rish
sudo systemctl status talaba-bot

# Botni o'chirish (avtomatik ishga tushmaydi)
sudo systemctl disable talaba-bot
```

### Kod yangilash (Git orqali):

```bash
cd /home/talaba_bot
git pull origin main
sudo systemctl restart talaba-bot
```

### Kod yangilash (Manual):

1. Windows'dan yangi fayllarni SCP orqali ko'chiring
2. Botni qayta ishga tushiring:

```bash
sudo systemctl restart talaba-bot
```

---

## 🔒 9-QADAM: Xavfsizlik (Tavsiya etiladi)

### Firewall sozlash:

```bash
# UFW o'rnatish
sudo apt install ufw -y

# SSH ruxsat berish
sudo ufw allow ssh
sudo ufw allow 22/tcp

# Firewall yoqish
sudo ufw enable

# Holatni ko'rish
sudo ufw status
```

### Yangi foydalanuvchi yaratish (root o'rniga):

```bash
# Yangi user yaratish
sudo adduser botuser

# Sudo huquqi berish
sudo usermod -aG sudo botuser

# Bot fayllarini ko'chirish
sudo mv /home/talaba_bot /home/botuser/
sudo chown -R botuser:botuser /home/botuser/talaba_bot

# Service faylini yangilash
sudo nano /etc/systemd/system/talaba-bot.service
# User=root ni User=botuser ga o'zgartiring
# WorkingDirectory=/home/botuser/talaba_bot ga o'zgartiring
```

---

## 🌐 10-QADAM: Webhook (Ixtiyoriy, Polling o'rniga)

Agar domeningiz bo'lsa va webhook ishlatmoqchi bo'lsangiz:

### Nginx o'rnatish:

```bash
sudo apt install nginx certbot python3-certbot-nginx -y
```

### SSL sertifikat olish:

```bash
sudo certbot --nginx -d yourdomain.com
```

### Bot kodini webhook uchun o'zgartirish:

`main.py` faylida:

```python
# Polling o'rniga webhook
await dp.start_webhook(
    bot,
    webhook_path="/webhook",
    skip_updates=True,
    host="0.0.0.0",
    port=8080
)
```

---

## ❓ Muammolarni Hal Qilish

### Bot ishlamayapti:

```bash
# Loglarni tekshiring
sudo journalctl -u talaba-bot -n 50

# Service holatini ko'ring
sudo systemctl status talaba-bot

# Qo'lda ishga tushirib xatolarni ko'ring
cd /home/talaba_bot
source venv/bin/activate
python -m talaba_bot.main
```

### Database xatolari:

```bash
# Database faylini tekshiring
ls -la /home/talaba_bot/*.db

# Agar yo'q bo'lsa, bot uni avtomatik yaratadi
```

### Kutubxona xatolari:

```bash
# Virtual environment'ni qayta yarating
cd /home/talaba_bot
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # Agar requirements.txt bo'lsa
```

---

## 📝 Requirements.txt Yaratish (Tavsiya)

Windows'da:

```powershell
cd C:\Users\user\Downloads\talaba_bot
pip freeze > requirements.txt
```

Serverda:

```bash
pip install -r requirements.txt
```

---

## 🎯 Xulosa

Endi botingiz VPS serverda 24/7 ishlaydi! 🎉

**Asosiy buyruqlar:**
- `sudo systemctl status talaba-bot` - Holatni ko'rish
- `sudo systemctl restart talaba-bot` - Qayta ishga tushirish
- `sudo journalctl -u talaba-bot -f` - Loglarni kuzatish

**Savollar bo'lsa, quyidagi narsalarni tekshiring:**
1. Loglar: `sudo journalctl -u talaba-bot -n 100`
2. Service holati: `sudo systemctl status talaba-bot`
3. .env fayli to'g'ri joylashganmi: `cat /home/talaba_bot/.env`

---

**Omad! 🚀**
