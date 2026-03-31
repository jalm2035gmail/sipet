from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app.api.deps import DBSession, Pagination, PaginationParams, get_current_active_user

router = APIRouter()


# ── Este router es genérico ───────────────────────────────────────────────────
# Cada recurso de negocio sigue el mismo patrón:
#   1. Importa su Repository y sus Schemas
#   2. Registra las 5 operaciones CRUD estándar
#
# Ejemplo completo con un recurso "Item" ------------------------------------


# ── Schemas de ejemplo (reemplazar por los reales en app/schemas/) ────────────
from pydantic import BaseModel
from datetime import datetime


class ItemCreate(BaseModel):
    name: str
    description: str | None = None
    is_active: bool = True


class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class ItemRead(BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[Any]


# ── CRUD endpoints ────────────────────────────────────────────────────────────

@router.get("/", response_model=PaginatedResponse)
def list_items(
    params: PaginationParams = Pagination,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    """Lista paginada. Reemplazar Item por el modelo real."""
    # from app.repositories.item_repo import ItemRepository
    # repo = ItemRepository(db)
    # total = repo.count()
    # items = repo.list(skip=params.skip, limit=params.limit)
    # return PaginatedResponse(total=total, skip=params.skip, limit=params.limit, items=items)
    return PaginatedResponse(total=0, skip=params.skip, limit=params.limit, items=[])


@router.post("/", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(
    data: ItemCreate,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    # from app.repositories.item_repo import ItemRepository
    # return ItemRepository(db).create(data)
    raise HTTPException(status_code=501, detail="Implement repository and uncomment")


@router.get("/{item_id}", response_model=ItemRead)
def get_item(
    item_id: int,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    # from app.repositories.item_repo import ItemRepository
    # item = ItemRepository(db).get_by_id(item_id)
    # if not item:
    #     raise HTTPException(status_code=404, detail="Item not found")
    # return item
    raise HTTPException(status_code=404, detail="Item not found")


@router.patch("/{item_id}", response_model=ItemRead)
def update_item(
    item_id: int,
    data: ItemUpdate,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    # from app.repositories.item_repo import ItemRepository
    # repo = ItemRepository(db)
    # item = repo.get_by_id(item_id)
    # if not item:
    #     raise HTTPException(status_code=404, detail="Item not found")
    # return repo.update(item, data)
    raise HTTPException(status_code=404, detail="Item not found")


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    db: Session = DBSession,
    current_user=Depends(get_current_active_user),
):
    # from app.repositories.item_repo import ItemRepository
    # repo = ItemRepository(db)
    # item = repo.get_by_id(item_id)
    # if not item:
    #     raise HTTPException(status_code=404, detail="Item not found")
    # repo.delete(item)
    raise HTTPException(status_code=404, detail="Item not found")
