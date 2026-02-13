from typing import Any, Dict, Optional


class ButtonTemplate:
    """Constantes para generar botones coherentes en la interfaz."""

    @staticmethod
    def _build(label: str, style: str, url: Optional[str] = None, action: Optional[str] = None, confirmation: bool = False, **extra: Any) -> Dict[str, Any]:
        button = {
            "label": label,
            "style": style,
            "url": url,
            "action": action,
            "confirmation": confirmation,
        }
        button.update({k: v for k, v in extra.items() if v is not None})
        return button

    @staticmethod
    def primary(label: str, url: Optional[str] = None, action: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        return ButtonTemplate._build(label, "primary", url, action, **extra)

    @staticmethod
    def secondary(label: str, url: Optional[str] = None, action: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        return ButtonTemplate._build(label, "secondary", url, action, **extra)

    @staticmethod
    def success(label: str, url: Optional[str] = None, action: Optional[str] = None, confirmation: bool = False, **extra: Any) -> Dict[str, Any]:
        return ButtonTemplate._build(label, "success", url, action, confirmation, **extra)

    @staticmethod
    def warning(label: str, url: Optional[str] = None, action: Optional[str] = None, confirmation: bool = False, **extra: Any) -> Dict[str, Any]:
        return ButtonTemplate._build(label, "warning", url, action, confirmation, **extra)

    @staticmethod
    def danger(label: str, url: Optional[str] = None, action: Optional[str] = None, confirmation: bool = True, **extra: Any) -> Dict[str, Any]:
        return ButtonTemplate._build(label, "danger", url, action, confirmation, **extra)

    @staticmethod
    def info(label: str, url: Optional[str] = None, action: Optional[str] = None, **extra: Any) -> Dict[str, Any]:
        return ButtonTemplate._build(label, "info", url, action, **extra)
