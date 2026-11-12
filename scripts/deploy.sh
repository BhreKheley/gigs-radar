#!/usr/bin/env bash
# ==============================================================================
# Gigs Radar — Automated Production Deployment Script
# Digunakan di server VPS untuk deploy update zero-downtime
# ==============================================================================
set -e

echo "🚀 [1/5] Mengambil perubahan kode terbaru dari Git..."
git pull origin main

echo "📦 [2/5] Membangun ulang container Docker..."
docker compose build web

echo "🔄 [3/5] Memulai layanan dan menerapkan migrasi database..."
docker compose up -d

echo "📊 [4/5] Mengumpulkan aset statis (collectstatic) & migrasi..."
docker compose exec -T web python manage.py migrate --noinput
docker compose exec -T web python manage.py collectstatic --noinput

echo "🔍 [5/5] Memverifikasi status kesehatan sistem via /healthz..."
sleep 3
curl -s -f http://localhost/healthz || (echo "❌ Healthcheck gagal! Periksa logs: docker compose logs web" && exit 1)

echo "✅ Deployment Sukses! Gigs Radar berhasil diperbarui dan berjalan 100% sehat."
