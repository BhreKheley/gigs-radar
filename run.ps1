Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Gigs Radar - Platform Geospasial Live Music Depok" -ForegroundColor Yellow
Write-Host " Tugas Proyek Akhir (TPA) DDP1 Fasilkom UI" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$pythonPath = ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonPath)) {
    Write-Host "[ERROR] Virtual environment .venv tidak ditemukan!" -ForegroundColor Red
    Write-Host "Jalankan: python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    Exit 1
}

if (-not (Test-Path "db.sqlite3")) {
    Write-Host "[INFO] db.sqlite3 belum ada." -ForegroundColor Yellow
    if (Test-Path "seed.sqlite3") {
        Write-Host "[INFO] Menyalin snapshot cold-start seed.sqlite3..." -ForegroundColor Green
        Copy-Item -Path "seed.sqlite3" -Destination "db.sqlite3"
    } else {
        Write-Host "[INFO] Menjalankan migrasi dan seeding..." -ForegroundColor Green
        & $pythonPath manage.py migrate
        & $pythonPath manage.py seed_demo
    }
}

Write-Host "[OK] Memulai server Django di http://127.0.0.1:8000/" -ForegroundColor Green
Write-Host "[INFO] Tekan CTRL+C untuk menghentikan server." -ForegroundColor Gray
Write-Host ""
& $pythonPath manage.py runserver 127.0.0.1:8000

