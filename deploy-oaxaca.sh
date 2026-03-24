#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export SERVER="${SERVER:-administrator@38.247.138.249}"

if [ -f "${SCRIPT_DIR}/.deploy-oaxaca.env" ]; then
  set -a
  . "${SCRIPT_DIR}/.deploy-oaxaca.env"
  set +a
fi

exec "${SCRIPT_DIR}/deploy/aliases/deploy-oaxaca.sh" "$@"
