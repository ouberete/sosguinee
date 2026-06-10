#!/bin/bash

set -e

echo "🚀 Démarrage de l'application Django..."

# Migrations
echo "📦 Application des migrations..."
python manage.py migrate --noinput

# Static files
echo "🎨 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Démarrage serveur
echo "🚀 Lancement de Gunicorn..."
exec gunicorn sosguinee.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2