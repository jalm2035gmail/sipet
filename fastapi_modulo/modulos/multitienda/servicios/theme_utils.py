from __future__ import annotations

import json


def decode_theme(raw_value) -> dict:
    current = raw_value
    for _ in range(3):
        if isinstance(current, dict):
            return current
        if not isinstance(current, str):
            return {}
        try:
            current = json.loads(current)
        except json.JSONDecodeError:
            return {}
    return {}
