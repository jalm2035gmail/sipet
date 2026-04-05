from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.models import User, UserType
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.users.routes import require_role
from fastapi_modulo.modulos.multitienda.marketplace.backend.apps.vendors import models, schemas
from fastapi_modulo.modulos.multitienda.marketplace.backend.core.db import get_db
from typing import List, Optional
import bcrypt
from pathlib import Path
import re
import secrets

_MODULE_ROOT = Path(__file__).resolve().parents[5]
_PRIVATE_UPLOAD_ROOT = _MODULE_ROOT / "private_storage" / "vendor_kyc"
_MAX_VENDOR_DOCUMENT_BYTES = 10 * 1024 * 1024
_ALLOWED_VENDOR_DOC_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
_ALLOWED_VENDOR_DOC_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
}
_ALLOWED_VENDOR_DOCUMENT_TYPES = {
    "ine",
    "pasaporte",
    "rfc",
    "constancia_fiscal",
    "comprobante_domicilio",
    "estado_cuenta",
    "acta_constitutiva",
    "curp",
    "otro",
}

router = APIRouter()


def _sanitize_vendor_document_type(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9_-]+", "_", str(value or "").strip().lower()).strip("_")
    if not normalized:
        raise HTTPException(status_code=400, detail="document_type invalido.")
    if normalized not in _ALLOWED_VENDOR_DOCUMENT_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de documento no permitido.")
    return normalized


def _safe_vendor_document_extension(filename: str) -> str:
    ext = Path(str(filename or "").strip()).suffix.lower()
    if ext not in _ALLOWED_VENDOR_DOC_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Extension de archivo no permitida.")
    return ext


def _matches_vendor_document_signature(content: bytes, ext: str) -> bool:
    if ext == ".pdf":
        return content.startswith(b"%PDF-")
    if ext == ".png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if ext in {".jpg", ".jpeg"}:
        return content.startswith(b"\xff\xd8\xff")
    return False


def _vendor_document_storage_key(store_id: int, internal_name: str) -> str:
    return f"vendor_kyc/{int(store_id)}/documents/{internal_name}"


def _vendor_document_storage_path(storage_key: str) -> Path:
    normalized = str(storage_key or "").strip().replace("\\", "/").lstrip("/")
    if ".." in normalized.split("/"):
        raise HTTPException(status_code=400, detail="Ruta de almacenamiento invalida.")
    path = (_PRIVATE_UPLOAD_ROOT / normalized.removeprefix("vendor_kyc/")).resolve()
    root = _PRIVATE_UPLOAD_ROOT.resolve()
    if root not in path.parents and path != root:
        raise HTTPException(status_code=400, detail="Ruta de almacenamiento invalida.")
    return path

# --- ADMIN ENDPOINTS ---

# Listar vendedores con filtros (solo superadmin)
@router.get("/admin/vendors/", response_model=List[schemas.VendorStoreRead])
def admin_list_vendors(
    status: Optional[str] = None,
    country: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(require_role("superadmin"))
):
    query = db.query(models.VendorStore)
    if status:
        query = query.filter(models.VendorStore.status == status)
    if country:
        query = query.filter(models.VendorStore.country == country)
    return query.all()

# Aprobar vendedores (masivo)
@router.post("/admin/vendors/approve/")
def approve_vendors(
    vendor_ids: List[int],
    db: Session = Depends(get_db),
    user=Depends(require_role("superadmin"))
):
    vendors = db.query(models.VendorStore).filter(models.VendorStore.id.in_(vendor_ids)).all()
    for vendor in vendors:
        vendor.status = "approved"
        vendor.is_active = True
        if vendor.vendor:
            vendor.vendor.is_active = True
        # TODO: enviar email de aprobación
    db.commit()
    return {"success": True, "count": len(vendors)}

# Rechazar vendedores (masivo)
@router.post("/admin/vendors/reject/")
def reject_vendors(
    vendor_ids: List[int],
    db: Session = Depends(get_db),
    user=Depends(require_role("superadmin"))
):
    vendors = db.query(models.VendorStore).filter(models.VendorStore.id.in_(vendor_ids)).all()
    for vendor in vendors:
        vendor.status = "rejected"
        vendor.is_active = False
        # TODO: enviar email de rechazo
    db.commit()
    return {"success": True, "count": len(vendors)}

# Ver documentos de un vendedor
@router.get("/admin/vendors/{vendor_id}/documents/", response_model=List[schemas.VendorDocumentRead])
def list_vendor_documents(
    vendor_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_role("superadmin"))
):
    docs = db.query(models.VendorDocument).filter_by(vendor_id=vendor_id).all()
    return docs

# Registro de vendedor (usuario + tienda, desactivados hasta aprobación)
@router.post("/register-vendor/")
def register_vendor(data: schemas.VendorRegistrationRequest, db: Session = Depends(get_db)):
    if db.query(User).filter_by(username=data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(User).filter_by(email=data.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    hashed_password = bcrypt.hashpw(data.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hashed_password,
        user_type=UserType.vendor,
        two_factor_enabled=data.two_factor_enabled,
        # first_name=data.first_name,  # Si tu modelo User lo soporta
        # last_name=data.last_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    store = models.VendorStore(
        vendor_id=user.id,
        store_name=data.store_name,
        phone=data.phone,
        address=data.address,
        country=data.country,
        status="pending",
        is_active=False
    )
    db.add(store)
    db.commit()
    return {"success": True, "message": "Vendor registered, pending approval"}

# Crear tienda (solo vendor)
@router.post("/", response_model=schemas.VendorStoreRead)
def create_store(store: schemas.VendorStoreCreate, db: Session = Depends(get_db), user=Depends(require_role("vendor"))):
    if db.query(models.VendorStore).filter_by(vendor_id=user.id).first():
        raise HTTPException(status_code=400, detail="Vendor already has a store")
    if db.query(models.VendorStore).filter_by(store_slug=store.store_slug).first():
        raise HTTPException(status_code=400, detail="Slug already exists")
    db_store = models.VendorStore(
        vendor_id=user.id,
        store_name=store.store_name,
        store_slug=store.store_slug,
        store_theme=store.store_theme,
        commission_rate=store.commission_rate,
        is_active=store.is_active
    )
    db.add(db_store)
    db.commit()
    db.refresh(db_store)
    return db_store

# Obtener tienda propia (solo vendor)
@router.get("/me", response_model=schemas.VendorStoreRead)
def get_my_store(db: Session = Depends(get_db), user=Depends(require_role("vendor"))):
    store = db.query(models.VendorStore).filter_by(vendor_id=user.id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store

# Listar todas las tiendas (público)
@router.get("/", response_model=list[schemas.VendorStoreRead])
def list_stores(db: Session = Depends(get_db)):
    return db.query(models.VendorStore).all()

# Obtener tienda por slug (público)
@router.get("/slug/{store_slug}", response_model=schemas.VendorStoreRead)
def get_store_by_slug(store_slug: str, db: Session = Depends(get_db)):
    store = db.query(models.VendorStore).filter_by(store_slug=store_slug).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store

# Actualizar tienda (solo vendor dueño)
@router.put("/me", response_model=schemas.VendorStoreRead)
def update_my_store(update: schemas.VendorStoreCreate, db: Session = Depends(get_db), user=Depends(require_role("vendor"))):
    store = db.query(models.VendorStore).filter_by(vendor_id=user.id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    for field, value in update.dict(exclude_unset=True).items():
        setattr(store, field, value)
    db.commit()
    db.refresh(store)
    return store

# Eliminar tienda (solo vendor dueño)
@router.delete("/me", status_code=204)
def delete_my_store(db: Session = Depends(get_db), user=Depends(require_role("vendor"))):
    store = db.query(models.VendorStore).filter_by(vendor_id=user.id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    db.delete(store)
    db.commit()

# Carga de documento KYC para vendedor autenticado
@router.post("/upload-document/")
async def upload_vendor_document(
    document_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_role("vendor"))
):
    # Busca la tienda del usuario actual
    store = db.query(models.VendorStore).filter_by(vendor_id=user.id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Vendor store not found")

    safe_document_type = _sanitize_vendor_document_type(document_type)
    safe_extension = _safe_vendor_document_extension(file.filename or "")
    if str(file.content_type or "").strip().lower() not in _ALLOWED_VENDOR_DOC_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Tipo MIME no permitido.")

    file_bytes = await file.read(_MAX_VENDOR_DOCUMENT_BYTES + 1)
    if not file_bytes:
        raise HTTPException(status_code=400, detail="El archivo esta vacio.")
    if len(file_bytes) > _MAX_VENDOR_DOCUMENT_BYTES:
        raise HTTPException(status_code=413, detail="El archivo excede el tamano maximo permitido.")
    if not _matches_vendor_document_signature(file_bytes, safe_extension):
        raise HTTPException(status_code=400, detail="El contenido del archivo no coincide con su extension.")

    file_dir = _PRIVATE_UPLOAD_ROOT / str(store.id) / "documents"
    file_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    internal_name = f"{safe_document_type}_{secrets.token_urlsafe(16)}{safe_extension}"
    storage_key = _vendor_document_storage_key(store.id, internal_name)
    file_path = _vendor_document_storage_path(storage_key)
    with file_path.open("wb") as buffer:
        buffer.write(file_bytes)
    file_path.chmod(0o600)
    await file.close()

    # Guardar registro en base de datos
    document = models.VendorDocument(
        vendor_id=store.id,
        document_type=safe_document_type,
        file=storage_key
    )
    db.add(document)
    db.commit()
    return {"message": "Document uploaded successfully"}
