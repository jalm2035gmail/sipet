import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from datetime import datetime

def _resolve_database_url() -> str:
    raw_url = (
        os.environ.get("DATABASE_URL")
        or os.environ.get("POSTGRES_URL")
        or os.environ.get("POSTGRESQL_URL")
        or ""
    ).strip()
    if raw_url:
        if raw_url.startswith("postgres://"):
            return raw_url.replace("postgres://", "postgresql://", 1)
        return raw_url
    app_env = (os.environ.get("APP_ENV") or os.environ.get("ENVIRONMENT") or "development").strip().lower()
    is_railway = any(str(value or "").strip() for key, value in os.environ.items() if key.startswith("RAILWAY_"))
    is_prod_like = app_env in {"production", "prod"} or is_railway
    if is_prod_like:
        raise RuntimeError(
            "DATABASE_URL no está configurada en producción/Railway. "
            "Define DATABASE_URL (PostgreSQL) para evitar fallback a SQLite local."
        )
    default_sqlite_name = f"strategic_planning_{app_env}.db"
    sqlite_db_path = (os.environ.get("SQLITE_DB_PATH") or "").strip()
    if sqlite_db_path and os.path.basename(sqlite_db_path).lower() == "strategic_planning.db" and not is_prod_like:
        sqlite_db_path = default_sqlite_name
    data_dir = (os.environ.get("SIPET_DATA_DIR") or os.path.expanduser("~/.sipet/data")).strip()
    if not sqlite_db_path:
        os.makedirs(data_dir, exist_ok=True)
        sqlite_db_path = os.path.join(data_dir, default_sqlite_name)
    elif not os.path.isabs(sqlite_db_path):
        os.makedirs(data_dir, exist_ok=True)
        sqlite_db_path = os.path.join(data_dir, sqlite_db_path)
    if os.path.isabs(sqlite_db_path):
        return f"sqlite:///{sqlite_db_path}"
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


class RegionOrganizacional(Base):
    __tablename__ = "organizational_regions"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False, default="")
    codigo = Column(String, unique=True, index=True, nullable=False, default="")
    descripcion = Column(String, default="")
    orden = Column(Integer, default=0, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
