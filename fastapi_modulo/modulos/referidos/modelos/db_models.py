from __future__ import annotations

import enum
import random
import string
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
    inspect,
    text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from fastapi_modulo.core.db import MAIN, get_current_engine

class BlacklistReferido(MAIN):
    """Blacklist de referidos y referentes por motivos de exclusión o fraude."""
    __tablename__ = "ref_blacklist"
    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(50), index=True)
    email = Column(String(255), index=True)
    motivo = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    created_by = Column(Integer, nullable=True)

class RevisionManual(MAIN):
    """Cola de revisión manual de referidos sospechosos o excluidos."""
    __tablename__ = "ref_revision_manual"
    id = Column(Integer, primary_key=True, autoincrement=True)
    referido_id = Column(Integer, ForeignKey("ref_referido.id"), nullable=False)
    motivo = Column(String(255))
    estado = Column(String(20), default="pendiente")  # pendiente, revisado, descartado
    created_at = Column(DateTime, default=func.now())
    reviewed_by = Column(Integer, nullable=True)
class ReferidoState(enum.Enum):
    draft = "draft"
    qualified = "qualified"
    converted = "converted"
    paid = "paid"
    rejected = "rejected"

class AmbassadorState(enum.Enum):
    active = "active"
    suspended = "suspended"
    blocked = "blocked"
    inactive = "inactive"

class AmbassadorRequestState(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

# Enum de roles para acceso a negocio
class BusinessRole(enum.Enum):
    admin_global = "admin_global"
    admin_negocio = "admin_negocio"
    operador = "operador"
    embajador = "embajador"


# Relación muchos-a-muchos usuario-negocio con rol
class RefUserBusinessAccess(MAIN):
    __tablename__ = "ref_user_business_access"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    business_id = Column(Integer, ForeignKey("ref_program_assignment.id"), nullable=False, index=True)
    role = Column(SAEnum(BusinessRole), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    business = relationship("RefProgramAssignment", backref="user_accesses")


def _gen_miu_code() -> str:
    """Genera un código MIU único: CGT + 5 caracteres alfanuméricos."""
    chars = string.ascii_uppercase + string.digits
    return "CGT" + "".join(random.choices(chars, k=5))


class RefReferente(MAIN):
    """Socio Referente: persona que refiere nuevos prospectos."""
    __tablename__ = "ref_referente"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    email = Column(String(255), index=True)
    phone = Column(String(50), index=True)
    miu_code = Column(String(20), unique=True, nullable=False, index=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    referidos = relationship("RefReferido", back_populates="referente", cascade="all, delete-orphan")


class RefIncentivo(MAIN):
    """Regla de incentivo/beneficio del programa."""
    __tablename__ = "ref_incentivo"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    beneficio = Column(String(255))
    active = Column(Boolean, default=True)
    incentive_type = Column(String(20), default="percent")  # percent | absolute | social
    percentage_value = Column(Float, default=0.0)
    fixed_value = Column(Numeric(12, 2), default=0)
    social_benefit = Column(String(500))
    apply_to = Column(String(20), default="all")  # all | product
    product_name = Column(String(255))
    min_amount = Column(Numeric(12, 2), default=0)
    max_amount = Column(Numeric(12, 2), default=0)
    min_date = Column(Date)
    max_date = Column(Date)
    partner_segment = Column(String(20))   # new | existing | vip
    scenario_type = Column(String(20), default="generic")  # generic | credit | commerce | health
    state_required = Column(String(20), default="converted")  # converted | paid
    program_assignment_id = Column(Integer, ForeignKey("ref_program_assignment.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())


class RefConfiguracion(MAIN):
    """Configuración global del programa de referidos."""
    __tablename__ = "ref_configuracion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, default="Parámetros del Programa")
    is_active = Column(Boolean, default=True)
    ca_description = Column(Text)
    incentive_rule_id = Column(Integer, ForeignKey("ref_incentivo.id"), nullable=True)
    validity_start = Column(Date)
    validity_end = Column(Date)
    kpi_target = Column(Float, default=0.0)
    scenario_type = Column(String(20), default="generic")
    use_whatsapp = Column(Boolean, default=False)
    use_sms = Column(Boolean, default=False)
    use_email = Column(Boolean, default=True)
    whatsapp_webhook_url = Column(String(500))
    sms_webhook_url = Column(String(500))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class RefReferido(MAIN):
    """Prospecto Referido: ciclo de vida completo del referido."""
    __tablename__ = "ref_referido"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cvr_code = Column(String(20), unique=True, index=True)  # CVR202500001
    ambassador_code = Column(String(50), index=True)  # Código embajador
    program_assignment_id = Column(Integer, ForeignKey("ref_program_assignment.id"), nullable=True, index=True)
    referente_id = Column(Integer, ForeignKey("ref_referente.id"), nullable=False)
    referente_miu = Column(String(20), index=True)
    nombre_prospecto = Column(String(255), nullable=False)
    email = Column(String(255), index=True)
    phone = Column(String(50), index=True)
    referral_source = Column(String(20), default="web")  # web | app | manual
    campaign_id = Column(Integer, ForeignKey("ref_campaign.id"), nullable=True)
    ip_address = Column(String(50))
    device_info = Column(String(255))
    channel = Column(String(50))
    conversion_evidence = Column(String(500))
    state = Column(SAEnum(ReferidoState), default=ReferidoState.draft, index=True, nullable=False)
    ca_met = Column(Boolean, default=False)
    conversion_date = Column(DateTime)
    product_acquired = Column(String(255))
    conversion_amount = Column(Numeric(12, 2), default=0)
    incentive_amount = Column(Numeric(12, 2), default=0)
    incentive_rule_id = Column(Integer, ForeignKey("ref_incentivo.id"), nullable=True)
    incentive_paid_date = Column(DateTime)
    approved_by = Column(Integer, nullable=True)  # user_id que aprobó/pagó
    ambassador_id = Column(Integer, ForeignKey("ref_brand_ambassador.id"), nullable=True)
    is_excluded = Column(Boolean, default=False)
    exclusion_reason = Column(Text)
    fraud_flag = Column(Boolean, default=False)
    fraud_score = Column(Float, default=0.0)
    fraud_reason = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    referente = relationship("RefReferente", back_populates="referidos")
    program_assignment = relationship("RefProgramAssignment", foreign_keys=[program_assignment_id])
    incentive_rule = relationship("RefIncentivo", foreign_keys=[incentive_rule_id])
    tracking_events = relationship("RefTrackingEvent", back_populates="referido", cascade="all, delete-orphan")
    registros = relationship("RefRegistro", back_populates="referido", cascade="all, delete-orphan")


class RefTrackingEvent(MAIN):
    """Historial de eventos / auditoría de un referido."""
    __tablename__ = "ref_tracking_event"

    id = Column(Integer, primary_key=True, autoincrement=True)
    referido_id = Column(Integer, ForeignKey("ref_referido.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(500), nullable=False)
    event_type = Column(String(20), default="note")  # note | state_change | ca | payment
    old_state = Column(String(20))
    new_state = Column(String(20))
    ca_met = Column(Boolean, default=False)
    incentive_amount = Column(Numeric(12, 2), default=0)
    user_id = Column(Integer)
    created_at = Column(DateTime, default=func.now())

    referido = relationship("RefReferido", back_populates="tracking_events")


class RefRegistro(MAIN):
    """Notas manuales y registros sobre un referido."""
    __tablename__ = "ref_registro"

    id = Column(Integer, primary_key=True, autoincrement=True)
    referido_id = Column(Integer, ForeignKey("ref_referido.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(500), nullable=False)
    note = Column(Text)
    event_date = Column(DateTime, default=func.now())
    user_id = Column(Integer)
    created_at = Column(DateTime, default=func.now())

    referido = relationship("RefReferido", back_populates="registros")


class RefProgramAssignment(MAIN):
    """Asignación de usuario a un negocio con su programa de referidos."""
    __tablename__ = "ref_program_assignment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    business_name = Column(String(255))
    business_slug = Column(String(255), index=True)
    website_url = Column(String(500))
    business_type = Column(String(50))  # credit | commerce | health | generic
    max_referrals = Column(Integer, default=0)
    commission_rate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    incentivos = relationship("RefIncentivo", back_populates=None, foreign_keys="RefIncentivo.program_assignment_id")
    ambassadors = relationship("RefBrandAmbassador", back_populates="business", cascade="all, delete-orphan")
    ambassador_requests = relationship("RefAmbassadorRequest", back_populates="business", cascade="all, delete-orphan")


class RefBrandAmbassador(MAIN):
    """Embajador de Marca vinculado a un negocio."""
    __tablename__ = "ref_brand_ambassador"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    code = Column(String(20), unique=True, nullable=False, index=True)
    phone = Column(String(50))
    street = Column(String(500))
    business_id = Column(Integer, ForeignKey("ref_program_assignment.id"), nullable=False)
    state = Column(SAEnum(AmbassadorState), default=AmbassadorState.active, nullable=False)
    created_at = Column(DateTime, default=func.now())
    @property
    def referral_link(self):
        # Link personalizado para el embajador
        return f"/referral/amb/{self.code}"
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    business = relationship("RefProgramAssignment", back_populates="ambassadors")
    referidos = relationship("RefReferido", foreign_keys="RefReferido.ambassador_id")


class RefAmbassadorRequest(MAIN):
    """Solicitud pública para convertirse en embajador de marca."""
    __tablename__ = "ref_ambassador_request"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    consent = Column(Boolean, default=False)
    business_name = Column(String(255), nullable=False)
    business_slug = Column(String(255))
    business_id = Column(Integer, ForeignKey("ref_program_assignment.id"), nullable=True)
    state = Column(SAEnum(AmbassadorRequestState), default=AmbassadorRequestState.pending, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    business = relationship("RefProgramAssignment", back_populates="ambassador_requests")


def ensure_referidos_schema(bind=None) -> None:
    target = bind or get_current_engine()
    RefReferente.__table__.create(bind=target, checkfirst=True)
    RefProgramAssignment.__table__.create(bind=target, checkfirst=True)
    RefIncentivo.__table__.create(bind=target, checkfirst=True)
    RefConfiguracion.__table__.create(bind=target, checkfirst=True)
    RefBrandAmbassador.__table__.create(bind=target, checkfirst=True)
    RefAmbassadorRequest.__table__.create(bind=target, checkfirst=True)
    RefReferido.__table__.create(bind=target, checkfirst=True)
    RefTrackingEvent.__table__.create(bind=target, checkfirst=True)
    RefRegistro.__table__.create(bind=target, checkfirst=True)
    RefUserBusinessAccess.__table__.create(bind=target, checkfirst=True)
    # Integración nuevas tablas
    try:
        from fastapi_modulo.modulos.referidos.modelos.campaign import RefCampaign
        from fastapi_modulo.modulos.referidos.modelos.settlement import RefSettlement
        RefCampaign.__table__.create(bind=target, checkfirst=True)
        RefSettlement.__table__.create(bind=target, checkfirst=True)
    except Exception as e:
        print(f"[referidos] warning al crear tablas campaign/settlement: {e}")
    inspector = inspect(target)
    referido_columns = {column["name"] for column in inspector.get_columns("ref_referido")}
    if "program_assignment_id" not in referido_columns:
        with target.begin() as conn:
            conn.execute(text("ALTER TABLE ref_referido ADD COLUMN program_assignment_id INTEGER"))
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_ref_referido_program_assignment_id "
                    "ON ref_referido (program_assignment_id)"
                )
            )
