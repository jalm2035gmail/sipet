from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from fastapi_modulo.core.db import MAIN


class DashboardPreference(MAIN):
    __tablename__ = "dashboard_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True, default=0)
    tenant_id = Column(Integer, nullable=False, index=True, default=0)
    item_key = Column(String(120), nullable=False, index=True)
    item_title = Column(String(200), nullable=True)
    priority_order = Column(Integer, nullable=False, default=0)
    is_favorite = Column(Boolean, nullable=False, default=False)
    is_pinned = Column(Boolean, nullable=False, default=False)
    is_hidden = Column(Boolean, nullable=False, default=False)
    theme = Column(String(32), nullable=True)
    layout = Column(String(32), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
