"""
tests/test_store.py
─────────────────────────────────────────────────────────────────────────────
Pruebas unitarias de frontend_store.py sobre SQLite in-memory.

Cubre:
  • Tablas creadas correctamente (schema)
  • pages: upsert, get, list, delete, is_home, publish
  • versions: save & list
  • contacts: save & list
  • tasas: list, upsert, delete
  • gallery: create, update, list, delete, get_by_filename
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine

from fastapi_modulo.core.db import MAIN
from fastapi_modulo.modulos_sipet.frontend.modelos.frontend_db_models import (
    FrontendBrand,
    FrontendContact,
    FrontendGalleryImage,
    FrontendPage,
    FrontendPageVersion,
    FrontendTasa,
)

# ── Schema ────────────────────────────────────────────────────────────────────

def test_frontend_tables_created(mem_engine):
    """Todas las tablas del módulo existen en el engine in-memory."""
    table_names = set(MAIN.metadata.tables.keys())
    assert "frontend_pages"          in table_names
    assert "frontend_page_versions"  in table_names
    assert "frontend_contacts"       in table_names
    assert "frontend_brand"          in table_names
    assert "frontend_tasas"          in table_names
    assert "frontend_gallery_images" in table_names


# ── Pages ─────────────────────────────────────────────────────────────────────

def test_upsert_and_get_page(patched_store):
    store = patched_store
    pid   = uuid.uuid4().hex
    store.upsert_page(pid, {"slug": "inicio", "title": "Inicio", "gjs_html": "<h1>Hi</h1>"})
    page = store.get_page(pid)
    assert page is not None
    assert page["slug"] == "inicio"
    assert page["title"] == "Inicio"


def test_list_pages_empty_then_populated(patched_store):
    store = patched_store
    assert store.list_pages() == []
    pid = uuid.uuid4().hex
    store.upsert_page(pid, {"slug": "about", "title": "About"})
    pages = store.list_pages()
    assert len(pages) == 1
    assert pages[0]["slug"] == "about"


def test_delete_page(patched_store):
    store = patched_store
    pid = uuid.uuid4().hex
    store.upsert_page(pid, {"slug": "del-me", "title": "Delete"})
    assert store.get_page(pid) is not None
    store.delete_page(pid)
    assert store.get_page(pid) is None


def test_is_home_only_one_at_a_time(patched_store):
    store = patched_store
    pid1 = uuid.uuid4().hex
    pid2 = uuid.uuid4().hex
    store.upsert_page(pid1, {"slug": "page1", "title": "P1", "is_home": True})
    store.upsert_page(pid2, {"slug": "page2", "title": "P2", "is_home": True})
    # Setting page2 as home should clear page1
    pages = {p["id"]: p for p in store.list_pages()}
    assert pages[pid2]["is_home"] is True
    assert pages[pid1]["is_home"] is False


def test_publish_page_sets_flag(patched_store):
    store = patched_store
    pid = uuid.uuid4().hex
    store.upsert_page(pid, {"slug": "pub-test", "title": "Pub", "published": False})
    store.publish_page(pid)
    page = store.get_page(pid)
    assert page["published"] is True


def test_get_page_by_slug_published_only(patched_store):
    store = patched_store
    pid = uuid.uuid4().hex
    store.upsert_page(pid, {"slug": "visible", "title": "Visible", "published": False})
    assert store.get_page_by_slug("visible", published_only=True) is None
    store.publish_page(pid)
    assert store.get_page_by_slug("visible", published_only=True) is not None


# ── Versions ──────────────────────────────────────────────────────────────────

def test_versions_saved_and_listed(patched_store):
    store = patched_store
    pid = uuid.uuid4().hex
    store.upsert_page(pid, {"slug": "ver-test", "title": "Ver"})
    store.upsert_page(pid, {"slug": "ver-test", "title": "Ver v2", "gjs_html": "<p>v2</p>"})
    versions = store.list_versions(pid)
    assert len(versions) >= 1


# ── Contacts ──────────────────────────────────────────────────────────────────

def test_save_and_list_contacts(patched_store):
    store = patched_store
    store.save_contact({"name": "Ana", "email": "ana@ex.com", "message": "Hola"})
    contacts = store.list_contacts()
    assert len(contacts) == 1
    assert contacts[0]["email"] == "ana@ex.com"


# ── Tasas ─────────────────────────────────────────────────────────────────────

def test_list_tasas_returns_defaults_when_empty(patched_store):
    store = patched_store
    tasas = store.list_tasas()
    assert len(tasas) >= 4
    ids = {t["id"] for t in tasas}
    assert "ahorro_vista" in ids


def test_upsert_and_delete_tasa(patched_store):
    store = patched_store
    store.upsert_tasa({"id": "test_tasa", "label": "Test", "rate": "5.00", "color": "#fff", "unit": "% anual"})
    tasas = store.list_tasas()
    assert any(t["id"] == "test_tasa" for t in tasas)
    store.delete_tasa("test_tasa")
    tasas = store.list_tasas()
    assert not any(t["id"] == "test_tasa" for t in tasas)


# ── Gallery ───────────────────────────────────────────────────────────────────

def test_create_gallery_image(patched_store):
    store = patched_store
    iid = uuid.uuid4().hex
    record = store.create_gallery_image(
        image_id=iid,
        filename="test.webp",
        url="/static/gallery/test.webp",
        orig_name="original.png",
        size_kb=42.5,
        status="optimized",
    )
    assert record["id"]       == iid
    assert record["filename"] == "test.webp"
    assert record["status"]   == "optimized"
    assert record["size_kb"]  == pytest.approx(42.5)


def test_list_and_delete_gallery_image(patched_store):
    store = patched_store
    iid = uuid.uuid4().hex
    store.create_gallery_image(
        image_id=iid, filename="a.webp", url="/static/gallery/a.webp",
        orig_name="a.png", size_kb=10.0, status="optimized",
    )
    items = store.list_gallery_images()
    assert any(i["id"] == iid for i in items)

    deleted = store.delete_gallery_image(iid)
    assert deleted == "a.webp"
    assert store.list_gallery_images() == []


def test_update_gallery_image_status(patched_store):
    store = patched_store
    iid = uuid.uuid4().hex
    store.create_gallery_image(
        image_id=iid, filename="b.webp", url="/static/gallery/b.webp",
        orig_name="b.png", size_kb=5.0, status="processing",
    )
    result = store.update_gallery_image(iid, status="optimized", size_kb=3.5)
    assert result is not None
    assert result["status"]  == "optimized"
    assert result["size_kb"] == pytest.approx(3.5)


def test_get_gallery_image_by_filename(patched_store):
    store = patched_store
    iid = uuid.uuid4().hex
    store.create_gallery_image(
        image_id=iid, filename="find-me.webp", url="/static/gallery/find-me.webp",
        orig_name="fm.png", size_kb=8.0, status="optimized",
    )
    found = store.get_gallery_image_by_filename("find-me.webp")
    assert found is not None
    assert found["id"] == iid
    assert store.get_gallery_image_by_filename("no-such.webp") is None


def test_failed_gallery_image_stored(patched_store):
    store = patched_store
    iid = uuid.uuid4().hex
    store.create_gallery_image(
        image_id=iid, filename="fail.png", url="", orig_name="fail.png",
        size_kb=0.0, status="uploaded",
    )
    store.update_gallery_image(iid, status="failed", error="Pillow not available")
    record = store.get_gallery_image_by_filename("fail.png")
    assert record["status"] == "failed"
    assert record["error"]  == "Pillow not available"
