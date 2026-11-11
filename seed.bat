@echo off
title Gigs Radar - Seed Demo Data
echo ========================================================
echo  Gigs Radar - Reset & Seeding Data Realistis Depok
echo ========================================================
echo.

IF NOT EXIST ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment .venv tidak ditemukan!
    pause
    exit /b 1
)

echo [1/3] Menjalankan migrasi basis data...
.venv\Scripts\python.exe manage.py migrate

echo.
echo [2/3] Menjalankan perintah seed_demo...
.venv\Scripts\python.exe manage.py seed_demo

echo.
echo [3/3] Memperbarui file snapshot seed.sqlite3 untuk Vercel...
copy /Y db.sqlite3 seed.sqlite3

echo.
echo [SELESAI] Data demo realistis Depok sukses diperbarui!
pause

