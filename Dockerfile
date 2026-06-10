FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires (inclut gettext pour i18n)
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev netcat-openbsd gettext && \
    rm -rf /var/lib/apt/lists/*


# Copier les fichiers de dépendances et installer les paquets Python
COPY requirements.txt .
<<<<<<< HEAD
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
=======
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir "celery[redis]==5.4.0" "sentry-sdk==2.29.1"
>>>>>>> chore/security-design-hardening

# Copier le script d'initialisation et lui donner les droits d'exécution
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copier tout le reste du projet
COPY . .

# Exposer le port sur lequel Gunicorn écoutera
EXPOSE 8000

# Utiliser le script comme point d'entrée
ENTRYPOINT ["/app/entrypoint.sh"]

