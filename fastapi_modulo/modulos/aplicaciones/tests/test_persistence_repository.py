from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi_modulo.db import MAIN
from fastapi_modulo.modulos.aplicaciones.repositorios.package_repository import get_module_upload_root
from fastapi_modulo.modulos.aplicaciones.repositorios import persistence_repository


def test_registry_state_and_audit_persistence(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    testing_session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    MAIN.metadata.create_all(bind=engine)
    monkeypatch.setattr(persistence_repository, "SessionLocal", testing_session_local)

    state = persistence_repository.upsert_registry_state(
        module_key="crm",
        enabled=True,
        tenant_id="default",
        installed_version="1.2.3",
        uploaded_at=None,
        updated_by="tester",
    )
    audit = persistence_repository.create_registry_audit(
        module_key="crm",
        action="toggle_state",
        payload={"enabled": True},
        result="success",
        user_id="tester",
        ip="127.0.0.1",
    )

    assert state.module_key == "crm"
    assert state.enabled is True
    assert audit.action == "toggle_state"


def test_package_and_protocol_persistence(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:")
    testing_session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    MAIN.metadata.create_all(bind=engine)
    monkeypatch.setattr(persistence_repository, "SessionLocal", testing_session_local)

    protocol = persistence_repository.replace_protocol_audit(
        "aplicaciones",
        {
            "has_init": True,
            "has_manifest": False,
            "missing": ["__manifest__.py"],
            "ok": False,
        },
    )
    upload = persistence_repository.create_package_upload(
        module_key="aplicaciones",
        original_filename="aplicaciones.zip",
        stored_filename="tmp.zip",
        checksum="abc123",
        file_size=128,
        uploaded_by="tester",
        applied=True,
    )

    assert protocol.module_key == "aplicaciones"
    assert protocol.ok is False
    assert upload.module_key == "aplicaciones"
    assert upload.applied is True


def test_module_upload_root_is_resolved_from_registry() -> None:
    crm_root = get_module_upload_root("crm")
    aplicaciones_root = get_module_upload_root("aplicaciones")

    assert crm_root is not None
    assert crm_root.endswith("/fastapi_modulo/modulos/crm")
    assert aplicaciones_root is not None
    assert aplicaciones_root.endswith("/fastapi_modulo/modulos/aplicaciones")
