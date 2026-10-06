#!/bin/bash

set -e

echo "🚀 Démarrage de l'application Django..."

# Migrations
echo "📦 Application des migrations..."
python manage.py migrate --noinput

# Static files
echo "🎨 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Démarrage de Celery si activé et autorisé pour ce conteneur
START_CELERY_PROCESSES="${RUN_CELERY_PROCESSES:-$ASYNC_EMAIL_ENABLED}"
if [ "$START_CELERY_PROCESSES" = "True" ] || [ "$START_CELERY_PROCESSES" = "true" ] || [ "$START_CELERY_PROCESSES" = "1" ]; then
    echo "🚀 Démarrage de Celery Worker et Beat en arrière-plan..."
    celery -A ensemble224 worker -l info -Q default,email &
    celery -A ensemble224 beat -l info &
fi

# Démarrage serveur
echo "🚀 Lancement de Gunicorn..."
exec gunicorn ensemble224.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2