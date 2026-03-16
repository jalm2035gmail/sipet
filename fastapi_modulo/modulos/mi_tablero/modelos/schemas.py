from __future__ import annotations

from pydantic import BaseModel, Field

from fastapi_modulo.modulos.mi_tablero.modelos.enums import DashboardLayout, DashboardTheme


class WidgetSchema(BaseModel):
    key: str = Field(..., min_length=1)
    title: str = ""
    enabled: bool = True
    priority_order: int = 0
    is_favorite: bool = False
    is_pinned: bool = False
    is_hidden: bool = False


class DashboardDesignerWidgetSchema(BaseModel):
    type: str = Field(..., min_length=1)
    x: int = Field(default=0, ge=0)
    y: int = Field(default=0, ge=0)
    w: int = Field(default=2, ge=1)
    h: int = Field(default=1, ge=1)


class DashboardDesignerLayoutSchema(BaseModel):
    widgets: list[DashboardDesignerWidgetSchema] = Field(default_factory=list)


class DashboardPreferenceSchema(BaseModel):
    theme: DashboardTheme = DashboardTheme.SYSTEM
    layout: DashboardLayout = DashboardLayout.GRID
    widgets: list[WidgetSchema] = Field(default_factory=list)
    designer_layout: DashboardDesignerLayoutSchema = Field(default_factory=DashboardDesignerLayoutSchema)


class DashboardModuleSchema(BaseModel):
    key: str
    label: str
    description: str = ""
    route: str
    icon: str = ""


class DashboardPreferenceUpdateSchema(BaseModel):
    theme: DashboardTheme = DashboardTheme.SYSTEM
    layout: DashboardLayout = DashboardLayout.GRID


class DashboardPreferenceItemUpdateSchema(BaseModel):
    item_key: str = Field(..., min_length=1)
    is_favorite: bool = False
    priority_order: int = Field(default=0, ge=0)
    is_pinned: bool = False
    is_hidden: bool = False


class DashboardWidgetOrderSchema(BaseModel):
    widgets: list[str] = Field(default_factory=list)


class DashboardWidgetMutationSchema(BaseModel):
    key: str = Field(..., min_length=1)
    title: str = ""
