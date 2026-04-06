from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from fastapi_modulo.modulos.multitienda.controladores import marketplace_backend as backend


class _FakeMappingsResult:
    def __init__(self, row):
        self._row = row

    def first(self):
        return self._row

    def mappings(self):
        return self


class _FakeDb:
    def __init__(self, rows):
        self._rows = list(rows)
        self.executed = []
        self.committed = False
        self.closed = False

    def execute(self, _statement, params=None):
        self.executed.append(dict(params or {}))
        row = self._rows.pop(0) if self._rows else None
        return _FakeMappingsResult(row)

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


def test_save_store_settings_allows_editing_with_same_admin(monkeypatch) -> None:
    fake_db = _FakeDb(
        [
            (55,),
            {
                "id": 7,
                "vendor_id": 55,
                "store_name": "Tu Negocio VALE",
                "store_slug": "tu-negocio-vale",
                "store_theme": "{}",
                "is_featured": True,
                "is_active": True,
            },
            None,
            {
                "id": 7,
                "vendor_id": 55,
                "store_name": "Tu Negocio VALE",
            },
        ]
    )
    monkeypatch.setattr(backend, "SessionLocal", lambda: fake_db)

    response = asyncio.run(
        backend.save_store_settings(
            None,
            payload_override={
                "is_edit": True,
                "store_id": "7",
                "store_name": "Tu Negocio VALE",
                "admin_user_id": "55",
                "is_active": True,
                "is_featured": True,
            },
        )
    )

    assert response.status_code == 201
    assert fake_db.committed is True
    assert fake_db.closed is True
    assert len(fake_db.executed) == 4
    assert all("store_id" not in params or "admin_user_id" not in params for params in fake_db.executed)


def test_save_store_settings_rejects_other_store_admin_conflict(monkeypatch) -> None:
    fake_db = _FakeDb(
        [
            (77,),
            {
                "id": 7,
                "vendor_id": 55,
                "store_name": "Tu Negocio VALE",
                "store_slug": "tu-negocio-vale",
                "store_theme": "{}",
                "is_featured": True,
                "is_active": True,
            },
            {
                "id": 8,
                "store_name": "Otra tienda",
            },
        ]
    )
    monkeypatch.setattr(backend, "SessionLocal", lambda: fake_db)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            backend.save_store_settings(
                None,
                payload_override={
                    "is_edit": True,
                    "store_id": "7",
                    "store_name": "Tu Negocio VALE",
                    "admin_user_id": "77",
                    "is_active": True,
                    "is_featured": True,
                },
            )
        )

    assert exc_info.value.status_code == 409
    assert "Otra tienda" in str(exc_info.value.detail)
    assert fake_db.closed is True
