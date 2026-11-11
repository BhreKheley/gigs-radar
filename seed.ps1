Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Gigs Radar - Reset & Seeding Data Realistis Depok" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$pythonPath = ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonPath)) {
    Write-Host "[ERROR] Virtual environment .venv tidak ditemukan!" -ForegroundColor Red
    Exit 1
}

Write-Host "[1/3] Menjalankan migrasi basis data..." -ForegroundColor Cyan
& $pythonPath manage.py migrate

Write-Host "`n[2/3] Menjalankan perintah seed_demo..." -ForegroundColor Cyan
& $pythonPath manage.py seed_demo

Write-Host "`n[3/3] Memperbarui file snapshot seed.sqlite3 untuk Vercel..." -ForegroundColor Cyan
Copy-Item -Path "db.sqlite3" -Destination "seed.sqlite3" -Force

Write-Host "`n[SELESAI] Data demo realistis Depok sukses diperbarui!" -ForegroundColor Green
