#!/bin/bash

# Talaba Bot - Avtomatik Backup Script
# Database va muhim fayllarni backup qiladi

BACKUP_DIR="/home/backups/talaba_bot"
BOT_DIR="/home/talaba_bot"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="talaba_bot_backup_$DATE"

echo "💾 Backup boshlanmoqda..."

# Backup papkasini yaratish
mkdir -p $BACKUP_DIR

# Backup yaratish
cd /home
tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" \
    --exclude='talaba_bot/venv' \
    --exclude='talaba_bot/__pycache__' \
    --exclude='talaba_bot/temp' \
    talaba_bot/

# Backup hajmini ko'rsatish
SIZE=$(du -h "$BACKUP_DIR/$BACKUP_NAME.tar.gz" | cut -f1)
echo "✅ Backup yaratildi: $BACKUP_NAME.tar.gz ($SIZE)"

# Eski backuplarni o'chirish (7 kundan eski)
find $BACKUP_DIR -name "talaba_bot_backup_*.tar.gz" -mtime +7 -delete
echo "🗑️  Eski backuplar tozalandi (7+ kun)"

# Backup ro'yxati
echo ""
echo "📋 Mavjud backuplar:"
ls -lh $BACKUP_DIR/*.tar.gz 2>/dev/null | awk '{print $9, "("$5")"}'

echo ""
echo "✅ Backup tugadi!"
echo "📁 Joylashuv: $BACKUP_DIR/$BACKUP_NAME.tar.gz"
