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
DATAMAIN_URL_VALUE="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
REMOTE_SAFE_DATAMAIN_URL_VALUE="${DATAMAIN_URL_VALUE//$/\\$}"
DATAMAIN_URL_ENV_VALUE="'${REMOTE_SAFE_DATAMAIN_URL_VALUE}'"
REMOTE_RESTART_SCRIPT="${REMOTE_RESTART_SCRIPT:-/usr/local/bin/avancoop-restart}"

echo "Configuracion activa:"
echo "  SERVER=$SERVER"
echo "  APP=avancoop"
echo "  REMOTE_DIR=$REMOTE_DIR"
echo "  DB_HOST=$DB_HOST"
echo "  DB_PORT=$DB_PORT"
echo "  DB_NAME=$DB_NAME"
echo "  DB_USER=$DB_USER"
echo "  RESTART_CMD=$REMOTE_RESTART_SCRIPT"

echo "Fijando configuracion de produccion en ${REMOTE_DIR}.env..."
ssh "$SERVER" "touch '${REMOTE_DIR}.env' && \
  grep -q '^APP_ENV=' '${REMOTE_DIR}.env' && sed -i 's|^APP_ENV=.*|APP_ENV=production|' '${REMOTE_DIR}.env' || echo 'APP_ENV=production' >> '${REMOTE_DIR}.env' && \
  grep -q '^DATABASE_URL=' '${REMOTE_DIR}.env' && sed -i \"s|^DATABASE_URL=.*|DATABASE_URL=${DATAMAIN_URL_ENV_VALUE}|\" '${REMOTE_DIR}.env' || echo \"DATABASE_URL=${DATAMAIN_URL_ENV_VALUE}\" >> '${REMOTE_DIR}.env' && \
  grep -q '^DATAMAIN_URL=' '${REMOTE_DIR}.env' && sed -i \"s|^DATAMAIN_URL=.*|DATAMAIN_URL=${DATAMAIN_URL_ENV_VALUE}|\" '${REMOTE_DIR}.env' || echo \"DATAMAIN_URL=${DATAMAIN_URL_ENV_VALUE}\" >> '${REMOTE_DIR}.env' && \
  grep -q '^SQLITE_DB_PATH=' '${REMOTE_DIR}.env' && sed -i 's|^SQLITE_DB_PATH=.*|SQLITE_DB_PATH=|' '${REMOTE_DIR}.env' || echo 'SQLITE_DB_PATH=' >> '${REMOTE_DIR}.env' && \
  grep -q '^AUTH_COOKIE_SECRET=' '${REMOTE_DIR}.env' || (python3 -c 'import secrets; print(\"AUTH_COOKIE_SECRET=\" + secrets.token_urlsafe(48))' >> '${REMOTE_DIR}.env')"

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
  --exclude 'fastapi_modulo/modulos_sipet/web/identidad_login.json' \
  --exclude 'fastapi_modulo/runtime_store/' \
  --exclude 'fastapi_modulo/templates/imagenes/' \
  --exclude 'fastapi_modulo/identidad_login.json' \
  --exclude 'fastapi_modulo/uploads/' \
  "$LOCAL_DIR" "$SERVER:$REMOTE_DIR"

echo "Reiniciando app con PostgreSQL..."
ssh -tt "$SERVER" "cd '${REMOTE_DIR}' && sudo '${REMOTE_RESTART_SCRIPT}'"

echo "Deploy completado. BD activa en PostgreSQL ${DB_NAME}"
