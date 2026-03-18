from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class BaseHTTPService:
    def __init__(
        self,
        *,
        base_url: str = "",
        timeout: float = 10.0,
        retries: int = 2,
        headers: dict[str, str] | None = None,
        auth: Any = None,
        client: Any = None,
    ) -> None:
        self.base_url = str(base_url or "").rstrip("/")
        self.timeout = float(timeout)
        self.retries = max(0, int(retries))
        self.headers = headers or {}
        self.auth = auth
        self.client = client

    # ── Utilidades ────────────────────────────────────────────────────────────

    def build_headers(self, headers: dict[str, str] | None = None) -> dict[str, str]:
        merged = {
            "Accept": "application/json",
            "User-Agent": "sipet-modulo-base-http/1.0",
            **self.headers,
        }
        if headers:
            merged.update(headers)
        return merged

    def build_url(self, path: str) -> str:
        normalized = str(path or "").strip()
        if normalized.startswith("http://") or normalized.startswith("https://"):
            return normalized
        if not self.base_url:
            return normalized
        return f"{self.base_url}/{normalized.lstrip('/')}"

    # ── Síncrono ──────────────────────────────────────────────────────────────

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | list[Any] | None = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        if httpx is None and self.client is None:
            raise HTTPException(status_code=500, detail="httpx no esta disponible.")
        url = self.build_url(path)
        request_headers = self.build_headers(headers)
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = self._send_request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    data=data,
                    headers=request_headers,
                )
                response.raise_for_status()
                payload = self._parse_json(response)
                logger.info(
                    "external_http_request",
                    extra={
                        "method": method,
                        "url": url,
                        "status_code": response.status_code,
                        "attempt": attempt + 1,
                    },
                )
                return {
                    "ok": True,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "data": payload,
                }
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "external_http_request_failed",
                    extra={
                        "method": method,
                        "url": url,
                        "attempt": attempt + 1,
                        "error": str(exc),
                    },
                )
                if attempt >= self.retries:
                    break
        raise self._map_error(last_error)

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return self.request("GET", path, params=params, headers=headers)

    def post(
        self,
        path: str,
        *,
        json: dict[str, Any] | list[Any] | None = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return self.request("POST", path, json=json, data=data, headers=headers)

    def put(
        self,
        path: str,
        *,
        json: dict[str, Any] | list[Any] | None = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return self.request("PUT", path, json=json, data=data, headers=headers)

    def patch(
        self,
        path: str,
        *,
        json: dict[str, Any] | list[Any] | None = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return self.request("PATCH", path, json=json, data=data, headers=headers)

    def delete(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return self.request("DELETE", path, params=params, headers=headers)

    def _send_request(self, **kwargs: Any) -> Any:
        if self.client is not None:
            return self.client.request(timeout=self.timeout, auth=self.auth, **kwargs)
        with httpx.Client(
            timeout=self.timeout,
            headers=self.headers,
            auth=self.auth,
            follow_redirects=True,
        ) as client:
            return client.request(**kwargs)

    # ── Asíncrono ─────────────────────────────────────────────────────────────

    async def request_async(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | list[Any] | None = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        if httpx is None:
            raise HTTPException(status_code=500, detail="httpx no esta disponible.")
        url = self.build_url(path)
        request_headers = self.build_headers(headers)
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    headers=self.headers,
                    auth=self.auth,
                    follow_redirects=True,
                ) as client:
                    response = await client.request(
                        method,
                        url,
                        params=params,
                        json=json,
                        data=data,
                        headers=request_headers,
                    )
                response.raise_for_status()
                payload = self._parse_json(response)
                logger.info(
                    "external_http_request_async",
                    extra={
                        "method": method,
                        "url": url,
                        "status_code": response.status_code,
                        "attempt": attempt + 1,
                    },
                )
                return {
                    "ok": True,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "data": payload,
                }
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "external_http_request_async_failed",
                    extra={
                        "method": method,
                        "url": url,
                        "attempt": attempt + 1,
                        "error": str(exc),
                    },
                )
                if attempt >= self.retries:
                    break
        raise self._map_error(last_error)

    async def get_async(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return await self.request_async("GET", path, params=params, headers=headers)

    async def post_async(
        self,
        path: str,
        *,
        json: dict[str, Any] | list[Any] | None = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return await self.request_async("POST", path, json=json, data=data, headers=headers)

    async def put_async(
        self,
        path: str,
        *,
        json: dict[str, Any] | list[Any] | None = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return await self.request_async("PUT", path, json=json, data=data, headers=headers)

    async def patch_async(
        self,
        path: str,
        *,
        json: dict[str, Any] | list[Any] | None = None,
        data: Any = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return await self.request_async("PATCH", path, json=json, data=data, headers=headers)

    async def delete_async(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return await self.request_async("DELETE", path, params=params, headers=headers)

    # ── Helpers internos ──────────────────────────────────────────────────────

    @staticmethod
    def _parse_json(response: Any) -> Any:
        try:
            return response.json()
        except Exception:
            return response.text

    @staticmethod
    def _map_error(exc: Exception | None) -> HTTPException:
        if exc is None:
            return HTTPException(status_code=502, detail="Error desconocido de integracion externa.")
        if httpx is not None and isinstance(exc, httpx.TimeoutException):
            return HTTPException(status_code=504, detail="Timeout en integracion externa.")
        if httpx is not None and isinstance(exc, httpx.HTTPStatusError):
            status_code = int(exc.response.status_code)
            detail = f"Error remoto {status_code}."
            return HTTPException(status_code=502 if status_code >= 500 else 424, detail=detail)
        if httpx is not None and isinstance(exc, httpx.RequestError):
            return HTTPException(status_code=502, detail="Fallo de conectividad con servicio externo.")
        return HTTPException(status_code=502, detail=str(exc))


__all__ = ["BaseHTTPService"]
