from __future__ import annotations

import importlib

from fastapi_modulo.modulos.intelicoop.modelos import intelicoop_scoring


def test_scoring_model_path_points_to_module_asset() -> None:
    assert intelicoop_scoring.MODEL_PATH.exists() is True
    assert intelicoop_scoring.MODEL_PATH.name == "modelo_scoring.pkl"


def test_store_module_does_not_create_schema_during_import(monkeypatch) -> None:
    from fastapi_modulo.core import db as core_db
    from fastapi_modulo.core.db import MAIN
    from fastapi_modulo.modulos.intelicoop.modelos import intelicoop_store

    calls: list[object] = []

    monkeypatch.setattr(core_db, "get_request_host", lambda: "")
    monkeypatch.setattr(core_db, "get_engine_for_host", lambda host=None: object())
    monkeypatch.setattr(MAIN.metadata, "create_all", lambda *args, **kwargs: calls.append((args, kwargs)))

    importlib.reload(intelicoop_store)

    assert calls == []
