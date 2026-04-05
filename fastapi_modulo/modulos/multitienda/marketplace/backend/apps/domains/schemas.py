from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel


class VendorDomainCreate(BaseModel):
    subdomain: str
    custom_domain: Optional[str] = None
    force_ssl: Optional[bool] = True
    redirect_to_subdomain: Optional[bool] = False


class VendorDomainUpdate(BaseModel):
    custom_domain: Optional[str] = None
    force_ssl: Optional[bool] = None
    redirect_to_subdomain: Optional[bool] = None
    status: Optional[str] = None


class VendorDomainRead(BaseModel):
    id: int
    vendor_id: int
    subdomain: str
    custom_domain: Optional[str] = None
    status: str
    verification_token: Optional[str] = None
    force_ssl: bool
    redirect_to_subdomain: bool
    hits: int
    ssl_expires_at: Optional[str] = None
    last_dns_check: Optional[str] = None
    verified_at: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class DomainRequestCreate(BaseModel):
    requested_domain: str
    purpose: Optional[str] = ""
    contact_name: str
    contact_email: str
    contact_phone: Optional[str] = ""


class DomainRequestReview(BaseModel):
    status: str  # approved / rejected
    review_notes: Optional[str] = ""
    rejection_reason: Optional[str] = ""


class DomainRequestRead(BaseModel):
    id: int
    vendor_id: int
    requested_domain: str
    contact_name: str
    contact_email: str
    status: str
    review_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: Optional[str] = None
    reviewed_at: Optional[str] = None

    class Config:
        from_attributes = True
