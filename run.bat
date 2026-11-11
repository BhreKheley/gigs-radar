@echo off
title Gigs Radar - Development Server
echo ========================================================
echo  Gigs Radar - Platform Geospasial Live Music Depok
echo  Tugas Proyek Akhir (TPA) DDP1 Fasilkom UI
echo ========================================================
echo.

IF NOT EXIST ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment .venv tidak ditemukan!
    echo Harap buat virtual environment dengan: python -m venv .venv
    pause
    exit /b 1
)

IF NOT EXIST "db.sqlite3" (
    echo [INFO] Basis data db.sqlite3 belum ditemukan.
    IF EXIST "seed.sqlite3" (
        echo [INFO] Menyalin snapshot cold-start seed.sqlite3...
        copy seed.sqlite3 db.sqlite3
    ) ELSE (
        echo [INFO] Menjalankan migrasi dan seeding data demo...
        .venv\Scripts\python.exe manage.py migrate
        .venv\Scripts\python.exe manage.py seed_demo
    )
)

echo [OK] Menjalankan server Django di http://127.0.0.1:8000/
echo [INFO] Tekan CTRL+C untuk menghentikan server.
echo.
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
pause
