from __future__ import annotations

from pathlib import Path

from fastapi_modulo.modulos.aplicaciones.servicios import protocol_service


def test_protocol_status_detects_missing_files_and_invalid_depends(monkeypatch, tmp_path: Path) -> None:
    module_dir = tmp_path / "demo"
    module_dir.mkdir()
    (module_dir / "controladores").mkdir()
    (module_dir / "__manifest__.py").write_text(
        "MANIFEST = {'route': 'bad', 'depends': ['missing_dep'], 'assets': {'css': ['static/css/miss.css']}}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(protocol_service, "iter_module_dirs", lambda: [module_dir])
    monkeypatch.setattr(protocol_service, "_definitions_by_dir", lambda: {})

    status = protocol_service.get_protocol_status_map()["demo"]

    assert "__init__.py" in status["missing"]
    assert "README.md" in status["missing"]
    assert "tests/" in status["missing"]
    assert "depends" in status["issues"]
    assert "route" in status["issues"]
    assert "assets" in status["issues"]


def test_build_init_source_uses_same_name_controller(tmp_path: Path) -> None:
    module_dir = tmp_path / "demo"
    controller_dir = module_dir / "controladores"
    controller_dir.mkdir(parents=True)
    (controller_dir / "demo.py").write_text("router = object()\n", encoding="utf-8")

    source = protocol_service.build_init_source(module_dir)

    assert "from fastapi_modulo.modulos.demo.controladores.demo import router" in source


def test_build_manifest_payload_detects_web_dependency(tmp_path: Path) -> None:
    module_dir = tmp_path / "demo"
    module_dir.mkdir()
    (module_dir / "controladores").mkdir()
    (module_dir / "tests").mkdir()
    (module_dir / "README.md").write_text("demo", encoding="utf-8")
    (module_dir / "sample.py").write_text("from fastapi_modulo.modulos.web.servicios.auth_service import x\n", encoding="utf-8")

    payload = protocol_service.build_manifest_payload(module_dir)

    assert "main" in payload["depends"]
    assert "web" in payload["depends"]


def test_ensure_protocol_files_creates_missing_init_and_manifest(tmp_path: Path) -> None:
    module_dir = tmp_path / "demo"
    (module_dir / "controladores").mkdir(parents=True)
    (module_dir / "controladores" / "demo.py").write_text("router = object()\n", encoding="utf-8")
    (module_dir / "tests").mkdir()
    (module_dir / "README.md").write_text("demo", encoding="utf-8")

    result = protocol_service.ensure_protocol_files(module_dirs=[module_dir])

    assert "demo" in result["created_init"]
    assert "demo" in result["created_manifest"]
    assert (module_dir / "__init__.py").is_file()
    assert (module_dir / "__manifest__.py").is_file()
