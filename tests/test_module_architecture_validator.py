from __future__ import annotations

from pathlib import Path

from scripts.validate_module_architecture import validate_module


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_validate_module_accepts_basic_valid_module(tmp_path: Path) -> None:
    module_dir = tmp_path / "modulo_ok"
    _write(
        module_dir / "__manifest__.py",
        """MANIFEST = {
    "name": "modulo_ok",
    "label": "Modulo OK",
    "summary": "Resumen",
    "version": "1.0.0",
    "depends": ["web"],
    "route": "/ok",
    "installable": True,
    "application": True,
    "assets": {"css": ["static/css/ok.css"], "js": ["static/js/ok.js"]},
    "structure": {"router": ["controladores/router.py"], "views": ["vistas/pagina.html"]},
}
""",
    )
    _write(module_dir / "controladores/router.py", "from fastapi_modulo.core import db as core_db\n\ndef get_db():\n    return core_db.SessionLocal()\n")
    _write(module_dir / "vistas/pagina.html", '<div class="text-slate-900 bg-white">Hola</div>\n')
    _write(module_dir / "static/css/ok.css", ".ok { color: #111827; }\n")
    _write(module_dir / "static/js/ok.js", "console.log('ok');\n")
    _write(module_dir / "tests/test_modulo_ok.py", "def test_smoke():\n    assert True\n")

    result = validate_module(module_dir)

    assert result.ok is True
    assert result.errors == []


def test_validate_module_reports_architecture_violations(tmp_path: Path) -> None:
    module_dir = tmp_path / "modulo_bad"
    _write(
        module_dir / "__manifest__.py",
        """MANIFEST = {
    "name": "modulo_bad",
    "label": "Modulo Bad",
    "summary": "Resumen",
    "version": "1.0.0",
    "depends": [],
    "route": "/bad",
    "installable": True,
    "application": True,
    "assets": {"css": ["static/css/missing.css"], "js": []},
    "structure": {"router": ["controladores/router.py"], "views": ["vistas/pagina.html"]},
}
""",
    )
    _write(
        module_dir / "controladores/router.py",
        "from sqlalchemy import create_engine\n"
        "from fastapi_modulo.core import db as core_db\n\n"
        "def broken():\n"
        "    create_engine('sqlite:///:memory:')\n"
        "    return core_db.get_session_factory_for_host('')()\n",
    )
    _write(module_dir / "vistas/pagina.html", '<script src="https://cdn.tailwindcss.com"></script><div class="text-{{ tone }}">Hola</div>\n')

    result = validate_module(module_dir)

    codes = {finding.code for finding in result.errors}
    assert result.ok is False
    assert "manifest.asset_missing" in codes
    assert "db.raw_engine" in codes
    assert "db.implicit_admin" in codes
    assert "styles.tailwind_cdn" in codes
    assert "styles.dynamic_tailwind" in codes


def test_validate_module_rejects_application_true_inside_modulos_sipet(tmp_path: Path) -> None:
    module_dir = tmp_path / "fastapi_modulo" / "modulos_sipet" / "core_fake"
    _write(
        module_dir / "__manifest__.py",
        """MANIFEST = {
    "name": "core_fake",
    "label": "Core Fake",
    "summary": "Resumen",
    "version": "1.0.0",
    "depends": [],
    "route": "/core-fake",
    "installable": True,
    "application": True,
}
""",
    )
    _write(module_dir / "tests/test_core_fake.py", "def test_smoke():\n    assert True\n")

    result = validate_module(module_dir)

    codes = {finding.code for finding in result.errors}
    assert result.ok is False
    assert "manifest.core_application" in codes
