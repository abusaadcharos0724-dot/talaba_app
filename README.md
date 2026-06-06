# 🎓 Talaba Servis Bot

Telegram bot talabalarga o'qish jarayonida yordam berish uchun mo'ljallangan.

## 🌟 Asosiy Funksiyalar

### 📚 Konspekt Yaratish
- **Fayl → Konspekt**: PDF/DOCX fayllardan avtomatik konspekt
- **Foto → Konspekt**: Rasmdan matn tanib konspekt yaratish (OCR)
- **Audio → Konspekt**: Ovozli xabardan matn va konspekt (Premium)

### 🎯 Talaba Vositalari
- **Referat Generator**: AI yordamida to'liq referat yaratish (DOCX format)
- **Test Generator**: Mavzu bo'yicha test savollari yaratish
- **Prezentatsiya**: PowerPoint taqdimot yaratish (PPTX format)
- **GPA Kalkulyator**: O'rtacha ball hisoblash

### 📅 Deadline Boshqaruvi
- Vazifalar va muddatlarni qo'shish
- 24 soat va 1 soat oldin avtomatik eslatmalar
- Barcha deadlinelarni ko'rish va o'chirish

### 📖 Onlayn Kutubxona
- Audio kitoblar
- PDF kitoblar
- Admin orqali kitob qo'shish/o'chirish

### 🏛️ Universitet Ma'lumotlari
- Universitet yangiliklari
- Dars jadvali
- Foydali kanallar ro'yxati
- Grant va stipendiya imkoniyatlari

### 👨‍💼 Admin Panel
- Foydalanuvchilar ro'yxati
- Premium boshqaruvi
- Statistika
- Broadcast xabarlar
- Kitobxona boshqaruvi

## 💎 Premium Xususiyatlar

- Audio → Konspekt
- Cheksiz referat va test generatsiyasi
- Prezentatsiya yaratish
- Tezkor qo'llab-quvvatlash

**Narx**: 25,000 so'm / 30 kun

## 🚀 O'rnatish

### Lokal (Windows)

1. Repository'ni klonlash:
```bash
git clone https://github.com/YOUR_USERNAME/talaba_bot.git
cd talaba_bot
```

2. Virtual environment yaratish:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Kutubxonalarni o'rnatish:
```bash
pip install -r requirements.txt
```

4. `.env` faylini yaratish:
```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_id
OPENAI_API_KEY=your_openai_api_key
HUMO_CARD=9860 1201 1367 9696
PREMIUM_PRICE=25000
```

5. Botni ishga tushirish:
```bash
python -m talaba_bot.main
```

### VPS Server (Ubuntu)

Batafsil qo'llanma: [VPS_DEPLOY_GUIDE.md](VPS_DEPLOY_GUIDE.md)

**Tezkor deploy:**
```bash
# Fayllarni serverga ko'chiring
scp -r talaba_bot root@YOUR_SERVER_IP:/home/

# Serverga kiring
ssh root@YOUR_SERVER_IP

# Deploy scriptni ishga tushiring
cd /home/talaba_bot
chmod +x deploy.sh
./deploy.sh
```

## 📋 Kerakli Kutubxonalar

- `aiogram` - Telegram Bot API
- `openai` - GPT-4 integratsiyasi
- `python-docx` - Word fayl yaratish
- `python-pptx` - PowerPoint yaratish
- `PyPDF2` - PDF o'qish
- `pytesseract` - OCR (matn tanish)
- `Pillow` - Rasm ishlash
- `beautifulsoup4` - Web scraping

## 🔧 Konfiguratsiya

### Environment Variables (.env)

| O'zgaruvchi | Tavsif | Majburiy |
|-------------|--------|----------|
| `BOT_TOKEN` | Telegram bot token | ✅ |
| `ADMIN_ID` | Admin Telegram ID | ✅ |
| `OPENAI_API_KEY` | OpenAI API kaliti | ✅ |
| `HUMO_CARD` | To'lov kartasi raqami | ❌ |
| `PREMIUM_PRICE` | Premium narxi (so'm) | ❌ |

### Database

Bot SQLite3 ishlatadi. Database fayli: `talaba_superbot.db`

Jadvallar:
- `users` - Foydalanuvchilar
- `deadlines` - Vazifa muddatlari
- `books` - Kutubxona kitoblari

## 📊 Arxitektura

```
talaba_bot/
├── main.py              # Asosiy fayl
├── config.py            # Konfiguratsiya
├── database.py          # Database funksiyalari
├── handlers/            # Telegram handler'lar
│   ├── common.py        # Asosiy menu
│   ├── konspekt.py      # Konspekt funksiyalari
│   ├── student_tools.py # Talaba vositalari
│   ├── admin.py         # Admin panel
│   ├── schedule.py      # Dars jadvali
│   ├── library.py       # Kutubxona
│   ├── university.py    # Universitet
│   ├── channels.py      # Kanallar
│   └── grants.py        # Grantlar
├── services/            # Xizmatlar
│   ├── ai_service.py    # OpenAI integratsiyasi
│   ├── file_parser.py   # Fayl o'qish
│   └── news_service.py  # Yangiliklar
└── utils/               # Yordamchi funksiyalar
    ├── docx_gen.py      # DOCX generator
    └── pptx_gen.py      # PPTX generator
```

## 🛠️ Muammolarni Hal Qilish

### Bot javob bermayapti
```bash
# Loglarni tekshiring
sudo journalctl -u talaba-bot -n 50

# Botni qayta ishga tushiring
sudo systemctl restart talaba-bot
```

### OpenAI xatolari
- API kalitini tekshiring
- Balans yetarli ekanligini tekshiring
- Internet aloqasini tekshiring

### OCR ishlamayapti
```bash
# Tesseract o'rnatilganini tekshiring
tesseract --version

# Agar yo'q bo'lsa, o'rnating
sudo apt install tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng -y
```

## 📝 Yangilanishlar

Bot kodini yangilash:

```bash
# Git orqali
cd /home/talaba_bot
git pull origin main
sudo systemctl restart talaba-bot

# Manual
# Yangi fayllarni SCP orqali ko'chiring
sudo systemctl restart talaba-bot
```

## 🔒 Xavfsizlik

- `.env` faylini hech qachon GitHub'ga yuklamang
- Admin ID ni to'g'ri sozlang
- VPS serverda firewall sozlang
- SSH parolni kuchli qiling yoki SSH key ishlating

## 📞 Qo'llab-quvvatlash

Savollar yoki muammolar bo'lsa:
- Telegram: @YOUR_SUPPORT_USERNAME
- Email: your_email@example.com

## 📄 Litsenziya

MIT License

## 🙏 Minnatdorchilik

- [aiogram](https://github.com/aiogram/aiogram) - Telegram Bot framework
- [OpenAI](https://openai.com/) - GPT-4 API
- [python-docx](https://github.com/python-openxml/python-docx) - Word fayl yaratish

---

**Yaratilgan:** 2025
**Versiya:** 1.0.0
