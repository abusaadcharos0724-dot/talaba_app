# 🏆 24/7 Ishonchli va Xavfsiz Bot - To'liq Qo'llanma

Bu qo'llanma botingizni professional darajada, uzilishsiz va xavfsiz ishlatish uchun.

---

## 📊 TAQQOSLASH: Turli Variantlar

| Variant | Narx/oy | Uptime | Xavfsizlik | Qiyinlik | Tavsiya |
|---------|---------|--------|------------|----------|---------|
| **VPS + Systemd** | $3-5 | 99.9% | ⭐⭐⭐⭐⭐ | O'rta | ✅ **ENG YAXSHI** |
| Uy kompyuteri | Elektr | 50-70% | ⭐⭐ | Oson | ❌ Tavsiya emas |
| Heroku Free | $0 | 80% | ⭐⭐⭐ | Oson | ⚠️ Cheklangan |
| PythonAnywhere | $5 | 95% | ⭐⭐⭐⭐ | Oson | ✅ Yaxshi |
| AWS/Google Cloud | $10+ | 99.9% | ⭐⭐⭐⭐⭐ | Qiyin | ⚠️ Qimmat |

---

## 🎯 MENING TAVSIYAM: VPS + Systemd

### ✅ Nima uchun?

1. **24/7 Ishlash** - Server hech qachon o'chirmaydi
2. **Avtomatik Tiklanish** - Crash bo'lsa avtomatik qayta ishga tushadi
3. **Xavfsiz** - Firewall, Fail2Ban, SSH himoya
4. **Arzon** - $3-5/oy (50,000 so'm)
5. **Professional** - Real production environment

---

## 🌟 VPS PROVAYDERLAR (Tavsiya)

### 🇺🇿 O'zbekiston (ENG YAXSHI tezlik uchun)

#### 1. **UZINFOCOM** ⭐ Tavsiya
```
💰 Narx: 50,000 so'm/oy
📍 Server: Toshkent
💳 To'lov: Click, Payme, Uzcard
🌐 Website: https://uzinfocom.uz
📧 Qo'llab-quvvatlash: O'zbek tilida

Paket: VPS-1
- 2 CPU
- 2GB RAM
- 20GB SSD
- Cheksiz traffic
```

#### 2. **UzCloud**
```
💰 Narx: 40,000 so'm/oy
📍 Server: Toshkent
💳 To'lov: Click, Payme
🌐 Website: https://uzcloud.uz
```

### 🌍 Xalqaro (Arzon narx)

#### 3. **Contabo** ⭐⭐ ENG ARZON
```
💰 Narx: $3.99/oy (~50,000 so'm)
📍 Server: Germaniya, AQSh
💳 To'lov: Visa, Mastercard, PayPal
🌐 Website: https://contabo.com

Paket: VPS S
- 4 vCore CPU
- 8GB RAM
- 200GB SSD
- 32TB traffic
```

#### 4. **DigitalOcean** ⭐ Oson boshqarish
```
💰 Narx: $6/oy
📍 Server: Global (12+ lokatsiya)
💳 To'lov: Visa, Mastercard, PayPal
🌐 Website: https://digitalocean.com
🎁 Bonus: $200 bepul kredit (60 kun)

Paket: Basic Droplet
- 1 CPU
- 1GB RAM
- 25GB SSD
```

#### 5. **Vultr** ⭐ Tez deployment
```
💰 Narx: $5/oy
📍 Server: Global (25+ lokatsiya)
💳 To'lov: Visa, Mastercard, PayPal
🌐 Website: https://vultr.com
🎁 Bonus: $100 bepul kredit

Paket: Regular Performance
- 1 CPU
- 1GB RAM
- 25GB SSD
```

---

## 🚀 TO'LIQ DEPLOY JARAYONI

### QADAM 1: VPS Sotib Olish

1. Yuqoridagi provayderlardan birini tanlang
2. Account yarating
3. VPS sotib oling (Ubuntu 22.04 tanlang)
4. SSH ma'lumotlarini oling:
   - IP manzil (masalan: 185.123.45.67)
   - Username (odatda: root)
   - Parol yoki SSH key

### QADAM 2: Fayllarni Tayyorlash

Windows PowerShell'da:

```powershell
# Bot papkasiga kiring
cd C:\Users\user\Downloads\talaba_bot

# Barcha fayllar borligini tekshiring
ls
```

Kerakli fayllar:
- ✅ main.py
- ✅ config.py
- ✅ database.py
- ✅ handlers/ papka
- ✅ services/ papka
- ✅ utils/ papka
- ✅ requirements.txt
- ✅ deploy.sh
- ✅ security_setup.sh
- ✅ backup.sh

### QADAM 3: Fayllarni Serverga Ko'chirish

**Variant A: SCP orqali (Tavsiya)**

```powershell
# Bot papkasini ko'chirish
scp -r C:\Users\user\Downloads\talaba_bot root@YOUR_SERVER_IP:/home/

# .env faylini ko'chirish
scp C:\Users\user\Downloads\.env root@YOUR_SERVER_IP:/home/talaba_bot/
```

**Variant B: WinSCP orqali (Osonroq)**

1. WinSCP yuklab oling: https://winscp.net/
2. Ochib, quyidagilarni kiriting:
   - File protocol: SCP
   - Host name: YOUR_SERVER_IP
   - User name: root
   - Password: YOUR_PASSWORD
3. Login bosing
4. Chap tomonda: `C:\Users\user\Downloads\talaba_bot`
5. O'ng tomonda: `/home/`
6. `talaba_bot` papkasini drag & drop qiling
7. `.env` faylini ham ko'chiring

### QADAM 4: Serverga Ulanish

```bash
ssh root@YOUR_SERVER_IP
# Parolni kiriting
```

### QADAM 5: Botni O'rnatish (Avtomatik)

```bash
cd /home/talaba_bot

# Deploy scriptga ruxsat berish
chmod +x deploy.sh

# Deploy qilish
./deploy.sh
```

**Bu script avtomatik:**
- ✅ Sistema yangilanishlarini o'rnatadi
- ✅ Python va kutubxonalarni o'rnatadi
- ✅ Virtual environment yaratadi
- ✅ Systemd service sozlaydi
- ✅ Botni ishga tushiradi

### QADAM 6: Xavfsizlikni Sozlash

```bash
# Xavfsizlik scriptga ruxsat berish
chmod +x security_setup.sh

# Xavfsizlikni sozlash
./security_setup.sh
```

**Bu script:**
- 🛡️ Firewall (UFW) sozlaydi
- 🚫 Fail2Ban o'rnatadi (brute-force himoya)
- 📊 Bot monitoring sozlaydi (har 5 daqiqada)
- 💾 Disk monitoring sozlaydi
- 🔐 Fayl ruxsatlarini to'g'rilaydi

### QADAM 7: Backup Sozlash

```bash
# Backup scriptga ruxsat berish
chmod +x backup.sh

# Birinchi backupni yaratish
./backup.sh

# Avtomatik backup (har kuni soat 2:00)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/talaba_bot/backup.sh") | crontab -
```

---

## 🎛️ BOT BOSHQARUVI

### Asosiy Buyruqlar

```bash
# Bot holatini ko'rish
sudo systemctl status talaba-bot

# Botni ishga tushirish
sudo systemctl start talaba-bot

# Botni to'xtatish
sudo systemctl stop talaba-bot

# Botni qayta ishga tushirish
sudo systemctl restart talaba-bot

# Loglarni real-time ko'rish
sudo journalctl -u talaba-bot -f

# Oxirgi 100 qator log
sudo journalctl -u talaba-bot -n 100

# Bugungi loglar
sudo journalctl -u talaba-bot --since today
```

### Kod Yangilash

```bash
# Serverga yangi fayllarni SCP orqali ko'chiring
# Keyin:
cd /home/talaba_bot
sudo systemctl restart talaba-bot
```

---

## 📊 MONITORING VA TEKSHIRISH

### Bot Ishlayaptimi?

```bash
# Service holati
sudo systemctl is-active talaba-bot
# Output: active (ishlamoqda) yoki inactive

# Jarayon mavjudmi?
ps aux | grep "talaba_bot"

# Port ochiqmi? (agar webhook ishlatilsa)
sudo netstat -tulpn | grep python
```

### Disk Space

```bash
# Disk hajmi
df -h

# Bot papka hajmi
du -sh /home/talaba_bot

# Eng katta fayllar
du -ah /home/talaba_bot | sort -rh | head -20
```

### Xotira (RAM)

```bash
# RAM holati
free -h

# Eng ko'p xotira ishlatayotgan jarayonlar
top
# (q bosib chiqish)
```

---

## 🔒 XAVFSIZLIK CHECKLIST

### Majburiy

- ✅ Firewall yoqilgan (`sudo ufw status`)
- ✅ Fail2Ban ishlayapti (`sudo systemctl status fail2ban`)
- ✅ .env fayli 600 ruxsatga ega (`ls -la .env`)
- ✅ Kuchli SSH paroli (16+ belgi)
- ✅ Muntazam backup (har kuni)

### Tavsiya etiladi

- ⭐ SSH key authentication (parol o'rniga)
- ⭐ Root login o'chirilgan
- ⭐ SSH port o'zgartirilgan (22 o'rniga 2222)
- ⭐ Alohida user (root o'rniga)
- ⭐ 2FA yoqilgan (agar provayderda bo'lsa)

### SSH Key Yaratish (Windows)

```powershell
# PowerShell'da
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Public keyni serverga ko'chirish
scp C:\Users\user\.ssh\id_rsa.pub root@YOUR_SERVER_IP:/root/.ssh/authorized_keys
```

---

## ❓ MUAMMOLARNI HAL QILISH

### Bot ishlamayapti

```bash
# 1. Loglarni tekshiring
sudo journalctl -u talaba-bot -n 50

# 2. Qo'lda ishga tushirib xatolarni ko'ring
cd /home/talaba_bot
source venv/bin/activate
python -m talaba_bot.main

# 3. .env faylini tekshiring
cat .env

# 4. Kutubxonalar o'rnatilganmi?
pip list
```

### Server sekin ishlayapti

```bash
# CPU va RAM ni tekshiring
htop

# Disk to'lganmi?
df -h

# Loglar hajmi
du -sh /var/log
```

### SSH ulanmayapti

```bash
# Firewall SSH ruxsat berganmi?
sudo ufw status | grep 22

# SSH service ishlayaptimi?
sudo systemctl status sshd
```

---

## 💰 XARAJATLAR HISOBI

### Minimal (O'zbekiston)

```
VPS (UzCloud):        40,000 so'm/oy
Domain (ixtiyoriy):   50,000 so'm/yil
-----------------------------------
Jami:                 40,000 so'm/oy
```

### Tavsiya (Contabo)

```
VPS (Contabo):        $3.99/oy (~50,000 so'm)
Domain (ixtiyoriy):   $10/yil
-----------------------------------
Jami:                 ~50,000 so'm/oy
```

---

## 🎯 XULOSA

### ENG YAXSHI VARIANT:

1. **VPS**: Contabo ($3.99/oy) yoki UzCloud (40,000 so'm/oy)
2. **OS**: Ubuntu 22.04 LTS
3. **Deploy**: Systemd service (men yaratgan scriptlar)
4. **Xavfsizlik**: Firewall + Fail2Ban + Monitoring
5. **Backup**: Har kuni avtomatik

### DEPLOY VAQTI:

- Tajribasiz: 30-60 daqiqa
- Tajribali: 10-15 daqiqa
- Avtomatik script: 5 daqiqa

### SAQLASH:

- Kod yangilash: 1 daqiqa
- Monitoring: Avtomatik
- Backup: Avtomatik
- Xavfsizlik: Avtomatik

---

## 📞 YORDAM KERAKMI?

Agar qadamma-qadam yordam kerak bo'lsa:

1. VPS sotib oling
2. Server IP, username, parolni ayting
3. Men har bir buyruqni yozib beraman
4. Siz copy-paste qilasiz

**Omad! 🚀**

---

**Eslatma:** Bu qo'llanma professional production environment uchun. Agar test qilmoqchi bo'lsangiz, avval arzon VPS ($3-5/oy) bilan boshlang.
