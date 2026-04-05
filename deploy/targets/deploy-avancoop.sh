#!/usr/bin/env bash
set -euo pipefail

# =========================
# Configuracion AVANCOOP (exclusiva)
# Nota: este deploy NO usa ./reiniciar.sh.
# Reinicia el servicio remoto configurado en RESTART_CMD.
# =========================
SERVER="${SERVER:-administrator@38.247.130.84}"
REMOTE_DIR="${REMOTE_DIR:-/opt/avancoop/}"
LOCAL_DIR="${LOCAL_DIR:-/Users/jalm/Dropbox/Apps/SIPET/}"
PERSISTENT_DB_DIR="${PERSISTENT_DB_DIR:-/var/lib/avancoop/data}"
PERSISTENT_DB_PATH="${PERSISTENT_DB_PATH:-${PERSISTENT_DB_DIR}/avandbcoop.db}"
LEGACY_DB_PATH="${LEGACY_DB_PATH:-/opt/avancoop/strategic_planning.db}"
PREVIOUS_PERSISTENT_DB_PATH="${PREVIOUS_PERSISTENT_DB_PATH:-${PERSISTENT_DB_DIR}/strategic_planning.db}"
DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-sipet_avancoop}"
DB_USER="${DB_USER:-sipet}"
DB_PASSWORD="${DB_PASSWORD:-XX\$26avancoop26\$XX}"
ENCODED_DB_PASSWORD="$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "${DB_PASSWORD}")"
DATAMAIN_URL_VALUE="postgresql://${DB_USER}:${ENCODED_DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
REMOTE_SAFE_DATAMAIN_URL_VALUE="${DATAMAIN_URL_VALUE//$/\\$}"
DATAMAIN_URL_ENV_VALUE="'${REMOTE_SAFE_DATAMAIN_URL_VALUE}'"
REMOTE_RESTART_SCRIPT="${REMOTE_RESTART_SCRIPT:-/usr/local/bin/avancoop-restart}"
DOMAIN_NAME="${DOMAIN_NAME:-avancoop.org}"
DOMAIN_CONFIG_DIR="${DOMAIN_CONFIG_DIR:-${REMOTE_DIR%/}/config/dominios}"

echo "Configuracion activa:"
echo "  SERVER=$SERVER"
echo "  APP=avancoop"
echo "  REMOTE_DIR=$REMOTE_DIR"
echo "  DB_HOST=$DB_HOST"
echo "  DB_PORT=$DB_PORT"
echo "  DB_NAME=$DB_NAME"
echo "  DB_USER=$DB_USER"
echo "  DOMAIN_NAME=$DOMAIN_NAME"
echo "  RESTART_CMD=$REMOTE_RESTART_SCRIPT"

echo "Fijando configuracion de produccion en ${REMOTE_DIR}.env..."
ssh "$SERVER" "touch '${REMOTE_DIR}.env' && \
  grep -q '^APP_ENV=' '${REMOTE_DIR}.env' && sed -i 's|^APP_ENV=.*|APP_ENV=production|' '${REMOTE_DIR}.env' || echo 'APP_ENV=production' >> '${REMOTE_DIR}.env' && \
  grep -q '^DATABASE_URL=' '${REMOTE_DIR}.env' && sed -i \"s|^DATABASE_URL=.*|DATABASE_URL=${DATAMAIN_URL_ENV_VALUE}|\" '${REMOTE_DIR}.env' || echo \"DATABASE_URL=${DATAMAIN_URL_ENV_VALUE}\" >> '${REMOTE_DIR}.env' && \
  grep -q '^DATAMAIN_URL=' '${REMOTE_DIR}.env' && sed -i \"s|^DATAMAIN_URL=.*|DATAMAIN_URL=${DATAMAIN_URL_ENV_VALUE}|\" '${REMOTE_DIR}.env' || echo \"DATAMAIN_URL=${DATAMAIN_URL_ENV_VALUE}\" >> '${REMOTE_DIR}.env' && \
  grep -q '^SQLITE_DB_PATH=' '${REMOTE_DIR}.env' && sed -i 's|^SQLITE_DB_PATH=.*|SQLITE_DB_PATH=|' '${REMOTE_DIR}.env' || echo 'SQLITE_DB_PATH=' >> '${REMOTE_DIR}.env' && \
  grep -q '^AUTH_COOKIE_SECRET=' '${REMOTE_DIR}.env' || (python3 -c 'import secrets; print(\"AUTH_COOKIE_SECRET=\" + secrets.token_urlsafe(48))' >> '${REMOTE_DIR}.env')"

echo "Publicando configuracion dedicada de AVANCOOP..."
REMOTE_DOMAIN_CONF="/tmp/${DOMAIN_NAME}.conf"
{
  printf '%s\n' "[options]"
  printf 'domain = %s\n' "${DOMAIN_NAME}"
  printf 'db_host = %s\n' "${DB_HOST}"
  printf 'db_port = %s\n' "${DB_PORT}"
  printf 'db_user = %s\n' "${DB_USER}"
  printf 'db_password = %s\n' "${DB_PASSWORD}"
  printf 'db_name = %s\n' "${DB_NAME}"
  printf '%s\n' "db_engine = postgresql"
  printf '%s\n' "dbfilter = ^%h$"
  printf '%s\n' "show_db_path = False"
  printf '%s\n' "admin_passwd = cambia_esta_clave"
  printf '%s\n' "list_db = False"
  printf '%s\n' "proxy_mode = True"
  printf '%s\n' "workers = 4"
  printf '%s\n' "max_cron_threads = 2"
  printf '%s\n' "log_level = info"
  printf '\n%s\n' "[superadmin]"
  printf '%s\n' "superadmin_user = 0konomiyaki"
  printf '%s\n' "superadmin_password = XX,$,26,sipet,26,$,XX"
  printf '%s\n' "superadmin_email = alopez@avancoop.org"
} > "${REMOTE_DOMAIN_CONF}"
scp "${REMOTE_DOMAIN_CONF}" "$SERVER:${REMOTE_DOMAIN_CONF}"
rm -f "${REMOTE_DOMAIN_CONF}"
ssh "$SERVER" "mkdir -p '${DOMAIN_CONFIG_DIR}' && cp '${REMOTE_DOMAIN_CONF}' '${DOMAIN_CONFIG_DIR}/${DOMAIN_NAME}.conf' && cp '${REMOTE_DOMAIN_CONF}' '${REMOTE_DIR%/}/sipet.conf' && rm -f '${REMOTE_DOMAIN_CONF}'"

echo "Instalando restart remoto exclusivo de AVANCOOP..."
ssh -tt "$SERVER" "cat > '/tmp/avancoop-restart.new' <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
cd /opt/avancoop

if [ -f '.venv/bin/activate' ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

if [ -f '.env' ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

export APP_ENV=\"\${APP_ENV:-production}\"
export PYTHONUNBUFFERED=1
PORT=\"\${PORT:-8000}\"
HOST=\"\${HOST:-0.0.0.0}\"
LOG_FILE=\"\${LOG_FILE:-uvicorn.log}\"
LOG_MAX_LINES=\"\${LOG_MAX_LINES:-1000}\"
UVICORN_LOG_LEVEL=\"\${UVICORN_LOG_LEVEL:-debug}\"
PYTHON_BIN=\"\${PYTHON_BIN:-python3}\"

if [ -x '.venv/bin/python' ]; then
  PYTHON_BIN=\"\$PWD/.venv/bin/python\"
fi

if [ -z \"\${AUTH_COOKIE_SECRET:-}\" ]; then
  AUTH_COOKIE_SECRET=\"\$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')\"
  export AUTH_COOKIE_SECRET
  if grep -q '^AUTH_COOKIE_SECRET=' .env 2>/dev/null; then
    sed -i.bak \"s|^AUTH_COOKIE_SECRET=.*|AUTH_COOKIE_SECRET=\${AUTH_COOKIE_SECRET}|g\" .env && rm -f .env.bak
  else
    printf '\nAUTH_COOKIE_SECRET=%s\n' \"\${AUTH_COOKIE_SECRET}\" >> .env
  fi
fi

if [ -f 'alembic.ini' ]; then
  if ! alembic upgrade heads; then
    echo 'Aviso: Alembic fallo durante el reinicio de AVANCOOP.'
  fi
fi

PIDS_EN_PUERTO=\"\$(lsof -ti:\"\$PORT\" 2>/dev/null || true)\"
if [ -n \"\$PIDS_EN_PUERTO\" ]; then
  echo \"Deteniendo procesos en el puerto \$PORT: \$PIDS_EN_PUERTO\"
  for PID in \$PIDS_EN_PUERTO; do
    kill \"\$PID\" 2>/dev/null || true
  done
  sleep 1
  PIDS_RESTANTES=\"\$(lsof -ti:\"\$PORT\" 2>/dev/null || true)\"
  if [ -n \"\$PIDS_RESTANTES\" ]; then
    for PID in \$PIDS_RESTANTES; do
      kill -9 \"\$PID\" 2>/dev/null || true
    done
  fi
fi

mkdir -p \"\$(dirname \"\$LOG_FILE\")\" 2>/dev/null || true
: > \"\$LOG_FILE\"
if command -v setsid >/dev/null 2>&1; then
  nohup setsid \"\$PYTHON_BIN\" scripts/run_with_capped_log.py --log-file \"\$LOG_FILE\" --max-lines \"\$LOG_MAX_LINES\" -- \"\$PYTHON_BIN\" -m uvicorn fastapi_modulo.modulos_sipet.modulo_base.runtime:app --host \"\$HOST\" --port \"\$PORT\" --log-level \"\$UVICORN_LOG_LEVEL\" > /dev/null 2>&1 < /dev/null &
else
  nohup \"\$PYTHON_BIN\" scripts/run_with_capped_log.py --log-file \"\$LOG_FILE\" --max-lines \"\$LOG_MAX_LINES\" -- \"\$PYTHON_BIN\" -m uvicorn fastapi_modulo.modulos_sipet.modulo_base.runtime:app --host \"\$HOST\" --port \"\$PORT\" --log-level \"\$UVICORN_LOG_LEVEL\" > /dev/null 2>&1 < /dev/null &
fi

echo 'Sistema AVANCOOP reiniciado.'
EOF
sudo install -o root -g root -m 755 '/tmp/avancoop-restart.new' '${REMOTE_RESTART_SCRIPT}'
rm -f '/tmp/avancoop-restart.new'"

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

echo "Reiniciando app con PostgreSQL..."
ssh -tt "$SERVER" "cd '${REMOTE_DIR}' && sudo '${REMOTE_RESTART_SCRIPT}'"

echo "Deploy completado. BD activa en PostgreSQL ${DB_NAME}"
