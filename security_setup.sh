#!/bin/bash

# Talaba Bot - Xavfsizlik Sozlamalari
# Bu script VPS serveringizni xavfsiz qiladi

echo "🔒 Xavfsizlik sozlamalari boshlanmoqda..."

# 1. Sistema yangilanishlari
echo "📦 Sistema yangilanmoqda..."
sudo apt update && sudo apt upgrade -y

# 2. Firewall (UFW) o'rnatish va sozlash
echo "🛡️ Firewall sozlanmoqda..."
sudo apt install ufw -y

# SSH portini ochish (MUHIM!)
sudo ufw allow 22/tcp
sudo ufw allow ssh

# HTTP/HTTPS (agar webhook ishlatmoqchi bo'lsangiz)
# sudo ufw allow 80/tcp
# sudo ufw allow 443/tcp

# Firewall'ni yoqish
echo "y" | sudo ufw enable

# Firewall holatini ko'rsatish
sudo ufw status verbose

# 3. Fail2Ban o'rnatish (Brute-force hujumlardan himoya)
echo "🚫 Fail2Ban o'rnatilmoqda..."
sudo apt install fail2ban -y

# Fail2Ban sozlamalari
sudo tee /etc/fail2ban/jail.local > /dev/null <<EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
EOF

sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# 4. SSH xavfsizligini oshirish
echo "🔐 SSH xavfsizligi oshirilmoqda..."

# SSH config backup
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Root login o'chirish (EHTIYOT: Avval boshqa user yarating!)
# sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# Password authentication o'chirish (faqat SSH key)
# sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# SSH portini o'zgartirish (ixtiyoriy, masalan 2222)
# sudo sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config
# sudo ufw allow 2222/tcp

# SSH restart
# sudo systemctl restart sshd

# 5. Avtomatik yangilanishlar
echo "🔄 Avtomatik xavfsizlik yangilanishlari sozlanmoqda..."
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades

# 6. .env fayli xavfsizligi
echo "📄 .env fayli himoyalanmoqda..."
if [ -f .env ]; then
    chmod 600 .env
    echo "✅ .env fayli faqat owner o'qiy oladi"
fi

# 7. Bot fayllar uchun to'g'ri ruxsatlar
echo "📁 Fayl ruxsatlari sozlanmoqda..."
chmod 755 deploy.sh
chmod 755 security_setup.sh
chmod 644 *.py
chmod 644 requirements.txt

# 8. Monitoring - Bot ishlamay qolsa qayta ishga tushirish
echo "📊 Monitoring sozlanmoqda..."
sudo tee /usr/local/bin/bot-monitor.sh > /dev/null <<'EOF'
#!/bin/bash
if ! systemctl is-active --quiet talaba-bot; then
    echo "$(date): Bot to'xtagan, qayta ishga tushirilmoqda..." >> /var/log/bot-monitor.log
    systemctl start talaba-bot
fi
EOF

chmod +x /usr/local/bin/bot-monitor.sh

# Cron job qo'shish (har 5 daqiqada tekshirish)
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/bot-monitor.sh") | crontab -

# 9. Disk space monitoring
echo "💾 Disk monitoring sozlanmoqda..."
sudo tee /usr/local/bin/disk-monitor.sh > /dev/null <<'EOF'
#!/bin/bash
THRESHOLD=80
CURRENT=$(df / | grep / | awk '{ print $5}' | sed 's/%//g')
if [ "$CURRENT" -gt "$THRESHOLD" ]; then
    echo "$(date): OGOHLANTIRISH! Disk $CURRENT% to'lgan!" >> /var/log/disk-monitor.log
    # Temp fayllarni tozalash
    find /home/talaba_bot/temp -type f -mtime +7 -delete
fi
EOF

chmod +x /usr/local/bin/disk-monitor.sh

# Cron job (har kuni soat 3 da)
(crontab -l 2>/dev/null; echo "0 3 * * * /usr/local/bin/disk-monitor.sh") | crontab -

# 10. Log rotation
echo "📝 Log rotation sozlanmoqda..."
sudo tee /etc/logrotate.d/talaba-bot > /dev/null <<EOF
/var/log/bot-monitor.log
/var/log/disk-monitor.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
EOF

echo ""
echo "✅ Xavfsizlik sozlamalari tugadi!"
echo ""
echo "📊 Holat:"
echo "  - Firewall: $(sudo ufw status | grep Status)"
echo "  - Fail2Ban: $(sudo systemctl is-active fail2ban)"
echo "  - Bot Monitoring: Har 5 daqiqada"
echo "  - Disk Monitoring: Har kuni soat 3:00"
echo ""
echo "🔐 Xavfsizlik Tavsiyalar:"
echo "  1. SSH parolni kuchli qiling (kamida 16 belgi)"
echo "  2. SSH key authentication ishlatishni o'ylab ko'ring"
echo "  3. Root login o'rniga alohida user yarating"
echo "  4. .env faylini hech qachon GitHub'ga yuklamang"
echo "  5. Muntazam backup oling"
echo ""
echo "📝 Foydali buyruqlar:"
echo "  - Firewall holati:     sudo ufw status verbose"
echo "  - Fail2Ban holati:     sudo fail2ban-client status sshd"
echo "  - Bot monitoring log:  tail -f /var/log/bot-monitor.log"
echo "  - Disk monitoring log: tail -f /var/log/disk-monitor.log"
echo ""
echo "🎉 Serveringiz endi xavfsiz!"
