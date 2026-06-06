#!/bin/bash

# Talaba Bot - Tezkor Deploy Script
# Bu script botni VPS serverda avtomatik o'rnatadi

echo "🚀 Talaba Bot Deploy Boshlandi..."

# 1. Sistema yangilanishlari
echo "📦 Sistema yangilanmoqda..."
sudo apt update && sudo apt upgrade -y

# 2. Python va kerakli paketlar
echo "🐍 Python va kerakli paketlar o'rnatilmoqda..."
sudo apt install python3 python3-pip python3-venv git tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng -y

# 3. Virtual environment yaratish
echo "🔧 Virtual environment yaratilmoqda..."
python3 -m venv venv
source venv/bin/activate

# 4. Python kutubxonalarini o'rnatish
echo "📚 Python kutubxonalari o'rnatilmoqda..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. .env faylini tekshirish
if [ ! -f .env ]; then
    echo "⚠️  .env fayli topilmadi!"
    echo "Iltimos, .env faylini yarating va kerakli ma'lumotlarni kiriting."
    echo ""
    echo "Misol:"
    echo "BOT_TOKEN=your_bot_token"
    echo "ADMIN_ID=your_admin_id"
    echo "OPENAI_API_KEY=your_openai_key"
    exit 1
fi

# 6. Systemd service yaratish
echo "⚙️  Systemd service sozlanmoqda..."
sudo tee /etc/systemd/system/talaba-bot.service > /dev/null <<EOF
[Unit]
Description=Talaba Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/python -m talaba_bot.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 7. Service'ni ishga tushirish
echo "🔄 Service ishga tushirilmoqda..."
sudo systemctl daemon-reload
sudo systemctl enable talaba-bot
sudo systemctl start talaba-bot

# 8. Holatni ko'rsatish
echo ""
echo "✅ Deploy tugadi!"
echo ""
echo "📊 Bot holati:"
sudo systemctl status talaba-bot --no-pager

echo ""
echo "📝 Foydali buyruqlar:"
echo "  - Holatni ko'rish:        sudo systemctl status talaba-bot"
echo "  - Loglarni ko'rish:       sudo journalctl -u talaba-bot -f"
echo "  - Qayta ishga tushirish:  sudo systemctl restart talaba-bot"
echo "  - To'xtatish:             sudo systemctl stop talaba-bot"
echo ""
echo "🎉 Bot muvaffaqiyatli ishga tushdi!"
