from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw


def generate_widget_icon(widget_type: str, size: int = 96) -> bytes:
    palette = {
        "apps": ("#14532d", "#dcfce7"),
        "alerts": ("#7c2d12", "#ffedd5"),
        "analytics": ("#1d4ed8", "#dbeafe"),
        "tasks": ("#5b21b6", "#ede9fe"),
    }
    background, foreground = palette.get(widget_type, ("#0f172a", "#e2e8f0"))
    image = Image.new("RGB", (size, size), background)
    draw = ImageDraw.Draw(image)
    padding = max(10, size // 8)
    draw.rounded_rectangle(
        (padding, padding, size - padding, size - padding),
        radius=size // 6,
        outline=foreground,
        width=max(4, size // 18),
    )
    draw.line(
        (size * 0.3, size * 0.58, size * 0.46, size * 0.42, size * 0.7, size * 0.64),
        fill=foreground,
        width=max(5, size // 14),
        joint="curve",
    )
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def generate_dashboard_thumbnail(layout: dict, size: tuple[int, int] = (320, 180)) -> bytes:
    width, height = size
    image = Image.new("RGB", (width, height), "#f8fafc")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, width - 8, height - 8), radius=24, fill="#e2e8f0", outline="#cbd5e1")
    widgets = layout.get("widgets", [])
    colors = ["#14532d", "#1d4ed8", "#7c3aed", "#b45309"]
    for index, widget in enumerate(widgets):
        x = 24 + int(widget.get("x", 0)) * 56
        y = 24 + int(widget.get("y", 0)) * 44
        w = int(widget.get("w", 2)) * 44
        h = int(widget.get("h", 1)) * 32
        draw.rounded_rectangle(
            (x, y, min(width - 20, x + w), min(height - 20, y + h)),
            radius=16,
            fill=colors[index % len(colors)],
        )
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def build_default_widgets() -> list[dict]:
    return [
        {"key": "quick_access", "title": "Accesos rapidos", "enabled": True},
        {"key": "favorites", "title": "Apps favoritas", "enabled": True},
        {"key": "recent", "title": "Apps recientes", "enabled": True},
        {"key": "pinned", "title": "Apps fijadas", "enabled": True},
        {"key": "alerts", "title": "Alertas", "enabled": True},
        {"key": "indicators", "title": "Indicadores", "enabled": True},
        {"key": "tasks", "title": "Tareas pendientes", "enabled": True},
        {"key": "personal_stats", "title": "Estadisticas personales", "enabled": True},
        {"key": "ordering", "title": "Orden y drag drop", "enabled": True},
        {"key": "customization", "title": "Personalizacion", "enabled": True},
        {"key": "recommendations", "title": "Recomendaciones", "enabled": True},
        {"key": "role_suggestions", "title": "Sugeridas por rol", "enabled": True},
    ]
