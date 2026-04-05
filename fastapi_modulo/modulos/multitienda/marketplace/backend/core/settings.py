from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_MODULE_ROOT = Path(__file__).resolve().parents[3]
_ENV_PATH = _MODULE_ROOT / ".env"

load_dotenv(_ENV_PATH, override=False)


def get_secret_key() -> str:
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise RuntimeError(
            "SECRET_KEY no esta definida. Configurala en el entorno o en multitienda/.env."
        )
    return secret_key


__all__ = ["get_secret_key"]
