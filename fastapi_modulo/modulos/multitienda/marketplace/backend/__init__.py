from __future__ import annotations

import sys

from . import apps as _apps
from . import core as _core

sys.modules.setdefault("backend", sys.modules[__name__])
sys.modules.setdefault("apps", _apps)
sys.modules.setdefault("core", _core)

__all__ = []
