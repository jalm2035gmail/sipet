from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from datetime import datetime

# Engine y SessionLocal
engine = create_engine('sqlite:///app.db', echo=False)
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
