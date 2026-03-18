from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi_modulo.modulos_sipet.modulo_base.core.task_queue import (
    build_module_task_registry,
    create_module_task_queue,
)
from fastapi_modulo.modulos_sipet.modulo_base.tareas.celery_app import celery_app

logger = logging.getLogger(__name__)

registry = build_module_task_registry("modulo_base")
registry.register("protocol_sync", queue="modulo_base_sync")
task_queue = create_module_task_queue("modulo_base", celery_app=celery_app, registry=registry)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_pandas() -> Any:
    try:
        import pandas as pd
        return pd
    except ImportError as exc:
        raise RuntimeError("pandas no esta disponible. Instala: pip install pandas") from exc


# ── Lógica de sincronización ──────────────────────────────────────────────────

def normalize_records(
    records: list[dict[str, Any]],
    *,
    required_fields: list[str] | None = None,
    rename: dict[str, str] | None = None,
    drop_nulls: bool = False,
) -> list[dict[str, Any]]:
    """
    Normaliza una lista de dicts usando pandas:
    - Renombra columnas según `rename` ({"campo_origen": "campo_destino"})
    - Filtra registros con campos requeridos vacíos si `drop_nulls=True`
    - Valida que existan los `required_fields`
    Devuelve la lista normalizada como dicts.
    """
    pd = _require_pandas()

    if not records:
        return []

    df = pd.DataFrame(records)

    if rename:
        df = df.rename(columns=rename)

    if required_fields:
        missing = [f for f in required_fields if f not in df.columns]
        if missing:
            raise ValueError(f"Campos requeridos ausentes en los registros: {missing}")
        if drop_nulls:
            df = df.dropna(subset=required_fields)

    return df.where(pd.notnull(df), None).to_dict(orient="records")


def diff_records(
    source: list[dict[str, Any]],
    target: list[dict[str, Any]],
    *,
    key: str = "id",
) -> dict[str, list[dict[str, Any]]]:
    """
    Compara dos listas de dicts por `key` y devuelve:
    - new: registros en source que no están en target
    - updated: registros cuya clave existe en ambos pero tienen diferencias
    - deleted: registros en target que ya no están en source
    - unchanged: registros idénticos en ambos

    Útil para sincronizaciones incrementales: solo procesas lo que cambió.
    """
    pd = _require_pandas()

    if not source and not target:
        return {"new": [], "updated": [], "deleted": [], "unchanged": []}

    df_src = pd.DataFrame(source).set_index(key) if source else pd.DataFrame()
    df_tgt = pd.DataFrame(target).set_index(key) if target else pd.DataFrame()

    src_keys = set(df_src.index) if not df_src.empty else set()
    tgt_keys = set(df_tgt.index) if not df_tgt.empty else set()

    new_keys = src_keys - tgt_keys
    deleted_keys = tgt_keys - src_keys
    common_keys = src_keys & tgt_keys

    new_records = df_src.loc[list(new_keys)].reset_index().to_dict(orient="records") if new_keys else []
    deleted_records = df_tgt.loc[list(deleted_keys)].reset_index().to_dict(orient="records") if deleted_keys else []

    updated = []
    unchanged = []
    for k in common_keys:
        row_src = df_src.loc[k].to_dict()
        row_tgt = df_tgt.loc[k].to_dict()
        if row_src != row_tgt:
            updated.append({key: k, **row_src})
        else:
            unchanged.append({key: k, **row_src})

    return {
        "new": new_records,
        "updated": updated,
        "deleted": deleted_records,
        "unchanged": unchanged,
    }


def build_sync_summary(
    diff: dict[str, list[dict[str, Any]]],
    *,
    tenant_id: str = "default",
    source_label: str = "origen",
) -> dict[str, Any]:
    """Construye el dict de resumen que se persiste en el estado de la tarea."""
    return {
        "kind": "sync",
        "tenant_id": tenant_id,
        "source_label": source_label,
        "new": len(diff.get("new", [])),
        "updated": len(diff.get("updated", [])),
        "deleted": len(diff.get("deleted", [])),
        "unchanged": len(diff.get("unchanged", [])),
        "total_processed": sum(
            len(v) for v in diff.values()
        ),
        "synced_at": _utcnow_iso(),
    }


# ── Tarea Celery ──────────────────────────────────────────────────────────────

if celery_app is not None:
    @celery_app.task(name="modulo_base.protocol_sync", bind=True, max_retries=3)
    def protocol_sync_task(
        self: Any,
        *,
        task_id: str = "",
        tenant_id: str = "default",
        source_records: list[dict[str, Any]] | None = None,
        target_records: list[dict[str, Any]] | None = None,
        diff_key: str = "id",
        required_fields: list[str] | None = None,
        rename: dict[str, str] | None = None,
        drop_nulls: bool = False,
        source_label: str = "origen",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Sincroniza dos conjuntos de registros (source vs target) usando pandas.

        Flujo:
          1. Normaliza source_records (renombra campos, valida requeridos)
          2. Calcula diff contra target_records
          3. Persiste el resumen en Redis via task_queue
          4. Devuelve el estado final

        Uso desde un servicio:
            task_queue.queue_task("protocol_sync", kwargs={
                "tenant_id": "acme",
                "source_records": [...],   # registros del sistema externo
                "target_records": [...],   # registros actuales en BD
                "diff_key": "codigo",
                "required_fields": ["codigo", "nombre"],
                "rename": {"code": "codigo", "name": "nombre"},
            })

        El llamador es responsable de aplicar el diff devuelto
        (new/updated/deleted) a la base de datos.
        """
        task_queue.report_task_state(
            "protocol_sync", task_id, status="running"
        )
        try:
            source = source_records or []
            target = target_records or []

            # 1 — Normalizar registros entrantes
            normalized = normalize_records(
                source,
                required_fields=required_fields,
                rename=rename,
                drop_nulls=drop_nulls,
            )

            # 2 — Calcular diferencias
            diff = diff_records(normalized, target, key=diff_key)

            # 3 — Construir resumen
            summary = build_sync_summary(diff, tenant_id=tenant_id, source_label=source_label)
            summary["diff"] = diff

            logger.info(
                "protocol_sync_completed",
                extra={
                    "tenant_id": tenant_id,
                    "new": summary["new"],
                    "updated": summary["updated"],
                    "deleted": summary["deleted"],
                },
            )

            # 4 — Persistir y devolver
            return task_queue.report_task_state(
                "protocol_sync",
                task_id,
                status="completed",
                result=summary,
            )

        except Exception as exc:
            logger.error(
                "protocol_sync_failed",
                extra={"tenant_id": tenant_id, "error": str(exc)},
                exc_info=True,
            )
            task_queue.report_task_state(
                "protocol_sync", task_id, status="failed", error=str(exc)
            )
            raise self.retry(exc=exc, countdown=15)


__all__ = [
    "build_sync_summary",
    "diff_records",
    "normalize_records",
    "registry",
    "task_queue",
]
