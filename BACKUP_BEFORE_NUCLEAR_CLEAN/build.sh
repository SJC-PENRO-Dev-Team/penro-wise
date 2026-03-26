#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "🔧 Installing dependencies..."
pip install -r requirements.txt

echo "🗑️  Clearing old static files..."
rm -rf staticfiles/*

echo "📦 Collecting static files (fresh)..."
python manage.py collectstatic --no-input --clear

echo "🗄️  Running database migrations..."
python manage.py migrate

echo "📁 Initializing document folder structure..."
python manage.py init_document_folders

echo "✅ Build completed successfully!"
