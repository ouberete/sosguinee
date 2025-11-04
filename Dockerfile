# Dockerfile pour Django (développement / simple)
FROM python:3.9-slim

# Assure des locales et OS deps minimum
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# OS deps utiles (psycopg2, pillow, etc. au cas où)
RUN apt-get update && apt-get install -y build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier les dépendances Python en premier pour profiter du cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code
COPY . .

# Exposer le port Django
EXPOSE 8000

# Par défaut on laisse la commande à compose (voir docker-compose.yml)
