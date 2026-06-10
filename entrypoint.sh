#!/bin/bash

set -e

echo "🚀 Démarrage de l'application Django..."

# Migrations
echo "📦 Application des migrations..."
python manage.py migrate --noinput

# Static files
echo "🎨 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Démarrage de Celery si activé
if [ "$ASYNC_EMAIL_ENABLED" = "True" ] || [ "$ASYNC_EMAIL_ENABLED" = "true" ] || [ "$ASYNC_EMAIL_ENABLED" = "1" ]; then
    echo "🚀 Démarrage de Celery Worker et Beat en arrière-plan..."
    celery -A sosguinee worker -l info -Q default,email &
    celery -A sosguinee beat -l info &
fi

# Démarrage serveur
echo "🚀 Lancement de Gunicorn..."
exec gunicorn sosguinee.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2