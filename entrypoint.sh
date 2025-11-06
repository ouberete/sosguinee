#!/bin/bash

echo "🚀 Démarrage de l'application Django..."

# Attente du démarrage de la base de données
echo "⏳ Attente de la base de données..."
while ! nc -z db 5432; do
  sleep 1
done
echo "✅ Base de données disponible."

# Appliquer les migrations
echo "📦 Application des migrations..."
python manage.py migrate --noinput

# Collecte des fichiers statiques
echo "🎨 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Démarrer gunicorn
echo "🚀 Lancement de Gunicorn..."
exec gunicorn sosguinee.wsgi:application --bind 0.0.0.0:8000