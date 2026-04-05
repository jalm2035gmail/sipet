from pathlib import Path

from fastapi_modulo.modulos.subastas.__manifest__ import MANIFEST


BASE = Path(__file__).resolve().parents[1]


def test_manifest_exists():
    assert (BASE / '__manifest__.py').exists()


def test_expected_structure():
    expected = [
        'controladores/subastas.py',
        'modelos/db_models.py',
        'modelos/schemas.py',
        'modelos/store.py',
        'vistas/subastas.html',
        'static/js/subastas.js',
        'static/css/subastas.css',
    ]
    for rel in expected:
        assert (BASE / rel).exists(), f'Falta {rel}'


def test_manifest_declares_sipet_runtime_contract():
    assert MANIFEST["name"] == "subastas"
    assert MANIFEST["route"] == "/subastas"
    assert "controladores/subastas.py" in MANIFEST["structure"]["router"]
    assert MANIFEST["icon"] == "fa-solid fa-gavel"
