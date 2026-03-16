from fastapi_modulo.modulos.aplicaciones.servicios.protocol_service import (
    PROTOCOL_MODE_REBUILD,
    PROTOCOL_MODE_REPAIR,
    build_manifest_payload,
    build_manifest_source,
    ensure_protocol_files,
    get_protocol_status_map,
    iter_module_dirs,
)


def test_protocol_status_map_has_known_modules() -> None:
    status = get_protocol_status_map()
    assert "crm" in status
    assert "aplicaciones" in status
    assert "has_readme" in status["crm"]
    assert "issues" in status["crm"]


def test_build_manifest_payload_for_crm() -> None:
    module_dir = next(path for path in iter_module_dirs() if path.name == "crm")
    payload = build_manifest_payload(module_dir)
    assert payload["name"] == "crm"
    assert "depends" in payload
    assert "assets" in payload


def test_build_manifest_source_exports_manifest() -> None:
    module_dir = next(path for path in iter_module_dirs() if path.name == "aplicaciones")
    source = build_manifest_source(module_dir)
    assert "MANIFEST =" in source
    assert "__all__" in source


def test_ensure_protocol_files_defaults_to_repair_mode() -> None:
    result = ensure_protocol_files(module_dirs=[])
    assert result["mode"] == PROTOCOL_MODE_REPAIR


def test_ensure_protocol_files_accepts_rebuild_mode(tmp_path) -> None:
    module_dir = tmp_path / "demo"
    module_dir.mkdir()
    (module_dir / "controladores").mkdir()
    (module_dir / "tests").mkdir()
    (module_dir / "README.md").write_text("demo", encoding="utf-8")
    (module_dir / "__init__.py").write_text("old\n", encoding="utf-8")
    (module_dir / "__manifest__.py").write_text("MANIFEST = {'name': 'demo'}\n", encoding="utf-8")
    result = ensure_protocol_files(mode=PROTOCOL_MODE_REBUILD, module_dirs=[module_dir])
    assert result["mode"] == PROTOCOL_MODE_REBUILD
    assert "demo" in result["updated_init"]
    assert "demo" in result["updated_manifest"]
