#!/usr/bin/env bash
# ==============================================================================
# Gigs Radar — Automated Database Backup Script
# Menghasilkan snapshot terkompresi .sql.gz dengan cap waktu
# ==============================================================================
set -e

BACKUP_DIR="/var/backups/gigsradar"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FILENAME="$BACKUP_DIR/gigsradar_backup_$TIMESTAMP.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "💾 Memulai backup database PostgreSQL Gigs Radar..."
docker compose exec -T db pg_dump -U gigsuser gigsradar_db | gzip > "$FILENAME"

echo "✅ Backup berhasil disimpan ke: $FILENAME"
echo "Ukuran file: $(du -h "$FILENAME" | cut -f1)"

# Hapus backup yang lebih tua dari 14 hari
find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime +14 -delete
echo "🧹 Pembersihan backup usang (> 14 hari) selesai."
