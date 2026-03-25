from __future__ import annotations

from types import SimpleNamespace

from fastapi_modulo.modulos.empleados.modelos import departamentos_service


class _FakeQuery:
    def __init__(self, rows):
        self._rows = rows

    def group_by(self, *_args, **_kwargs):
        return self

    def all(self):
        return list(self._rows)


class _FakeSession:
    def __init__(self, rows):
        self._rows = rows

    def query(self, *_args, **_kwargs):
        return _FakeQuery(self._rows)

    def close(self):
        return None


def test_build_empleados_count_map_aggregates_rows_from_database(monkeypatch) -> None:
    grouped_rows = [
        ("direccion", 3),
        ("talento", 2),
        ("", 99),
    ]
    monkeypatch.setattr(departamentos_service.core_db, "get_request_host", lambda: "test.local")
    monkeypatch.setattr(
        departamentos_service.core_db,
        "get_session_factory_for_host",
        lambda host: (lambda: _FakeSession(grouped_rows)),
    )

    rows = [
        SimpleNamespace(codigo="DIR", nombre="Direccion"),
        SimpleNamespace(codigo="TH", nombre="Talento"),
        SimpleNamespace(codigo="", nombre="Direccion"),
    ]

    counts = departamentos_service.build_empleados_count_map(rows)

    assert counts["dir"] == 3
    assert counts["th"] == 2
    assert counts["direccion"] == 3
