from __future__ import annotations

from pathlib import Path
import re

_ROOT_RELATIVE_URL_PATTERN = re.compile(r'(?P<prefix>(?:href|src|action)=["\']|url\(["\']?)\/(?!\/|static\/|multitienda\/)')
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "marketplace" / "backend" / "templates" / "multitienda"


def load_multitienda_template(name: str) -> str:
    return (_TEMPLATES_DIR / name).read_text(encoding="utf-8")


def _prefix_root_relative_urls(content: str, root_path: str) -> str:
    normalized_root = (root_path or "").rstrip("/")
    if not normalized_root:
        return content
    return _ROOT_RELATIVE_URL_PATTERN.sub(lambda match: f"{match.group('prefix')}{normalized_root}/", content)
