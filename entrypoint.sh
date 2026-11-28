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

# Traductions : corrige les séquences \uXXXX (invalides dans un .po),
# supprime les anciens .mo puis recompile. Une erreur ne bloque pas le démarrage.
echo "🌍 Compilation des traductions..."
python - <<'PY'
import re, glob
for p in glob.glob("locale/*/LC_MESSAGES/django.po"):
    s = open(p, encoding="utf-8").read()
    s2 = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), s)
    if s2 != s:
        open(p, "w", encoding="utf-8").write(s2)
PY
find locale -name "*.mo" -delete
python manage.py compilemessages || echo "⚠️ Compilation des traductions échouée, le site démarre quand même"

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
