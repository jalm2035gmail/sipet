from __future__ import annotations

import os

EDITOR_ENABLED = (os.environ.get("WEB_BACKEND_EDITOR_ENABLED") or "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


def backend_visual_editor_config() -> dict:
    return {
        "enabled": EDITOR_ENABLED,
        "provider": "grapesjs" if EDITOR_ENABLED else "",
        "scopes": [
            "backend_home",
            "dashboard_inicial",
            "banners_institucionales",
            "widgets_landing_interno",
        ],
    }
