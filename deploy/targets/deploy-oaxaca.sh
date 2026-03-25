#!/usr/bin/env bash
set -euo pipefail

SERVER="${SERVER:-}"
REMOTE_DIR="${REMOTE_DIR:-/opt/sipet/}"
LOCAL_DIR="${LOCAL_DIR:-/Users/jalm/Dropbox/Apps/SIPET/}"
DATABASE_BACKEND="${DATABASE_BACKEND:-postgresql}"
PERSISTENT_DB_DIR="${PERSISTENT_DB_DIR:-/var/lib/sipet/data}"
PERSISTENT_DB_PATH="${PERSISTENT_DB_PATH:-${PERSISTENT_DB_DIR}/sipet.db}"
RESTART_CMD="${RESTART_CMD:-/usr/local/bin/sipet-restart}"
SYSTEMD_SERVICE_NAME="${SYSTEMD_SERVICE_NAME:-sipet}"
POSTGRES_DB="${POSTGRES_DB:-sipet}"
POSTGRES_USER="${POSTGRES_USER:-sipet}"
POSTGRES_HOST="${POSTGRES_HOST:-127.0.0.1}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
DOMAIN_NAME="${DOMAIN_NAME:-oaxaca.tunegociovale.com}"
DOMAIN_CONFIG_DIR="${DOMAIN_CONFIG_DIR:-${REMOTE_DIR%/}/config/dominios}"
DOMAIN_DB_NAME="${DOMAIN_DB_NAME:-sipet_oaxaca}"
DOMAIN_DB_USER="${DOMAIN_DB_USER:-${POSTGRES_USER}}"
DOMAIN_DB_PASSWORD="${DOMAIN_DB_PASSWORD:-}"
DOMAIN_DB_HOST="${DOMAIN_DB_HOST:-${POSTGRES_HOST}}"
DOMAIN_DB_PORT="${DOMAIN_DB_PORT:-${POSTGRES_PORT}}"
DOMAIN_DB_ENGINE="${DOMAIN_DB_ENGINE:-postgresql}"
DOMAIN_DBFILTER="${DOMAIN_DBFILTER:-^%h$}"
SUPERADMIN_USER="${SUPERADMIN_USER:-0konomiyaki}"
SUPERADMIN_PASSWORD="${SUPERADMIN_PASSWORD:-XX,$,26,sipet,26,$,XX}"
SUPERADMIN_EMAIL="${SUPERADMIN_EMAIL:-alopez@avancoop.org}"
REMOTE_IMPORTED_MODULES_DIR="${REMOTE_IMPORTED_MODULES_DIR:-${REMOTE_DIR%/}/fastapi_modulo/modulos}"

if [ -z "${SERVER}" ]; then
  echo "ERROR: Define SERVER=usuario@host antes de ejecutar este deploy."
  exit 1
fi

echo "Configuracion activa:"
echo "  SERVER=$SERVER"
echo "  REMOTE_DIR=$REMOTE_DIR"
echo "  DATABASE_BACKEND=$DATABASE_BACKEND"
echo "  DOMAIN_NAME=$DOMAIN_NAME"
echo "  DOMAIN_DB_NAME=$DOMAIN_DB_NAME"
echo "  REMOTE_IMPORTED_MODULES_DIR=$REMOTE_IMPORTED_MODULES_DIR"

echo "Preparando directorios remotos..."
ssh -tt "$SERVER" "sudo mkdir -p '${REMOTE_DIR%/}' '${REMOTE_DIR%/}/fastapi_modulo/modulos' '${PERSISTENT_DB_DIR}' '${DOMAIN_CONFIG_DIR}' && sudo chown -R administrator:administrator '${REMOTE_DIR%/}'"

echo "Validando directorio remoto de modulos importados..."
ssh "$SERVER" "test -d '${REMOTE_IMPORTED_MODULES_DIR}' || { echo 'ERROR: ${REMOTE_IMPORTED_MODULES_DIR} no existe en servidor. Este deploy preserva fastapi_modulo/modulos y requiere que ya exista en remoto.'; exit 1; }"

echo "Preservando modulos importados remotos en ${REMOTE_IMPORTED_MODULES_DIR} (no se sincronizan desde local)."

echo "Fijando configuracion de produccion en ${REMOTE_DIR}.env..."
ssh "$SERVER" "touch '${REMOTE_DIR}.env' && \
  grep -q '^APP_ENV=' '${REMOTE_DIR}.env' && sed -i 's|^APP_ENV=.*|APP_ENV=production|' '${REMOTE_DIR}.env' || echo 'APP_ENV=production' >> '${REMOTE_DIR}.env' && \
  grep -q '^SQLITE_DB_PATH=' '${REMOTE_DIR}.env' && sed -i 's|^SQLITE_DB_PATH=.*|SQLITE_DB_PATH=${PERSISTENT_DB_PATH}|' '${REMOTE_DIR}.env' || echo 'SQLITE_DB_PATH=${PERSISTENT_DB_PATH}' >> '${REMOTE_DIR}.env' && \
  grep -q '^AUTH_COOKIE_SECRET=' '${REMOTE_DIR}.env' || (python3 -c 'import secrets; print(\"AUTH_COOKIE_SECRET=\" + secrets.token_urlsafe(48))' >> '${REMOTE_DIR}.env')"

echo "Desplegando codigo..."
rsync -az --delete \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.env' \
  --exclude 'sipet.conf' \
  --exclude 'fastapi_modulo/modulos/' \
  --exclude 'fastapi_modulo/modulos_sipet/web/identidad_login.json' \
  --exclude 'fastapi_modulo/runtime_store/' \
  --exclude 'fastapi_modulo/templates/imagenes/' \
  --exclude 'fastapi_modulo/identidad_login.json' \
  --exclude 'fastapi_modulo/uploads/' \
  "$LOCAL_DIR" "$SERVER:$REMOTE_DIR"

echo "Publicando configuracion dedicada del dominio..."
REMOTE_DOMAIN_CONF="/tmp/${DOMAIN_NAME}.conf"
EXISTING_DOMAIN_DB_PASSWORD="$(ssh "$SERVER" "python3 -c \"from configparser import ConfigParser; from pathlib import Path; path = Path('${DOMAIN_CONFIG_DIR}/${DOMAIN_NAME}.conf'); parser = ConfigParser(interpolation=None); parser.read(path, encoding='utf-8'); print(parser.get('options', 'db_password', fallback='')) if path.exists() else print('')\"" | tr -d '\r')"
if [ -z "${DOMAIN_DB_PASSWORD}" ] && [ -n "${EXISTING_DOMAIN_DB_PASSWORD}" ]; then
  DOMAIN_DB_PASSWORD="${EXISTING_DOMAIN_DB_PASSWORD}"
fi
{
  printf '%s\n' "[options]"
  printf 'domain = %s\n' "${DOMAIN_NAME}"
  printf 'db_host = %s\n' "${DOMAIN_DB_HOST}"
  printf 'db_port = %s\n' "${DOMAIN_DB_PORT}"
  printf 'db_user = %s\n' "${DOMAIN_DB_USER}"
  if [ -n "${DOMAIN_DB_PASSWORD}" ]; then
    printf 'db_password = %s\n' "${DOMAIN_DB_PASSWORD}"
  fi
  printf 'db_name = %s\n' "${DOMAIN_DB_NAME}"
  printf 'db_engine = %s\n' "${DOMAIN_DB_ENGINE}"
  printf 'dbfilter = %s\n' "${DOMAIN_DBFILTER}"
  printf '%s\n' "show_db_path = False"
  printf '%s\n' "admin_passwd = cambia_esta_clave"
  printf '%s\n' "list_db = False"
  printf '%s\n' "proxy_mode = True"
  printf '%s\n' "workers = 4"
  printf '%s\n' "max_cron_threads = 2"
  printf '%s\n' "log_level = info"
  printf '\n%s\n' "[superadmin]"
  printf 'superadmin_user = %s\n' "${SUPERADMIN_USER}"
  printf 'superadmin_password = %s\n' "${SUPERADMIN_PASSWORD}"
  printf 'superadmin_email = %s\n' "${SUPERADMIN_EMAIL}"
} > "${REMOTE_DOMAIN_CONF}"
scp "${REMOTE_DOMAIN_CONF}" "$SERVER:${REMOTE_DOMAIN_CONF}"
rm -f "${REMOTE_DOMAIN_CONF}"
ssh "$SERVER" "cp '${REMOTE_DOMAIN_CONF}' '${DOMAIN_CONFIG_DIR}/${DOMAIN_NAME}.conf' && rm -f '${REMOTE_DOMAIN_CONF}'"

echo "Instalando dependencias y reiniciando app..."
ssh -tt "$SERVER" "cd '${REMOTE_DIR}' && sudo '${REMOTE_DIR%/}/.venv/bin/pip' install -r requirements.txt && bash -lc \"if [ -x '${RESTART_CMD}' ]; then sudo '${RESTART_CMD}'; else sudo systemctl restart '${SYSTEMD_SERVICE_NAME}' && sudo systemctl --no-pager --full status '${SYSTEMD_SERVICE_NAME}' || true; fi\""

echo "Deploy Oaxaca completado. Backend=${DATABASE_BACKEND}"
