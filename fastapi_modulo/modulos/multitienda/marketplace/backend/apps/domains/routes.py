from __future__ import annotations

import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.dependencies import require_role
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.domains.models import (
    DomainRequest,
    VendorDomain,
)
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.domains.schemas import (
    DomainRequestCreate,
    DomainRequestReview,
    VendorDomainCreate,
    VendorDomainUpdate,
)

router = APIRouter(tags=["domains"])


def _serialize_domain(d: VendorDomain) -> dict:
    return {
        "id": d.id,
        "vendor_id": d.vendor_id,
        "subdomain": d.subdomain,
        "custom_domain": d.custom_domain,
        "status": d.status,
        "verification_token": d.verification_token,
        "force_ssl": d.force_ssl,
        "redirect_to_subdomain": d.redirect_to_subdomain,
        "hits": d.hits,
        "ssl_expires_at": d.ssl_expires_at.isoformat() if d.ssl_expires_at else None,
        "last_dns_check": d.last_dns_check.isoformat() if d.last_dns_check else None,
        "verified_at": d.verified_at.isoformat() if d.verified_at else None,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


def _serialize_request(r: DomainRequest) -> dict:
    return {
        "id": r.id,
        "vendor_id": r.vendor_id,
        "requested_domain": r.requested_domain,
        "purpose": r.purpose,
        "contact_name": r.contact_name,
        "contact_email": r.contact_email,
        "contact_phone": r.contact_phone,
        "status": r.status,
        "review_notes": r.review_notes,
        "rejection_reason": r.rejection_reason,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
    }


# ─── Dominio de la tienda ────────────────────────────────────────────────────

@router.get("/domains/my")
def get_my_domain(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("vendor")),
):
    domain = db.query(VendorDomain).filter(
        VendorDomain.vendor_id == current_user.vendor_id
    ).first()
    if not domain:
        return {"domain": None}
    return {"domain": _serialize_domain(domain)}


@router.post("/domains/my", status_code=201)
def create_my_domain(
    body: VendorDomainCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("vendor")),
):
    existing = db.query(VendorDomain).filter(
        VendorDomain.vendor_id == current_user.vendor_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ya tienes un dominio configurado. Usa PUT para actualizar.")

    conflict_sub = db.query(VendorDomain).filter(VendorDomain.subdomain == body.subdomain).first()
    if conflict_sub:
        raise HTTPException(status_code=409, detail="El subdominio ya está en uso.")

    domain = VendorDomain(
        vendor_id=current_user.vendor_id,
        subdomain=body.subdomain.strip().lower(),
        custom_domain=body.custom_domain,
        force_ssl=body.force_ssl if body.force_ssl is not None else True,
        redirect_to_subdomain=body.redirect_to_subdomain or False,
        verification_token=secrets.token_urlsafe(24),
        status="pending",
    )
    db.add(domain)
    db.commit()
    db.refresh(domain)
    return _serialize_domain(domain)


@router.put("/domains/my")
def update_my_domain(
    body: VendorDomainUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("vendor")),
):
    domain = db.query(VendorDomain).filter(
        VendorDomain.vendor_id == current_user.vendor_id
    ).first()
    if not domain:
        raise HTTPException(status_code=404, detail="No tienes un dominio configurado.")

    if body.custom_domain is not None:
        domain.custom_domain = body.custom_domain or None
    if body.force_ssl is not None:
        domain.force_ssl = body.force_ssl
    if body.redirect_to_subdomain is not None:
        domain.redirect_to_subdomain = body.redirect_to_subdomain
    domain.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(domain)
    return _serialize_domain(domain)


@router.post("/domains/my/verify")
def verify_domain(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("vendor")),
):
    """Marca el dominio como verificado (el check real del DNS lo haría un worker)."""
    domain = db.query(VendorDomain).filter(
        VendorDomain.vendor_id == current_user.vendor_id
    ).first()
    if not domain:
        raise HTTPException(status_code=404, detail="No tienes un dominio configurado.")
    domain.status = "active"
    domain.verified_at = datetime.utcnow()
    domain.last_dns_check = datetime.utcnow()
    db.commit()
    return {"status": domain.status, "verified_at": domain.verified_at.isoformat()}


# ─── Solicitudes de dominio (admin) ──────────────────────────────────────────

@router.get("/domains/requests")
def list_domain_requests(
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("superadmin")),
):
    q = db.query(DomainRequest)
    if status:
        q = q.filter(DomainRequest.status == status)
    total = q.count()
    items = q.order_by(DomainRequest.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": [_serialize_request(r) for r in items]}


@router.post("/domains/requests", status_code=201)
def submit_domain_request(
    body: DomainRequestCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("vendor")),
):
    req = DomainRequest(
        vendor_id=current_user.vendor_id,
        requested_domain=body.requested_domain.strip().lower(),
        purpose=body.purpose or "",
        contact_name=body.contact_name,
        contact_email=body.contact_email,
        contact_phone=body.contact_phone or "",
        status="pending",
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return _serialize_request(req)


@router.put("/domains/requests/{request_id}/review")
def review_domain_request(
    request_id: int,
    body: DomainRequestReview,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("superadmin")),
):
    req = db.query(DomainRequest).filter(DomainRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
    if body.status not in {"approved", "rejected"}:
        raise HTTPException(status_code=422, detail="status debe ser 'approved' o 'rejected'.")
    req.status = body.status
    req.review_notes = body.review_notes or ""
    req.rejection_reason = body.rejection_reason or ""
    req.reviewed_by_id = current_user.id
    req.reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(req)
    return _serialize_request(req)
