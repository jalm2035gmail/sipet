import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from datetime import datetime

def _resolve_database_url() -> str:
    raw_url = (os.environ.get("DATABASE_URL") or "").strip()
    if raw_url:
        if raw_url.startswith("postgres://"):
            return raw_url.replace("postgres://", "postgresql://", 1)
        return raw_url
    app_env = (os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or "development").strip().lower()
    default_sqlite_name = f"strategic_planning_{app_env}.db"
    sqlite_db_path = (os.environ.get("SQLITE_DB_PATH") or default_sqlite_name).strip()
    return f"sqlite:///./{sqlite_db_path}"


DATABASE_URL = _resolve_database_url()
CONNECT_ARGS = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite:///") else {}

# Engine y SessionLocal
engine = create_engine(DATABASE_URL, connect_args=CONNECT_ARGS, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Modelo DepartamentoOrganizacional
from sqlalchemy.orm import declarative_base
Base = declarative_base()

class DepartamentoOrganizacional(Base):
    __tablename__ = "organizational_departments"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, default="")
    codigo = Column(String, unique=True, index=True, nullable=False, default="")
    padre = Column(String, default="N/A")
    responsable = Column(String, default="")
    color = Column(String, default="#1d4ed8")
    estado = Column(String, default="Activo")
    orden = Column(Integer, default=0, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
