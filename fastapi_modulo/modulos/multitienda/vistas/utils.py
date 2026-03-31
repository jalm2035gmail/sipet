from __future__ import annotations

import re

_ROOT_RELATIVE_URL_PATTERN = re.compile(r'(?P<prefix>(?:href|src|action)=["\']|url\(["\']?)\/(?!\/)')


def _prefix_root_relative_urls(content: str, root_path: str) -> str:
    normalized_root = (root_path or "").rstrip("/")
    if not normalized_root:
        return content
    return _ROOT_RELATIVE_URL_PATTERN.sub(lambda match: f"{match.group('prefix')}{normalized_root}/", content)
