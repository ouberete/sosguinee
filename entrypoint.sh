#!/bin/bash

set -e

echo "🚀 Démarrage de l'application Django..."

# Attente de PostgreSQL
echo "⏳ Attente de PostgreSQL..."
while ! nc -z "${POSTGRES_HOST:-db}" "${POSTGRES_PORT:-5432}"; do
    sleep 1
done
echo "✅ PostgreSQL est prêt."

# Migrations
echo "📦 Application des migrations..."
python manage.py migrate --noinput

# Fichiers statiques
echo "🎨 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "🌍 Compilation des traductions..."
find locale -name "*.mo" -delete
python manage.py compilemessages

# Démarrage de Celery dans ce conteneur (désactivé avec Docker Compose :
# les services celery_worker et celery_beat s'en chargent séparément)
START_CELERY_PROCESSES="${RUN_CELERY_PROCESSES:-$ASYNC_EMAIL_ENABLED}"
if [ "$START_CELERY_PROCESSES" = "True" ] || [ "$START_CELERY_PROCESSES" = "true" ] || [ "$START_CELERY_PROCESSES" = "1" ]; then
    echo "🚀 Démarrage de Celery Worker et Beat en arrière-plan..."
    celery -A ensemble224 worker -l info -Q default,email &
    celery -A ensemble224 beat -l info &
fi

# Démarrage du serveur
echo "🚀 Lancement de Gunicorn..."
exec gunicorn ensemble224.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --access-logfile -



    
