from typing import Any, Dict, List, Optional


class CardTemplate:
    """Generador de estructuras tipo tarjeta para dashboards/listados."""

    @staticmethod
    def basic(
        title: str,
        subtitle: Optional[str] = None,
        content: Optional[Dict[str, Any]] = None,
        actions: Optional[List[Dict[str, Any]]] = None,
        badges: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        return {
            "title": title,
            "subtitle": subtitle,
            "content": content or {},
            "actions": actions or [],
            "badges": badges or [],
        }
