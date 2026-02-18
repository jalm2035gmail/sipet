#!/bin/bash
# Script para reiniciar el sistema, cargar módulos y base de datos

# Activar entorno virtual .venv si existe
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Cargar variables de entorno desde .env (desarrollo local)
if [ -f ".env" ]; then
    set -a
    # shellcheck disable=SC1091
    source ".env"
    set +a
fi

# Fallback local para evitar que FastAPI falle al iniciar por secreto faltante
if [ -z "${AUTH_COOKIE_SECRET:-}" ]; then
    AUTH_COOKIE_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')
    export AUTH_COOKIE_SECRET
    echo "Aviso: AUTH_COOKIE_SECRET no estaba definida. Se generó una temporal para este reinicio."
fi

# Instalar dependencias
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# Migrar base de datos (ejemplo para Alembic)
if [ -d "fastapi_modulo" ] && [ -f "fastapi_modulo/alembic.ini" ]; then
    alembic upgrade head
fi

# Cargar módulos personalizados (placeholder)
# Aquí puedes agregar comandos para cargar módulos
# echo "Cargando módulos..."

# Reiniciar el sistema (FastAPI)
PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"
LOG_FILE="${LOG_FILE:-uvicorn.log}"

# Detener procesos previos
PID=$(lsof -ti:"$PORT")
if [ ! -z "$PID" ]; then
    echo "Matando proceso en el puerto $PORT (PID: $PID)"
    kill -9 $PID
fi

# Iniciar el servidor y guardar logs reales
echo "Iniciando servidor FastAPI en ${HOST}:${PORT}..."
uvicorn fastapi_modulo.main:app --host "$HOST" --port "$PORT" > "$LOG_FILE" 2>&1 &
sleep 3
lsof -i:"$PORT" > /dev/null
if [ $? -eq 0 ]; then
    echo "Servidor iniciado correctamente en ${HOST}:${PORT}."
else
    echo "Error: El servidor no se inició. Revisa $LOG_FILE para detalles."
    if [ -f "$LOG_FILE" ]; then
        echo "Ultimas lineas del log:"
        tail -n 40 "$LOG_FILE"
    fi
fi

echo "Sistema actualizado y reiniciado."
