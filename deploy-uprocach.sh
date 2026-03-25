#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/.deploy-uprocach.env" ]; then
  set -a
  # Archivo local con credenciales/host del deploy de Uprocach.
  . "${SCRIPT_DIR}/.deploy-uprocach.env"
  set +a
fi
exec "${SCRIPT_DIR}/deploy/aliases/deploy-uprocach.sh" "$@"
