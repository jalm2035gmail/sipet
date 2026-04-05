#!/usr/bin/env bash
set -euo pipefail

# =========================
# Configuracion SIPET Produccion (Uprocach)
# Similar al flujo de AVANCOOP, con valores sobreescribibles via variables.
# Ejemplo:
#   SERVER=administrator@203.0.113.10 deploy/aliases/deploy-uprocach.sh
# =========================

SERVER="${SERVER:-}"
REMOTE_DIR="${REMOTE_DIR:-/opt/sipet/}"
LOCAL_DIR="${LOCAL_DIR:-/Users/jalm/Dropbox/Apps/SIPET/}"
DATABASE_BACKEND="${DATABASE_BACKEND:-postgresql}"
PERSISTENT_DB_DIR="${PERSISTENT_DB_DIR:-/var/lib/sipet/data}"
PERSISTENT_DB_PATH="${PERSISTENT_DB_PATH:-${PERSISTENT_DB_DIR}/sipet.db}"
LEGACY_DB_PATH="${LEGACY_DB_PATH:-/opt/sipet/sipet.db}"
LEGACY_DB_FALLBACK_PATH="${LEGACY_DB_FALLBACK_PATH:-/opt/sipet/strategic_planning.db}"
PREVIOUS_PERSISTENT_DB_PATH="${PREVIOUS_PERSISTENT_DB_PATH:-${PERSISTENT_DB_DIR}/strategic_planning.db}"
RESTART_CMD="${RESTART_CMD:-/usr/local/bin/sipet-restart}"
SYSTEMD_SERVICE_NAME="${SYSTEMD_SERVICE_NAME:-sipet}"
POSTGRES_DB="${POSTGRES_DB:-sipet}"
POSTGRES_USER="${POSTGRES_USER:-sipet}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
POSTGRES_HOST="${POSTGRES_HOST:-127.0.0.1}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
REMOTE_IMPORTED_MODULES_DIR="${REMOTE_IMPORTED_MODULES_DIR:-${REMOTE_DIR%/}/fastapi_modulo/modulos}"

if [ "${DATABASE_BACKEND}" = "postgresql" ]; then
  if [ -z "${POSTGRES_PASSWORD}" ]; then
    echo "ERROR: Define POSTGRES_PASSWORD para deploy con PostgreSQL."
    exit 1
  fi
  DATAMAIN_URL_VALUE="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
else
  DATAMAIN_URL_VALUE="sqlite:////${PERSISTENT_DB_PATH#/}"
fi

if [ -z "$SERVER" ]; then
  echo "ERROR: Define SERVER=usuario@host antes de ejecutar este deploy."
  exit 1
fi

echo "Configuracion activa:"
echo "  SERVER=$SERVER"
echo "  APP=sipet"
echo "  DATABASE_BACKEND=$DATABASE_BACKEND"
echo "  REMOTE_DIR=$REMOTE_DIR"
echo "  PERSISTENT_DB_DIR=$PERSISTENT_DB_DIR"
echo "  PERSISTENT_DB_PATH=$PERSISTENT_DB_PATH"
echo "  REMOTE_IMPORTED_MODULES_DIR=$REMOTE_IMPORTED_MODULES_DIR"
echo "  RESTART_CMD=$RESTART_CMD"
echo "  SYSTEMD_SERVICE_NAME=$SYSTEMD_SERVICE_NAME"

echo "Validando directorio remoto de modulos importados..."
ssh "$SERVER" "test -d '${REMOTE_IMPORTED_MODULES_DIR}' || { echo 'ERROR: ${REMOTE_IMPORTED_MODULES_DIR} no existe en servidor. Este deploy preserva fastapi_modulo/modulos y requiere que ya exista en remoto.'; exit 1; }"

echo "Preservando modulos importados remotos en ${REMOTE_IMPORTED_MODULES_DIR} (no se sincronizan desde local)."

if [ "${DATABASE_BACKEND}" = "sqlite" ]; then
  echo "Validando ruta persistente de MAIN de datos en servidor..."
  ssh "$SERVER" "test -d '${PERSISTENT_DB_DIR}' || { echo 'ERROR: ${PERSISTENT_DB_DIR} no existe en servidor.'; exit 1; }"

  echo "Migrando BD legacy si aplica..."
  ssh "$SERVER" "if [ -f '${LEGACY_DB_PATH}' ] && [ ! -f '${PERSISTENT_DB_PATH}' ]; then cp '${LEGACY_DB_PATH}' '${PERSISTENT_DB_PATH}'; elif [ -f '${LEGACY_DB_FALLBACK_PATH}' ] && [ ! -f '${PERSISTENT_DB_PATH}' ]; then cp '${LEGACY_DB_FALLBACK_PATH}' '${PERSISTENT_DB_PATH}'; fi"

  echo "Migrando BD persistente previa si aplica..."
  ssh "$SERVER" "if [ -f '${PREVIOUS_PERSISTENT_DB_PATH}' ] && [ ! -f '${PERSISTENT_DB_PATH}' ]; then cp '${PREVIOUS_PERSISTENT_DB_PATH}' '${PERSISTENT_DB_PATH}'; fi"
fi

echo "Fijando configuracion de produccion en ${REMOTE_DIR}.env..."
ssh "$SERVER" "touch '${REMOTE_DIR}.env' && \
  grep -q '^APP_ENV=' '${REMOTE_DIR}.env' && sed -i 's|^APP_ENV=.*|APP_ENV=production|' '${REMOTE_DIR}.env' || echo 'APP_ENV=production' >> '${REMOTE_DIR}.env' && \
  grep -q '^DATAMAIN_URL=' '${REMOTE_DIR}.env' && sed -i 's|^DATAMAIN_URL=.*|DATAMAIN_URL=${DATAMAIN_URL_VALUE}|' '${REMOTE_DIR}.env' || echo 'DATAMAIN_URL=${DATAMAIN_URL_VALUE}' >> '${REMOTE_DIR}.env' && \
  grep -q '^SQLITE_DB_PATH=' '${REMOTE_DIR}.env' && sed -i 's|^SQLITE_DB_PATH=.*|SQLITE_DB_PATH=${PERSISTENT_DB_PATH}|' '${REMOTE_DIR}.env' || echo 'SQLITE_DB_PATH=${PERSISTENT_DB_PATH}' >> '${REMOTE_DIR}.env' && \
  grep -q '^AUTH_COOKIE_SECRET=' '${REMOTE_DIR}.env' || (python3 -c 'import secrets; print(\"AUTH_COOKIE_SECRET=\" + secrets.token_urlsafe(48))' >> '${REMOTE_DIR}.env')"

echo "Desplegando codigo..."
rsync -az --delete \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.env' \
  --exclude 'fastapi_modulo/modulos/' \
  --exclude 'fastapi_modulo/modulos_sipet/frontend/pages_store.json' \
  --exclude 'fastapi_modulo/modulos_sipet/frontend/versions_store.json' \
  --exclude 'fastapi_modulo/modulos_sipet/frontend/contact_store.json' \
  --exclude 'fastapi_modulo/modulos_sipet/frontend/brand_store.json' \
  --exclude 'fastapi_modulo/modulos_sipet/frontend/tasas_store.json' \
  --exclude 'fastapi_modulo/modulos_sipet/web/identidad_login.json' \
  --exclude 'fastapi_modulo/runtime_store/' \
  --exclude 'fastapi_modulo/templates/imagenes/' \
  --exclude 'fastapi_modulo/identidad_login.json' \
  --exclude 'fastapi_modulo/uploads/' \
  "$LOCAL_DIR" "$SERVER:$REMOTE_DIR"

echo "Reiniciando app..."
REMOTE_RESTART_SNIPPET="if [ -x '${RESTART_CMD}' ]; then sudo '${RESTART_CMD}'; else sudo systemctl restart '${SYSTEMD_SERVICE_NAME}' && sudo systemctl --no-pager --full status '${SYSTEMD_SERVICE_NAME}' || true; fi"
if [ "${DATABASE_BACKEND}" = "sqlite" ]; then
  ssh -tt "$SERVER" "cd '${REMOTE_DIR}' && SQLITE_DB_PATH='${PERSISTENT_DB_PATH}' bash -lc \"${REMOTE_RESTART_SNIPPET}\""
else
  ssh -tt "$SERVER" "cd '${REMOTE_DIR}' && bash -lc \"${REMOTE_RESTART_SNIPPET}\""
fi

echo "Deploy completado. Backend=${DATABASE_BACKEND}"
