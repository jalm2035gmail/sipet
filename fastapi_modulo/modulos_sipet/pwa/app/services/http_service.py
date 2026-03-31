import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


# ── Sync client (uso puntual) ─────────────────────────────────────────────────

def get(url: str, params: dict | None = None, headers: dict | None = None) -> dict:
    with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
        r = client.get(url, params=params, headers=headers)
        r.raise_for_status()
        return r.json()


def post(url: str, json: dict | None = None, headers: dict | None = None) -> dict:
    with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
        r = client.post(url, json=json, headers=headers)
        r.raise_for_status()
        return r.json()


# ── Async client (para usar dentro de endpoints async de FastAPI) ──────────────

async def async_get(url: str, params: dict | None = None, headers: dict | None = None) -> Any:
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        r = await client.get(url, params=params, headers=headers)
        r.raise_for_status()
        return r.json()


async def async_post(url: str, json: dict | None = None, headers: dict | None = None) -> Any:
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        r = await client.post(url, json=json, headers=headers)
        r.raise_for_status()
        return r.json()


# ── Webhook dispatcher ────────────────────────────────────────────────────────

async def send_webhook(url: str, payload: dict, secret: str | None = None) -> bool:
    headers = {"Content-Type": "application/json"}
    if secret:
        import hmac, hashlib, json
        body = json.dumps(payload, separators=(",", ":")).encode()
        sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        headers["X-Signature-SHA256"] = f"sha256={sig}"

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            logger.info("Webhook sent to %s — status %s", url, r.status_code)
            return True
    except httpx.HTTPError as exc:
        logger.error("Webhook failed to %s: %s", url, exc)
        return False
