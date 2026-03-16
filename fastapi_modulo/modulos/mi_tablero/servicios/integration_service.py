from __future__ import annotations

from typing import Any

import httpx


async def fetch_external_indicator(url: str, timeout: float = 5.0) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url)
        response.raise_for_status()
        content_type = str(response.headers.get("content-type") or "")
        payload: Any
        if "application/json" in content_type:
            payload = response.json()
        else:
            payload = {"text": response.text}
    return {
        "url": url,
        "status_code": response.status_code,
        "payload": payload,
    }
