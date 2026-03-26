from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
from fastapi import HTTPException

from fastapi_modulo.modulos_sipet.aplicaciones.repositorios import package_repository


def _build_zip(path: Path, members: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in members.items():
            archive.writestr(name, content)


def test_inspect_module_zip_reports_new_changed_and_unchanged(monkeypatch, tmp_path: Path) -> None:
    module_root = tmp_path / "modulo"
    module_root.mkdir()
    (module_root / "keep.txt").write_text("same", encoding="utf-8")
    (module_root / "edit.txt").write_text("old", encoding="utf-8")
    zip_path = tmp_path / "package.zip"
    _build_zip(
        zip_path,
        {
            "modulo/keep.txt": b"same",
            "modulo/edit.txt": b"new",
            "modulo/new.txt": b"fresh",
        },
    )
    monkeypatch.setattr(package_repository, "get_module_upload_root", lambda module_key: str(module_root))

    inspection = package_repository.inspect_module_zip("modulo", str(zip_path))

    assert inspection["total_files"] == 3
    assert inspection["new_files"] == 1
    assert inspection["changed_files"] == 1
    assert inspection["unchanged_files"] == 1
    assert (module_root / "new.txt").exists() is False
    assert Path(str(inspection["staging_root"])).is_dir()
    package_repository.cleanup_staging_dir(str(inspection["staging_root"]))


def test_inspect_module_zip_rejects_disallowed_extensions(monkeypatch, tmp_path: Path) -> None:
    module_root = tmp_path / "modulo"
    module_root.mkdir()
    zip_path = tmp_path / "package.zip"
    _build_zip(zip_path, {"modulo/install.exe": b"binary"})
    monkeypatch.setattr(package_repository, "get_module_upload_root", lambda module_key: str(module_root))

    with pytest.raises(HTTPException) as exc:
        package_repository.inspect_module_zip("modulo", str(zip_path))

    assert exc.value.status_code == 400
    assert "no permitido" in str(exc.value.detail)


def test_validate_upload_metadata_rejects_invalid_content_type() -> None:
    with pytest.raises(HTTPException) as exc:
        package_repository.validate_upload_metadata(
            filename="module.zip",
            content_type="text/plain",
            file_size=128,
            has_zip_signature=True,
        )

    assert exc.value.status_code == 400
    assert "MIME" in str(exc.value.detail)


def test_apply_module_zip_uses_staging_before_target(monkeypatch, tmp_path: Path) -> None:
    module_root = tmp_path / "modulo"
    module_root.mkdir()
    (module_root / "edit.txt").write_text("old", encoding="utf-8")
    zip_path = tmp_path / "package.zip"
    _build_zip(zip_path, {"modulo/edit.txt": b"new", "modulo/new.txt": b"fresh"})
    monkeypatch.setattr(package_repository, "get_module_upload_root", lambda module_key: str(module_root))

    inspection = package_repository.inspect_module_zip("modulo", str(zip_path))
    package_repository.apply_module_zip(str(zip_path), inspection)

    assert (module_root / "edit.txt").read_text(encoding="utf-8") == "new"
    assert (module_root / "new.txt").read_text(encoding="utf-8") == "fresh"
    package_repository.cleanup_staging_dir(str(inspection["staging_root"]))


def test_inspect_module_zip_accepts_alias_root_named_after_module_key(monkeypatch, tmp_path: Path) -> None:
    module_root = tmp_path / "empleados"
    module_root.mkdir()
    zip_path = tmp_path / "package.zip"
    _build_zip(zip_path, {"organizacion/empleados.txt": b"fresh"})
    monkeypatch.setattr(package_repository, "get_module_upload_root", lambda module_key: str(module_root))

    inspection = package_repository.inspect_module_zip("organizacion", str(zip_path))

    preview_paths = [entry["path"] for entry in inspection["preview_files"]]
    assert preview_paths == ["empleados.txt"]
    package_repository.cleanup_staging_dir(str(inspection["staging_root"]))


def test_restore_module_snapshot_restores_previous_state(monkeypatch, tmp_path: Path) -> None:
    module_root = tmp_path / "modulo"
    module_root.mkdir()
    (module_root / "state.txt").write_text("before", encoding="utf-8")
    snapshot_path = tmp_path / "snapshot.zip"
    _build_zip(snapshot_path, {"state.txt": b"before"})
    (module_root / "state.txt").write_text("after", encoding="utf-8")
    monkeypatch.setattr(package_repository, "get_module_upload_root", lambda module_key: str(module_root))

    restored_files = package_repository.restore_module_snapshot("modulo", str(snapshot_path))

    assert restored_files == 1
    assert (module_root / "state.txt").read_text(encoding="utf-8") == "before"


def test_get_module_upload_root_rejects_core_modules_under_modulos_sipet(monkeypatch, tmp_path: Path) -> None:
    core_root = tmp_path / "fastapi_modulo" / "modulos_sipet" / "frontend"
    core_root.mkdir(parents=True)
    monkeypatch.setattr(
        package_repository,
        "_resolve_module_root_from_manifest",
        lambda module_key: str(core_root),
    )
    monkeypatch.setattr(package_repository, "_resolve_module_root_from_router", lambda module_key: None)
    monkeypatch.setattr(package_repository, "_resolve_module_root_from_key", lambda module_key: None)
    monkeypatch.setattr(package_repository, "IMPORTABLE_MODULES_ROOT", str(tmp_path / "fastapi_modulo" / "modulos"))

    assert package_repository.get_module_upload_root("frontend") is None
