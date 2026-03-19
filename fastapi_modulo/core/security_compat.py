from __future__ import annotations

from types import SimpleNamespace


def ensure_bcrypt_passlib_compat() -> None:
    """
    passlib 1.7.x intenta leer bcrypt.__about__.__version__.
    bcrypt 4.1+ y 5.x ya no exponen __about__, así que agregamos
    un shim mínimo para evitar el AttributeError.
    """
    try:
        import bcrypt  # type: ignore
    except Exception:
        return
    if hasattr(bcrypt, "__about__"):
        return
    version = getattr(bcrypt, "__version__", "")
    bcrypt.__about__ = SimpleNamespace(__version__=version)  # type: ignore[attr-defined]
