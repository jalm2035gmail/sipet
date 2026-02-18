from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.base import Base

def _normalize_database_url(raw_url: str) -> str:
    db_url = (raw_url or "").strip()
    if db_url.startswith("postgres://"):
        return db_url.replace("postgres://", "postgresql://", 1)
    return db_url


DATABASE_URL = _normalize_database_url(settings.DATABASE_URL)
IS_SQLITE_DATABASE = DATABASE_URL.startswith("sqlite:///")

# Crear engine con soporte SQLite (asegura hilo único) o Postgres
engine_kwargs = {"connect_args": {"check_same_thread": False}} if IS_SQLITE_DATABASE else {}
engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    """Dependencia FastAPI para obtener una sesión de DB."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


__all__ = ["engine", "Base", "get_db"]
