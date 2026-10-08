#!/usr/bin/env bash
# ==============================================================================
# Script de restauration - Ensemble 224
# Vérifie l'empreinte SHA256 avant toute restauration.
# ==============================================================================

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <chemin_vers_fichier_backup>"
    echo "Exemple SQLite : $0 backups/db_sqlite_20261007_120000.sqlite3"
    echo "Exemple Postgres : $0 backups/db_postgres_ensemble224_20261007_120000.dump"
    exit 1
fi

BACKUP_FILE="$1"
SHA_FILE="${BACKUP_FILE}.sha256"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Fichier introuvable : $BACKUP_FILE"
    exit 1
fi

# 1. Vérification d'intégrité SHA256 si disponible
if [ -f "$SHA_FILE" ]; then
    echo "🔍 Vérification de l'intégrité SHA256..."
    shasum -a 256 -c "$SHA_FILE"
    echo "✅ Intégrité vérifiée."
else
    echo "⚠️ Avertissement : fichier d'empreinte $SHA_FILE absent. Poursuite sans vérification d'empreinte."
fi

# 2. Restauration SQLite
if [[ "$BACKUP_FILE" == *.sqlite3 ]]; then
    echo "📦 Restauration SQLite vers db.sqlite3..."
    if [ -f "db.sqlite3" ]; then
        cp db.sqlite3 "db.sqlite3.pre_restore_$(date +%s).bak"
        echo "   (Copie de sécurité de la base existante créée : db.sqlite3.pre_restore_*.bak)"
    fi
    cp "$BACKUP_FILE" db.sqlite3
    echo "✅ Restauration SQLite terminée avec succès dans db.sqlite3."
    exit 0
fi

# 3. Restauration PostgreSQL
TARGET_DB="${RESTORE_DB:-${POSTGRES_NAME:-ensemble224}}"
DB_USER="${POSTGRES_USER:-ensemble224}"
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"

echo "⚠️ ATTENTION : Vous allez restaurer $BACKUP_FILE dans la base PostgreSQL '$TARGET_DB' sur $DB_HOST."
if [ -z "${FORCE_RESTORE:-}" ]; then
    read -r -p "Confirmer la restauration ? (oui/non) : " confirmation
    if [ "$confirmation" != "oui" ]; then
        echo "Restauration annulée."
        exit 0
    fi
fi

if [ -n "${DATABASE_URL:-}" ]; then
    pg_restore --clean --if-exists --no-owner --no-privileges -d "$DATABASE_URL" "$BACKUP_FILE"
else
    PGPASSWORD="${POSTGRES_PASSWORD:-}" pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" --clean --if-exists --no-owner --no-privileges -d "$TARGET_DB" "$BACKUP_FILE"
fi

echo "✅ Restauration PostgreSQL terminée avec succès dans $TARGET_DB."
