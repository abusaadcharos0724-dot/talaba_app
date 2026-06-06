@echo off
title Talaba Bot Runner
cd /d "%~dp0"

echo ==========================================
echo Talaba Bot ishga tushirilmoqda...
echo Vaqt: %time%
echo ==========================================
echo.

python main.py

echo.
echo ==========================================
echo Bot to'xtadi yoki xatolik yuz berdi.
echo Chiqish uchun istalgan tugmani bosing.
echo ==========================================
pause
