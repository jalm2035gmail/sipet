from __future__ import annotations

import os
from pathlib import Path


GRAPESJS_ENABLED = (os.environ.get("MODULE_BASE_GRAPESJS_ENABLED") or "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


class VisualEditorContract:
    def __init__(self, module_root: str | Path, module_key: str) -> None:
        self.module_root = Path(module_root).resolve()
        self.module_key = str(module_key or "").strip()
        self.visual_root = self.module_root / "visual"
        self.landing_dir = self.visual_root / "landing"
        self.presentations_dir = self.visual_root / "presentations"
        self.widgets_dir = self.visual_root / "widgets"
        self.forms_dir = self.visual_root / "forms"

    def ensure_structure(self) -> None:
        self.landing_dir.mkdir(parents=True, exist_ok=True)
        self.presentations_dir.mkdir(parents=True, exist_ok=True)
        self.widgets_dir.mkdir(parents=True, exist_ok=True)
        self.forms_dir.mkdir(parents=True, exist_ok=True)

    def editor_config(self) -> dict[str, object]:
        return {
            "enabled": GRAPESJS_ENABLED,
            "provider": "grapesjs" if GRAPESJS_ENABLED else "",
            "module_key": self.module_key,
            "scopes": ["landing", "presentations", "widgets", "forms"],
            "storage": {
                "landing": str(self.landing_dir),
                "presentations": str(self.presentations_dir),
                "widgets": str(self.widgets_dir),
                "forms": str(self.forms_dir),
            },
        }

    def build_asset_manifest(self) -> dict[str, str]:
        return {
            "css": "/static/vendor/grapesjs/css/grapes.min.css",
            "js": "/static/vendor/grapesjs/grapes.min.js",
        }


__all__ = ["GRAPESJS_ENABLED", "VisualEditorContract"]
