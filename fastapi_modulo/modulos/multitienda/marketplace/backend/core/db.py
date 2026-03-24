from sqlalchemy.orm import declarative_base

from fastapi_modulo.core import db as sipet_db

Base = declarative_base()
engine = sipet_db.get_current_engine()
SessionLocal = sipet_db.SessionLocal


def get_db():
    db = sipet_db.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    return sipet_db.SessionLocal()
