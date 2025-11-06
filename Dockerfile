FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*


# Copier les fichiers de dépendances et installer les paquets Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copier le script d'initialisation et lui donner les droits d’exécution
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copier tout le reste du projet
COPY . .

# Exposer le port sur lequel Gunicorn écoutera
EXPOSE 8000

# Utiliser le script comme point d'entrée
ENTRYPOINT ["/app/entrypoint.sh"]
