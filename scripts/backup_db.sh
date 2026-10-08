#!/usr/bin/env bash
# ==============================================================================
# Script de sauvegarde automatisé - Ensemble 224
# Supporte PostgreSQL et SQLite avec vérification d'empreinte SHA256.
# ==============================================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "$BACKUP_DIR"

# 1. Sauvegarde SQLite si le fichier existe et qu'aucune base Postgres n'est configurée
if [ -f "db.sqlite3" ] && [ -z "${DATABASE_URL:-}" ] && [ "${USE_POSTGRES:-False}" != "True" ]; then
    BACKUP_FILE="${BACKUP_DIR}/db_sqlite_${TIMESTAMP}.sqlite3"
    echo "📦 [SQLite] Création de la sauvegarde : ${BACKUP_FILE}..."
    if command -v sqlite3 >/dev/null 2>&1; then
        sqlite3 db.sqlite3 ".backup '${BACKUP_FILE}'"
    else
        cp db.sqlite3 "${BACKUP_FILE}"
    fi
    shasum -a 256 "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"
    echo "✅ [SQLite] Sauvegarde terminée avec succès :"
    echo "   Fichier : ${BACKUP_FILE}"
    cat "${BACKUP_FILE}.sha256"
    exit 0
fi

# 2. Sauvegarde PostgreSQL
DB_NAME="${POSTGRES_NAME:-ensemble224}"
DB_USER="${POSTGRES_USER:-ensemble224}"
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"

BACKUP_FILE="${BACKUP_DIR}/db_postgres_${DB_NAME}_${TIMESTAMP}.dump"
echo "📦 [PostgreSQL] Sauvegarde de la base ${DB_NAME} sur ${DB_HOST}:${DB_PORT}..."

if [ -n "${DATABASE_URL:-}" ]; then
    pg_dump -Fc "$DATABASE_URL" > "$BACKUP_FILE"
else
    PGPASSWORD="${POSTGRES_PASSWORD:-}" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -Fc "$DB_NAME" > "$BACKUP_FILE"
fi

shasum -a 256 "$BACKUP_FILE" > "${BACKUP_FILE}.sha256"
echo "✅ [PostgreSQL] Sauvegarde terminée avec succès :"
echo "   Fichier : ${BACKUP_FILE}"
cat "${BACKUP_FILE}.sha256"
