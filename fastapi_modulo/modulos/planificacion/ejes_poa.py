from __future__ import annotations

from datetime import datetime, timedelta
from textwrap import dedent
from typing import Any, Dict, List, Set
import sqlite3

from fastapi import APIRouter, Body, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()


_CORE_BOUND = False


def _bind_core_symbols() -> None:
    global _CORE_BOUND
    if _CORE_BOUND:
        return
    from fastapi_modulo import main as core

    names = [
        'render_backend_page',
        'SessionLocal',
        'StrategicAxisConfig',
        'StrategicObjectiveConfig',
        'POAActivity',
        'POASubactivity',
        'POADeliverableApproval',
        'UserNotificationRead',
        'DocumentoEvidencia',
        'PublicQuizSubmission',
        'Usuario',
        '_date_to_iso',
        '_activity_status',
        # '_allowed_objectives_for_user',
        'is_admin_or_superadmin',
        '_parse_date_field',
        '_validate_date_range',
        '_validate_child_date_range',
        '_current_user_record',
        '_user_aliases',
        '_resolve_process_owner_for_objective',
        '_is_user_process_owner',
        '_notification_user_key',
        '_normalize_tenant_id',
        # '_get_document_tenant',
            # '_can_authorize_documents',  # commented out: not present in fastapi_modulo.main
        'get_current_tenant',
        'is_superadmin',
    ]
    for name in names:
        globals()[name] = getattr(core, name)
    _CORE_BOUND = True


def _serialize_strategic_objective(obj: StrategicObjectiveConfig) -> Dict[str, Any]:
    _bind_core_symbols()
    return {
        "id": obj.id,
        "eje_id": obj.eje_id,
        "codigo": obj.codigo or "",
        "nombre": obj.nombre or "",
        "lider": obj.lider or "",
        "fecha_inicial": _date_to_iso(obj.fecha_inicial),
        "fecha_final": _date_to_iso(obj.fecha_final),
        "descripcion": obj.descripcion or "",
        "orden": obj.orden or 0,
    }


def _serialize_strategic_axis(axis: StrategicAxisConfig) -> Dict[str, Any]:
    _bind_core_symbols()
    objetivos = sorted(axis.objetivos or [], key=lambda item: (item.orden or 0, item.id or 0))
    return {
        "id": axis.id,
        "nombre": axis.nombre or "",
        "codigo": axis.codigo or "",
        "lider_departamento": axis.lider_departamento or "",
        "responsabilidad_directa": axis.responsabilidad_directa or "",
        "descripcion": axis.descripcion or "",
        "orden": axis.orden or 0,
        "objetivos_count": len(objetivos),
        "objetivos": [_serialize_strategic_objective(obj) for obj in objetivos],
    }


def _compose_axis_code(base_code: str, order_value: int) -> str:
    raw_prefix = (base_code or "").strip().lower()
    safe_prefix = "".join(ch for ch in raw_prefix if ch.isalnum()) or "m1"
    safe_order = int(order_value or 0)
    if safe_order <= 0:
        safe_order = 1
    return f"{safe_prefix}-{safe_order:02d}"


def _compose_objective_code(axis_code: str, order_value: int) -> str:
    raw_axis = (axis_code or "").strip().lower()
    axis_parts = [part for part in raw_axis.split("-") if part]
    if len(axis_parts) >= 2:
        axis_prefix = f"{axis_parts[0]}-{axis_parts[1]}"
    elif axis_parts:
        axis_prefix = f"{axis_parts[0]}-01"
    else:
        axis_prefix = "m1-01"
    safe_order = int(order_value or 0)
    if safe_order <= 0:
        safe_order = 1
    return f"{axis_prefix}-{safe_order:02d}"


def _collaborator_belongs_to_department(db, collaborator_name: str, department: str) -> bool:
    name = (collaborator_name or "").strip()
    dep = (department or "").strip()
    if not name or not dep:
        return False
    exists = (
        db.query(Usuario.id)
        .filter(Usuario.nombre == name, Usuario.departamento == dep)
        .first()
    )
    return bool(exists)


MAX_SUBTASK_DEPTH = 4
VALID_ACTIVITY_PERIODICITIES = {
    "diaria",
    "semanal",
    "quincenal",
    "mensual",
    "bimensual",
    "cada_xx_dias",
}


def _descendant_subactivity_ids(db, activity_id: int, root_id: int) -> List[int]:
    rows = (
        db.query(POASubactivity.id, POASubactivity.parent_subactivity_id)
        .filter(POASubactivity.activity_id == activity_id)
        .all()
    )
    children: Dict[int, List[int]] = {}
    for sub_id, parent_id in rows:
        if parent_id is None:
            continue
        children.setdefault(int(parent_id), []).append(int(sub_id))
    collected: List[int] = []
    stack = [int(root_id)]
    while stack:
        current = stack.pop()
        for child in children.get(current, []):
            collected.append(child)
            stack.append(child)
    return collected


def _serialize_poa_subactivity(item: POASubactivity) -> Dict[str, Any]:
    _bind_core_symbols()
    return {
        "id": item.id,
        "activity_id": item.activity_id,
        "parent_subactivity_id": item.parent_subactivity_id,
        "nivel": item.nivel or 1,
        "nombre": item.nombre or "",
        "codigo": item.codigo or "",
        "responsable": item.responsable or "",
        "entregable": item.entregable or "",
        "fecha_inicial": _date_to_iso(item.fecha_inicial),
        "fecha_final": _date_to_iso(item.fecha_final),
        "descripcion": item.descripcion or "",
    }


def _serialize_poa_activity(item: POAActivity, subactivities: List[POASubactivity]) -> Dict[str, Any]:
    _bind_core_symbols()
    return {
        "id": item.id,
        "objective_id": item.objective_id,
        "nombre": item.nombre or "",
        "codigo": item.codigo or "",
        "responsable": item.responsable or "",
        "entregable": item.entregable or "",
        "fecha_inicial": _date_to_iso(item.fecha_inicial),
        "fecha_final": _date_to_iso(item.fecha_final),
        "inicio_forzado": bool(item.inicio_forzado),
        "recurrente": bool(item.recurrente),
        "periodicidad": item.periodicidad or "",
        "cada_xx_dias": item.cada_xx_dias or 0,
        "status": _activity_status(item),
        "entrega_estado": item.entrega_estado or "ninguna",
        "entrega_solicitada_por": item.entrega_solicitada_por or "",
        "entrega_solicitada_at": item.entrega_solicitada_at.isoformat() if item.entrega_solicitada_at else "",
        "entrega_aprobada_por": item.entrega_aprobada_por or "",
        "entrega_aprobada_at": item.entrega_aprobada_at.isoformat() if item.entrega_aprobada_at else "",
        "created_by": item.created_by or "",
        "descripcion": item.descripcion or "",
        "subactivities": [
            _serialize_poa_subactivity(sub)
            for sub in sorted(subactivities, key=lambda x: ((x.nivel or 1), x.id or 0))
        ],
    }


EJES_ESTRATEGICOS_HTML = dedent("""
    <section class="axm-wrap">
      <style>
        .axm-wrap *{ box-sizing:border-box; }
        .axm-wrap{
          font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
          color:#0f172a;
          padding: 10px;
        }
        .axm-tabs{
          display:flex;
          align-items:center;
          gap: 6px;
          flex-wrap: wrap;
          border-bottom: 1px solid rgba(148,163,184,.28);
          padding-bottom: 8px;
          margin-bottom: 12px;
        }
        .axm-tab{
          border: 1px solid rgba(148,163,184,.32);
          background: #fff;
          border-radius: 12px;
          padding: 8px 12px;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          font-weight: 700;
          color: #0f172a;
          cursor: pointer;
        }
        .axm-tab.active{
          background: rgba(15,61,46,.10);
          border-color: rgba(15,61,46,.34);
        }
        .axm-tab .tab-icon{
          width: 16px;
          height: 16px;
          display: inline-block;
          flex: 0 0 auto;
        }
        .axm-tab-panel{
          background: rgba(255,255,255,.92);
          border: 1px solid rgba(148,163,184,.30);
          border-radius: 18px;
          min-height: 62vh;
          display:flex;
          align-items:center;
          justify-content:center;
          text-align:center;
          padding: 20px;
          font-size: 28px;
          font-weight: 700;
          color: #0f172a;
        }
        .axm-identidad{
          display: none;
          background: rgba(255,255,255,.92);
          border: 1px solid rgba(148,163,184,.30);
          border-radius: 18px;
          padding: 14px;
          margin-bottom: 12px;
        }
        .axm-id-acc{
          border: 1px solid rgba(148,163,184,.32);
          border-radius: 14px;
          background: #fff;
          margin-bottom: 10px;
          overflow: hidden;
        }
        .axm-id-acc:last-child{ margin-bottom: 0; }
        .axm-id-acc > summary{
          cursor: pointer;
          padding: 12px 14px;
          font-weight: 800;
          background: rgba(15,61,46,.08);
          border-bottom: 1px solid rgba(148,163,184,.24);
          list-style: none;
        }
        .axm-id-acc > summary::-webkit-details-marker{ display:none; }
        .axm-id-grid{
          display:grid;
          grid-template-columns: minmax(280px, 1fr) minmax(320px, 1fr);
          gap: 12px;
          padding: 12px;
        }
        .axm-id-left{
          display:grid;
          gap: 8px;
          align-content:start;
        }
        .axm-id-lines{
          display:grid;
          gap: 8px;
        }
        .axm-id-row{
          display:grid;
          grid-template-columns: 78px 1fr auto auto;
          gap: 8px;
          align-items:center;
        }
        .axm-id-code{
          width: 100%;
          border: 1px solid rgba(148,163,184,.42);
          border-radius: 10px;
          padding: 9px 10px;
          font-size: 13px;
          font-weight: 700;
          text-transform: uppercase;
          background: #fff;
          color: #0f3d2e;
        }
        .axm-id-tag{
          font-size: 12px;
          font-weight: 800;
          color: #0f3d2e;
          text-transform: uppercase;
        }
        .axm-id-input{
          width: 100%;
          border: 1px solid rgba(148,163,184,.42);
          border-radius: 10px;
          padding: 9px 10px;
          font-size: 14px;
          background: #fff;
        }
        .axm-id-remove{
          border: 1px solid rgba(239,68,68,.28);
          background: #fff5f5;
          color: #b91c1c;
          border-radius: 10px;
          padding: 8px 10px;
          font-weight: 700;
          cursor: pointer;
        }
        .axm-id-action{
          width: 34px;
          height: 34px;
          border-radius: 10px;
          border: 1px solid rgba(148,163,184,.32);
          background: #fff;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          padding: 0;
        }
        .axm-id-action img{
          width: 16px;
          height: 16px;
          object-fit: contain;
          display: block;
        }
        .axm-id-action.edit{
          border-color: rgba(15,61,46,.28);
          background: rgba(15,61,46,.08);
        }
        .axm-id-action.delete{
          border-color: rgba(239,68,68,.28);
          background: #fff5f5;
        }
        .axm-id-add{
          justify-self:start;
          border: 0;
          border-radius: 0;
          padding: 0;
          background: transparent;
          color: #0f3d2e;
          font-weight: 400;
          font-style: italic;
          cursor: pointer;
          text-decoration: underline;
          text-underline-offset: 2px;
        }
        .axm-id-right{
          border: 0;
          border-radius: 0;
          background: transparent;
          box-shadow: 14px 0 24px -16px rgba(15,23,42,.35);
          padding: 14px;
          min-height: 180px;
          display: grid;
          align-content: center;
          justify-items: center;
          gap: 8px;
        }
        .axm-id-right h4{
          margin: 0;
          font-size: 14px;
          color: var(--sidebar-bottom, #0f172a);
          letter-spacing: .02em;
          text-transform: uppercase;
          text-align: center;
        }
        .axm-id-full{
          margin: 0;
          color: #1f2937;
          line-height: 1.6;
          white-space: pre-line;
          text-align: center;
        }
        @media (max-width: 980px){
          .axm-id-grid{ grid-template-columns: 1fr; }
        }
        .axm-intro{
          background: rgba(255,255,255,.92);
          border: 1px solid rgba(148,163,184,.30);
          border-radius: 18px;
          padding: 14px;
          margin-bottom: 12px;
          color: #0f172a;
          line-height: 1.55;
        }
        .axm-intro p{
          margin: 0 0 8px;
          color: #334155;
        }
        .axm-intro ul{
          margin: 0;
          padding-left: 18px;
          color: #334155;
          display: grid;
          gap: 4px;
        }
        .axm-grid{
          display:grid;
          grid-template-columns: 1fr;
          gap: 14px;
        }
        .axm-card{
          background: rgba(255,255,255,.92);
          border: 1px solid rgba(148,163,184,.30);
          border-radius: 18px;
          padding: 14px;
          box-shadow: 0 8px 20px rgba(15,23,42,.06);
        }
        .axm-title{ margin:0; font-size: 20px; letter-spacing: -0.02em; }
        .axm-sub{ margin: 6px 0 0; color:#64748b; font-size:13px; }
        .axm-list{ margin-top: 12px; display:flex; flex-direction:column; gap: 10px; max-height: 65vh; overflow:auto; }
        .axm-axis-btn{
          width: 100%;
          border: 1px solid rgba(148,163,184,.32);
          background: rgba(255,255,255,.96);
          border-radius: 14px;
          padding: 12px;
          text-align: left;
          display:flex;
          align-items:center;
          justify-content:space-between;
          gap: 10px;
          cursor:pointer;
        }
        .axm-axis-btn.active{
          background: rgba(15,61,46,.08);
          border-color: rgba(15,61,46,.32);
        }
        .axm-axis-meta{ color:#64748b; font-size: 12px; }
        .axm-count{
          font-size: 12px;
          font-weight: 800;
          border:1px solid rgba(15,23,42,.14);
          border-radius: 999px;
          padding: 4px 8px;
          background: rgba(15,23,42,.04);
        }
        .axm-row{ display:grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .axm-field{ display:flex; flex-direction:column; gap: 6px; margin-top: 10px; }
        .axm-field label{ font-size: 12px; color:#475569; font-weight:700; letter-spacing: .02em; }
        .axm-base-grid{
          display: grid;
          grid-template-columns: 16fr 20fr;
          gap: 10px;
          align-items: end;
        }
        .axm-axis-main-row{
          display: grid;
          grid-template-columns: 15fr 50fr 15fr 20fr;
          gap: 10px;
          align-items: end;
        }
        .axm-axis-main-row .axm-field{
          margin-top: 0;
        }
        .axm-axis-main-row .axm-base-grid{
          display: contents;
        }
        .axm-axis-main-row .axm-base-grid > *{
          min-width: 0;
        }
        .axm-base-preview{
          min-height: 40px;
          display: flex;
          align-items: center;
          padding: 6px 8px;
          border: 1px dashed rgba(148,163,184,.45);
          border-radius: 10px;
          color: #64748b;
          font-size: 11px;
          font-style: italic;
          line-height: 1.35;
          background: rgba(255,255,255,.7);
        }
        .axm-input, .axm-textarea{
          width:100%;
          border:1px solid rgba(148,163,184,.42);
          border-radius: 12px;
          padding: 10px 12px;
          font-size: 14px;
          background: #fff;
        }
        .axm-axis-code-readonly{
          width: auto !important;
          min-width: 64px;
          max-width: 78px;
          padding-right: 10px;
          text-align: center;
          font-weight: 400;
          font-style: italic;
        }
        .axm-textarea{ min-height: 82px; resize: vertical; }
        .axm-actions{ display:flex; gap:8px; flex-wrap:wrap; margin-top: 12px; }
        .axm-btn{
          border:1px solid rgba(148,163,184,.42);
          border-radius: 12px;
          padding: 9px 12px;
          background:#fff;
          cursor:pointer;
          font-weight:700;
          font-size: 13px;
        }
        .axm-btn.primary{ background:#0f3d2e; border-color:#0f3d2e; color:#fff; }
        .axm-btn.warn{ background:#ef4444; border-color:#ef4444; color:#fff; }
        .axm-obj-layout{
          margin-top: 12px;
          display:grid;
          grid-template-columns: 30% 70%;
          gap: 0;
          align-items: start;
          border: 1px solid rgba(148,163,184,.30);
          border-radius: 14px;
          overflow: hidden;
          background: rgba(255,255,255,.95);
        }
        .axm-obj-layout > aside{
          padding: 12px;
          border-right: 1px solid rgba(148,163,184,.26);
          background: #e5e7eb;
        }
        .axm-obj-layout > section{
          padding: 12px;
        }
        .axm-obj-axis-list{
          display: flex;
          flex-direction: column;
          gap: 8px;
          max-height: 380px;
          overflow: auto;
        }
        .axm-obj-axis-btn{
          width: 100%;
          text-align: left;
          border: 1px solid rgba(148,163,184,.32);
          border-radius: 12px;
          padding: 10px 12px;
          background: rgba(229,231,235,.92);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          color: #334155;
          font-size: 12px;
          font-style: italic;
          font-weight: 400;
        }
        .axm-obj-axis-btn strong{
          font-size: 12px;
          font-style: italic;
          font-weight: 400;
        }
        .axm-obj-axis-btn.active{
          background: #ffffff;
          border-color: rgba(15,61,46,.30);
        }
        .axm-obj-axis-arrow{
          font-size: 18px;
          color: #64748b;
          line-height: 1;
        }
        .axm-obj-list{ display:flex; flex-direction:column; gap: 8px; max-height: 320px; overflow:auto; }
        .axm-obj-btn{
          width: 100%;
          text-align: left;
          border:1px solid rgba(148,163,184,.32);
          border-radius: 12px;
          padding: 10px;
          background: rgba(255,255,255,.95);
          cursor: pointer;
        }
        .axm-obj-btn.active{
          background: rgba(15,61,46,.08);
          border-color: rgba(15,61,46,.30);
        }
        .axm-obj-sub{
          margin-top: 4px;
          font-size: 11px;
          font-style: italic;
          color: #64748b;
        }
        .axm-obj-form{
          border:1px solid rgba(148,163,184,.32);
          border-radius: 12px;
          padding: 14px;
          background: rgba(255,255,255,.95);
        }
        .axm-obj-form .axm-row{
          grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
        }
        .axm-obj-form .axm-input,
        .axm-obj-form .axm-textarea{
          min-width: 0;
          width: 100%;
        }
        .axm-obj-form .axm-textarea{
          min-height: 116px;
        }
        .axm-obj-grid{ display:grid; grid-template-columns: 150px 1fr; gap: 8px; }
        .axm-msg{ margin-top: 10px; font-size: 13px; color:#0f3d2e; min-height: 1.2em; }
        .axm-modal{
          position: fixed;
          inset: 0;
          background: rgba(15,23,42,.45);
          display: none;
          align-items: center;
          justify-content: center;
          z-index: 99999;
          padding: 24px 12px;
        }
        .axm-modal.open{
          display: flex;
        }
        .axm-modal-dialog{
          width: min(1280px, 96vw);
          max-height: 92vh;
          overflow: auto;
          background: #eef4f2;
          border: 1px solid rgba(148,163,184,.35);
          border-radius: 24px;
          box-shadow: 0 24px 44px rgba(15,23,42,.28);
          padding: 20px;
        }
        .axm-modal-head{
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          margin-bottom: 8px;
        }
        .axm-close{
          width: 34px;
          height: 34px;
          border-radius: 10px;
          border: 1px solid rgba(148,163,184,.40);
          background: #fff;
          color: #0f172a;
          font-size: 20px;
          line-height: 1;
          cursor: pointer;
        }
        .axm-arbol{
          display: none;
          background: rgba(255,255,255,.92);
          border: 1px solid rgba(148,163,184,.30);
          border-radius: 18px;
          padding: 14px;
          margin-bottom: 12px;
        }
        .axm-arbol h3{
          margin: 0;
          font-size: 18px;
        }
        .axm-arbol-sub{
          margin: 6px 0 12px;
          color: #64748b;
          font-size: 13px;
        }
        .axm-tree-roots{
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
        }
        .axm-tree-root{
          border: 1px solid rgba(148,163,184,.28);
          border-radius: 12px;
          padding: 10px;
          background: #fff;
        }
        .axm-tree-root h4{
          margin: 0 0 6px;
          font-size: 13px;
          color: #0f3d2e;
          text-transform: uppercase;
          letter-spacing: .02em;
        }
        .axm-tree-lines{
          margin: 0;
          padding: 0;
          list-style: none;
          display: grid;
          gap: 6px;
        }
        .axm-tree-line{
          font-size: 13px;
          color: #1f2937;
          display: flex;
          gap: 6px;
          align-items: baseline;
        }
        .axm-tree-code{
          display: inline-flex;
          min-width: 44px;
          justify-content: center;
          border: 1px solid rgba(15,61,46,.30);
          border-radius: 999px;
          padding: 2px 8px;
          font-size: 11px;
          font-weight: 800;
          color: #0f3d2e;
          background: rgba(15,61,46,.08);
          text-transform: uppercase;
        }
        .axm-tree-divider{
          margin: 12px auto;
          width: 2px;
          height: 24px;
          background: rgba(15,61,46,.35);
          border-radius: 999px;
        }
        .axm-tree-axes{
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
          gap: 10px;
        }
        .axm-tree-axis{
          border: 1px solid rgba(148,163,184,.30);
          border-radius: 12px;
          background: #fff;
          padding: 10px;
          box-shadow: 0 8px 18px rgba(15,23,42,.06);
        }
        .axm-tree-axis h5{
          margin: 6px 0 4px;
          font-size: 15px;
        }
        .axm-tree-axis p{
          margin: 0;
          font-size: 12px;
          color: #64748b;
        }
        @media (max-width: 980px){
          .axm-obj-layout{ grid-template-columns: 1fr; }
          .axm-obj-layout > aside{ border-right: 0; border-bottom: 1px solid rgba(148,163,184,.26); }
          .axm-obj-form .axm-row{ grid-template-columns: 1fr; }
        }
        @media (max-width: 980px){
          .axm-grid{ grid-template-columns: 1fr; }
          .axm-list{ max-height: 36vh; }
          .axm-row{ grid-template-columns: 1fr; }
          .axm-obj-grid{ grid-template-columns: 1fr; }
          .axm-tree-roots{ grid-template-columns: 1fr; }
          .axm-axis-main-row{ grid-template-columns: 1fr; }
          .axm-axis-main-row .axm-base-grid{ display: grid; grid-template-columns: 1fr; }
        }
      </style>

      <article class="axm-intro">
        <p>Para entender a fondo la planificación estratégica de la organización, hemos dispuesto de manera clara la jerarquía que seguimos. Como podrán ver en el Resumen Gráfico, todo parte de nuestra Misión y Visión (que definen nuestra razón de ser y hacia dónde nos dirigimos). De ahí se despliegan los grandes Ejes Estratégicos, que son nuestros pilares fundamentales.</p>
        <p>Les invitamos a consultar cada una de las pestañas para explorar el detalle de estos niveles:</p>
        <ul>
          <li>Primer pestaña se definen los componentes de la misión y visión.</li>
          <li>Segunda pestaña, encontrarán los Objetivos Estratégicos, que traducen cada eje en metas concretas.</li>
          <li>Tercera, están las Líneas de Acción, que describen el camino elegido para alcanzar esos objetivos.</li>
          <li>Cuarta pestaña, se detallan las lineas de acción, donde veremos los hitos específicos y los recursos necesarios para hacer realidad nuestra visión, esta es la base del POA.</li>
        </ul>
      </article>

      <div class="axm-tabs">
        <button type="button" class="axm-tab active" data-axm-tab="identidad"><img src="/templates/icon/identidad.svg" alt="" class="tab-icon">Identidad</button>
        <button type="button" class="axm-tab" data-axm-tab="ejes"><img src="/templates/icon/ejes.svg" alt="" class="tab-icon">Ejes estratégicos</button>
        <button type="button" class="axm-tab" data-axm-tab="objetivos"><img src="/templates/icon/objetivos.svg" alt="" class="tab-icon">Objetivos</button>
        <button type="button" class="axm-tab" data-axm-tab="arbol"><img src="/templates/icon/mapa.svg" alt="" class="tab-icon">Arbol estratégico</button>
      </div>
      <section class="axm-identidad" id="axm-identidad-panel">
        <details class="axm-id-acc" open>
          <summary>Misión</summary>
          <div class="axm-id-grid">
            <div class="axm-id-left">
              <div class="axm-id-lines" id="axm-mision-lines"></div>
              <button type="button" class="axm-id-add" id="axm-mision-add">Agregar línea</button>
              <div id="axm-mision-hidden" style="display:none;"></div>
            </div>
            <div class="axm-id-right">
              <h4>Misión</h4>
              <p class="axm-id-full" id="axm-mision-full"></p>
            </div>
          </div>
        </details>
        <details class="axm-id-acc">
          <summary>Visión</summary>
          <div class="axm-id-grid">
            <div class="axm-id-left">
              <div class="axm-id-lines" id="axm-vision-lines"></div>
              <button type="button" class="axm-id-add" id="axm-vision-add">Agregar línea</button>
              <div id="axm-vision-hidden" style="display:none;"></div>
            </div>
            <div class="axm-id-right">
              <h4>Visión</h4>
              <p class="axm-id-full" id="axm-vision-full"></p>
            </div>
          </div>
        </details>
      </section>
      <section class="axm-arbol" id="axm-arbol-panel">
        <h3>Arbol estratégico</h3>
        <p class="axm-arbol-sub">Base: Misión y Visión. Ramas: ejes estratégicos con su código original.</p>
        <div class="axm-tree-roots" id="axm-tree-roots"></div>
        <div class="axm-tree-divider"></div>
        <div class="axm-tree-axes" id="axm-tree-axes"></div>
      </section>
      <section class="axm-tab-panel" id="axm-tab-panel">No tiene acceso, consulte con el administrador</section>
      <section class="axm-card" id="axm-objetivos-panel" style="display:none;">
        <h3 style="margin:0;font-size:16px;">Objetivos del eje</h3>
        <div class="axm-obj-layout">
          <aside>
            <h4 style="margin:0 0 8px;font-size:14px;">Ejes estratégicos</h4>
            <div class="axm-obj-axis-list" id="axm-obj-axis-list"></div>
          </aside>
          <section>
            <div class="axm-actions" style="margin-top:0;justify-content:space-between;">
              <h4 id="axm-obj-axis-title" style="margin:0;font-size:14px;">Objetivos</h4>
              <button class="axm-btn primary" id="axm-add-obj" type="button">Agregar objetivo</button>
            </div>
            <div class="axm-obj-list" id="axm-obj-list"></div>
          </section>
        </div>
      </section>

      <div class="axm-grid">
        <aside class="axm-card">
          <h2 class="axm-title">Ejes estratégicos</h2>
          <p class="axm-sub">Selecciona un eje para editarlo o crea uno nuevo.</p>
          <div class="axm-actions">
            <button class="axm-btn primary" id="axm-add-axis" type="button" onclick="(function(){var m=document.getElementById('axm-axis-modal');if(m){m.classList.add('open');m.style.display='flex';document.body.style.overflow='hidden';}})();">Agregar eje</button>
          </div>
          <div class="axm-list" id="axm-axis-list"></div>
        </aside>
      </div>

      <div class="axm-modal" id="axm-axis-modal" role="dialog" aria-modal="true" aria-labelledby="axm-axis-modal-title">
        <section class="axm-modal-dialog">
          <div class="axm-modal-head">
            <h2 class="axm-title" id="axm-axis-modal-title">Gestión de ejes y objetivos</h2>
            <button class="axm-close" id="axm-axis-modal-close" type="button" aria-label="Cerrar">×</button>
          </div>
          <p class="axm-sub">Edita, guarda o elimina ejes estratégicos y sus objetivos.</p>
          <div class="axm-axis-main-row">
            <div class="axm-field">
              <label for="axm-axis-code">Código del eje (xx-yy)</label>
              <input id="axm-axis-code" class="axm-input axm-axis-code-readonly" type="text" readonly>
            </div>
            <div class="axm-field">
              <label for="axm-axis-name">Nombre del eje</label>
              <input id="axm-axis-name" class="axm-input" type="text" placeholder="Ej. Gobernanza y cumplimiento">
            </div>
            <div class="axm-base-grid">
              <div class="axm-field">
                <label for="axm-axis-base-code">Cod base</label>
                <select id="axm-axis-base-code" class="axm-input">
                  <option value="m1">m1</option>
                </select>
              </div>
              <div class="axm-field">
                <label for="axm-axis-base-preview">Texto cod base</label>
                <div id="axm-axis-base-preview" class="axm-base-preview">Selecciona un código para ver su línea asociada.</div>
              </div>
            </div>
          </div>
          <div class="axm-row">
            <div class="axm-field">
              <label for="axm-axis-leader">Líder del eje estratégico</label>
              <select id="axm-axis-leader" class="axm-input">
                <option value="">Selecciona departamento</option>
              </select>
            </div>
            <div class="axm-field">
              <label for="axm-axis-owner">Responsabilidad directa</label>
              <select id="axm-axis-owner" class="axm-input">
                <option value="">Selecciona colaborador</option>
              </select>
            </div>
          </div>
          <div class="axm-field">
            <label for="axm-axis-desc">Descripción</label>
            <textarea id="axm-axis-desc" class="axm-textarea" placeholder="Describe el propósito del eje"></textarea>
          </div>
          <div class="axm-actions">
            <button class="axm-btn primary" id="axm-save-axis" type="button">Guardar eje</button>
            <button class="axm-btn warn" id="axm-delete-axis" type="button">Eliminar eje</button>
          </div>
          <div class="axm-msg" id="axm-axis-msg" aria-live="polite"></div>
        </section>
      </div>
      <div class="axm-modal" id="axm-obj-modal" role="dialog" aria-modal="true" aria-labelledby="axm-obj-modal-title">
        <section class="axm-modal-dialog">
          <div class="axm-modal-head">
            <h2 class="axm-title" id="axm-obj-modal-title">Objetivo estratégico</h2>
            <button class="axm-close" id="axm-obj-modal-close" type="button" aria-label="Cerrar">×</button>
          </div>
          <div class="axm-obj-form">
            <div class="axm-field" style="margin-top:0;">
              <label for="axm-obj-name">Nombre</label>
              <input id="axm-obj-name" class="axm-input" type="text" placeholder="Nombre del objetivo">
            </div>
            <div class="axm-field">
              <label for="axm-obj-code">Código (xx-yy-zz)</label>
              <input id="axm-obj-code" class="axm-input" type="text" placeholder="xx-yy-zz" readonly>
            </div>
            <div class="axm-field">
              <label for="axm-obj-leader">Lider</label>
              <select id="axm-obj-leader" class="axm-input">
                <option value="">Selecciona colaborador</option>
              </select>
            </div>
            <div class="axm-row">
              <div class="axm-field">
                <label for="axm-obj-start">Fecha inicial</label>
                <input id="axm-obj-start" class="axm-input" type="date">
              </div>
              <div class="axm-field">
                <label for="axm-obj-end">Fecha final</label>
                <input id="axm-obj-end" class="axm-input" type="date">
              </div>
            </div>
            <div class="axm-field">
              <label for="axm-obj-desc">Descripción</label>
              <textarea id="axm-obj-desc" class="axm-textarea" placeholder="Descripción del objetivo"></textarea>
            </div>
            <div class="axm-actions">
              <button class="axm-btn primary" id="axm-save-obj" type="button">Guardar objetivo</button>
              <button class="axm-btn warn" id="axm-delete-obj" type="button">Eliminar objetivo</button>
            </div>
            <div class="axm-msg" id="axm-msg" aria-live="polite"></div>
          </div>
        </section>
      </div>

      <script>
        (() => {
          const tabs = document.querySelectorAll(".axm-tab[data-axm-tab]");
          const panel = document.getElementById("axm-tab-panel");
          const identidadPanel = document.getElementById("axm-identidad-panel");
          const blockedContainer = document.querySelector(".axm-grid");
          const objetivosPanel = document.getElementById("axm-objetivos-panel");
          const arbolPanel = document.getElementById("axm-arbol-panel");
          const treeRootsEl = document.getElementById("axm-tree-roots");
          const treeAxesEl = document.getElementById("axm-tree-axes");
          const setupIdentityComposer = (prefix, linesId, hiddenId, fullId, addId) => {
            const linesHost = document.getElementById(linesId);
            const hiddenHost = document.getElementById(hiddenId);
            const fullHost = document.getElementById(fullId);
            const addBtn = document.getElementById(addId);
            if (!linesHost || !hiddenHost || !fullHost || !addBtn) return null;
            let lines = [{ code: `${prefix}1`, text: "" }];
            let onChange = () => {};
            const cleanCode = (value, idx) => {
              const raw = (value || "").trim().toLowerCase();
              return raw || `${prefix}${idx + 1}`;
            };
            const getLines = () => lines.map((item, idx) => ({
              code: cleanCode(item.code, idx),
              text: (item.text || "").trim(),
            }));
            const syncOutputs = () => {
              const safe = getLines();
              hiddenHost.innerHTML = "";
              safe.forEach((item, idx) => {
                const hiddenText = document.createElement("input");
                hiddenText.type = "hidden";
                hiddenText.name = `${prefix}${idx + 1}`;
                hiddenText.value = item.text || "";
                hiddenHost.appendChild(hiddenText);

                const hiddenCode = document.createElement("input");
                hiddenCode.type = "hidden";
                hiddenCode.name = `${prefix}${idx + 1}_code`;
                hiddenCode.value = item.code || "";
                hiddenHost.appendChild(hiddenCode);
              });
              fullHost.textContent = safe.map((line) => line.text).filter(Boolean).join(" ");
              onChange(safe);
            };
            const render = () => {
              linesHost.innerHTML = "";
              const safe = lines.length ? lines : [{ code: `${prefix}1`, text: "" }];
              safe.forEach((value, idx) => {
                const row = document.createElement("div");
                row.className = "axm-id-row";
                const codeInput = document.createElement("input");
                codeInput.type = "text";
                codeInput.className = "axm-id-code";
                codeInput.value = cleanCode(value.code, idx);
                codeInput.placeholder = `Código ${prefix}${idx + 1}`;
                codeInput.addEventListener("input", () => {
                  lines[idx].code = codeInput.value;
                  syncOutputs();
                });
                const input = document.createElement("input");
                input.type = "text";
                input.className = "axm-id-input";
                input.value = value.text || "";
                input.placeholder = `Escribe ${prefix}${idx + 1}`;
                input.addEventListener("input", () => {
                  lines[idx].text = input.value;
                  syncOutputs();
                });
                const editBtn = document.createElement("button");
                editBtn.type = "button";
                editBtn.className = "axm-id-action edit";
                editBtn.setAttribute("aria-label", `Editar ${prefix}${idx + 1}`);
                editBtn.innerHTML = '<img src="/icon/editar.svg" alt="">';
                editBtn.addEventListener("click", () => {
                  input.focus();
                  input.select();
                });
                const removeBtn = document.createElement("button");
                removeBtn.type = "button";
                removeBtn.className = "axm-id-action delete";
                removeBtn.setAttribute("aria-label", `Eliminar ${prefix}${idx + 1}`);
                removeBtn.innerHTML = '<img src="/icon/eliminar.svg" alt="">';
                removeBtn.addEventListener("click", () => {
                  lines.splice(idx, 1);
                  if (!lines.length) lines = [{ code: `${prefix}1`, text: "" }];
                  render();
                });
                row.appendChild(codeInput);
                row.appendChild(input);
                row.appendChild(editBtn);
                row.appendChild(removeBtn);
                linesHost.appendChild(row);
              });
              syncOutputs();
            };
            addBtn.addEventListener("click", () => {
              lines.push({ code: `${prefix}${lines.length + 1}`, text: "" });
              render();
            });
            render();
            return {
              getLines,
              onChange: (handler) => {
                onChange = typeof handler === "function" ? handler : () => {};
                onChange(getLines());
              },
            };
          };
          const misionComposer = setupIdentityComposer("m", "axm-mision-lines", "axm-mision-hidden", "axm-mision-full", "axm-mision-add");
          const visionComposer = setupIdentityComposer("v", "axm-vision-lines", "axm-vision-hidden", "axm-vision-full", "axm-vision-add");
          const applyTabView = (tabKey) => {
            const showIdentidad = tabKey === "identidad";
            const showEjes = tabKey === "ejes";
            const showObjetivos = tabKey === "objetivos";
            const showArbol = tabKey === "arbol";
            if (panel) {
              panel.textContent = "No tiene acceso, consulte con el administrador";
              panel.style.display = showIdentidad || showEjes || showObjetivos || showArbol ? "none" : "flex";
            }
            if (identidadPanel) {
              identidadPanel.style.display = showIdentidad ? "block" : "none";
            }
            if (blockedContainer) {
              blockedContainer.style.display = showEjes ? "grid" : "none";
            }
            if (objetivosPanel) {
              objetivosPanel.style.display = showObjetivos ? "block" : "none";
            }
            if (arbolPanel) {
              arbolPanel.style.display = showArbol ? "block" : "none";
            }
            if (showArbol) {
              renderStrategicTree();
            }
          };
          if (tabs.length) {
            tabs.forEach((tabBtn) => {
              tabBtn.addEventListener("click", () => {
                tabs.forEach((btn) => btn.classList.remove("active"));
                tabBtn.classList.add("active");
                applyTabView(tabBtn.getAttribute("data-axm-tab"));
              });
            });
          }
          const activeTab = document.querySelector(".axm-tab.active");
          applyTabView(activeTab ? activeTab.getAttribute("data-axm-tab") : "identidad");

          const axisListEl = document.getElementById("axm-axis-list");
          const axisModalEl = document.getElementById("axm-axis-modal");
          const axisModalCloseEl = document.getElementById("axm-axis-modal-close");
          const objModalEl = document.getElementById("axm-obj-modal");
          const objModalCloseEl = document.getElementById("axm-obj-modal-close");
          const objAxisListEl = document.getElementById("axm-obj-axis-list");
          const objAxisTitleEl = document.getElementById("axm-obj-axis-title");
          const objListEl = document.getElementById("axm-obj-list");
          const axisNameEl = document.getElementById("axm-axis-name");
          const axisBaseCodeEl = document.getElementById("axm-axis-base-code");
          const axisBasePreviewEl = document.getElementById("axm-axis-base-preview");
          const axisCodeEl = document.getElementById("axm-axis-code");
          const axisLeaderEl = document.getElementById("axm-axis-leader");
          const axisOwnerEl = document.getElementById("axm-axis-owner");
          const axisDescEl = document.getElementById("axm-axis-desc");
          const objNameEl = document.getElementById("axm-obj-name");
          const objCodeEl = document.getElementById("axm-obj-code");
          const objLeaderEl = document.getElementById("axm-obj-leader");
          const objStartEl = document.getElementById("axm-obj-start");
          const objEndEl = document.getElementById("axm-obj-end");
          const objDescEl = document.getElementById("axm-obj-desc");
          const msgEl = document.getElementById("axm-msg");
          const axisMsgEl = document.getElementById("axm-axis-msg");
          const addAxisBtn = document.getElementById("axm-add-axis");
          const saveAxisBtn = document.getElementById("axm-save-axis");
          const deleteAxisBtn = document.getElementById("axm-delete-axis");
          const addObjBtn = document.getElementById("axm-add-obj");
          const saveObjBtn = document.getElementById("axm-save-obj");
          const deleteObjBtn = document.getElementById("axm-delete-obj");

          let axes = [];
          let departments = [];
          let axisDepartmentCollaborators = [];
          let collaborators = [];
          let selectedAxisId = null;
          let selectedObjectiveId = null;
          const toId = (value) => {
            const n = Number(value);
            return Number.isFinite(n) ? n : null;
          };
          const axisPosition = (axis) => {
            const idx = axes.findIndex((item) => toId(item.id) === toId(axis?.id));
            return idx >= 0 ? idx + 1 : Math.max(1, Number(axis?.orden || 1));
          };
          const objectivePosition = (objective) => {
            const axis = selectedAxis();
            const list = (axis && Array.isArray(axis.objetivos)) ? axis.objetivos : [];
            const idx = list.findIndex((item) => toId(item.id) === toId(objective?.id));
            return idx >= 0 ? idx + 1 : Math.max(1, Number(objective?.orden || 1));
          };
          const buildAxisCode = (baseCode, orderNumber) => {
            const normalizedBase = String(baseCode || "").trim().toLowerCase().replace(/[^a-z0-9]/g, "") || "m1";
            const numericOrder = Number(orderNumber);
            const safeOrder = Number.isFinite(numericOrder) && numericOrder > 0 ? numericOrder : 1;
            return `${normalizedBase}-${String(safeOrder).padStart(2, "0")}`;
          };
          const buildObjectiveCode = (axisCode, orderNumber) => {
            const rawAxis = String(axisCode || "").trim().toLowerCase();
            const parts = rawAxis.split("-").filter(Boolean);
            const axisPrefix = parts.length >= 2 ? `${parts[0]}-${parts[1]}` : (parts.length === 1 ? `${parts[0]}-01` : "m1-01");
            const numericOrder = Number(orderNumber);
            const safeOrder = Number.isFinite(numericOrder) && numericOrder > 0 ? numericOrder : 1;
            return `${axisPrefix}-${String(safeOrder).padStart(2, "0")}`;
          };
          const getIdentityCodeOptions = () => {
            const missionCodes = (misionComposer ? misionComposer.getLines() : []).map((line) => String(line.code || "").trim().toLowerCase());
            const visionCodes = (visionComposer ? visionComposer.getLines() : []).map((line) => String(line.code || "").trim().toLowerCase());
            const combined = missionCodes.concat(visionCodes).map((value) => value.replace(/[^a-z0-9]/g, "")).filter(Boolean);
            const unique = [];
            combined.forEach((value) => {
              if (!unique.includes(value)) unique.push(value);
            });
            if (!unique.length) unique.push("m1", "v1");
            return unique;
          };
          const getIdentityCodeEntries = () => {
            const mission = (misionComposer ? misionComposer.getLines() : []).map((line) => ({
              code: String(line.code || "").trim().toLowerCase().replace(/[^a-z0-9]/g, ""),
              text: String(line.text || "").trim(),
            }));
            const vision = (visionComposer ? visionComposer.getLines() : []).map((line) => ({
              code: String(line.code || "").trim().toLowerCase().replace(/[^a-z0-9]/g, ""),
              text: String(line.text || "").trim(),
            }));
            const merged = mission.concat(vision).filter((item) => item.code);
            const deduped = [];
            merged.forEach((item) => {
              if (!deduped.some((entry) => entry.code === item.code)) deduped.push(item);
            });
            if (!deduped.length) deduped.push({ code: "m1", text: "" }, { code: "v1", text: "" });
            return deduped;
          };
          const updateAxisBasePreview = () => {
            if (!axisBasePreviewEl) return;
            const selectedCode = axisBaseCodeEl && axisBaseCodeEl.value ? axisBaseCodeEl.value : "";
            const entries = getIdentityCodeEntries();
            const match = entries.find((item) => item.code === selectedCode);
            axisBasePreviewEl.textContent = (match && match.text)
              ? match.text
              : "Sin texto para este código. Puedes editarlo en Identidad.";
          };

          const openAxisModal = () => {
            if (!axisModalEl) return;
            if (axisModalEl.parentElement !== document.body) {
              document.body.appendChild(axisModalEl);
            }
            axisModalEl.classList.add("open");
            axisModalEl.style.display = "flex";
            axisModalEl.style.position = "fixed";
            axisModalEl.style.inset = "0";
            document.body.style.overflow = "hidden";
          };
          const closeAxisModal = () => {
            if (!axisModalEl) return;
            axisModalEl.classList.remove("open");
            axisModalEl.style.display = "none";
            document.body.style.overflow = "";
          };
          const openObjModal = () => {
            if (!objModalEl) return;
            if (objModalEl.parentElement !== document.body) {
              document.body.appendChild(objModalEl);
            }
            objModalEl.classList.add("open");
            objModalEl.style.display = "flex";
            objModalEl.style.position = "fixed";
            objModalEl.style.inset = "0";
            document.body.style.overflow = "hidden";
          };
          const closeObjModal = () => {
            if (!objModalEl) return;
            objModalEl.classList.remove("open");
            objModalEl.style.display = "none";
            document.body.style.overflow = "";
          };
          axisModalCloseEl && axisModalCloseEl.addEventListener("click", closeAxisModal);
          axisModalEl && axisModalEl.addEventListener("click", (event) => {
            if (event.target === axisModalEl) closeAxisModal();
          });
          objModalCloseEl && objModalCloseEl.addEventListener("click", closeObjModal);
          objModalEl && objModalEl.addEventListener("click", (event) => {
            if (event.target === objModalEl) closeObjModal();
          });
          if (axisModalEl && axisModalEl.parentElement !== document.body) {
            document.body.appendChild(axisModalEl);
          }
          if (objModalEl && objModalEl.parentElement !== document.body) {
            document.body.appendChild(objModalEl);
          }
          document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && axisModalEl && axisModalEl.classList.contains("open")) {
              closeAxisModal();
            }
            if (event.key === "Escape" && objModalEl && objModalEl.classList.contains("open")) {
              closeObjModal();
            }
          });

          const renderStrategicTree = () => {
            if (!treeRootsEl || !treeAxesEl) return;
            const missionLines = misionComposer ? misionComposer.getLines() : [];
            const visionLines = visionComposer ? visionComposer.getLines() : [];
            const rootBlock = (title, items) => {
              const linesHtml = (items || [])
                .filter((line) => (line.text || "").trim())
                .map((line) => `<li class="axm-tree-line"><span class="axm-tree-code">${line.code || "-"}</span><span>${line.text}</span></li>`)
                .join("");
              return `
                <article class="axm-tree-root">
                  <h4>${title}</h4>
                  <ul class="axm-tree-lines">${linesHtml || '<li class="axm-tree-line">Sin líneas definidas</li>'}</ul>
                </article>
              `;
            };
            treeRootsEl.innerHTML = `${rootBlock("Misión", missionLines)}${rootBlock("Visión", visionLines)}`;

            treeAxesEl.innerHTML = (axes || []).map((axis) => `
              <article class="axm-tree-axis">
                <span class="axm-tree-code">${axis.codigo || "sin-codigo"}</span>
                <h5>${axis.nombre || "Eje sin nombre"}</h5>
                <p>Conserva el código original definido para este eje.</p>
              </article>
            `).join("") || '<article class="axm-tree-axis"><h5>Sin ejes estratégicos</h5><p>Agrega ejes en la pestaña Ejes estratégicos.</p></article>';
          };

          const showMsg = (text, isError = false) => {
            const color = isError ? "#b91c1c" : "#0f3d2e";
            if (msgEl) {
              msgEl.style.color = color;
              msgEl.textContent = text || "";
            }
            if (axisMsgEl) {
              axisMsgEl.style.color = color;
              axisMsgEl.textContent = text || "";
            }
          };

          const requestJson = async (url, options = {}) => {
            const response = await fetch(url, {
              headers: { "Content-Type": "application/json" },
              credentials: "same-origin",
              ...options,
            });
            const raw = await response.text();
            const contentType = (response.headers.get("content-type") || "").toLowerCase();
            let payload = {};
            try {
              payload = raw ? JSON.parse(raw) : {};
            } catch (_err) {
              payload = {};
            }
            const redirectedToLogin = response.redirected && /\/login\b/.test(response.url || "");
            const looksLikeJson = contentType.includes("application/json");
            const successFlag = payload && typeof payload === "object" ? payload.success : undefined;
            if (redirectedToLogin) {
              throw new Error("Tu sesión expiró. Inicia sesión nuevamente.");
            }
            if (!response.ok || !looksLikeJson || successFlag !== true) {
              const fallback = raw && !payload.error ? raw.slice(0, 180) : "";
              throw new Error(payload.error || payload.detail || fallback || "No se pudo completar la operación.");
            }
            return payload;
          };

          const selectedAxis = () => {
            const targetId = toId(selectedAxisId);
            return axes.find((axis) => toId(axis.id) === targetId) || null;
          };
          const selectedObjective = () => {
            const axis = selectedAxis();
            if (!axis) return null;
            return (axis.objetivos || []).find((obj) => obj.id === selectedObjectiveId) || null;
          };
          const visualRangeError = (start, end, label) => {
            if (!start && !end) return "";
            if (!start || !end) return `${label}: completa fecha inicial y fecha final.`;
            if (start > end) return `${label}: la fecha inicial no puede ser mayor que la final.`;
            return "";
          };

          const renderDepartmentOptions = (selectedValue = "") => {
            if (!axisLeaderEl) return;
            const options = ['<option value="">Selecciona departamento</option>']
              .concat(
                departments.map((name) => {
                  const selected = name === selectedValue ? "selected" : "";
                  return `<option value="${name}" ${selected}>${name}</option>`;
                })
              );
            axisLeaderEl.innerHTML = options.join("");
          };
          const renderAxisOwnerOptions = (selectedValue = "") => {
            if (!axisOwnerEl) return;
            const options = ['<option value="">Selecciona colaborador</option>']
              .concat(
                axisDepartmentCollaborators.map((name) => {
                  const selected = name === selectedValue ? "selected" : "";
                  return `<option value="${name}" ${selected}>${name}</option>`;
                })
              );
            axisOwnerEl.innerHTML = options.join("");
          };
          const loadAxisDepartmentCollaborators = async (department, selectedValue = "") => {
            if (!axisOwnerEl) return;
            const dep = (department || "").trim();
            if (!dep) {
              axisDepartmentCollaborators = [];
              renderAxisOwnerOptions("");
              return;
            }
            try {
              const payload = await requestJson(`/api/strategic-axes/collaborators-by-department?department=${encodeURIComponent(dep)}`);
              axisDepartmentCollaborators = Array.isArray(payload.data) ? payload.data : [];
              renderAxisOwnerOptions(selectedValue || "");
            } catch (_err) {
              axisDepartmentCollaborators = [];
              renderAxisOwnerOptions("");
            }
          };

          const renderCollaboratorOptions = (selectedValue = "") => {
            if (!objLeaderEl) return;
            const options = ['<option value="">Selecciona colaborador</option>']
              .concat(
                collaborators.map((name) => {
                  const selected = name === selectedValue ? "selected" : "";
                  return `<option value="${name}" ${selected}>${name}</option>`;
                })
              );
            objLeaderEl.innerHTML = options.join("");
          };
          const setCollaboratorLoading = (isLoading) => {
            if (!objLeaderEl) return;
            objLeaderEl.disabled = !!isLoading;
            if (isLoading) {
              objLeaderEl.innerHTML = '<option value="">Cargando colaboradores...</option>';
            }
          };

          const renderAxisList = () => {
            if (!axisListEl) return;
            axisListEl.innerHTML = axes.map((axis) => `
              <button class="axm-axis-btn ${toId(axis.id) === toId(selectedAxisId) ? "active" : ""}" type="button" data-axis-id="${axis.id}">
                <span>
                  <strong>${axis.nombre}</strong>
                  <div class="axm-axis-meta">${axis.codigo || "Sin código"} • ${axis.lider_departamento || "Sin líder"}</div>
                </span>
                <span class="axm-count">${axis.objetivos_count || 0}</span>
              </button>
            `).join("");
            axisListEl.querySelectorAll("[data-axis-id]").forEach((button) => {
              button.addEventListener("click", async () => {
                selectedAxisId = toId(button.getAttribute("data-axis-id"));
                selectedObjectiveId = null;
                renderAll();
                openAxisModal();
                try {
                  await loadCollaborators();
                  renderAll();
                } catch (_error) {
                  showMsg("No se pudieron cargar colaboradores para el eje seleccionado.", true);
                }
              });
            });
            const activeBtn = axisListEl.querySelector(".axm-axis-btn.active");
            if (activeBtn && typeof activeBtn.scrollIntoView === "function") {
              activeBtn.scrollIntoView({ block: "nearest", behavior: "smooth" });
            }
          };
          const renderObjectiveAxisList = () => {
            if (!objAxisListEl) return;
            objAxisListEl.innerHTML = (axes || []).map((axis) => `
              <button class="axm-obj-axis-btn ${toId(axis.id) === toId(selectedAxisId) ? "active" : ""}" type="button" data-obj-axis-id="${axis.id}">
                <span>
                  <strong>${axis.nombre || "Eje sin nombre"}</strong>
                </span>
                <span class="axm-obj-axis-arrow">›</span>
              </button>
            `).join("");
            objAxisListEl.querySelectorAll("[data-obj-axis-id]").forEach((button) => {
              button.addEventListener("click", async () => {
                selectedAxisId = toId(button.getAttribute("data-obj-axis-id"));
                selectedObjectiveId = null;
                renderAll();
                try {
                  await loadCollaborators();
                  renderAll();
                } catch (_error) {
                  showMsg("No se pudieron cargar colaboradores para el eje seleccionado.", true);
                }
              });
            });
          };

          const renderAxisEditor = () => {
            const axis = selectedAxis();
            if (!axis) {
              axisNameEl.value = "";
              if (axisBaseCodeEl) axisBaseCodeEl.innerHTML = "";
              if (axisCodeEl) axisCodeEl.value = "";
              if (axisBasePreviewEl) axisBasePreviewEl.textContent = "Selecciona un código para ver su línea asociada.";
              renderDepartmentOptions("");
              axisDepartmentCollaborators = [];
              renderAxisOwnerOptions("");
              axisDescEl.value = "";
              return;
            }
            axisNameEl.value = axis.nombre || "";
            const entries = getIdentityCodeEntries();
            const options = entries.map((item) => item.code);
            const codeParts = String(axis.codigo || "").split("-");
            const inferredBase = String(codeParts[0] || "").trim().toLowerCase().replace(/[^a-z0-9]/g, "");
            const selectedBase = options.includes(inferredBase) ? inferredBase : options[0];
            if (axisBaseCodeEl) {
              axisBaseCodeEl.innerHTML = options.map((code) => `<option value="${code}" ${code === selectedBase ? "selected" : ""}>${code}</option>`).join("");
              axisBaseCodeEl.onchange = () => {
                if (axisCodeEl) axisCodeEl.value = buildAxisCode(axisBaseCodeEl.value, axisPosition(axis));
                updateAxisBasePreview();
              };
            }
            if (axisCodeEl) axisCodeEl.value = buildAxisCode(selectedBase, axisPosition(axis));
            updateAxisBasePreview();
            renderDepartmentOptions(axis.lider_departamento || "");
            loadAxisDepartmentCollaborators(axis.lider_departamento || "", axis.responsabilidad_directa || "");
            axisDescEl.value = axis.descripcion || "";
          };

          const renderObjectives = () => {
            const axis = selectedAxis();
            if (objAxisTitleEl) {
              objAxisTitleEl.textContent = axis ? `Objetivos: ${axis.nombre || "Eje seleccionado"}` : "Objetivos";
            }
            if (!axis || !objListEl) {
              if (objListEl) objListEl.innerHTML = "";
              selectedObjectiveId = null;
              if (objNameEl) objNameEl.value = "";
              if (objCodeEl) objCodeEl.value = "";
              if (objDescEl) objDescEl.value = "";
              if (objStartEl) objStartEl.value = "";
              if (objEndEl) objEndEl.value = "";
              renderCollaboratorOptions("");
              if (objListEl) objListEl.innerHTML = '<div class="axm-axis-meta">Selecciona un eje en la columna izquierda.</div>';
              return;
            }
            if (!selectedObjectiveId || !(axis.objetivos || []).some((obj) => obj.id === selectedObjectiveId)) {
              selectedObjectiveId = (axis.objetivos || [])[0]?.id || null;
            }
            objListEl.innerHTML = (axis.objetivos || []).map((obj) => `
              <button class="axm-obj-btn ${obj.id === selectedObjectiveId ? "active" : ""}" type="button" data-obj-id="${obj.id}">
                <strong>${obj.codigo || "OBJ"} - ${obj.nombre || "Sin nombre"}</strong>
                <div class="axm-obj-sub">Fecha inicial: ${obj.fecha_inicial || "N/D"} · Fecha final: ${obj.fecha_final || "N/D"}</div>
              </button>
            `).join("");

            objListEl.querySelectorAll("[data-obj-id]").forEach((button) => {
              button.addEventListener("click", () => {
                selectedObjectiveId = Number(button.getAttribute("data-obj-id"));
                renderAll();
                openObjModal();
              });
            });

            const objective = selectedObjective();
            if (!objective) return;
            if (objNameEl) objNameEl.value = objective.nombre || "";
            if (objCodeEl) objCodeEl.value = buildObjectiveCode(axis.codigo || "", objectivePosition(objective));
            if (objDescEl) objDescEl.value = objective.descripcion || "";
            if (objStartEl) objStartEl.value = objective.fecha_inicial || "";
            if (objEndEl) objEndEl.value = objective.fecha_final || "";
            renderCollaboratorOptions(objective.lider || "");
          };

          const renderAll = () => {
            renderAxisList();
            renderObjectiveAxisList();
            renderAxisEditor();
            renderObjectives();
            renderStrategicTree();
          };

          if (misionComposer) misionComposer.onChange(() => {
            renderStrategicTree();
            renderAxisEditor();
          });
          if (visionComposer) visionComposer.onChange(() => {
            renderStrategicTree();
            renderAxisEditor();
          });

          const loadAxes = async () => {
            const payload = await requestJson("/api/strategic-axes");
            axes = Array.isArray(payload.data) ? payload.data : [];
            const currentId = toId(selectedAxisId);
            if (!currentId || !axes.some((axis) => toId(axis.id) === currentId)) {
              selectedAxisId = axes.length ? toId(axes[0].id) : null;
            }
            renderAll();
          };

          const loadDepartments = async () => {
            const payload = await requestJson("/api/strategic-axes/departments");
            departments = Array.isArray(payload.data) ? payload.data : [];
            renderDepartmentOptions(selectedAxis()?.lider_departamento || "");
          };

          const loadCollaborators = async () => {
            const axis = selectedAxis();
            if (!axis || !axis.id) {
              collaborators = [];
              setCollaboratorLoading(false);
              renderCollaboratorOptions("");
              return;
            }
            setCollaboratorLoading(true);
            try {
              const payload = await requestJson(`/api/strategic-axes/${axis.id}/collaborators`);
              collaborators = Array.isArray(payload.data) ? payload.data : [];
              renderCollaboratorOptions(selectedObjective()?.lider || "");
            } finally {
              setCollaboratorLoading(false);
            }
          };

          addAxisBtn && addAxisBtn.addEventListener("click", async () => {
            showMsg("Creando eje...");
            addAxisBtn.disabled = true;
            openAxisModal();
            try {
              const payload = await requestJson("/api/strategic-axes", {
                method: "POST",
                body: JSON.stringify({
                  nombre: "Nuevo eje estratégico (editar nombre)",
                  base_code: getIdentityCodeOptions()[0] || "m1",
                  codigo: "",
                  lider_departamento: "",
                  responsabilidad_directa: "",
                  descripcion: "",
                  orden: axes.length + 1,
                }),
              });
              selectedAxisId = toId(payload.data?.id);
              await loadAxes();
              await loadCollaborators();
              showMsg(`Eje agregado${selectedAxisId ? ` (ID ${selectedAxisId})` : ""}.`);
              if (axisNameEl) {
                axisNameEl.focus();
                axisNameEl.select();
              }
            } catch (err) {
              showMsg(err.message || "No se pudo crear el eje.", true);
            } finally {
              addAxisBtn.disabled = false;
            }
          });

          saveAxisBtn && saveAxisBtn.addEventListener("click", async () => {
            const axis = selectedAxis();
            if (!axis) {
              showMsg("Selecciona un eje para guardar.", true);
              return;
            }
            const body = {
              nombre: axisNameEl.value.trim(),
              base_code: axisBaseCodeEl && axisBaseCodeEl.value ? axisBaseCodeEl.value.trim() : "",
              codigo: axisCodeEl && axisCodeEl.value ? axisCodeEl.value.trim() : "",
              lider_departamento: axisLeaderEl && axisLeaderEl.value ? axisLeaderEl.value.trim() : "",
              responsabilidad_directa: axisOwnerEl && axisOwnerEl.value ? axisOwnerEl.value.trim() : "",
              descripcion: axisDescEl.value.trim(),
              orden: axisPosition(axis),
            };
            if (!body.nombre) {
              showMsg("El nombre del eje es obligatorio.", true);
              return;
            }
            try {
              await requestJson(`/api/strategic-axes/${axis.id}`, { method: "PUT", body: JSON.stringify(body) });
              await loadAxes();
              await loadCollaborators();
              showMsg("Eje guardado correctamente.");
            } catch (err) {
              showMsg(err.message || "No se pudo guardar el eje.", true);
            }
          });

          deleteAxisBtn && deleteAxisBtn.addEventListener("click", async () => {
            const axis = selectedAxis();
            if (!axis) return;
            if (!window.confirm("¿Eliminar este eje y todos sus objetivos?")) return;
            try {
              await requestJson(`/api/strategic-axes/${axis.id}`, { method: "DELETE" });
              selectedAxisId = null;
              await loadAxes();
              await loadCollaborators();
              showMsg("Eje eliminado.");
              closeAxisModal();
            } catch (err) {
              showMsg(err.message || "No se pudo eliminar el eje.", true);
            }
          });

          addObjBtn && addObjBtn.addEventListener("click", async () => {
            const axis = selectedAxis();
            if (!axis) {
              showMsg("Primero selecciona un eje.", true);
              return;
            }
            openObjModal();
            const body = {
              codigo: buildObjectiveCode(axis.codigo || "", (axis.objetivos || []).length + 1),
              nombre: "Nuevo objetivo",
              lider: "",
              descripcion: "",
              orden: (axis.objetivos || []).length + 1,
            };
            try {
              const payload = await requestJson(`/api/strategic-axes/${axis.id}/objectives`, { method: "POST", body: JSON.stringify(body) });
              await loadAxes();
              selectedObjectiveId = payload.data?.id || selectedObjectiveId;
              renderAll();
              showMsg("Objetivo agregado.");
              if (objNameEl) {
                objNameEl.focus();
                objNameEl.select();
              }
            } catch (err) {
              showMsg(err.message || "No se pudo agregar el objetivo.", true);
            }
          });

          saveObjBtn && saveObjBtn.addEventListener("click", async () => {
            const objective = selectedObjective();
            if (!objective) {
              showMsg("Selecciona un objetivo.", true);
              return;
            }
            const body = {
              nombre: objNameEl && objNameEl.value ? objNameEl.value.trim() : "",
              codigo: objCodeEl && objCodeEl.value ? objCodeEl.value.trim() : "",
              lider: objLeaderEl && objLeaderEl.value ? objLeaderEl.value.trim() : "",
              fecha_inicial: objStartEl && objStartEl.value ? objStartEl.value : "",
              fecha_final: objEndEl && objEndEl.value ? objEndEl.value : "",
              descripcion: objDescEl && objDescEl.value ? objDescEl.value.trim() : "",
              orden: objectivePosition(objective),
            };
            if (!body.nombre) {
              showMsg("El nombre del objetivo es obligatorio.", true);
              return;
            }
            const objectiveDateError = visualRangeError(body.fecha_inicial, body.fecha_final, "Objetivo");
            if (objectiveDateError) {
              showMsg(objectiveDateError, true);
              return;
            }
            try {
              await requestJson(`/api/strategic-objectives/${objective.id}`, { method: "PUT", body: JSON.stringify(body) });
              await loadAxes();
              renderAll();
              showMsg("Objetivo guardado correctamente.");
            } catch (err) {
              showMsg(err.message || "No se pudo guardar el objetivo.", true);
            }
          });

          deleteObjBtn && deleteObjBtn.addEventListener("click", async () => {
            const objective = selectedObjective();
            if (!objective) return;
            if (!window.confirm("¿Eliminar este objetivo?")) return;
            try {
              await requestJson(`/api/strategic-objectives/${objective.id}`, { method: "DELETE" });
              selectedObjectiveId = null;
              await loadAxes();
              renderAll();
              showMsg("Objetivo eliminado.");
            } catch (err) {
              showMsg(err.message || "No se pudo eliminar el objetivo.", true);
            }
          });

          axisLeaderEl && axisLeaderEl.addEventListener("change", async () => {
            await loadAxisDepartmentCollaborators(axisLeaderEl.value || "", "");
          });

          Promise.all([loadDepartments(), loadAxes()]).then(loadCollaborators).catch((err) => {
            showMsg(err.message || "No se pudieron cargar los ejes.", true);
          });
        })();
      </script>
    </section>
""")

POA_LIMPIO_HTML = dedent("""
    <section class="poa-board-wrap">
      <style>
        .poa-board-wrap *{ box-sizing:border-box; }
        .poa-board-wrap{
          padding: 10px;
          color: #0f172a;
        }
        .poa-board-head{
          background: rgba(255,255,255,.92);
          border: 1px solid rgba(148,163,184,.28);
          border-radius: 14px;
          padding: 12px 14px;
          margin-bottom: 10px;
        }
        .poa-board-head h2{
          margin: 0;
          font-size: 20px;
        }
        .poa-board-head p{
          margin: 6px 0 0;
          color: #64748b;
          font-size: 13px;
        }
        .poa-board-msg{
          min-height: 20px;
          margin: 0 2px 10px;
          font-size: 13px;
          color: #0f3d2e;
        }
        .poa-board-grid{
          display: flex;
          align-items: stretch;
          gap: 10px;
          overflow: auto;
          padding-bottom: 8px;
        }
        .poa-axis-col{
          flex: 0 0 320px;
          width: 320px;
          border: 1px solid rgba(148,163,184,.30);
          border-radius: 14px;
          background: rgba(255,255,255,.95);
          box-shadow: 0 8px 20px rgba(15,23,42,.06);
          transition: width .18s ease, flex-basis .18s ease;
        }
        .poa-axis-col.collapsed{
          flex-basis: 72px;
          width: 72px;
        }
        .poa-axis-head{
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          padding: 10px;
          border-bottom: 1px solid rgba(148,163,184,.24);
          min-height: 48px;
        }
        .poa-axis-title{
          margin: 0;
          font-size: 18px;
          line-height: 1.2;
          max-width: 255px;
        }
        .poa-axis-col.collapsed .poa-axis-title{
          writing-mode: vertical-rl;
          transform: rotate(180deg);
          font-size: 14px;
          max-width: none;
          white-space: nowrap;
        }
        .poa-axis-toggle{
          border: 1px solid rgba(148,163,184,.30);
          background: #fff;
          border-radius: 8px;
          width: 28px;
          height: 28px;
          font-size: 18px;
          line-height: 1;
          cursor: pointer;
          color: #334155;
          flex: 0 0 auto;
        }
        .poa-axis-cards{
          padding: 10px;
          display: grid;
          gap: 8px;
          align-content: start;
        }
        .poa-axis-col.collapsed .poa-axis-cards{
          display: none;
        }
        .poa-obj-card{
          border: 1px solid rgba(148,163,184,.28);
          border-radius: 12px;
          padding: 10px;
          background: #fff;
          cursor: pointer;
        }
        .poa-obj-card h4{
          margin: 0;
          font-size: 15px;
          line-height: 1.3;
        }
        .poa-obj-card .meta{
          margin-top: 6px;
          font-size: 12px;
          color: #64748b;
        }
        .poa-obj-card .code{
          display: inline-block;
          margin-top: 8px;
          border: 1px solid rgba(15,61,46,.26);
          border-radius: 999px;
          padding: 2px 8px;
          font-size: 11px;
          font-weight: 700;
          color: #0f3d2e;
          background: rgba(15,61,46,.08);
        }
        .poa-obj-card .code-next{
          margin-top: 4px;
          font-size: 11px;
          color: #64748b;
          font-style: italic;
        }
        .poa-modal{
          position: fixed;
          inset: 0;
          display: none;
          align-items: center;
          justify-content: center;
          background: rgba(15,23,42,.44);
          z-index: 99999;
          padding: 16px;
        }
        .poa-modal.open{ display: flex; }
        .poa-modal-dialog{
          width: min(940px, 96vw);
          max-height: 92vh;
          overflow: auto;
          border: 1px solid rgba(148,163,184,.32);
          border-radius: 16px;
          background: #f8fafc;
          box-shadow: 0 22px 44px rgba(15,23,42,.26);
          padding: 14px;
        }
        .poa-modal-head{
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          margin-bottom: 8px;
        }
        .poa-branch-path{
          margin: 0 0 8px;
          font-size: 11px;
          font-style: italic;
          color: #64748b;
          line-height: 1.35;
        }
        .poa-modal-close{
          width: 32px;
          height: 32px;
          border: 1px solid rgba(148,163,184,.34);
          border-radius: 10px;
          background: #fff;
          font-size: 20px;
          line-height: 1;
          cursor: pointer;
        }
        .poa-form-grid{
          display: grid;
          gap: 10px;
        }
        .poa-row{
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
        }
        .poa-field{
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .poa-field label{
          font-size: 12px;
          font-weight: 700;
          color: #475569;
        }
        .poa-assigned-by{
          margin: 0 0 2px;
          font-size: 11px;
          font-style: italic;
          color: #64748b;
        }
        .poa-input, .poa-textarea, .poa-select{
          width: 100%;
          border: 1px solid rgba(148,163,184,.42);
          border-radius: 12px;
          padding: 10px 12px;
          font-size: 14px;
          background: #fff;
          color: #0f172a;
        }
        .poa-select[multiple]{
          min-height: 104px;
          padding: 8px;
        }
        .poa-textarea{ min-height: 110px; resize: vertical; }
        .poa-tabs{
          display: flex;
          gap: 6px;
          border-bottom: 1px solid rgba(148,163,184,.28);
          margin-top: 2px;
        }
        .poa-tab{
          border: 1px solid rgba(148,163,184,.32);
          border-bottom: 0;
          border-radius: 10px 10px 0 0;
          background: #fff;
          padding: 8px 10px;
          font-size: 13px;
          font-weight: 700;
          color: #334155;
          cursor: pointer;
        }
        .poa-tab.active{
          background: rgba(15,61,46,.10);
          border-color: rgba(15,61,46,.34);
          color: #0f3d2e;
        }
        .poa-tab-panel{
          display: none;
          border: 1px solid rgba(148,163,184,.28);
          border-top: 0;
          border-radius: 0 0 12px 12px;
          background: #fff;
          padding: 12px;
        }
        .poa-tab-panel.active{ display: block; }
        .poa-actions{
          display: flex;
          gap: 8px;
          margin-top: 10px;
        }
        .poa-btn{
          border: 1px solid rgba(148,163,184,.34);
          border-radius: 10px;
          padding: 9px 12px;
          background: #fff;
          font-weight: 700;
          font-size: 13px;
          cursor: pointer;
        }
        .poa-btn.primary{
          background: #0f3d2e;
          border-color: #0f3d2e;
          color: #fff;
        }
        .poa-modal-msg{
          min-height: 18px;
          margin-top: 8px;
          font-size: 12px;
          color: #0f3d2e;
        }
        .poa-state-strip{
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 8px;
          margin-bottom: 10px;
        }
        .poa-state-btn{
          border: 1px solid rgba(148,163,184,.34);
          border-radius: 10px;
          padding: 8px;
          font-size: 12px;
          font-weight: 700;
          background: #fff;
          color: #334155;
        }
        .poa-state-btn.active{
          border-color: rgba(15,61,46,.45);
          background: rgba(15,61,46,.12);
          color: #0f3d2e;
        }
        .poa-state-actions{
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
          margin-bottom: 8px;
        }
        .poa-summary{
          display: grid;
          grid-template-columns: minmax(0, 1fr) minmax(180px, 240px);
          gap: 10px;
          margin-bottom: 10px;
        }
        .poa-summary-item{
          border: 1px solid rgba(148,163,184,.28);
          border-radius: 10px;
          padding: 8px 10px;
          background: #fff;
        }
        .poa-summary-label{
          font-size: 11px;
          color: #64748b;
          text-transform: uppercase;
          letter-spacing: .03em;
        }
        .poa-summary-value{
          margin-top: 4px;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          font-size: 13px;
          font-weight: 700;
          color: #0f172a;
        }
        .poa-semaforo{
          width: 10px;
          height: 10px;
          border-radius: 50%;
          display: inline-block;
          border: 1px solid rgba(15,23,42,.22);
          background: #cbd5e1;
        }
        .poa-semaforo.gray{ background: #9ca3af; }
        .poa-semaforo.yellow{ background: #eab308; }
        .poa-semaforo.orange{ background: #f97316; }
        .poa-semaforo.green{ background: #22c55e; }
        .poa-semaforo.red{ background: #ef4444; }
        .poa-sub-header{
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          margin-bottom: 8px;
        }
        .poa-sub-list{
          display: grid;
          gap: 8px;
        }
        .poa-sub-item{
          border: 1px solid rgba(148,163,184,.26);
          border-radius: 10px;
          padding: 8px;
          background: #fff;
        }
        .poa-sub-item h5{
          margin: 0;
          font-size: 14px;
        }
        .poa-sub-meta{
          margin-top: 4px;
          font-size: 12px;
          color: #64748b;
          font-style: italic;
        }
        .poa-sub-actions{
          margin-top: 6px;
          display: flex;
          gap: 6px;
        }
        .poa-sub-btn{
          border: 1px solid rgba(148,163,184,.34);
          border-radius: 8px;
          padding: 5px 8px;
          background: #fff;
          font-size: 12px;
          font-weight: 700;
          cursor: pointer;
        }
        .poa-sub-btn.warn{
          border-color: rgba(239,68,68,.28);
          color: #b91c1c;
          background: #fff5f5;
        }
        @media (max-width: 860px){
          .poa-row{ grid-template-columns: 1fr; }
        }
      </style>

      <div class="poa-board-head">
        <h2>Tablero POA por eje</h2>
        <p>Cada columna corresponde a un eje y contiene las tarjetas de sus objetivos.</p>
      </div>
      <div class="poa-board-msg" id="poa-board-msg" aria-live="polite"></div>
      <div class="poa-board-grid" id="poa-board-grid"></div>
      <div class="poa-modal" id="poa-activity-modal" role="dialog" aria-modal="true" aria-labelledby="poa-activity-title">
        <section class="poa-modal-dialog">
          <div class="poa-modal-head">
            <div>
              <h3 id="poa-activity-title" style="margin:0;font-size:18px;">Nueva actividad</h3>
              <p id="poa-activity-subtitle" style="margin:4px 0 0;color:#64748b;font-size:12px;"></p>
            </div>
            <button class="poa-modal-close" id="poa-activity-close" type="button" aria-label="Cerrar">×</button>
          </div>
          <p class="poa-branch-path" id="poa-activity-branch"></p>
          <div class="poa-summary">
            <div class="poa-summary-item">
              <div class="poa-summary-label">Estatus</div>
              <div class="poa-summary-value" id="poa-status-value"><span class="poa-semaforo gray"></span>No iniciado</div>
            </div>
            <div class="poa-summary-item">
              <div class="poa-summary-label">Avance</div>
              <div class="poa-summary-value" id="poa-progress-value">0%</div>
            </div>
          </div>
          <div class="poa-state-strip" id="poa-state-strip">
            <button type="button" class="poa-state-btn" id="poa-state-no-iniciado" disabled>No iniciado</button>
            <button type="button" class="poa-state-btn" id="poa-state-en-proceso">En proceso</button>
            <button type="button" class="poa-state-btn" id="poa-state-terminado">Terminado</button>
            <button type="button" class="poa-state-btn" id="poa-state-en-revision" disabled>En revisión</button>
          </div>
          <div class="poa-state-actions" id="poa-state-actions">
            <button type="button" class="poa-btn" id="poa-approval-approve" style="display:none;">Aprobar entregable</button>
            <button type="button" class="poa-btn" id="poa-approval-reject" style="display:none;">Rechazar entregable</button>
          </div>

          <div class="poa-form-grid">
            <p class="poa-assigned-by" id="poa-assigned-by">Asignado por: N/D</p>
            <div class="poa-row">
              <div class="poa-field">
                <label for="poa-act-name">Nombre</label>
                <input id="poa-act-name" class="poa-input" type="text" placeholder="Nombre de la actividad">
              </div>
              <div class="poa-field">
                <label for="poa-act-milestone">Entregable</label>
                <input id="poa-act-milestone" class="poa-input" type="text" placeholder="Nombre del entregable">
              </div>
            </div>
            <div class="poa-row">
              <div class="poa-field">
                <label for="poa-act-owner">Responsable</label>
                <select id="poa-act-owner" class="poa-select">
                  <option value="">Selecciona responsable</option>
                </select>
              </div>
              <div class="poa-field">
                <label for="poa-act-assigned">Personas asignadas</label>
                <select id="poa-act-assigned" class="poa-select" multiple></select>
              </div>
            </div>
            <div class="poa-row">
              <div class="poa-field">
                <label for="poa-act-start">Fecha inicial</label>
                <input id="poa-act-start" class="poa-input" type="date">
              </div>
              <div class="poa-field">
                <label for="poa-act-end">Fecha final</label>
                <input id="poa-act-end" class="poa-input" type="date">
              </div>
            </div>
            <div class="poa-row">
              <div class="poa-field">
                <label for="poa-act-recurrente">Recurrente</label>
                <label style="display:flex;align-items:center;gap:8px;margin-top:8px;color:#334155;font-size:13px;">
                  <input id="poa-act-recurrente" type="checkbox">
                  Habilitar recurrencia
                </label>
              </div>
              <div class="poa-field">
                <label for="poa-act-periodicidad">Periodicidad</label>
                <select id="poa-act-periodicidad" class="poa-select" disabled>
                  <option value="">Selecciona periodicidad</option>
                  <option value="diaria">diaria</option>
                  <option value="semanal">semanal</option>
                  <option value="quincenal">quincenal</option>
                  <option value="mensual">mensual</option>
                  <option value="bimensual">bimensual</option>
                  <option value="cada_xx_dias">Cada xx dias</option>
                </select>
              </div>
            </div>
            <div class="poa-field" id="poa-act-every-days-wrap" style="display:none;">
              <label for="poa-act-every-days">Cada xx dias</label>
              <input id="poa-act-every-days" class="poa-input" type="number" min="1" step="1" placeholder="Ej. 3">
            </div>
          </div>

          <div class="poa-tabs" id="poa-tabs">
            <button type="button" class="poa-tab active" data-poa-tab="desc">Descripción</button>
            <button type="button" class="poa-tab" data-poa-tab="sub">Subtareas</button>
            <button type="button" class="poa-tab" data-poa-tab="kpi">Kpis</button>
            <button type="button" class="poa-tab" data-poa-tab="budget">Presupuesto</button>
          </div>
          <section class="poa-tab-panel active" data-poa-panel="desc">
            <div class="poa-field" style="margin-top:0;">
              <label for="poa-act-desc">Descripción</label>
              <textarea id="poa-act-desc" class="poa-textarea" placeholder="Descripción de la actividad"></textarea>
            </div>
          </section>
          <section class="poa-tab-panel" data-poa-panel="sub">
            <div class="poa-sub-header">
              <p id="poa-sub-hint" style="margin:0;color:#64748b;font-size:13px;">Guarda primero la actividad para habilitar subtareas.</p>
              <button type="button" class="poa-btn" id="poa-sub-add">Agregar subtarea</button>
            </div>
            <div class="poa-sub-list" id="poa-sub-list"></div>
          </section>
          <section class="poa-tab-panel" data-poa-panel="kpi">
            <p style="margin:0;color:#64748b;font-size:13px;">Kpis: en construcción.</p>
          </section>
          <section class="poa-tab-panel" data-poa-panel="budget">
            <p style="margin:0;color:#64748b;font-size:13px;">Presupuesto: en construcción.</p>
          </section>

          <div class="poa-actions">
            <button type="button" class="poa-btn primary" id="poa-act-save">Guardar actividad</button>
            <button type="button" class="poa-btn" id="poa-act-cancel">Cancelar</button>
          </div>
          <div class="poa-modal-msg" id="poa-act-msg" aria-live="polite"></div>
        </section>
      </div>
      <div class="poa-modal" id="poa-sub-modal" role="dialog" aria-modal="true" aria-labelledby="poa-sub-title">
        <section class="poa-modal-dialog">
          <div class="poa-modal-head">
            <h3 id="poa-sub-title" style="margin:0;font-size:18px;">Subtarea</h3>
            <button class="poa-modal-close" id="poa-sub-close" type="button" aria-label="Cerrar">×</button>
          </div>
          <p class="poa-branch-path" id="poa-sub-branch"></p>
          <div class="poa-form-grid">
            <div class="poa-field">
              <label for="poa-sub-name">Nombre</label>
              <input id="poa-sub-name" class="poa-input" type="text" placeholder="Nombre de la subtarea">
            </div>
            <div class="poa-row">
              <div class="poa-field">
                <label for="poa-sub-owner">Responsable</label>
                <select id="poa-sub-owner" class="poa-select">
                  <option value="">Selecciona responsable</option>
                </select>
              </div>
              <div class="poa-field">
                <label for="poa-sub-assigned">Personas asignadas</label>
                <select id="poa-sub-assigned" class="poa-select" multiple></select>
              </div>
            </div>
            <div class="poa-row">
              <div class="poa-field">
                <label for="poa-sub-start">Fecha inicial</label>
                <input id="poa-sub-start" class="poa-input" type="date">
              </div>
              <div class="poa-field">
                <label for="poa-sub-end">Fecha final</label>
                <input id="poa-sub-end" class="poa-input" type="date">
              </div>
            </div>
            <div class="poa-field">
              <label for="poa-sub-desc">Descripción</label>
              <textarea id="poa-sub-desc" class="poa-textarea" placeholder="Descripción de la subtarea"></textarea>
            </div>
          </div>
          <div class="poa-actions">
            <button type="button" class="poa-btn primary" id="poa-sub-save">Guardar subtarea</button>
            <button type="button" class="poa-btn" id="poa-sub-cancel">Cancelar</button>
          </div>
          <div class="poa-modal-msg" id="poa-sub-msg" aria-live="polite"></div>
        </section>
      </div>

      <script>
        (() => {
          const gridEl = document.getElementById("poa-board-grid");
          const msgEl = document.getElementById("poa-board-msg");
          const modalEl = document.getElementById("poa-activity-modal");
          const closeBtn = document.getElementById("poa-activity-close");
          const cancelBtn = document.getElementById("poa-act-cancel");
          const saveBtn = document.getElementById("poa-act-save");
          const subAddBtn = document.getElementById("poa-sub-add");
          const subListEl = document.getElementById("poa-sub-list");
          const subHintEl = document.getElementById("poa-sub-hint");
          const titleEl = document.getElementById("poa-activity-title");
          const subtitleEl = document.getElementById("poa-activity-subtitle");
          const activityBranchEl = document.getElementById("poa-activity-branch");
          const assignedByEl = document.getElementById("poa-assigned-by");
          const actNameEl = document.getElementById("poa-act-name");
          const actMilestoneEl = document.getElementById("poa-act-milestone");
          const actOwnerEl = document.getElementById("poa-act-owner");
          const actAssignedEl = document.getElementById("poa-act-assigned");
          const actStartEl = document.getElementById("poa-act-start");
          const actEndEl = document.getElementById("poa-act-end");
          const actRecurrenteEl = document.getElementById("poa-act-recurrente");
          const actPeriodicidadEl = document.getElementById("poa-act-periodicidad");
          const actEveryDaysWrapEl = document.getElementById("poa-act-every-days-wrap");
          const actEveryDaysEl = document.getElementById("poa-act-every-days");
          const actDescEl = document.getElementById("poa-act-desc");
          const actMsgEl = document.getElementById("poa-act-msg");
          const stateNoIniciadoBtn = document.getElementById("poa-state-no-iniciado");
          const stateEnProcesoBtn = document.getElementById("poa-state-en-proceso");
          const stateTerminadoBtn = document.getElementById("poa-state-terminado");
          const stateEnRevisionBtn = document.getElementById("poa-state-en-revision");
          const statusValueEl = document.getElementById("poa-status-value");
          const progressValueEl = document.getElementById("poa-progress-value");
          const approveBtn = document.getElementById("poa-approval-approve");
          const rejectBtn = document.getElementById("poa-approval-reject");
          const subModalEl = document.getElementById("poa-sub-modal");
          const subCloseBtn = document.getElementById("poa-sub-close");
          const subCancelBtn = document.getElementById("poa-sub-cancel");
          const subSaveBtn = document.getElementById("poa-sub-save");
          const subBranchEl = document.getElementById("poa-sub-branch");
          const subNameEl = document.getElementById("poa-sub-name");
          const subOwnerEl = document.getElementById("poa-sub-owner");
          const subAssignedEl = document.getElementById("poa-sub-assigned");
          const subStartEl = document.getElementById("poa-sub-start");
          const subEndEl = document.getElementById("poa-sub-end");
          const subDescEl = document.getElementById("poa-sub-desc");
          const subMsgEl = document.getElementById("poa-sub-msg");
          if (!gridEl) return;
          let objectivesById = {};
          let activitiesByObjective = {};
          let approvalsByActivity = {};
          let currentObjective = null;
          let currentActivityId = null;
          let currentActivityData = null;
          let currentSubactivities = [];
          let editingSubId = null;
          let currentParentSubId = 0;
          let isSaving = false;

          const escapeHtml = (value) => String(value || "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
          const fmtDate = (iso) => {
            const value = String(iso || "").trim();
            if (!value) return "N/D";
            const date = new Date(value);
            if (Number.isNaN(date.getTime())) return value;
            return date.toLocaleDateString("es-CR");
          };
          const todayIso = () => {
            const now = new Date();
            const y = now.getFullYear();
            const m = String(now.getMonth() + 1).padStart(2, "0");
            const d = String(now.getDate()).padStart(2, "0");
            return `${y}-${m}-${d}`;
          };
          const showMsg = (text, isError = false) => {
            if (!msgEl) return;
            msgEl.textContent = text || "";
            msgEl.style.color = isError ? "#b91c1c" : "#0f3d2e";
          };
          const showModalMsg = (text, isError = false) => {
            if (!actMsgEl) return;
            actMsgEl.textContent = text || "";
            actMsgEl.style.color = isError ? "#b91c1c" : "#0f3d2e";
          };
          const showSubMsg = (text, isError = false) => {
            if (!subMsgEl) return;
            subMsgEl.textContent = text || "";
            subMsgEl.style.color = isError ? "#b91c1c" : "#0f3d2e";
          };
          const openModal = () => {
            if (!modalEl) return;
            modalEl.classList.add("open");
            document.body.style.overflow = "hidden";
          };
          const closeModal = () => {
            if (!modalEl) return;
            modalEl.classList.remove("open");
            document.body.style.overflow = "";
          };
          const openSubModal = () => {
            if (!subModalEl) return;
            subModalEl.classList.add("open");
            document.body.style.overflow = "hidden";
          };
          const closeSubModal = () => {
            if (!subModalEl) return;
            subModalEl.classList.remove("open");
            document.body.style.overflow = modalEl && modalEl.classList.contains("open") ? "hidden" : "";
          };
          const nextCode = (objectiveCode) => {
            const code = String(objectiveCode || "").trim().toLowerCase();
            if (!code) return "m1-01-01-aa-bb-cc-dd-ee";
            return `${code}-aa-bb-cc-dd-ee`;
          };
          const buildBranchText = (activityName = "Actividad", slots = {}) => {
            const axisLabel = String(currentObjective?.axis_name || "Eje estratégico").trim() || "Eje estratégico";
            const objectiveLabel = String(currentObjective?.nombre || "Objetivo").trim() || "Objetivo";
            const activityLabel = String(activityName || "Actividad").trim() || "Actividad";
            const tarea = String(slots.tarea || "Tarea").trim() || "Tarea";
            const subtarea = String(slots.subtarea || "Subtarea").trim() || "Subtarea";
            const subsub = String(slots.subsubtarea || "Subsubtarea").trim() || "Subsubtarea";
            return `Ruta: ${axisLabel} / ${objectiveLabel} / ${activityLabel} / ${tarea} / ${subtarea} / ${subsub}`;
          };
          const renderActivityBranch = () => {
            if (!activityBranchEl) return;
            activityBranchEl.textContent = buildBranchText(actNameEl && actNameEl.value ? actNameEl.value : "Actividad");
          };
          const resolveSubBranchSlots = (targetLevel, targetName, parentId) => {
            const byId = {};
            (currentSubactivities || []).forEach((item) => {
              byId[Number(item.id || 0)] = item;
            });
            let tarea = "Tarea";
            let subtarea = "Subtarea";
            let subsubtarea = "Subsubtarea";
            let walker = Number(parentId || 0);
            while (walker) {
              const node = byId[walker];
              if (!node) break;
              const level = Number(node.nivel || 1);
              const name = String(node.nombre || "").trim();
              if (level === 1 && name) tarea = name;
              if (level === 2 && name) subtarea = name;
              if (level === 3 && name) subsubtarea = name;
              walker = Number(node.parent_subactivity_id || 0);
            }
            const cleanTarget = String(targetName || "").trim();
            if (targetLevel === 1 && cleanTarget) tarea = cleanTarget;
            if (targetLevel === 2 && cleanTarget) subtarea = cleanTarget;
            if (targetLevel === 3 && cleanTarget) subsubtarea = cleanTarget;
            return { tarea, subtarea, subsubtarea };
          };
          const renderSubBranch = (targetLevel = 1, targetName = "", parentId = 0) => {
            if (!subBranchEl) return;
            const slots = resolveSubBranchSlots(targetLevel, targetName, parentId);
            const actName = actNameEl && actNameEl.value ? actNameEl.value : "Actividad";
            subBranchEl.textContent = buildBranchText(actName, slots);
          };
          const setDateBounds = (objective) => {
            const minDate = String(objective?.fecha_inicial || "");
            const maxDate = String(objective?.fecha_final || "");
            [actStartEl, actEndEl].forEach((el) => {
              if (!el) return;
              el.min = minDate || "";
              el.max = maxDate || "";
            });
          };
          const fillCollaborators = async (objective) => {
            if (!actOwnerEl || !actAssignedEl) return;
            const axisId = Number(objective?.eje_id || 0);
            if (!axisId) {
              actOwnerEl.innerHTML = '<option value="">Selecciona responsable</option>';
              actAssignedEl.innerHTML = "";
              return;
            }
            try {
              const response = await fetch(`/api/strategic-axes/${axisId}/collaborators`, {
                headers: { "Content-Type": "application/json" },
                credentials: "same-origin",
              });
              const payload = await response.json().catch(() => ({}));
              const list = Array.isArray(payload.data) ? payload.data : [];
              actOwnerEl.innerHTML = '<option value="">Selecciona responsable</option>' + list.map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join("");
              actAssignedEl.innerHTML = list.map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join("");
            } catch (_err) {
              actOwnerEl.innerHTML = '<option value="">Selecciona responsable</option>';
              actAssignedEl.innerHTML = "";
            }
          };
          const currentApprovalForActivity = () => {
            if (!currentActivityId) return null;
            return approvalsByActivity[Number(currentActivityId)] || null;
          };
          const renderStateStrip = () => {
            const rawStatus = String(currentActivityData?.status || "").trim().toLowerCase();
            const endDate = String(currentActivityData?.fecha_final || "").trim();
            const displayStatus = (() => {
              if (rawStatus === "terminada") return "Terminada";
              if (rawStatus === "en revisión") return "En revisión";
              if (rawStatus === "atrasada") return "Atrasada";
              if (endDate && todayIso() > endDate) return "Atrasada";
              if (rawStatus === "en proceso") return "En proceso";
              return "No iniciado";
            })();
            [stateNoIniciadoBtn, stateEnProcesoBtn, stateTerminadoBtn, stateEnRevisionBtn].forEach((btn) => {
              if (btn) btn.classList.remove("active");
            });
            if (displayStatus === "No iniciado" && stateNoIniciadoBtn) stateNoIniciadoBtn.classList.add("active");
            if (displayStatus === "En proceso" && stateEnProcesoBtn) stateEnProcesoBtn.classList.add("active");
            if (displayStatus === "Terminada" && stateTerminadoBtn) stateTerminadoBtn.classList.add("active");
            if (displayStatus === "En revisión" && stateEnRevisionBtn) stateEnRevisionBtn.classList.add("active");
            if (stateEnProcesoBtn) stateEnProcesoBtn.disabled = !currentActivityId;
            if (stateTerminadoBtn) stateTerminadoBtn.disabled = !currentActivityId;
            if (statusValueEl) {
              const tone = displayStatus === "Terminada" ? "green"
                : displayStatus === "En revisión" ? "orange"
                  : displayStatus === "En proceso" ? "yellow"
                    : displayStatus === "Atrasada" ? "red"
                      : "gray";
              statusValueEl.innerHTML = `<span class="poa-semaforo ${tone}"></span>${escapeHtml(displayStatus)}`;
            }
            const subList = Array.isArray(currentSubactivities) ? currentSubactivities : [];
            let progress = 0;
            if (subList.length) {
              const completed = subList.filter((sub) => {
                const subEnd = String(sub?.fecha_final || "").trim();
                return !!subEnd && subEnd <= todayIso();
              }).length;
              progress = Math.round((completed / subList.length) * 100);
            } else {
              progress = displayStatus === "Terminada" ? 100 : 0;
            }
            if (progressValueEl) progressValueEl.textContent = `${progress}%`;
            const approval = currentApprovalForActivity();
            const canReview = !!approval;
            if (approveBtn) approveBtn.style.display = canReview ? "inline-flex" : "none";
            if (rejectBtn) rejectBtn.style.display = canReview ? "inline-flex" : "none";
          };
          const resetActivityForm = () => {
            if (actNameEl) actNameEl.value = "";
            if (actMilestoneEl) actMilestoneEl.value = "";
            if (actStartEl) actStartEl.value = "";
            if (actEndEl) actEndEl.value = "";
            if (actRecurrenteEl) actRecurrenteEl.checked = false;
            if (actPeriodicidadEl) actPeriodicidadEl.value = "";
            if (actEveryDaysEl) actEveryDaysEl.value = "";
            if (actDescEl) actDescEl.value = "";
            if (actOwnerEl) actOwnerEl.value = "";
            if (actAssignedEl) Array.from(actAssignedEl.options || []).forEach((opt) => { opt.selected = false; });
            currentActivityId = null;
            currentActivityData = null;
            currentSubactivities = [];
            editingSubId = null;
            currentParentSubId = 0;
            syncRecurringFields();
            renderStateStrip();
          };
          const populateActivityForm = (activity) => {
            if (!activity) return;
            if (actNameEl) actNameEl.value = activity.nombre || "";
            if (actMilestoneEl) actMilestoneEl.value = activity.entregable || "";
            if (actOwnerEl) actOwnerEl.value = activity.responsable || "";
            if (actStartEl) actStartEl.value = activity.fecha_inicial || "";
            if (actEndEl) actEndEl.value = activity.fecha_final || "";
            if (actDescEl) actDescEl.value = activity.descripcion || "";
            if (actRecurrenteEl) actRecurrenteEl.checked = !!activity.recurrente;
            if (actPeriodicidadEl) actPeriodicidadEl.value = activity.periodicidad || "";
            if (actEveryDaysEl) actEveryDaysEl.value = activity.cada_xx_dias || "";
            currentActivityId = Number(activity.id || 0);
            currentActivityData = activity;
            currentSubactivities = Array.isArray(activity.subactivities) ? activity.subactivities : [];
            syncRecurringFields();
            renderSubtasks();
            renderStateStrip();
            renderActivityBranch();
          };
          const openActivityForm = async (objectiveId) => {
            const objective = objectivesById[Number(objectiveId)];
            if (!objective) return;
            currentObjective = objective;
            const existing = (activitiesByObjective[Number(objective.id || 0)] || [])[0] || null;
            if (titleEl) titleEl.textContent = existing ? "Editar actividad" : "Nueva actividad";
            if (subtitleEl) subtitleEl.textContent = `${objective.codigo || ""} · ${objective.nombre || "Objetivo"}`;
            if (assignedByEl) assignedByEl.textContent = `Asignado por: ${existing?.created_by || objective.lider || "N/D"}`;
            resetActivityForm();
            showModalMsg("");
            setDateBounds(objective);
            await fillCollaborators(objective);
            if (existing) {
              populateActivityForm(existing);
            } else {
              renderActivityBranch();
              renderSubtasks();
            }
            openModal();
            if (actNameEl) actNameEl.focus();
          };
          const orderSubtasks = (items) => {
            const childrenByParent = {};
            (items || []).forEach((item) => {
              const parent = Number(item.parent_subactivity_id || 0);
              if (!childrenByParent[parent]) childrenByParent[parent] = [];
              childrenByParent[parent].push(item);
            });
            Object.keys(childrenByParent).forEach((key) => {
              childrenByParent[key].sort((a, b) => Number(a.id || 0) - Number(b.id || 0));
            });
            const out = [];
            const visit = (parentId) => {
              const list = childrenByParent[parentId] || [];
              list.forEach((item) => {
                out.push(item);
                visit(Number(item.id || 0));
              });
            };
            visit(0);
            return out;
          };
          const renderSubtasks = () => {
            if (!subListEl || !subHintEl) return;
            if (!currentActivityId) {
              subHintEl.textContent = "Guarda primero la actividad para habilitar subtareas.";
              subListEl.innerHTML = "";
              return;
            }
            subHintEl.textContent = "Gestiona las subtareas de esta actividad.";
            if (!currentSubactivities.length) {
              subListEl.innerHTML = '<div class="poa-sub-meta">Sin subtareas registradas.</div>';
              return;
            }
            subListEl.innerHTML = orderSubtasks(currentSubactivities).map((item) => {
              const level = Number(item.nivel || 1);
              const marginLeft = Math.max(0, (level - 1) * 18);
              return `
              <article class="poa-sub-item" data-sub-id="${Number(item.id || 0)}" style="margin-left:${marginLeft}px;">
                <h5>${escapeHtml(item.nombre || "Subtarea sin nombre")}</h5>
                <div class="poa-sub-meta">Nivel ${level} · ${escapeHtml(fmtDate(item.fecha_inicial))} - ${escapeHtml(fmtDate(item.fecha_final))} · Responsable: ${escapeHtml(item.responsable || "N/D")}</div>
                <div class="poa-sub-actions">
                  <button type="button" class="poa-sub-btn" data-sub-add-child="${Number(item.id || 0)}">Agregar hija</button>
                  <button type="button" class="poa-sub-btn" data-sub-edit="${Number(item.id || 0)}">Editar</button>
                  <button type="button" class="poa-sub-btn warn" data-sub-delete="${Number(item.id || 0)}">Eliminar</button>
                </div>
              </article>
            `;
            }).join("");
            subListEl.querySelectorAll("[data-sub-add-child]").forEach((btn) => {
              btn.addEventListener("click", () => openSubtaskForm(0, Number(btn.getAttribute("data-sub-add-child"))));
            });
            subListEl.querySelectorAll("[data-sub-edit]").forEach((btn) => {
              btn.addEventListener("click", () => openSubtaskForm(Number(btn.getAttribute("data-sub-edit")), 0));
            });
            subListEl.querySelectorAll("[data-sub-delete]").forEach((btn) => {
              btn.addEventListener("click", async () => deleteSubtask(Number(btn.getAttribute("data-sub-delete"))));
            });
          };
          const fillSubCollaborators = async () => {
            if (!subOwnerEl || !subAssignedEl || !currentObjective) return;
            const axisId = Number(currentObjective.eje_id || 0);
            if (!axisId) {
              subOwnerEl.innerHTML = '<option value="">Selecciona responsable</option>';
              subAssignedEl.innerHTML = "";
              return;
            }
            try {
              const response = await fetch(`/api/strategic-axes/${axisId}/collaborators`, {
                headers: { "Content-Type": "application/json" },
                credentials: "same-origin",
              });
              const payload = await response.json().catch(() => ({}));
              const list = Array.isArray(payload.data) ? payload.data : [];
              subOwnerEl.innerHTML = '<option value="">Selecciona responsable</option>' + list.map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join("");
              subAssignedEl.innerHTML = list.map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`).join("");
            } catch (_err) {
              subOwnerEl.innerHTML = '<option value="">Selecciona responsable</option>';
              subAssignedEl.innerHTML = "";
            }
          };
          const setSubDateBounds = (parentSub = null) => {
            const minDate = parentSub?.fecha_inicial || (actStartEl && actStartEl.value ? actStartEl.value : "");
            const maxDate = parentSub?.fecha_final || (actEndEl && actEndEl.value ? actEndEl.value : "");
            [subStartEl, subEndEl].forEach((el) => {
              if (!el) return;
              el.min = minDate || "";
              el.max = maxDate || "";
            });
          };
          const openSubtaskForm = async (subId = 0, parentId = 0) => {
            if (!currentActivityId) {
              showModalMsg("Guarda la actividad antes de crear subtareas.", true);
              return;
            }
            editingSubId = subId || 0;
            currentParentSubId = parentId || 0;
            await fillSubCollaborators();
            const found = currentSubactivities.find((item) => Number(item.id || 0) === Number(editingSubId));
            if (found && found.parent_subactivity_id) {
              currentParentSubId = Number(found.parent_subactivity_id || 0);
            }
            const parentSub = currentSubactivities.find((item) => Number(item.id || 0) === Number(currentParentSubId)) || null;
            const targetLevel = found ? Number(found.nivel || 1) : (parentSub ? Number(parentSub.nivel || 1) + 1 : 1);
            setSubDateBounds(parentSub);
            if (subNameEl) subNameEl.value = found?.nombre || "";
            if (subOwnerEl) subOwnerEl.value = found?.responsable || "";
            if (subStartEl) subStartEl.value = found?.fecha_inicial || "";
            if (subEndEl) subEndEl.value = found?.fecha_final || "";
            if (subDescEl) subDescEl.value = found?.descripcion || "";
            renderSubBranch(targetLevel, found?.nombre || "", currentParentSubId);
            showSubMsg("");
            openSubModal();
            if (subNameEl) subNameEl.focus();
          };
          const saveSubtask = async () => {
            if (!currentActivityId) {
              showSubMsg("Guarda primero la actividad.", true);
              return;
            }
            const nombre = (subNameEl && subNameEl.value ? subNameEl.value : "").trim();
            const responsable = (subOwnerEl && subOwnerEl.value ? subOwnerEl.value : "").trim();
            const fechaInicial = subStartEl && subStartEl.value ? subStartEl.value : "";
            const fechaFinal = subEndEl && subEndEl.value ? subEndEl.value : "";
            const baseDesc = (subDescEl && subDescEl.value ? subDescEl.value : "").trim();
            const assigned = subAssignedEl ? Array.from(subAssignedEl.selectedOptions || []).map((opt) => opt.value).filter(Boolean) : [];
            if (!nombre || !responsable) {
              showSubMsg("Nombre y responsable son obligatorios.", true);
              return;
            }
            if (!fechaInicial || !fechaFinal) {
              showSubMsg("Fecha inicial y fecha final son obligatorias.", true);
              return;
            }
            if (fechaInicial > fechaFinal) {
              showSubMsg("La fecha inicial no puede ser mayor que la final.", true);
              return;
            }
            if ((subStartEl && subStartEl.min && fechaInicial < subStartEl.min) || (subEndEl && subEndEl.max && fechaFinal > subEndEl.max)) {
              showSubMsg("Las fechas deben estar dentro del rango de la actividad.", true);
              return;
            }
            const descripcion = assigned.length
              ? `${baseDesc}${baseDesc ? "\\n\\n" : ""}Personas asignadas: ${assigned.join(", ")}`
              : baseDesc;
            const payload = {
              nombre,
              responsable,
              fecha_inicial: fechaInicial,
              fecha_final: fechaFinal,
              descripcion,
            };
            if (!editingSubId && currentParentSubId) {
              payload.parent_subactivity_id = currentParentSubId;
            }
            showSubMsg("Guardando subtarea...");
            try {
              const url = editingSubId ? `/api/poa/subactivities/${editingSubId}` : `/api/poa/activities/${currentActivityId}/subactivities`;
              const method = editingSubId ? "PUT" : "POST";
              const response = await fetch(url, {
                method,
                headers: { "Content-Type": "application/json" },
                credentials: "same-origin",
                body: JSON.stringify(payload),
              });
              const data = await response.json().catch(() => ({}));
              if (!response.ok || data.success === false) {
                throw new Error(data.error || "No se pudo guardar la subtarea.");
              }
              const item = data.data || {};
              if (editingSubId) {
                currentSubactivities = currentSubactivities.map((sub) => Number(sub.id || 0) === Number(editingSubId) ? item : sub);
              } else {
                currentSubactivities = [item, ...currentSubactivities];
              }
              renderSubtasks();
              closeSubModal();
              showModalMsg("Subtarea guardada.");
            } catch (error) {
              showSubMsg(error.message || "No se pudo guardar la subtarea.", true);
            }
          };
          const deleteSubtask = async (subId) => {
            if (!subId) return;
            if (!window.confirm("¿Eliminar esta subtarea?")) return;
            try {
              const response = await fetch(`/api/poa/subactivities/${subId}`, {
                method: "DELETE",
                headers: { "Content-Type": "application/json" },
                credentials: "same-origin",
              });
              const data = await response.json().catch(() => ({}));
              if (!response.ok || data.success === false) {
                throw new Error(data.error || "No se pudo eliminar la subtarea.");
              }
              const removeIds = new Set([Number(subId)]);
              let changed = true;
              while (changed) {
                changed = false;
                currentSubactivities.forEach((item) => {
                  const itemId = Number(item.id || 0);
                  const parentId = Number(item.parent_subactivity_id || 0);
                  if (!removeIds.has(itemId) && removeIds.has(parentId)) {
                    removeIds.add(itemId);
                    changed = true;
                  }
                });
              }
              currentSubactivities = currentSubactivities.filter((item) => !removeIds.has(Number(item.id || 0)));
              renderSubtasks();
              showModalMsg("Subtarea eliminada.");
            } catch (error) {
              showModalMsg(error.message || "No se pudo eliminar la subtarea.", true);
            }
          };
          const validateActivityDates = () => {
            const start = actStartEl && actStartEl.value ? actStartEl.value : "";
            const end = actEndEl && actEndEl.value ? actEndEl.value : "";
            if (!start || !end) return "Fecha inicial y fecha final son obligatorias.";
            if (start > end) return "La fecha inicial no puede ser mayor que la fecha final.";
            const minDate = String(currentObjective?.fecha_inicial || "");
            const maxDate = String(currentObjective?.fecha_final || "");
            if (minDate && start < minDate) return "La fecha inicial no puede ser menor a la del objetivo.";
            if (maxDate && end > maxDate) return "La fecha final no puede ser mayor a la del objetivo.";
            return "";
          };
          const syncRecurringFields = () => {
            const enabled = !!(actRecurrenteEl && actRecurrenteEl.checked);
            if (actPeriodicidadEl) {
              actPeriodicidadEl.disabled = !enabled;
              if (!enabled) actPeriodicidadEl.value = "";
            }
            const showEveryDays = enabled && actPeriodicidadEl && actPeriodicidadEl.value === "cada_xx_dias";
            if (actEveryDaysWrapEl) actEveryDaysWrapEl.style.display = showEveryDays ? "block" : "none";
            if (actEveryDaysEl && !showEveryDays) actEveryDaysEl.value = "";
          };
          const saveActivity = async () => {
            if (isSaving) return;
            if (!currentObjective) {
              showModalMsg("Selecciona un objetivo válido.", true);
              return;
            }
            const nombre = (actNameEl && actNameEl.value ? actNameEl.value : "").trim();
            const entregable = (actMilestoneEl && actMilestoneEl.value ? actMilestoneEl.value : "").trim();
            const responsable = (actOwnerEl && actOwnerEl.value ? actOwnerEl.value : "").trim();
            const fechaInicial = actStartEl && actStartEl.value ? actStartEl.value : "";
            const fechaFinal = actEndEl && actEndEl.value ? actEndEl.value : "";
            const recurrente = !!(actRecurrenteEl && actRecurrenteEl.checked);
            const periodicidad = (actPeriodicidadEl && actPeriodicidadEl.value ? actPeriodicidadEl.value : "").trim();
            const cadaXxDiasRaw = (actEveryDaysEl && actEveryDaysEl.value ? actEveryDaysEl.value : "").trim();
            const cadaXxDias = cadaXxDiasRaw ? Number(cadaXxDiasRaw) : 0;
            const descripcionBase = (actDescEl && actDescEl.value ? actDescEl.value : "").trim();
            const assigned = actAssignedEl ? Array.from(actAssignedEl.selectedOptions || []).map((opt) => opt.value).filter(Boolean) : [];
            if (!nombre) {
              showModalMsg("Nombre es obligatorio.", true);
              return;
            }
            if (!responsable) {
              showModalMsg("Responsable es obligatorio.", true);
              return;
            }
            if (!entregable) {
              showModalMsg("Entregable es obligatorio.", true);
              return;
            }
            const dateError = validateActivityDates();
            if (dateError) {
              showModalMsg(dateError, true);
              return;
            }
            if (recurrente) {
              if (!periodicidad) {
                showModalMsg("Selecciona una periodicidad para la actividad recurrente.", true);
                return;
              }
              if (periodicidad === "cada_xx_dias" && (!Number.isInteger(cadaXxDias) || cadaXxDias <= 0)) {
                showModalMsg("Cada xx dias debe ser un entero mayor a 0.", true);
                return;
              }
            }
            const descripcion = assigned.length
              ? `${descripcionBase}${descripcionBase ? "\\n\\n" : ""}Personas asignadas: ${assigned.join(", ")}`
              : descripcionBase;
            const payload = {
              objective_id: Number(currentObjective.id || 0),
              nombre,
              entregable,
              responsable,
              fecha_inicial: fechaInicial,
              fecha_final: fechaFinal,
              recurrente,
              periodicidad: recurrente ? periodicidad : "",
              cada_xx_dias: recurrente && periodicidad === "cada_xx_dias" ? cadaXxDias : 0,
              descripcion,
            };
            isSaving = true;
            if (saveBtn) saveBtn.disabled = true;
            showModalMsg("Guardando actividad...");
            try {
              const response = await fetch(currentActivityId ? `/api/poa/activities/${currentActivityId}` : "/api/poa/activities", {
                method: currentActivityId ? "PUT" : "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "same-origin",
                body: JSON.stringify(payload),
              });
              const data = await response.json().catch(() => ({}));
              if (!response.ok || data.success === false) {
                throw new Error(data.error || "No se pudo guardar la actividad.");
              }
              currentActivityId = Number(data.data?.id || currentActivityId || 0);
              currentActivityData = data.data || currentActivityData;
              currentSubactivities = Array.isArray(data.data?.subactivities) ? data.data.subactivities : currentSubactivities;
              renderSubtasks();
              renderStateStrip();
              showModalMsg("Actividad guardada correctamente.");
              await loadBoard();
            } catch (error) {
              showModalMsg(error.message || "No se pudo guardar la actividad.", true);
            } finally {
              isSaving = false;
              if (saveBtn) saveBtn.disabled = false;
            }
          };
          const markInProgress = async () => {
            if (!currentActivityId) {
              showModalMsg("Guarda primero la actividad para cambiar su estado.", true);
              return;
            }
            showModalMsg("Actualizando estado...");
            try {
              const response = await fetch(`/api/poa/activities/${currentActivityId}/mark-in-progress`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "same-origin",
              });
              const data = await response.json().catch(() => ({}));
              if (!response.ok || data.success === false) {
                throw new Error(data.error || "No se pudo marcar en proceso.");
              }
              currentActivityData = data.data || currentActivityData;
              currentSubactivities = Array.isArray(data.data?.subactivities) ? data.data.subactivities : currentSubactivities;
              renderStateStrip();
              showModalMsg("Actividad en proceso.");
              await loadBoard();
            } catch (error) {
              showModalMsg(error.message || "No se pudo marcar en proceso.", true);
            }
          };
          const markFinished = async () => {
            if (!currentActivityId) {
              showModalMsg("Guarda primero la actividad para declararla terminada.", true);
              return;
            }
            const entregableName = (actMilestoneEl && actMilestoneEl.value ? actMilestoneEl.value : "").trim() || "N/D";
            const sendReview = window.confirm(`El entregable es ${entregableName}, ¿Quiere enviarlo a revisión?`);
            showModalMsg(sendReview ? "Enviando a revisión..." : "Declarando terminado...");
            try {
              const response = await fetch(`/api/poa/activities/${currentActivityId}/mark-finished`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "same-origin",
                body: JSON.stringify({ enviar_revision: sendReview }),
              });
              const data = await response.json().catch(() => ({}));
              if (!response.ok || data.success === false) {
                throw new Error(data.error || "No se pudo actualizar el estado.");
              }
              currentActivityData = data.data || currentActivityData;
              currentSubactivities = Array.isArray(data.data?.subactivities) ? data.data.subactivities : currentSubactivities;
              renderStateStrip();
              showModalMsg(data.message || "Estado actualizado.");
              await loadBoard();
            } catch (error) {
              showModalMsg(error.message || "No se pudo actualizar el estado.", true);
            }
          };
          const resolveApproval = async (action) => {
            const approval = currentApprovalForActivity();
            if (!approval) {
              showModalMsg("No hay entregable pendiente para revisar.", true);
              return;
            }
            showModalMsg(action === "autorizar" ? "Aprobando entregable..." : "Rechazando entregable...");
            try {
              const response = await fetch(`/api/poa/approvals/${approval.id}/decision`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "same-origin",
                body: JSON.stringify({ accion: action, comentario: "" }),
              });
              const data = await response.json().catch(() => ({}));
              if (!response.ok || data.success === false) {
                throw new Error(data.error || "No se pudo procesar la revisión.");
              }
              showModalMsg(data.message || "Revisión procesada.");
              await loadBoard();
              if (currentObjective) {
                const latest = (activitiesByObjective[Number(currentObjective.id || 0)] || [])
                  .find((item) => Number(item.id || 0) === Number(currentActivityId))
                  || null;
                if (latest) {
                  currentActivityData = latest;
                  currentSubactivities = Array.isArray(latest.subactivities) ? latest.subactivities : [];
                }
                renderStateStrip();
              }
            } catch (error) {
              showModalMsg(error.message || "No se pudo procesar la revisión.", true);
            }
          };
          closeBtn && closeBtn.addEventListener("click", closeModal);
          cancelBtn && cancelBtn.addEventListener("click", closeModal);
          subCloseBtn && subCloseBtn.addEventListener("click", closeSubModal);
          subCancelBtn && subCancelBtn.addEventListener("click", closeSubModal);
          subSaveBtn && subSaveBtn.addEventListener("click", saveSubtask);
          subAddBtn && subAddBtn.addEventListener("click", () => openSubtaskForm(0, 0));
          modalEl && modalEl.addEventListener("click", (event) => {
            if (event.target === modalEl) closeModal();
          });
          subModalEl && subModalEl.addEventListener("click", (event) => {
            if (event.target === subModalEl) closeSubModal();
          });
          document.addEventListener("keydown", (event) => {
            if (event.key === "Escape" && modalEl && modalEl.classList.contains("open")) closeModal();
            if (event.key === "Escape" && subModalEl && subModalEl.classList.contains("open")) closeSubModal();
          });
          saveBtn && saveBtn.addEventListener("click", saveActivity);
          stateEnProcesoBtn && stateEnProcesoBtn.addEventListener("click", markInProgress);
          stateTerminadoBtn && stateTerminadoBtn.addEventListener("click", markFinished);
          approveBtn && approveBtn.addEventListener("click", () => resolveApproval("autorizar"));
          rejectBtn && rejectBtn.addEventListener("click", () => resolveApproval("rechazar"));
          actNameEl && actNameEl.addEventListener("input", renderActivityBranch);
          actRecurrenteEl && actRecurrenteEl.addEventListener("change", syncRecurringFields);
          actPeriodicidadEl && actPeriodicidadEl.addEventListener("change", syncRecurringFields);
          subNameEl && subNameEl.addEventListener("input", () => {
            const found = currentSubactivities.find((item) => Number(item.id || 0) === Number(editingSubId));
            const targetLevel = found ? Number(found.nivel || 1) : (() => {
              const parentSub = currentSubactivities.find((item) => Number(item.id || 0) === Number(currentParentSubId));
              return parentSub ? Number(parentSub.nivel || 1) + 1 : 1;
            })();
            renderSubBranch(targetLevel, subNameEl.value || "", currentParentSubId);
          });
          document.querySelectorAll("[data-poa-tab]").forEach((tabBtn) => {
            tabBtn.addEventListener("click", () => {
              const tabKey = tabBtn.getAttribute("data-poa-tab");
              document.querySelectorAll("[data-poa-tab]").forEach((btn) => btn.classList.remove("active"));
              document.querySelectorAll("[data-poa-panel]").forEach((panel) => panel.classList.remove("active"));
              tabBtn.classList.add("active");
              const panel = document.querySelector(`[data-poa-panel="${tabKey}"]`);
              if (panel) panel.classList.add("active");
            });
          });

          const renderBoard = (payload) => {
            const objectives = Array.isArray(payload.objectives) ? payload.objectives : [];
            const activities = Array.isArray(payload.activities) ? payload.activities : [];
            const pendingApprovals = Array.isArray(payload.pending_approvals) ? payload.pending_approvals : [];
            objectivesById = {};
            activitiesByObjective = {};
            approvalsByActivity = {};
            objectives.forEach((obj) => {
              objectivesById[Number(obj.id || 0)] = obj;
            });
            const activityCountByObjective = {};
            activities.forEach((item) => {
              const key = Number(item.objective_id || 0);
              if (!key) return;
              activityCountByObjective[key] = (activityCountByObjective[key] || 0) + 1;
              if (!activitiesByObjective[key]) activitiesByObjective[key] = [];
              activitiesByObjective[key].push(item);
            });
            Object.keys(activitiesByObjective).forEach((key) => {
              activitiesByObjective[key].sort((a, b) => Number(b.id || 0) - Number(a.id || 0));
            });
            pendingApprovals.forEach((approval) => {
              const actId = Number(approval.activity_id || 0);
              if (!actId) return;
              approvalsByActivity[actId] = approval;
            });
            if (currentActivityId && currentObjective) {
              const latest = (activitiesByObjective[Number(currentObjective.id || 0)] || [])
                .find((item) => Number(item.id || 0) === Number(currentActivityId))
                || null;
              if (latest) {
                currentActivityData = latest;
                currentSubactivities = Array.isArray(latest.subactivities) ? latest.subactivities : [];
              }
              renderStateStrip();
            }
            const grouped = {};
            objectives.forEach((obj) => {
              const axisName = String(obj.axis_name || "Sin eje").trim() || "Sin eje";
              if (!grouped[axisName]) grouped[axisName] = [];
              grouped[axisName].push(obj);
            });
            const axisNames = Object.keys(grouped).sort((a, b) => a.localeCompare(b, "es"));
            if (!axisNames.length) {
              gridEl.innerHTML = '<div class="poa-obj-card" style="min-width:320px;"><h4>Sin objetivos</h4><div class="meta">No hay objetivos disponibles para mostrar.</div></div>';
              return;
            }
            gridEl.innerHTML = axisNames.map((axisName) => {
              const items = grouped[axisName] || [];
              const cards = items.map((obj) => {
                const countActivities = activityCountByObjective[Number(obj.id || 0)] || 0;
                return `
                  <article class="poa-obj-card" data-objective-id="${Number(obj.id || 0)}">
                    <h4>${escapeHtml(obj.nombre || "Objetivo sin nombre")}</h4>
                    <div class="meta">Fecha inicial: ${escapeHtml(fmtDate(obj.fecha_inicial))}</div>
                    <div class="meta">Fecha final: ${escapeHtml(fmtDate(obj.fecha_final))}</div>
                    <div class="meta">Actividades: ${countActivities}</div>
                    <span class="code">${escapeHtml(obj.codigo || "xx-yy-zz")}</span>
                    <div class="code-next">${escapeHtml(nextCode(obj.codigo || ""))}</div>
                  </article>
                `;
              }).join("");
              return `
                <section class="poa-axis-col" data-axis-col>
                  <header class="poa-axis-head">
                    <h3 class="poa-axis-title">${escapeHtml(axisName)}</h3>
                    <button type="button" class="poa-axis-toggle" data-axis-toggle aria-label="Colapsar columna">−</button>
                  </header>
                  <div class="poa-axis-cards">${cards || '<article class="poa-obj-card"><div class="meta">Sin objetivos</div></article>'}</div>
                </section>
              `;
            }).join("");

            gridEl.querySelectorAll("[data-axis-toggle]").forEach((button) => {
              button.addEventListener("click", () => {
                const col = button.closest("[data-axis-col]");
                if (!col) return;
                const collapsed = col.classList.toggle("collapsed");
                button.textContent = collapsed ? "+" : "−";
                button.setAttribute("aria-label", collapsed ? "Mostrar columna" : "Colapsar columna");
              });
            });
            gridEl.querySelectorAll("[data-objective-id]").forEach((card) => {
              card.addEventListener("click", async () => {
                await openActivityForm(card.getAttribute("data-objective-id"));
              });
            });
          };

          const loadBoard = async () => {
            showMsg("Cargando tablero POA...");
            try {
              const response = await fetch("/api/poa/board-data", {
                headers: { "Content-Type": "application/json" },
                credentials: "same-origin",
              });
              const payload = await response.json().catch(() => ({}));
              if (!response.ok || payload.success === false) {
                throw new Error(payload.error || "No se pudo cargar la vista POA.");
              }
              renderBoard(payload);
              showMsg("");
            } catch (error) {
              showMsg(error.message || "No se pudo cargar la vista POA.", true);
            }
          };

          loadBoard();
        })();
      </script>
    </section>
""")


@router.get("/planes", response_class=HTMLResponse)
@router.get("/plan-estrategico", response_class=HTMLResponse)
@router.get("/ejes-estrategicos", response_class=HTMLResponse)
def ejes_estrategicos_page(request: Request):
    _bind_core_symbols()
    return render_backend_page(
        request,
        title="Ejes estratégicos",
        description="Edición y administración de ejes y objetivos estratégicos.",
        content=EJES_ESTRATEGICOS_HTML,
        hide_floating_actions=True,
        show_page_header=True,
        view_buttons=[
            {"label": "Form", "icon": "/templates/icon/formulario.svg", "view": "form", "active": True},
        ],
    )


@router.get("/poa", response_class=HTMLResponse)
@router.get("/poa/crear", response_class=HTMLResponse)
def poa_page(request: Request):
    _bind_core_symbols()
    return render_backend_page(
        request,
        title="POA",
        description="Pantalla de trabajo POA.",
        content=POA_LIMPIO_HTML,
        hide_floating_actions=True,
        show_page_header=True,
        view_buttons=[
            {"label": "Form", "icon": "/templates/icon/formulario.svg", "view": "form", "active": True},
        ],
    )


@router.get("/api/strategic-axes")
def list_strategic_axes(request: Request):
    _bind_core_symbols()
    db = SessionLocal()
    try:
        axes = (
            db.query(StrategicAxisConfig)
            .filter(StrategicAxisConfig.is_active == True)
            .order_by(StrategicAxisConfig.orden.asc(), StrategicAxisConfig.id.asc())
            .all()
        )
        return JSONResponse({"success": True, "data": [_serialize_strategic_axis(axis) for axis in axes]})
    finally:
        db.close()


@router.get("/api/strategic-axes/departments")
def list_strategic_axis_departments():
    _bind_core_symbols()
    db = SessionLocal()
    try:
        departments = []
        rows = (
            db.query(Usuario.departamento)
            .filter(Usuario.departamento.isnot(None))
            .all()
        )
        for row in rows:
            value = (row[0] or "").strip()
            if value:
                departments.append(value)
        unique_departments = sorted(set(departments), key=lambda item: item.lower())
        return JSONResponse({"success": True, "data": unique_departments})
    finally:
        db.close()


@router.get("/api/strategic-axes/collaborators-by-department")
def list_collaborators_by_department(department: str = Query(default="")):
    _bind_core_symbols()
    dep = (department or "").strip()
    if not dep:
        return JSONResponse({"success": True, "data": []})
    db = SessionLocal()
    try:
        rows = (
            db.query(Usuario.nombre)
            .filter(Usuario.departamento == dep)
            .all()
        )
        collaborators = []
        for row in rows:
            value = (row[0] or "").strip()
            if value:
                collaborators.append(value)
        unique_collaborators = sorted(set(collaborators), key=lambda item: item.lower())
        return JSONResponse({"success": True, "data": unique_collaborators})
    finally:
        db.close()


@router.get("/api/strategic-axes/{axis_id}/collaborators")
def list_strategic_axis_collaborators(axis_id: int):
    _bind_core_symbols()
    db = SessionLocal()
    try:
        axis = db.query(StrategicAxisConfig).filter(StrategicAxisConfig.id == axis_id).first()
        if not axis:
            return JSONResponse({"success": False, "error": "Eje no encontrado"}, status_code=404)
        department = (axis.lider_departamento or "").strip()
        if not department:
            return JSONResponse({"success": True, "data": []})
        rows = (
            db.query(Usuario.nombre)
            .filter(Usuario.departamento == department)
            .all()
        )
        collaborators = []
        for row in rows:
            value = (row[0] or "").strip()
            if value:
                collaborators.append(value)
        unique_collaborators = sorted(set(collaborators), key=lambda item: item.lower())
        return JSONResponse({"success": True, "data": unique_collaborators})
    finally:
        db.close()


@router.post("/api/strategic-axes")
def create_strategic_axis(request: Request, data: dict = Body(...)):
    _bind_core_symbols()
    nombre = (data.get("nombre") or "").strip()
    if not nombre:
        return JSONResponse({"success": False, "error": "El nombre del eje es obligatorio"}, status_code=400)

    db = SessionLocal()
    try:
        max_order = db.query(func.max(StrategicAxisConfig.orden)).scalar() or 0
        axis_order = int(data.get("orden") or (max_order + 1))
        base_code = (data.get("base_code") or "").strip()
        if not base_code:
            raw_code = (data.get("codigo") or "").strip().lower()
            base_code = raw_code.split("-", 1)[0] if "-" in raw_code else raw_code
        axis = StrategicAxisConfig(
            nombre=nombre,
            codigo=_compose_axis_code(base_code, axis_order),
            lider_departamento=(data.get("lider_departamento") or "").strip(),
            responsabilidad_directa=(data.get("responsabilidad_directa") or "").strip(),
            descripcion=(data.get("descripcion") or "").strip(),
            orden=axis_order,
            is_active=True,
        )
        db.add(axis)
        db.commit()
        db.refresh(axis)
        return JSONResponse({"success": True, "data": _serialize_strategic_axis(axis)})
    except (sqlite3.OperationalError, SQLAlchemyError):
        db.rollback()
        return JSONResponse(
            {"success": False, "error": "No se pudo escribir en la base de datos (modo solo lectura o bloqueo)."},
            status_code=500,
        )
    finally:
        db.close()


@router.put("/api/strategic-axes/{axis_id}")
def update_strategic_axis(axis_id: int, data: dict = Body(...)):
    _bind_core_symbols()
    db = SessionLocal()
    try:
        axis = db.query(StrategicAxisConfig).filter(StrategicAxisConfig.id == axis_id).first()
        if not axis:
            return JSONResponse({"success": False, "error": "Eje no encontrado"}, status_code=404)
        nombre = (data.get("nombre") or "").strip()
        if not nombre:
            return JSONResponse({"success": False, "error": "El nombre del eje es obligatorio"}, status_code=400)
        axis_order = int(data.get("orden") or axis.orden or 1)
        base_code = (data.get("base_code") or "").strip()
        if not base_code:
            raw_code = (data.get("codigo") or axis.codigo or "").strip().lower()
            base_code = raw_code.split("-", 1)[0] if "-" in raw_code else raw_code
        axis.nombre = nombre
        axis.codigo = _compose_axis_code(base_code, axis_order)
        axis.lider_departamento = (data.get("lider_departamento") or "").strip()
        axis.responsabilidad_directa = (data.get("responsabilidad_directa") or "").strip()
        axis.descripcion = (data.get("descripcion") or "").strip()
        axis.orden = axis_order
        db.add(axis)
        db.commit()
        db.refresh(axis)
        return JSONResponse({"success": True, "data": _serialize_strategic_axis(axis)})
    except (sqlite3.OperationalError, SQLAlchemyError):
        db.rollback()
        return JSONResponse(
            {"success": False, "error": "No se pudo escribir en la base de datos (modo solo lectura o bloqueo)."},
            status_code=500,
        )
    finally:
        db.close()


@router.delete("/api/strategic-axes/{axis_id}")
def delete_strategic_axis(axis_id: int):
    _bind_core_symbols()
    db = SessionLocal()
    try:
        axis = db.query(StrategicAxisConfig).filter(StrategicAxisConfig.id == axis_id).first()
        if not axis:
            return JSONResponse({"success": False, "error": "Eje no encontrado"}, status_code=404)
        db.delete(axis)
        db.commit()
        return JSONResponse({"success": True})
    except (sqlite3.OperationalError, SQLAlchemyError):
        db.rollback()
        return JSONResponse(
            {"success": False, "error": "No se pudo escribir en la base de datos (modo solo lectura o bloqueo)."},
            status_code=500,
        )
    finally:
        db.close()


@router.post("/api/strategic-axes/{axis_id}/objectives")
def create_strategic_objective(axis_id: int, data: dict = Body(...)):
    _bind_core_symbols()
    nombre = (data.get("nombre") or "").strip()
    if not nombre:
        return JSONResponse({"success": False, "error": "El nombre del objetivo es obligatorio"}, status_code=400)
    db = SessionLocal()
    try:
        axis = db.query(StrategicAxisConfig).filter(StrategicAxisConfig.id == axis_id).first()
        if not axis:
            return JSONResponse({"success": False, "error": "Eje no encontrado"}, status_code=404)
        start_date, start_error = _parse_date_field(data.get("fecha_inicial"), "Fecha inicial", required=False)
        if start_error:
            return JSONResponse({"success": False, "error": start_error}, status_code=400)
        end_date, end_error = _parse_date_field(data.get("fecha_final"), "Fecha final", required=False)
        if end_error:
            return JSONResponse({"success": False, "error": end_error}, status_code=400)
        if (start_date and not end_date) or (end_date and not start_date):
            return JSONResponse(
                {"success": False, "error": "Objetivo: fecha inicial y fecha final deben definirse juntas"},
                status_code=400,
            )
        if start_date and end_date:
            range_error = _validate_date_range(start_date, end_date, "Objetivo")
            if range_error:
                return JSONResponse({"success": False, "error": range_error}, status_code=400)
        objective_leader = (data.get("lider") or "").strip()
        axis_department = (axis.lider_departamento or "").strip()
        if objective_leader and axis_department:
            if not _collaborator_belongs_to_department(db, objective_leader, axis_department):
                return JSONResponse(
                    {
                        "success": False,
                        "error": "El líder debe pertenecer al personal del área/departamento del eje.",
                    },
                    status_code=400,
                )
        max_order = (
            db.query(func.max(StrategicObjectiveConfig.orden))
            .filter(StrategicObjectiveConfig.eje_id == axis_id)
            .scalar()
            or 0
        )
        objective_order = int(data.get("orden") or (max_order + 1))
        objective = StrategicObjectiveConfig(
            eje_id=axis_id,
            codigo=_compose_objective_code(axis.codigo or "", objective_order),
            nombre=nombre,
            lider=objective_leader,
            fecha_inicial=start_date,
            fecha_final=end_date,
            descripcion=(data.get("descripcion") or "").strip(),
            orden=objective_order,
            is_active=True,
        )
        db.add(objective)
        db.commit()
        db.refresh(objective)
        return JSONResponse({"success": True, "data": _serialize_strategic_objective(objective)})
    except (sqlite3.OperationalError, SQLAlchemyError):
        db.rollback()
        return JSONResponse(
            {"success": False, "error": "No se pudo escribir en la base de datos (modo solo lectura o bloqueo)."},
            status_code=500,
        )
    finally:
        db.close()


@router.put("/api/strategic-objectives/{objective_id}")
def update_strategic_objective(objective_id: int, data: dict = Body(...)):
    _bind_core_symbols()
    db = SessionLocal()
    try:
        objective = db.query(StrategicObjectiveConfig).filter(StrategicObjectiveConfig.id == objective_id).first()
        if not objective:
            return JSONResponse({"success": False, "error": "Objetivo no encontrado"}, status_code=404)
        nombre = (data.get("nombre") or "").strip()
        if not nombre:
            return JSONResponse({"success": False, "error": "El nombre del objetivo es obligatorio"}, status_code=400)
        start_date, start_error = _parse_date_field(data.get("fecha_inicial"), "Fecha inicial", required=False)
        if start_error:
            return JSONResponse({"success": False, "error": start_error}, status_code=400)
        end_date, end_error = _parse_date_field(data.get("fecha_final"), "Fecha final", required=False)
        if end_error:
            return JSONResponse({"success": False, "error": end_error}, status_code=400)
        if (start_date and not end_date) or (end_date and not start_date):
            return JSONResponse(
                {"success": False, "error": "Objetivo: fecha inicial y fecha final deben definirse juntas"},
                status_code=400,
            )
        if start_date and end_date:
            range_error = _validate_date_range(start_date, end_date, "Objetivo")
            if range_error:
                return JSONResponse({"success": False, "error": range_error}, status_code=400)
        axis = db.query(StrategicAxisConfig).filter(StrategicAxisConfig.id == objective.eje_id).first()
        objective_leader = (data.get("lider") or "").strip()
        axis_department = (axis.lider_departamento or "").strip() if axis else ""
        if objective_leader and axis_department:
            if not _collaborator_belongs_to_department(db, objective_leader, axis_department):
                return JSONResponse(
                    {
                        "success": False,
                        "error": "El líder debe pertenecer al personal del área/departamento del eje.",
                    },
                    status_code=400,
                )
        objective_order = int(data.get("orden") or objective.orden or 1)
        objective.codigo = _compose_objective_code((axis.codigo if axis else ""), objective_order)
        objective.nombre = nombre
        objective.lider = objective_leader
        objective.fecha_inicial = start_date
        objective.fecha_final = end_date
        objective.descripcion = (data.get("descripcion") or "").strip()
        objective.orden = objective_order
        db.add(objective)
        db.commit()
        db.refresh(objective)
        return JSONResponse({"success": True, "data": _serialize_strategic_objective(objective)})
    finally:
        db.close()


@router.delete("/api/strategic-objectives/{objective_id}")
def delete_strategic_objective(objective_id: int):
    _bind_core_symbols()
    db = SessionLocal()
    try:
        objective = db.query(StrategicObjectiveConfig).filter(StrategicObjectiveConfig.id == objective_id).first()
        if not objective:
            return JSONResponse({"success": False, "error": "Objetivo no encontrado"}, status_code=404)
        db.delete(objective)
        db.commit()
        return JSONResponse({"success": True})
    finally:
        db.close()


def _allowed_objectives_for_user(request: Request, db) -> List[StrategicObjectiveConfig]:
    _bind_core_symbols()
    if is_admin_or_superadmin(request):
        return (
            db.query(StrategicObjectiveConfig)
            .filter(StrategicObjectiveConfig.is_active == True)
            .order_by(StrategicObjectiveConfig.orden.asc(), StrategicObjectiveConfig.id.asc())
            .all()
        )

    session_username = (getattr(request.state, "user_name", None) or request.cookies.get("user_name") or "").strip()
    user = _current_user_record(request, db)
    aliases = _user_aliases(user, session_username)
    user_department = (user.departamento or "").strip().lower() if user and user.departamento else ""

    objectives = (
        db.query(StrategicObjectiveConfig)
        .join(StrategicAxisConfig, StrategicAxisConfig.id == StrategicObjectiveConfig.eje_id)
        .filter(StrategicObjectiveConfig.is_active == True)
        .order_by(StrategicObjectiveConfig.orden.asc(), StrategicObjectiveConfig.id.asc())
        .all()
    )
    allowed: List[StrategicObjectiveConfig] = []
    for obj in objectives:
        axis = db.query(StrategicAxisConfig).filter(StrategicAxisConfig.id == obj.eje_id).first()
        objective_leader = (obj.lider or "").strip().lower()
        axis_department = (axis.lider_departamento or "").strip().lower() if axis else ""
        if objective_leader and objective_leader in aliases:
            allowed.append(obj)
            continue
        if user_department and axis_department and axis_department == user_department:
            allowed.append(obj)
    return allowed


@router.get("/api/poa/board-data")
def poa_board_data(request: Request):
    _bind_core_symbols()
    db = SessionLocal()
    try:
        objectives = _allowed_objectives_for_user(request, db)
        objective_ids = [obj.id for obj in objectives]
        objective_axis_map = {obj.id: obj.eje_id for obj in objectives}
        axis_ids = sorted(set(objective_axis_map.values()))
        axes = (
            db.query(StrategicAxisConfig)
            .filter(StrategicAxisConfig.id.in_(axis_ids))
            .all()
            if axis_ids else []
        )
        axis_name_map = {axis.id: axis.nombre for axis in axes}

        activities = (
            db.query(POAActivity)
            .filter(POAActivity.objective_id.in_(objective_ids))
            .order_by(POAActivity.id.asc())
            .all()
            if objective_ids else []
        )
        activity_ids = [item.id for item in activities]
        subactivities = (
            db.query(POASubactivity)
            .filter(POASubactivity.activity_id.in_(activity_ids))
            .order_by(POASubactivity.id.asc())
            .all()
            if activity_ids else []
        )
        sub_by_activity: Dict[int, List[POASubactivity]] = {}
        for sub in subactivities:
            sub_by_activity.setdefault(sub.activity_id, []).append(sub)

        pending_approvals = (
            db.query(POADeliverableApproval)
            .filter(POADeliverableApproval.status == "pendiente")
            .order_by(POADeliverableApproval.created_at.desc())
            .all()
        )
        approvals_for_user = []
        for approval in pending_approvals:
            if not _is_user_process_owner(request, db, approval.process_owner):
                continue
            activity = next((item for item in activities if item.id == approval.activity_id), None)
            if not activity:
                activity = db.query(POAActivity).filter(POAActivity.id == approval.activity_id).first()
            objective = next((item for item in objectives if item.id == approval.objective_id), None)
            if not objective:
                objective = db.query(StrategicObjectiveConfig).filter(StrategicObjectiveConfig.id == approval.objective_id).first()
            approvals_for_user.append(
                {
                    "id": approval.id,
                    "activity_id": approval.activity_id,
                    "objective_id": approval.objective_id,
                    "process_owner": approval.process_owner or "",
                    "requester": approval.requester or "",
                    "created_at": approval.created_at.isoformat() if approval.created_at else "",
                    "activity_nombre": (activity.nombre if activity else ""),
                    "activity_codigo": (activity.codigo if activity else ""),
                    "objective_nombre": (objective.nombre if objective else ""),
                    "objective_codigo": (objective.codigo if objective else ""),
                }
            )

        return JSONResponse(
            {
                "success": True,
                "objectives": [
                    {
                        **_serialize_strategic_objective(obj),
                        "axis_name": axis_name_map.get(obj.eje_id, ""),
                    }
                    for obj in objectives
                ],
                "activities": [
                    _serialize_poa_activity(activity, sub_by_activity.get(activity.id, []))
                    for activity in activities
                ],
                "pending_approvals": approvals_for_user,
            }
        )
    finally:
        db.close()


@router.get("/api/notificaciones/resumen")
def notifications_summary(request: Request):
    _bind_core_symbols()
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        today = now.date()
        tenant_id = _normalize_tenant_id(get_current_tenant(request))
        user_key = _notification_user_key(request, db)
        items: List[Dict[str, Any]] = []

        pending_approvals = (
            db.query(POADeliverableApproval)
            .filter(POADeliverableApproval.status == "pendiente")
            .order_by(POADeliverableApproval.created_at.desc())
            .all()
        )
        for approval in pending_approvals:
            if not _is_user_process_owner(request, db, approval.process_owner):
                continue
            activity = db.query(POAActivity).filter(POAActivity.id == approval.activity_id).first()
            objective = db.query(StrategicObjectiveConfig).filter(StrategicObjectiveConfig.id == approval.objective_id).first()
            items.append(
                {
                    "id": f"poa-approval-{approval.id}",
                    "kind": "poa_aprobacion",
                    "title": "Aprobación de entregable pendiente",
                    "message": (
                        f"Actividad {(activity.nombre if activity else 'sin nombre')} "
                        f"({activity.codigo if activity else ''}) - Objetivo {(objective.nombre if objective else '')}"
                    ).strip(),
                    "created_at": (approval.created_at or now).isoformat(),
                    "href": "/poa/crear",
                }
            )

        # ...línea eliminada: _can_authorize_documents(request) no existe...
            tenant_id = _get_document_tenant(request)
            docs_query = db.query(DocumentoEvidencia).filter(DocumentoEvidencia.estado.in_(["enviado", "actualizado"]))
            if is_superadmin(request):
                header_tenant = request.headers.get("x-tenant-id")
                if header_tenant and _normalize_tenant_id(header_tenant) != "all":
                    docs_query = docs_query.filter(
                        func.lower(DocumentoEvidencia.tenant_id) == _normalize_tenant_id(header_tenant).lower()
                    )
                elif not header_tenant:
                    docs_query = docs_query.filter(func.lower(DocumentoEvidencia.tenant_id) == tenant_id.lower())
            else:
                docs_query = docs_query.filter(func.lower(DocumentoEvidencia.tenant_id) == tenant_id.lower())
            docs_pending = docs_query.order_by(DocumentoEvidencia.updated_at.desc()).limit(20).all()
            for doc in docs_pending:
                items.append(
                    {
                        "id": f"doc-approval-{doc.id}",
                        "kind": "documento_autorizacion",
                        "title": "Documento pendiente de autorización",
                        "message": f"{(doc.titulo or '').strip()} · Estado: {(doc.estado or '').strip()}",
                        "created_at": (doc.updated_at or doc.enviado_at or doc.creado_at or now).isoformat(),
                        "href": "/reportes/documentos",
                    }
                )

        if is_superadmin(request):
            quiz_rows = (
                db.query(PublicQuizSubmission)
                .order_by(PublicQuizSubmission.created_at.desc(), PublicQuizSubmission.id.desc())
                .limit(20)
                .all()
            )
            for quiz in quiz_rows:
                items.append(
                    {
                        "id": f"quiz-submission-{quiz.id}",
                        "kind": "quiz_descuento",
                        "title": "Nuevo cuestionario de descuento",
                        "message": (
                            f"{(quiz.nombre or '').strip()} · {(quiz.cooperativa or '').strip()} · "
                            f"{int(quiz.correctas or 0)}/10 correctas · {int(quiz.descuento or 0)}% de descuento"
                        ),
                        "created_at": (quiz.created_at or now).isoformat(),
                        "href": "/usuarios",
                    }
                )

        session_username = (getattr(request.state, "user_name", None) or request.cookies.get("user_name") or "").strip()
        user = _current_user_record(request, db)
        aliases = sorted(_user_aliases(user, session_username))
        if aliases:
            lookahead = today + timedelta(days=2)
            own_activities = (
                db.query(POAActivity)
                .filter(func.lower(POAActivity.responsable).in_(aliases))
                .order_by(POAActivity.fecha_final.asc(), POAActivity.id.asc())
                .all()
            )
            for activity in own_activities:
                if not activity.fecha_final:
                    continue
                if (activity.entrega_estado or "").strip().lower() == "aprobada":
                    continue
                if activity.fecha_final > lookahead:
                    continue
                delta_days = (activity.fecha_final - today).days
                if delta_days < 0:
                    title = "Actividad vencida"
                    message = f"{activity.nombre} venció el {activity.fecha_final.isoformat()}"
                elif delta_days == 0:
                    title = "Actividad vence hoy"
                    message = f"{activity.nombre} vence hoy"
                else:
                    title = "Actividad por vencer"
                    message = f"{activity.nombre} vence el {activity.fecha_final.isoformat()}"
                items.append(
                    {
                        "id": f"activity-deadline-{activity.id}",
                        "kind": "actividad_fecha",
                        "title": title,
                        "message": message,
                        "created_at": datetime.combine(activity.fecha_final, datetime.min.time()).isoformat(),
                        "href": "/poa/crear",
                    }
                )

        items.sort(key=lambda item: item.get("created_at") or "", reverse=True)
        limited_items = items[:25]
        notification_ids = [str(item.get("id") or "").strip() for item in limited_items if str(item.get("id") or "").strip()]
        read_ids: Set[str] = set()
        if user_key and notification_ids:
            read_rows = (
                db.query(UserNotificationRead.notification_id)
                .filter(
                    UserNotificationRead.tenant_id == tenant_id,
                    UserNotificationRead.user_key == user_key,
                    UserNotificationRead.notification_id.in_(notification_ids),
                )
                .all()
            )
            read_ids = {str(row[0]) for row in read_rows}
        for item in limited_items:
            item["read"] = str(item.get("id") or "") in read_ids

        counts = {
            "poa_aprobacion": 0,
            "documento_autorizacion": 0,
            "actividad_fecha": 0,
            "quiz_descuento": 0,
        }
        for item in limited_items:
            kind = str(item.get("kind") or "")
            if kind in counts:
                counts[kind] += 0 if item.get("read") else 1
        unread = sum(0 if item.get("read") else 1 for item in limited_items)

        return JSONResponse(
            {
                "success": True,
                "total": len(limited_items),
                "unread": unread,
                "counts": counts,
                "items": limited_items,
            }
        )
    finally:
        db.close()


@router.post("/api/notificaciones/marcar-leida")
def mark_notification_read(request: Request, data: dict = Body(default={})):
    _bind_core_symbols()
    notification_id = (data.get("id") or "").strip()
    if not notification_id:
        return JSONResponse({"success": False, "error": "ID de notificación requerido"}, status_code=400)

    db = SessionLocal()
    try:
        tenant_id = _normalize_tenant_id(get_current_tenant(request))
        user_key = _notification_user_key(request, db)
        if not user_key:
            return JSONResponse({"success": False, "error": "Usuario no autenticado"}, status_code=401)

        row = (
            db.query(UserNotificationRead)
            .filter(
                UserNotificationRead.tenant_id == tenant_id,
                UserNotificationRead.user_key == user_key,
                UserNotificationRead.notification_id == notification_id,
            )
            .first()
        )
        if row:
            row.read_at = datetime.utcnow()
            db.add(row)
        else:
            db.add(
                UserNotificationRead(
                    tenant_id=tenant_id,
                    user_key=user_key,
                    notification_id=notification_id,
                    read_at=datetime.utcnow(),
                )
            )
        db.commit()
        return JSONResponse({"success": True})
    finally:
        db.close()


@router.post("/api/notificaciones/marcar-todas-leidas")
def mark_all_notifications_read(request: Request, data: dict = Body(default={})):
    _bind_core_symbols()
    raw_ids = data.get("ids")
    ids = [str(value).strip() for value in (raw_ids if isinstance(raw_ids, list) else [])]
    ids = [value for value in ids if value][:200]

    db = SessionLocal()
    try:
        tenant_id = _normalize_tenant_id(get_current_tenant(request))
        user_key = _notification_user_key(request, db)
        if not user_key:
            return JSONResponse({"success": False, "error": "Usuario no autenticado"}, status_code=401)
        if not ids:
            return JSONResponse({"success": True, "updated": 0})

        existing = (
            db.query(UserNotificationRead)
            .filter(
                UserNotificationRead.tenant_id == tenant_id,
                UserNotificationRead.user_key == user_key,
                UserNotificationRead.notification_id.in_(ids),
            )
            .all()
        )
        existing_by_id = {row.notification_id: row for row in existing}
        now = datetime.utcnow()
        updates = 0
        for notif_id in ids:
            row = existing_by_id.get(notif_id)
            if row:
                row.read_at = now
                db.add(row)
            else:
                db.add(
                    UserNotificationRead(
                        tenant_id=tenant_id,
                        user_key=user_key,
                        notification_id=notif_id,
                        read_at=now,
                    )
                )
            updates += 1
        db.commit()
        return JSONResponse({"success": True, "updated": updates})
    finally:
        db.close()


@router.post("/api/poa/activities")
def create_poa_activity(request: Request, data: dict = Body(...)):
    _bind_core_symbols()
    objective_id = int(data.get("objective_id") or 0)
    nombre = (data.get("nombre") or "").strip()
    responsable = (data.get("responsable") or "").strip()
    entregable = (data.get("entregable") or "").strip()
    if not objective_id or not nombre or not responsable or not entregable:
        return JSONResponse(
            {"success": False, "error": "Objetivo, nombre, responsable y entregable son obligatorios"},
            status_code=400,
        )
    start_date, start_error = _parse_date_field(data.get("fecha_inicial"), "Fecha inicial", required=True)
    if start_error:
        return JSONResponse({"success": False, "error": start_error}, status_code=400)
    end_date, end_error = _parse_date_field(data.get("fecha_final"), "Fecha final", required=True)
    if end_error:
        return JSONResponse({"success": False, "error": end_error}, status_code=400)
    range_error = _validate_date_range(start_date, end_date, "Actividad")
    if range_error:
        return JSONResponse({"success": False, "error": range_error}, status_code=400)
    recurrente = bool(data.get("recurrente"))
    periodicidad = (data.get("periodicidad") or "").strip().lower()
    try:
        cada_xx_dias = int(data.get("cada_xx_dias") or 0)
    except (TypeError, ValueError):
        return JSONResponse({"success": False, "error": "Cada xx días debe ser un número válido"}, status_code=400)
    if recurrente:
        if periodicidad not in VALID_ACTIVITY_PERIODICITIES:
            return JSONResponse({"success": False, "error": "Selecciona una periodicidad válida"}, status_code=400)
        if periodicidad == "cada_xx_dias":
            if cada_xx_dias <= 0:
                return JSONResponse({"success": False, "error": "Cada xx días debe ser mayor a 0"}, status_code=400)
    else:
        periodicidad = ""
        cada_xx_dias = 0

    db = SessionLocal()
    try:
        allowed_ids = {obj.id for obj in _allowed_objectives_for_user(request, db)}
        if objective_id not in allowed_ids and not is_admin_or_superadmin(request):
            return JSONResponse({"success": False, "error": "No autorizado para este objetivo"}, status_code=403)
        objective = db.query(StrategicObjectiveConfig).filter(StrategicObjectiveConfig.id == objective_id).first()
        if not objective:
            return JSONResponse({"success": False, "error": "Objetivo no encontrado"}, status_code=404)
        parent_error = _validate_child_date_range(
            start_date,
            end_date,
            objective.fecha_inicial,
            objective.fecha_final,
            "Actividad",
            "Objetivo",
        )
        if parent_error:
            return JSONResponse({"success": False, "error": parent_error}, status_code=400)
        created_by = (getattr(request.state, "user_name", None) or request.cookies.get("user_name") or "").strip()
        activity = POAActivity(
            objective_id=objective_id,
            nombre=nombre,
            codigo=(data.get("codigo") or "").strip(),
            responsable=responsable,
            entregable=entregable,
            fecha_inicial=start_date,
            fecha_final=end_date,
            inicio_forzado=bool(data.get("inicio_forzado")),
            descripcion=(data.get("descripcion") or "").strip(),
            recurrente=recurrente,
            periodicidad=periodicidad,
            cada_xx_dias=(cada_xx_dias if periodicidad == "cada_xx_dias" else None),
            created_by=created_by,
        )
        db.add(activity)
        db.commit()
        db.refresh(activity)
        return JSONResponse({"success": True, "data": _serialize_poa_activity(activity, [])})
    finally:
        db.close()


@router.put("/api/poa/activities/{activity_id}")
def update_poa_activity(request: Request, activity_id: int, data: dict = Body(...)):
    _bind_core_symbols()
    db = SessionLocal()
    try:
        activity = db.query(POAActivity).filter(POAActivity.id == activity_id).first()
        if not activity:
            return JSONResponse({"success": False, "error": "Actividad no encontrada"}, status_code=404)
        allowed_ids = {obj.id for obj in _allowed_objectives_for_user(request, db)}
        if activity.objective_id not in allowed_ids and not is_admin_or_superadmin(request):
            return JSONResponse({"success": False, "error": "No autorizado para editar esta actividad"}, status_code=403)
        nombre = (data.get("nombre") or "").strip()
        responsable = (data.get("responsable") or "").strip()
        entregable = (data.get("entregable") or "").strip()
        if not nombre or not responsable or not entregable:
            return JSONResponse(
                {"success": False, "error": "Nombre, responsable y entregable son obligatorios"},
                status_code=400,
            )
        start_date, start_error = _parse_date_field(data.get("fecha_inicial"), "Fecha inicial", required=True)
        if start_error:
            return JSONResponse({"success": False, "error": start_error}, status_code=400)
        end_date, end_error = _parse_date_field(data.get("fecha_final"), "Fecha final", required=True)
        if end_error:
            return JSONResponse({"success": False, "error": end_error}, status_code=400)
        range_error = _validate_date_range(start_date, end_date, "Actividad")
        if range_error:
            return JSONResponse({"success": False, "error": range_error}, status_code=400)
        recurrente = bool(data.get("recurrente"))
        periodicidad = (data.get("periodicidad") or "").strip().lower()
        try:
            cada_xx_dias = int(data.get("cada_xx_dias") or 0)
        except (TypeError, ValueError):
            return JSONResponse({"success": False, "error": "Cada xx días debe ser un número válido"}, status_code=400)
        if recurrente:
            if periodicidad not in VALID_ACTIVITY_PERIODICITIES:
                return JSONResponse({"success": False, "error": "Selecciona una periodicidad válida"}, status_code=400)
            if periodicidad == "cada_xx_dias":
                if cada_xx_dias <= 0:
                    return JSONResponse({"success": False, "error": "Cada xx días debe ser mayor a 0"}, status_code=400)
        else:
            periodicidad = ""
            cada_xx_dias = 0
        objective = db.query(StrategicObjectiveConfig).filter(StrategicObjectiveConfig.id == activity.objective_id).first()
        if not objective:
            return JSONResponse({"success": False, "error": "Objetivo no encontrado"}, status_code=404)
        parent_error = _validate_child_date_range(
            start_date,
            end_date,
            objective.fecha_inicial,
            objective.fecha_final,
            "Actividad",
            "Objetivo",
        )
        if parent_error:
            return JSONResponse({"success": False, "error": parent_error}, status_code=400)
        activity.nombre = nombre
        activity.codigo = (data.get("codigo") or "").strip()
        activity.responsable = responsable
        activity.entregable = entregable
        activity.fecha_inicial = start_date
        activity.fecha_final = end_date
        activity.inicio_forzado = bool(data.get("inicio_forzado")) if "inicio_forzado" in data else bool(activity.inicio_forzado)
        activity.descripcion = (data.get("descripcion") or "").strip()
        activity.recurrente = recurrente
        activity.periodicidad = periodicidad
        activity.cada_xx_dias = cada_xx_dias if periodicidad == "cada_xx_dias" else None
        db.add(activity)
        db.commit()
        db.refresh(activity)
        subs = db.query(POASubactivity).filter(POASubactivity.activity_id == activity.id).all()
        return JSONResponse({"success": True, "data": _serialize_poa_activity(activity, subs)})
    finally:
        db.close()


@router.delete("/api/poa/activities/{activity_id}")
def delete_poa_activity(request: Request, activity_id: int):
    _bind_core_symbols()
    db = SessionLocal()
    try:
        activity = db.query(POAActivity).filter(POAActivity.id == activity_id).first()
        if not activity:
            return JSONResponse({"success": False, "error": "Actividad no encontrada"}, status_code=404)
        allowed_ids = {obj.id for obj in _allowed_objectives_for_user(request, db)}
        if activity.objective_id not in allowed_ids and not is_admin_or_superadmin(request):
            return JSONResponse({"success": False, "error": "No autorizado para eliminar esta actividad"}, status_code=403)
        db.query(POASubactivity).filter(POASubactivity.activity_id == activity.id).delete()
        db.delete(activity)
        db.commit()
        return JSONResponse({"success": True})
    finally:
        db.close()


@router.post("/api/poa/activities/{activity_id}/mark-in-progress")
def mark_poa_activity_in_progress(request: Request, activity_id: int):
    _bind_core_symbols()
    db = SessionLocal()
    try:
        activity = db.query(POAActivity).filter(POAActivity.id == activity_id).first()
        if not activity:
            return JSONResponse({"success": False, "error": "Actividad no encontrada"}, status_code=404)
        allowed_ids = {obj.id for obj in _allowed_objectives_for_user(request, db)}
        if activity.objective_id not in allowed_ids and not is_admin_or_superadmin(request):
            return JSONResponse({"success": False, "error": "No autorizado para esta actividad"}, status_code=403)
        session_username = (getattr(request.state, "user_name", None) or request.cookies.get("user_name") or "").strip()
        user = _current_user_record(request, db)
        aliases = _user_aliases(user, session_username)
        is_activity_owner = (activity.responsable or "").strip().lower() in aliases
        if not (is_activity_owner or is_admin_or_superadmin(request)):
            return JSONResponse({"success": False, "error": "Solo el responsable puede habilitar en proceso"}, status_code=403)
        if (activity.entrega_estado or "").strip().lower() == "aprobada":
            return JSONResponse({"success": False, "error": "La actividad ya está aprobada y terminada"}, status_code=409)
        activity.inicio_forzado = True
        if (activity.entrega_estado or "").strip().lower() == "rechazada":
            activity.entrega_estado = "ninguna"
        db.add(activity)
        db.commit()
        db.refresh(activity)
        subs = db.query(POASubactivity).filter(POASubactivity.activity_id == activity.id).all()
        return JSONResponse({"success": True, "data": _serialize_poa_activity(activity, subs)})
    finally:
        db.close()


@router.post("/api/poa/activities/{activity_id}/mark-finished")
def mark_poa_activity_finished(request: Request, activity_id: int, data: dict = Body(default={})):
    _bind_core_symbols()
    send_review = bool(data.get("enviar_revision"))
    db = SessionLocal()
    try:
        activity = db.query(POAActivity).filter(POAActivity.id == activity_id).first()
        if not activity:
            return JSONResponse({"success": False, "error": "Actividad no encontrada"}, status_code=404)
        allowed_ids = {obj.id for obj in _allowed_objectives_for_user(request, db)}
        if activity.objective_id not in allowed_ids and not is_admin_or_superadmin(request):
            return JSONResponse({"success": False, "error": "No autorizado para esta actividad"}, status_code=403)
        session_username = (getattr(request.state, "user_name", None) or request.cookies.get("user_name") or "").strip()
        user = _current_user_record(request, db)
        aliases = _user_aliases(user, session_username)
        is_activity_owner = (activity.responsable or "").strip().lower() in aliases
        if not (is_activity_owner or is_admin_or_superadmin(request)):
            return JSONResponse({"success": False, "error": "Solo el responsable puede declarar terminado"}, status_code=403)
        current_status = _activity_status(activity)
        if current_status == "No iniciada":
            return JSONResponse(
                {"success": False, "error": "La actividad no ha iniciado; habilítala en proceso o espera la fecha inicial"},
                status_code=409,
            )
        if (activity.entrega_estado or "").strip().lower() == "aprobada":
            return JSONResponse({"success": False, "error": "La actividad ya fue aprobada y terminada"}, status_code=409)

        if send_review:
            pending = (
                db.query(POADeliverableApproval)
                .filter(
                    POADeliverableApproval.activity_id == activity.id,
                    POADeliverableApproval.status == "pendiente",
                )
                .first()
            )
            if pending:
                return JSONResponse(
                    {"success": False, "error": "Ya existe una aprobación pendiente para esta actividad"},
                    status_code=409,
                )

            objective = db.query(StrategicObjectiveConfig).filter(StrategicObjectiveConfig.id == activity.objective_id).first()
            if not objective:
                return JSONResponse({"success": False, "error": "Objetivo no encontrado"}, status_code=404)
            axis = db.query(StrategicAxisConfig).filter(StrategicAxisConfig.id == objective.eje_id).first()
            process_owner = (activity.created_by or "").strip() or _resolve_process_owner_for_objective(objective, axis)
            if not process_owner:
                return JSONResponse(
                    {"success": False, "error": "No se pudo identificar el validador del entregable"},
                    status_code=400,
                )
            approval = POADeliverableApproval(
                activity_id=activity.id,
                objective_id=objective.id,
                process_owner=process_owner,
                requester=session_username or (activity.responsable or ""),
                status="pendiente",
            )
            activity.entrega_estado = "pendiente"
            activity.entrega_solicitada_por = session_username or (activity.responsable or "")
            activity.entrega_solicitada_at = datetime.utcnow()
            activity.entrega_aprobada_por = ""
            activity.entrega_aprobada_at = None
            db.add(approval)
            db.add(activity)
            db.commit()
            db.refresh(activity)
            subs = db.query(POASubactivity).filter(POASubactivity.activity_id == activity.id).all()
            return JSONResponse(
                {
                    "success": True,
                    "message": "Entregable enviado a revisión",
                    "data": _serialize_poa_activity(activity, subs),
                }
            )

        activity.entrega_estado = "declarada"
        activity.entrega_solicitada_por = ""
        activity.entrega_solicitada_at = None
        activity.entrega_aprobada_por = ""
        activity.entrega_aprobada_at = None
        db.add(activity)
        db.commit()
        db.refresh(activity)
        subs = db.query(POASubactivity).filter(POASubactivity.activity_id == activity.id).all()
        return JSONResponse(
            {
                "success": True,
                "message": "Actividad declarada terminada",
                "data": _serialize_poa_activity(activity, subs),
            }
        )
    finally:
        db.close()


@router.post("/api/poa/activities/{activity_id}/request-completion")
def request_poa_activity_completion(request: Request, activity_id: int):
    _bind_core_symbols()
    db = SessionLocal()
    try:
        activity = db.query(POAActivity).filter(POAActivity.id == activity_id).first()
        if not activity:
            return JSONResponse({"success": False, "error": "Actividad no encontrada"}, status_code=404)
        allowed_ids = {obj.id for obj in _allowed_objectives_for_user(request, db)}
        if activity.objective_id not in allowed_ids and not is_admin_or_superadmin(request):
            return JSONResponse({"success": False, "error": "No autorizado para esta actividad"}, status_code=403)
        session_username = (getattr(request.state, "user_name", None) or request.cookies.get("user_name") or "").strip()
        user = _current_user_record(request, db)
        aliases = _user_aliases(user, session_username)
        is_activity_owner = (activity.responsable or "").strip().lower() in aliases
        if not (is_activity_owner or is_admin_or_superadmin(request)):
            return JSONResponse({"success": False, "error": "Solo el responsable puede solicitar terminación"}, status_code=403)
        if _activity_status(activity) == "No iniciada":
            return JSONResponse(
                {"success": False, "error": "La actividad no ha iniciado; no se puede solicitar terminación"},
                status_code=409,
            )
        if (activity.entrega_estado or "").strip().lower() == "aprobada":
            return JSONResponse({"success": False, "error": "La actividad ya fue aprobada y terminada"}, status_code=409)

        pending = (
            db.query(POADeliverableApproval)
            .filter(
                POADeliverableApproval.activity_id == activity.id,
                POADeliverableApproval.status == "pendiente",
            )
            .first()
        )
        if pending:
            return JSONResponse({"success": False, "error": "Ya existe una aprobación pendiente para esta actividad"}, status_code=409)

        objective = db.query(StrategicObjectiveConfig).filter(StrategicObjectiveConfig.id == activity.objective_id).first()
        if not objective:
            return JSONResponse({"success": False, "error": "Objetivo no encontrado"}, status_code=404)
        axis = db.query(StrategicAxisConfig).filter(StrategicAxisConfig.id == objective.eje_id).first()
        process_owner = (activity.created_by or "").strip() or _resolve_process_owner_for_objective(objective, axis)
        if not process_owner:
            return JSONResponse(
                {"success": False, "error": "No se pudo identificar dueño del proceso (líder objetivo/departamento eje)"},
                status_code=400,
            )

        approval = POADeliverableApproval(
            activity_id=activity.id,
            objective_id=objective.id,
            process_owner=process_owner,
            requester=session_username or (activity.responsable or ""),
            status="pendiente",
        )
        activity.entrega_estado = "pendiente"
        activity.entrega_solicitada_por = session_username or (activity.responsable or "")
        activity.entrega_solicitada_at = datetime.utcnow()
        activity.entrega_aprobada_por = ""
        activity.entrega_aprobada_at = None
        db.add(approval)
        db.add(activity)
        db.commit()
        return JSONResponse({"success": True, "message": "Solicitud de aprobación enviada al dueño del proceso"})
    finally:
        db.close()


@router.post("/api/poa/approvals/{approval_id}/decision")
def decide_poa_deliverable_approval(request: Request, approval_id: int, data: dict = Body(default={})):
    _bind_core_symbols()
    action = (data.get("accion") or "").strip().lower()
    if action not in {"autorizar", "rechazar"}:
        return JSONResponse({"success": False, "error": "Acción inválida. Usa autorizar o rechazar"}, status_code=400)
    comment = (data.get("comentario") or "").strip()

    db = SessionLocal()
    try:
        approval = db.query(POADeliverableApproval).filter(POADeliverableApproval.id == approval_id).first()
        if not approval:
            return JSONResponse({"success": False, "error": "Solicitud de aprobación no encontrada"}, status_code=404)
        if approval.status != "pendiente":
            return JSONResponse({"success": False, "error": "Esta solicitud ya fue resuelta"}, status_code=409)
        if not _is_user_process_owner(request, db, approval.process_owner):
            return JSONResponse({"success": False, "error": "No autorizado para resolver esta aprobación"}, status_code=403)

        activity = db.query(POAActivity).filter(POAActivity.id == approval.activity_id).first()
        if not activity:
            return JSONResponse({"success": False, "error": "Actividad no encontrada"}, status_code=404)
        resolver_user = (getattr(request.state, "user_name", None) or request.cookies.get("user_name") or "").strip()

        approval.status = "autorizada" if action == "autorizar" else "rechazada"
        approval.comment = comment
        approval.resolved_by = resolver_user
        approval.resolved_at = datetime.utcnow()
        db.add(approval)

        if action == "autorizar":
            activity.entrega_estado = "aprobada"
            activity.entrega_aprobada_por = resolver_user
            activity.entrega_aprobada_at = datetime.utcnow()
        else:
            activity.entrega_estado = "rechazada"
            activity.entrega_aprobada_por = ""
            activity.entrega_aprobada_at = None
        db.add(activity)
        db.commit()
        return JSONResponse({"success": True, "message": "Aprobación procesada correctamente"})
    finally:
        db.close()


@router.post("/api/poa/activities/{activity_id}/subactivities")
def create_poa_subactivity(request: Request, activity_id: int, data: dict = Body(...)):
    _bind_core_symbols()
    nombre = (data.get("nombre") or "").strip()
    responsable = (data.get("responsable") or "").strip()
    if not nombre or not responsable:
        return JSONResponse({"success": False, "error": "Nombre y responsable son obligatorios"}, status_code=400)
    start_date, start_error = _parse_date_field(data.get("fecha_inicial"), "Fecha inicial", required=True)
    if start_error:
        return JSONResponse({"success": False, "error": start_error}, status_code=400)
    end_date, end_error = _parse_date_field(data.get("fecha_final"), "Fecha final", required=True)
    if end_error:
        return JSONResponse({"success": False, "error": end_error}, status_code=400)
    range_error = _validate_date_range(start_date, end_date, "Subactividad")
    if range_error:
        return JSONResponse({"success": False, "error": range_error}, status_code=400)

    db = SessionLocal()
    try:
        activity = db.query(POAActivity).filter(POAActivity.id == activity_id).first()
        if not activity:
            return JSONResponse({"success": False, "error": "Actividad no encontrada"}, status_code=404)
        session_username = (getattr(request.state, "user_name", None) or request.cookies.get("user_name") or "").strip()
        user = _current_user_record(request, db)
        aliases = _user_aliases(user, session_username)
        is_activity_owner = (activity.responsable or "").strip().lower() in aliases
        if not (is_activity_owner or is_admin_or_superadmin(request)):
            return JSONResponse(
                {"success": False, "error": "Solo el responsable de la actividad puede asignar subactividades"},
                status_code=403,
            )
        parent_error = _validate_child_date_range(
            start_date,
            end_date,
            activity.fecha_inicial,
            activity.fecha_final,
            "Subactividad",
            "Actividad",
        )
        if parent_error:
            return JSONResponse({"success": False, "error": parent_error}, status_code=400)
        parent_sub_id = int(data.get("parent_subactivity_id") or 0)
        parent_sub = None
        sub_level = 1
        if parent_sub_id:
            parent_sub = (
                db.query(POASubactivity)
                .filter(POASubactivity.id == parent_sub_id, POASubactivity.activity_id == activity.id)
                .first()
            )
            if not parent_sub:
                return JSONResponse({"success": False, "error": "Subactividad padre no encontrada"}, status_code=404)
            sub_level = int(parent_sub.nivel or 1) + 1
            if sub_level > MAX_SUBTASK_DEPTH:
                return JSONResponse(
                    {"success": False, "error": f"Profundidad máxima permitida: {MAX_SUBTASK_DEPTH} niveles"},
                    status_code=400,
                )
            child_error = _validate_child_date_range(
                start_date,
                end_date,
                parent_sub.fecha_inicial,
                parent_sub.fecha_final,
                "Subactividad",
                "Subactividad padre",
            )
            if child_error:
                return JSONResponse({"success": False, "error": child_error}, status_code=400)
        assigned_by = session_username
        sub = POASubactivity(
            activity_id=activity.id,
            parent_subactivity_id=parent_sub.id if parent_sub else None,
            nivel=sub_level,
            nombre=nombre,
            codigo=(data.get("codigo") or "").strip(),
            responsable=responsable,
            entregable=(data.get("entregable") or "").strip(),
            fecha_inicial=start_date,
            fecha_final=end_date,
            descripcion=(data.get("descripcion") or "").strip(),
            assigned_by=assigned_by,
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return JSONResponse({"success": True, "data": _serialize_poa_subactivity(sub)})
    finally:
        db.close()


@router.put("/api/poa/subactivities/{subactivity_id}")
def update_poa_subactivity(request: Request, subactivity_id: int, data: dict = Body(...)):
    _bind_core_symbols()
    db = SessionLocal()
    try:
        sub = db.query(POASubactivity).filter(POASubactivity.id == subactivity_id).first()
        if not sub:
            return JSONResponse({"success": False, "error": "Subactividad no encontrada"}, status_code=404)
        activity = db.query(POAActivity).filter(POAActivity.id == sub.activity_id).first()
        if not activity:
            return JSONResponse({"success": False, "error": "Actividad no encontrada"}, status_code=404)
        session_username = (getattr(request.state, "user_name", None) or request.cookies.get("user_name") or "").strip()
        user = _current_user_record(request, db)
        aliases = _user_aliases(user, session_username)
        is_activity_owner = (activity.responsable or "").strip().lower() in aliases
        if not (is_activity_owner or is_admin_or_superadmin(request)):
            return JSONResponse({"success": False, "error": "No autorizado para editar subactividad"}, status_code=403)
        nombre = (data.get("nombre") or "").strip()
        responsable = (data.get("responsable") or "").strip()
        if not nombre or not responsable:
            return JSONResponse({"success": False, "error": "Nombre y responsable son obligatorios"}, status_code=400)
        start_date, start_error = _parse_date_field(data.get("fecha_inicial"), "Fecha inicial", required=True)
        if start_error:
            return JSONResponse({"success": False, "error": start_error}, status_code=400)
        end_date, end_error = _parse_date_field(data.get("fecha_final"), "Fecha final", required=True)
        if end_error:
            return JSONResponse({"success": False, "error": end_error}, status_code=400)
        range_error = _validate_date_range(start_date, end_date, "Subactividad")
        if range_error:
            return JSONResponse({"success": False, "error": range_error}, status_code=400)
        parent_error = _validate_child_date_range(
            start_date,
            end_date,
            activity.fecha_inicial,
            activity.fecha_final,
            "Subactividad",
            "Actividad",
        )
        if parent_error:
            return JSONResponse({"success": False, "error": parent_error}, status_code=400)
        parent_sub = None
        if sub.parent_subactivity_id:
            parent_sub = (
                db.query(POASubactivity)
                .filter(POASubactivity.id == sub.parent_subactivity_id, POASubactivity.activity_id == activity.id)
                .first()
            )
        if parent_sub:
            child_error = _validate_child_date_range(
                start_date,
                end_date,
                parent_sub.fecha_inicial,
                parent_sub.fecha_final,
                "Subactividad",
                "Subactividad padre",
            )
            if child_error:
                return JSONResponse({"success": False, "error": child_error}, status_code=400)
        sub.nombre = nombre
        sub.codigo = (data.get("codigo") or "").strip()
        sub.responsable = responsable
        sub.entregable = (data.get("entregable") or "").strip()
        sub.fecha_inicial = start_date
        sub.fecha_final = end_date
        sub.descripcion = (data.get("descripcion") or "").strip()
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return JSONResponse({"success": True, "data": _serialize_poa_subactivity(sub)})
    finally:
        db.close()


@router.delete("/api/poa/subactivities/{subactivity_id}")
def delete_poa_subactivity(request: Request, subactivity_id: int):
    _bind_core_symbols()
    db = SessionLocal()
    try:
        sub = db.query(POASubactivity).filter(POASubactivity.id == subactivity_id).first()
        if not sub:
            return JSONResponse({"success": False, "error": "Subactividad no encontrada"}, status_code=404)
        activity = db.query(POAActivity).filter(POAActivity.id == sub.activity_id).first()
        if not activity:
            return JSONResponse({"success": False, "error": "Actividad no encontrada"}, status_code=404)
        session_username = (getattr(request.state, "user_name", None) or request.cookies.get("user_name") or "").strip()
        user = _current_user_record(request, db)
        aliases = _user_aliases(user, session_username)
        is_activity_owner = (activity.responsable or "").strip().lower() in aliases
        if not (is_activity_owner or is_admin_or_superadmin(request)):
            return JSONResponse({"success": False, "error": "No autorizado para eliminar subactividad"}, status_code=403)
        descendants = _descendant_subactivity_ids(db, activity.id, sub.id)
        if descendants:
            db.query(POASubactivity).filter(POASubactivity.id.in_(descendants)).delete(synchronize_session=False)
        db.delete(sub)
        db.commit()
        return JSONResponse({"success": True})
    finally:
        db.close()
