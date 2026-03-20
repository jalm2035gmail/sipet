#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${APP_NAME:-sipet}"
APP_USER="${APP_USER:-sipet}"
APP_GROUP="${APP_GROUP:-sipet}"
APP_DIR="${APP_DIR:-/opt/sipet}"
DATA_DIR="${DATA_DIR:-/var/lib/sipet/data}"
LOG_DIR="${LOG_DIR:-/var/log/sipet}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-${APP_DIR}/.venv}"
SERVICE_NAME="${SERVICE_NAME:-sipet}"
PORT="${PORT:-8000}"
DATABASE_BACKEND="${DATABASE_BACKEND:-postgresql}"
POSTGRES_DB="${POSTGRES_DB:-sipet}"
POSTGRES_USER="${POSTGRES_USER:-sipet}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
POSTGRES_HOST="${POSTGRES_HOST:-127.0.0.1}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

if [ "$(id -u)" -ne 0 ]; then
  echo "ERROR: Ejecuta este script como root en el servidor remoto."
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y --no-install-recommends \
  python3 \
  python3-venv \
  python3-pip \
  build-essential \
  pkg-config \
  default-libmysqlclient-dev \
  libpq-dev \
  libjpeg-dev \
  zlib1g-dev \
  libfreetype6-dev \
  libopenblas-dev \
  liblapack-dev \
  curl \
  rsync \
  postgresql \
  postgresql-contrib

if ! getent group "${APP_GROUP}" >/dev/null 2>&1; then
  groupadd --system "${APP_GROUP}"
fi

if ! id -u "${APP_USER}" >/dev/null 2>&1; then
  useradd --system --gid "${APP_GROUP}" --home-dir "${APP_DIR}" --shell /usr/sbin/nologin "${APP_USER}"
fi

mkdir -p "${APP_DIR}" "${DATA_DIR}" "${LOG_DIR}"
chown -R "${APP_USER}:${APP_GROUP}" "${APP_DIR}" "${DATA_DIR}" "${LOG_DIR}"

if [ ! -x "${VENV_DIR}/bin/python" ]; then
  sudo -u "${APP_USER}" "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install --upgrade pip wheel setuptools

if [ "${DATABASE_BACKEND}" = "postgresql" ]; then
  if [ -z "${POSTGRES_PASSWORD}" ]; then
    echo "ERROR: Define POSTGRES_PASSWORD para inicializar PostgreSQL."
    exit 1
  fi

  systemctl enable postgresql
  systemctl start postgresql

  sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${POSTGRES_USER}'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER ${POSTGRES_USER} WITH PASSWORD '${POSTGRES_PASSWORD}';"

  sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${POSTGRES_DB}'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER};"

  sudo -u postgres psql -c "ALTER ROLE ${POSTGRES_USER} SET client_encoding TO 'utf8';"
  sudo -u postgres psql -c "ALTER ROLE ${POSTGRES_USER} SET default_transaction_isolation TO 'read committed';"
  sudo -u postgres psql -c "ALTER ROLE ${POSTGRES_USER} SET timezone TO 'UTC';"
fi

cat >/usr/local/bin/sipet-restart <<EOF
#!/usr/bin/env bash
set -euo pipefail
systemctl restart ${SERVICE_NAME}
systemctl --no-pager --full status ${SERVICE_NAME} || true
EOF
chmod 755 /usr/local/bin/sipet-restart

cat >/etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=SIPET FastAPI
After=network.target

[Service]
Type=simple
User=${APP_USER}
Group=${APP_GROUP}
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
Environment=PORT=${PORT}
ExecStart=${VENV_DIR}/bin/uvicorn fastapi_modulo.modulos_sipet.modulo_base.runtime:app --host 0.0.0.0 --port \${PORT}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"

echo "Bootstrap completado."
echo "APP_DIR=${APP_DIR}"
echo "DATA_DIR=${DATA_DIR}"
echo "VENV_DIR=${VENV_DIR}"
echo "SERVICE_NAME=${SERVICE_NAME}"
echo "DATABASE_BACKEND=${DATABASE_BACKEND}"
