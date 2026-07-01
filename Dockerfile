FROM python:3.12-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires (inclut gettext pour i18n)
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev netcat-openbsd gettext && \
    rm -rf /var/lib/apt/lists/*


# Copier les fichiers de dépendances et installer les paquets Python
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir "celery[redis]==5.4.0" "sentry-sdk==2.29.1"

# Copier tout le reste du projet
COPY . .

# Donner les droits d'exécution et retirer les retours à la ligne Windows (CRLF) qui font crasher Fly.io
RUN chmod +x /app/entrypoint.sh && \
    sed -i 's/\r$//' /app/entrypoint.sh

# Exposer le port sur lequel Gunicorn écoutera
EXPOSE 8000

# Utiliser le script comme commande de démarrage
CMD ["/app/entrypoint.sh"]

