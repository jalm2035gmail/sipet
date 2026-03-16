from __future__ import annotations

from pathlib import Path

from fastapi_modulo.modulos.aplicaciones.servicios import package_service


def test_build_snapshot_audit_payload_includes_previous_and_incoming_checksums(tmp_path: Path) -> None:
    target = tmp_path / "module.py"
    staged = tmp_path / "stage.py"
    target.write_text("before", encoding="utf-8")
    staged.write_text("after", encoding="utf-8")

    payload = package_service._build_snapshot_audit_payload(
        module_key="crm",
        original_filename="crm.zip",
        checksum="zip-checksum",
        inspection={
            "entries": [
                {
                    "relative_path": "module.py",
                    "destination": str(target),
                    "staged_path": str(staged),
                    "file_size": 5,
                    "status": "changed",
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
    assert payload["affected_files"][0]["previous_checksum"]
    assert payload["affected_files"][0]["incoming_checksum"]
