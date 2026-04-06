from __future__ import annotations

from pathlib import Path

from fastapi_modulo.modulos_sipet.aplicaciones.servicios import package_service


def test_build_snapshot_audit_payload_reuses_precomputed_checksums() -> None:
    payload = package_service._build_snapshot_audit_payload(
        module_key="crm",
        original_filename="crm.zip",
        checksum="zip-checksum",
        inspection={
            "entries": [
                {
                    "relative_path": "module.py",
                    "destination": "/tmp/missing-target.py",
                    "staged_path": "/tmp/missing-stage.py",
                    "file_size": 5,
                    "status": "changed",
                    "existed_before": True,
                    "destination_checksum": "previous-sha",
                    "staged_checksum": "incoming-sha",
                },
                {
                    "relative_path": "new_file.py",
                    "destination": "/tmp/new-target.py",
                    "staged_path": "/tmp/new-stage.py",
                    "file_size": 3,
                    "status": "new",
                    "existed_before": False,
                    "destination_checksum": "",
                    "staged_checksum": "new-incoming-sha",
                }
            ]
        },
        snapshot_path="/tmp/snapshot.zip",
        user_id="tester",
    )

    assert payload["requested_by"] == "tester"
    assert payload["snapshot_path"] == "/tmp/snapshot.zip"
    assert payload["affected_files"][0]["path"] == "module.py"
    assert payload["affected_files"][0]["status"] == "changed"
    assert payload["affected_files"][0]["previous_checksum"] == "previous-sha"
    assert payload["affected_files"][0]["incoming_checksum"] == "incoming-sha"
    assert payload["snapshot_mode"] == "full_fallback"
    assert payload["rollback_strategy"] == "differential_ready_full_fallback"
    assert payload["rollback_manifest"]["modified_files"] == ["module.py"]
    assert payload["rollback_manifest"]["created_files"] == ["new_file.py"]
    assert payload["rollback_manifest"]["removed_files"] == []


def test_apply_prepared_module_package_skips_snapshot_when_everything_is_unchanged(tmp_path: Path, monkeypatch) -> None:
    module_root = tmp_path / "module"
    staging_root = tmp_path / "staging"
    module_root.mkdir()
    staging_root.mkdir()
    audits: list[tuple[str, dict]] = []
    uploads: list[dict] = []
    invalidations: list[tuple[str, str]] = []
    cleaned: list[str] = []

    monkeypatch.setattr(package_service, "_snapshot_module_root", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("snapshot should not run")))
    monkeypatch.setattr(package_service, "apply_staged_entries", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("apply should not run")))
    monkeypatch.setattr(
        package_service,
        "create_registry_audit",
        lambda module_key, action, payload, result, user_id, ip: audits.append((action, payload)),
    )
    monkeypatch.setattr(package_service, "create_package_upload", lambda **kwargs: uploads.append(kwargs))
    monkeypatch.setattr(package_service, "invalidate_zip_inspection", lambda module_key, checksum: invalidations.append((module_key, checksum)))
    monkeypatch.setattr(package_service, "cleanup_staging_dir", lambda staging_root: cleaned.append(staging_root))

    payload = package_service.apply_prepared_module_package(
        module_key="crm",
        inspection_payload={
            "target_root": str(module_root),
            "staging_root": str(staging_root),
            "total_files": 1,
            "total_uncompressed_size": 12,
            "new_files": 0,
            "changed_files": 0,
            "unchanged_files": 1,
            "preview_files": [],
            "warnings": [],
            "architecture_ok": True,
            "architecture_errors": [],
            "architecture_warnings": [],
            "entries": [],
        },
        original_filename="crm.zip",
        checksum="abc123",
        file_size=12,
        content_type="application/zip",
        stored_filename="crm-upload.zip",
        user_id="tester",
        tenant_id="default",
        ip="127.0.0.1",
    )

    assert payload["updated_files"] == 0
    assert any("No se aplicaron cambios" in warning for warning in payload["warnings"])
    assert any(action == "upload_package_noop" for action, _payload in audits)
    assert uploads[0]["applied"] is False
    assert invalidations == [("crm", "abc123")]
    assert cleaned == [str(staging_root)]


def test_build_import_process_state_uses_inspection_id_when_available() -> None:
    payload = package_service._build_import_process_state(
        state="ready_to_apply",
        module_key="crm",
        checksum="ABC123",
        inspection_payload={
            "inspection_id": "crm-inspection-1",
            "target_root": "/tmp/crm",
            "staging_root": "/tmp/stage",
            "new_files": 1,
            "changed_files": 2,
            "unchanged_files": 3,
        },
        user_id="tester",
        detail="Listo",
    )

    assert payload["process_id"] == "crm-inspection-1"
    assert payload["inspection_id"] == "crm-inspection-1"
    assert payload["state"] == "ready_to_apply"
    assert payload["new_files"] == 1
    assert payload["changed_files"] == 2
    assert payload["unchanged_files"] == 3


def test_snapshot_module_root_tolerates_missing_module_dir(tmp_path: Path) -> None:
    missing_root = tmp_path / "missing-module"

    snapshot_path = package_service._snapshot_module_root("crm", str(missing_root))

    assert Path(snapshot_path).is_file()
