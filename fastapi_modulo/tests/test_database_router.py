from __future__ import annotations

from pathlib import Path

import pytest

from fastapi_modulo.core import database_router


def test_resolve_default_database_url_uses_global_sipet_conf_only(monkeypatch, tmp_path: Path) -> None:
    global_conf = tmp_path / "sipet.conf"
    global_conf.write_text(
        "[options]\n"
        "sqlite_db_path = /tmp/global.db\n",
        encoding="utf-8",
    )
    domain_dir = tmp_path / "dominios"
    domain_dir.mkdir()
    (domain_dir / "example.com.conf").write_text(
        "[options]\n"
        "sqlite_db_path = /tmp/domain.db\n"
        "domain = example.com\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(database_router, "SIPET_CONFIG_PATH", global_conf)
    monkeypatch.setattr(database_router, "DOMAIN_CONFIG_DIR", domain_dir)
    monkeypatch.setenv("APP_DOMAIN", "example.com")

    resolved = database_router.resolve_default_database_url()

    assert resolved == "sqlite:////tmp/global.db"


def test_database_router_rejects_conflicting_host_database_sources(monkeypatch, tmp_path: Path) -> None:
    global_conf = tmp_path / "sipet.conf"
    global_conf.write_text("[options]\nsqlite_db_path = /tmp/global.db\n", encoding="utf-8")
    domain_dir = tmp_path / "dominios"
    domain_dir.mkdir()
    (domain_dir / "example.com.conf").write_text(
        "[options]\n"
        "sqlite_db_path = /tmp/domain.db\n"
        "domain = example.com\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(database_router, "SIPET_CONFIG_PATH", global_conf)
    monkeypatch.setattr(database_router, "DOMAIN_CONFIG_DIR", domain_dir)
    monkeypatch.setenv("HOST_DATAMAIN_MAP", "example.com=/tmp/other.db")

    router = database_router.DatabaseRouter()

    with pytest.raises(RuntimeError, match="múltiples bases configuradas"):
        router.get_database_url_for_host("example.com")


def test_database_router_global_database_url_uses_global_default(monkeypatch, tmp_path: Path) -> None:
    global_conf = tmp_path / "sipet.conf"
    global_conf.write_text("[options]\nsqlite_db_path = /tmp/global.db\n", encoding="utf-8")
    domain_dir = tmp_path / "dominios"
    domain_dir.mkdir()
    (domain_dir / "example.com.conf").write_text(
        "[options]\n"
        "sqlite_db_path = /tmp/domain.db\n"
        "domain = example.com\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(database_router, "SIPET_CONFIG_PATH", global_conf)
    monkeypatch.setattr(database_router, "DOMAIN_CONFIG_DIR", domain_dir)

    router = database_router.DatabaseRouter()

    assert router.get_global_database_url() == "sqlite:////tmp/global.db"
