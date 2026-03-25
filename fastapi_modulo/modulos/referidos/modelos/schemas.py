from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal

from pydantic import BaseModel, field_validator


# ──────────────────────────────── Referente ────────────────────────────────

class ReferenteCreate(BaseModel):
    nombre: str
    email: Optional[str] = None
    phone: Optional[str] = None


class ReferenteRead(ReferenteCreate):
    id: int
    miu_code: str
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ──────────────────────────────── Incentivo ────────────────────────────────

class IncentivoCreate(BaseModel):
    name: str
    beneficio: Optional[str] = None
    incentive_type: str = "percent"
    percentage_value: float = 0.0
    fixed_value: Decimal = Decimal("0")
    social_benefit: Optional[str] = None
    apply_to: str = "all"
    product_name: Optional[str] = None
    min_amount: Decimal = Decimal("0")
    max_amount: Decimal = Decimal("0")
    min_date: Optional[date] = None
    max_date: Optional[date] = None
    partner_segment: Optional[str] = None
    scenario_type: str = "generic"
    state_required: str = "converted"
    program_assignment_id: Optional[int] = None


class IncentivoRead(IncentivoCreate):
    id: int
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ──────────────────────────────── Configuracion ────────────────────────────

class ConfiguracionUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    ca_description: Optional[str] = None
    incentive_rule_id: Optional[int] = None
    validity_start: Optional[date] = None
    validity_end: Optional[date] = None
    kpi_target: Optional[float] = None
    scenario_type: Optional[str] = None
    use_whatsapp: Optional[bool] = None
    use_sms: Optional[bool] = None
    use_email: Optional[bool] = None
    whatsapp_webhook_url: Optional[str] = None
    sms_webhook_url: Optional[str] = None


class ConfiguracionRead(BaseModel):
    id: int
    name: str
    is_active: bool
    ca_description: Optional[str]
    incentive_rule_id: Optional[int]
    validity_start: Optional[date]
    validity_end: Optional[date]
    kpi_target: float
    scenario_type: str
    use_whatsapp: bool
    use_sms: bool
    use_email: bool
    whatsapp_webhook_url: Optional[str]
    sms_webhook_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ──────────────────────────────── Referido ────────────────────────────────

class ReferidoCreate(BaseModel):
    referente_id: int
    nombre_prospecto: str
    email: Optional[str] = None
    phone: Optional[str] = None
    referral_source: str = "web"
    product_acquired: Optional[str] = None
    ambassador_id: Optional[int] = None


class ReferidoUpdate(BaseModel):
    nombre_prospecto: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    product_acquired: Optional[str] = None
    conversion_amount: Optional[Decimal] = None
    incentive_rule_id: Optional[int] = None


class ReferidoRead(BaseModel):
    id: int
    cvr_code: str
    referente_id: int
    referente_miu: Optional[str]
    nombre_prospecto: str
    email: Optional[str]
    phone: Optional[str]
    referral_source: str
    state: str
    ca_met: bool
    conversion_date: Optional[datetime]
    product_acquired: Optional[str]
    conversion_amount: Decimal
    incentive_amount: Decimal
    incentive_rule_id: Optional[int]
    incentive_paid_date: Optional[datetime]
    ambassador_id: Optional[int]
    is_excluded: bool
    exclusion_reason: Optional[str]
    fraud_flag: bool
    fraud_score: float
    fraud_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConvertirReferidoInput(BaseModel):
    conversion_amount: Optional[Decimal] = None
    product_acquired: Optional[str] = None


class RechazarReferidoInput(BaseModel):
    reason: Optional[str] = None


# ──────────────────────────────── TrackingEvent ────────────────────────────

class TrackingEventRead(BaseModel):
    id: int
    referido_id: int
    name: str
    event_type: str
    old_state: Optional[str]
    new_state: Optional[str]
    ca_met: bool
    incentive_amount: Decimal
    user_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ──────────────────────────────── ProgramAssignment ────────────────────────

class ProgramAssignmentCreate(BaseModel):
    user_id: int
    business_name: Optional[str] = None
    business_type: str = "generic"
    website_url: Optional[str] = None
    max_referrals: int = 0
    commission_rate: float = 0.0


class ProgramAssignmentRead(ProgramAssignmentCreate):
    id: int
    business_slug: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ──────────────────────────────── BrandAmbassador ────────────────────────

class AmbassadorCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    street: Optional[str] = None
    business_id: int


class AmbassadorRead(AmbassadorCreate):
    id: int
    state: str
    created_at: datetime

    class Config:
        from_attributes = True


# ──────────────────────────────── AmbassadorRequest ────────────────────────

class AmbassadorRequestCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    consent: bool
    business_name: str
    business_slug: str
    business_id: Optional[int] = None


class AmbassadorRequestRead(AmbassadorRequestCreate):
    id: int
    state: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
