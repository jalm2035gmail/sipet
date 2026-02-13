from typing import Any, Dict, Optional


class ApiResponseTemplate:
    """Utilitarios para dar forma a las respuestas API."""

    @staticmethod
    def success(
        data: Any = None,
        message: str = "Operación exitosa",
        status_code: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"success": True, "data": data, "message": message}
        meta = dict(metadata or {})
        if status_code:
            meta.setdefault("status_code", status_code)
        if meta:
            payload["metadata"] = meta
        return payload

    @staticmethod
    def paginated(
        data: Any,
        total: int,
        skip: int,
        limit: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "success": True,
            "data": data,
            "total": total,
            "skip": skip,
            "limit": limit,
        }
        if metadata:
            payload["metadata"] = metadata
        return payload

    @staticmethod
    def error(detail: str, status_code: int, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "success": False,
            "detail": detail,
            "status_code": status_code,
        }
        if metadata:
            payload["metadata"] = metadata
        return payload
