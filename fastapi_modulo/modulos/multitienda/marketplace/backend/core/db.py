import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from fastapi_modulo.core import db as sipet_db


def _resolve_database_url() -> str:
    explicit = str(os.getenv("DATABASE_URL") or "").strip()
    if explicit:
        return explicit
    try:
        current = sipet_db.get_current_dataMAIN_info().get("url", "").strip()
        if current:
            return current
    except Exception:
        pass
    return "sqlite:///./base_datos/multitienda.db"


DATABASE_URL = _resolve_database_url()
IS_SQLITE = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if IS_SQLITE else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    return SessionLocal()
