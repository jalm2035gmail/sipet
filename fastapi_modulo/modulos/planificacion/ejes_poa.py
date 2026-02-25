from __future__ import annotations

from datetime import datetime, timedelta
from textwrap import dedent
from typing import Any, Dict, List, Set

from fastapi import APIRouter, Body, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import func

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
        '_allowed_objectives_for_user',
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
        '_get_document_tenant',
        '_can_authorize_documents',
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
        "descripcion": axis.descripcion or "",
        "orden": axis.orden or 0,
        "objetivos_count": len(objetivos),
        "objetivos": [_serialize_strategic_objective(obj) for obj in objetivos],
    }


def _serialize_poa_subactivity(item: POASubactivity) -> Dict[str, Any]:
    _bind_core_symbols()
    return {
        "id": item.id,
        "activity_id": item.activity_id,
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
        "status": _activity_status(item),
        "entrega_estado": item.entrega_estado or "ninguna",
        "entrega_solicitada_por": item.entrega_solicitada_por or "",
        "entrega_solicitada_at": item.entrega_solicitada_at.isoformat() if item.entrega_solicitada_at else "",
        "entrega_aprobada_por": item.entrega_aprobada_por or "",
        "entrega_aprobada_at": item.entrega_aprobada_at.isoformat() if item.entrega_aprobada_at else "",
        "descripcion": item.descripcion or "",
        "subactivities": [_serialize_poa_subactivity(sub) for sub in subactivities],
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
        .axm-grid{
          display:grid;
          grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
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
        .axm-input, .axm-textarea{
          width:100%;
          border:1px solid rgba(148,163,184,.42);
          border-radius: 12px;
          padding: 10px 12px;
          font-size: 14px;
          background: #fff;
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
          grid-template-columns: minmax(280px, 0.95fr) minmax(460px, 1.35fr);
          gap: 14px;
          align-items: start;
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
        @media (max-width: 1200px){
          .axm-obj-layout{ grid-template-columns: 1fr; }
          .axm-obj-form .axm-row{ grid-template-columns: 1fr; }
        }
        @media (max-width: 980px){
          .axm-grid{ grid-template-columns: 1fr; }
          .axm-list{ max-height: 36vh; }
          .axm-row{ grid-template-columns: 1fr; }
          .axm-obj-layout{ grid-template-columns: 1fr; }
          .axm-obj-grid{ grid-template-columns: 1fr; }
        }
      </style>

      <div class="axm-grid">
        <aside class="axm-card">
          <h2 class="axm-title">Ejes estratégicos</h2>
          <p class="axm-sub">Selecciona un eje para editarlo o crea uno nuevo.</p>
          <div class="axm-actions">
            <button class="axm-btn primary" id="axm-add-axis" type="button">Agregar eje</button>
          </div>
          <div class="axm-list" id="axm-axis-list"></div>
        </aside>

        <section class="axm-card">
          <h2 class="axm-title">Gestión de ejes y objetivos</h2>
          <p class="axm-sub">Edita, guarda o elimina ejes estratégicos y sus objetivos.</p>
          <div class="axm-row">
            <div class="axm-field">
              <label for="axm-axis-name">Nombre del eje</label>
              <input id="axm-axis-name" class="axm-input" type="text" placeholder="Ej. Gobernanza y cumplimiento">
            </div>
            <div class="axm-field">
              <label for="axm-axis-code">Código</label>
              <input id="axm-axis-code" class="axm-input" type="text" placeholder="Ej. AX-01">
            </div>
          </div>
          <div class="axm-field">
            <label for="axm-axis-leader">Líder del eje estratégico</label>
            <select id="axm-axis-leader" class="axm-input">
              <option value="">Selecciona departamento</option>
            </select>
          </div>
          <div class="axm-field">
            <label for="axm-axis-desc">Descripción</label>
            <textarea id="axm-axis-desc" class="axm-textarea" placeholder="Describe el propósito del eje"></textarea>
          </div>
          <div class="axm-actions">
            <button class="axm-btn primary" id="axm-save-axis" type="button">Guardar eje</button>
            <button class="axm-btn warn" id="axm-delete-axis" type="button">Eliminar eje</button>
          </div>

          <hr style="border:0;border-top:1px solid rgba(148,163,184,.28);margin:14px 0;">

          <h3 style="margin:0;font-size:16px;">Objetivos del eje</h3>
          <div class="axm-obj-layout">
            <div>
              <div class="axm-actions" style="margin-top:0;">
                <button class="axm-btn primary" id="axm-add-obj" type="button">Agregar objetivo</button>
              </div>
              <div class="axm-obj-list" id="axm-obj-list"></div>
            </div>
            <div class="axm-obj-form">
              <div class="axm-field" style="margin-top:0;">
                <label for="axm-obj-name">Nombre</label>
                <input id="axm-obj-name" class="axm-input" type="text" placeholder="Nombre del objetivo">
              </div>
              <div class="axm-field">
                <label for="axm-obj-code">Código</label>
                <input id="axm-obj-code" class="axm-input" type="text" placeholder="Ej. OE-13">
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
            </div>
          </div>
          <div class="axm-msg" id="axm-msg" aria-live="polite"></div>
        </section>
      </div>

      <script>
        (() => {
          const axisListEl = document.getElementById("axm-axis-list");
          const objListEl = document.getElementById("axm-obj-list");
          const axisNameEl = document.getElementById("axm-axis-name");
          const axisCodeEl = document.getElementById("axm-axis-code");
          const axisLeaderEl = document.getElementById("axm-axis-leader");
          const axisDescEl = document.getElementById("axm-axis-desc");
          const objNameEl = document.getElementById("axm-obj-name");
          const objCodeEl = document.getElementById("axm-obj-code");
          const objLeaderEl = document.getElementById("axm-obj-leader");
          const objStartEl = document.getElementById("axm-obj-start");
          const objEndEl = document.getElementById("axm-obj-end");
          const objDescEl = document.getElementById("axm-obj-desc");
          const msgEl = document.getElementById("axm-msg");
          const addAxisBtn = document.getElementById("axm-add-axis");
          const saveAxisBtn = document.getElementById("axm-save-axis");
          const deleteAxisBtn = document.getElementById("axm-delete-axis");
          const addObjBtn = document.getElementById("axm-add-obj");
          const saveObjBtn = document.getElementById("axm-save-obj");
          const deleteObjBtn = document.getElementById("axm-delete-obj");

          let axes = [];
          let departments = [];
          let collaborators = [];
          let selectedAxisId = null;
          let selectedObjectiveId = null;

          const showMsg = (text, isError = false) => {
            if (!msgEl) return;
            msgEl.style.color = isError ? "#b91c1c" : "#0f3d2e";
            msgEl.textContent = text || "";
          };

          const requestJson = async (url, options = {}) => {
            const response = await fetch(url, {
              headers: { "Content-Type": "application/json" },
              credentials: "same-origin",
              ...options,
            });
            const payload = await response.json().catch(() => ({}));
            if (!response.ok || payload.success === false) {
              throw new Error(payload.error || "No se pudo completar la operación.");
            }
            return payload;
          };

          const selectedAxis = () => axes.find((axis) => axis.id === selectedAxisId) || null;
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

          const renderAxisList = () => {
            if (!axisListEl) return;
            axisListEl.innerHTML = axes.map((axis) => `
              <button class="axm-axis-btn ${axis.id === selectedAxisId ? "active" : ""}" type="button" data-axis-id="${axis.id}">
                <span>
                  <strong>${axis.nombre}</strong>
                  <div class="axm-axis-meta">${axis.codigo || "Sin código"} • ${axis.lider_departamento || "Sin líder"}</div>
                </span>
                <span class="axm-count">${axis.objetivos_count || 0}</span>
              </button>
            `).join("");
            axisListEl.querySelectorAll("[data-axis-id]").forEach((button) => {
              button.addEventListener("click", async () => {
                selectedAxisId = Number(button.getAttribute("data-axis-id"));
                selectedObjectiveId = null;
                await loadCollaborators();
                renderAll();
              });
            });
          };

          const renderAxisEditor = () => {
            const axis = selectedAxis();
            if (!axis) {
              axisNameEl.value = "";
              axisCodeEl.value = "";
              renderDepartmentOptions("");
              axisDescEl.value = "";
              return;
            }
            axisNameEl.value = axis.nombre || "";
            axisCodeEl.value = axis.codigo || "";
            renderDepartmentOptions(axis.lider_departamento || "");
            axisDescEl.value = axis.descripcion || "";
          };

          const renderObjectives = () => {
            const axis = selectedAxis();
            if (!axis || !objListEl) {
              if (objListEl) objListEl.innerHTML = "";
              selectedObjectiveId = null;
              if (objNameEl) objNameEl.value = "";
              if (objCodeEl) objCodeEl.value = "";
              if (objDescEl) objDescEl.value = "";
              if (objStartEl) objStartEl.value = "";
              if (objEndEl) objEndEl.value = "";
              renderCollaboratorOptions("");
              return;
            }
            if (!selectedObjectiveId || !(axis.objetivos || []).some((obj) => obj.id === selectedObjectiveId)) {
              selectedObjectiveId = (axis.objetivos || [])[0]?.id || null;
            }
            objListEl.innerHTML = (axis.objetivos || []).map((obj) => `
              <button class="axm-obj-btn ${obj.id === selectedObjectiveId ? "active" : ""}" type="button" data-obj-id="${obj.id}">
                <strong>${obj.codigo || "OBJ"} - ${obj.nombre || "Sin nombre"}</strong>
              </button>
            `).join("");

            objListEl.querySelectorAll("[data-obj-id]").forEach((button) => {
              button.addEventListener("click", () => {
                selectedObjectiveId = Number(button.getAttribute("data-obj-id"));
                renderAll();
              });
            });

            const objective = selectedObjective();
            if (!objective) return;
            if (objNameEl) objNameEl.value = objective.nombre || "";
            if (objCodeEl) objCodeEl.value = objective.codigo || "";
            if (objDescEl) objDescEl.value = objective.descripcion || "";
            if (objStartEl) objStartEl.value = objective.fecha_inicial || "";
            if (objEndEl) objEndEl.value = objective.fecha_final || "";
            renderCollaboratorOptions(objective.lider || "");
          };

          const renderAll = () => {
            renderAxisList();
            renderAxisEditor();
            renderObjectives();
          };

          const loadAxes = async () => {
            const payload = await requestJson("/api/strategic-axes");
            axes = Array.isArray(payload.data) ? payload.data : [];
            if (!selectedAxisId || !axes.some((axis) => axis.id === selectedAxisId)) {
              selectedAxisId = axes.length ? axes[0].id : null;
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
              renderCollaboratorOptions("");
              return;
            }
            const payload = await requestJson(`/api/strategic-axes/${axis.id}/collaborators`);
            collaborators = Array.isArray(payload.data) ? payload.data : [];
            renderCollaboratorOptions(selectedObjective()?.lider || "");
          };

          addAxisBtn && addAxisBtn.addEventListener("click", async () => {
            try {
              const payload = await requestJson("/api/strategic-axes", {
                method: "POST",
                body: JSON.stringify({
                  nombre: "Nuevo eje estratégico",
                  codigo: "",
                  lider_departamento: "",
                  descripcion: "",
                  orden: axes.length + 1,
                }),
              });
              selectedAxisId = payload.data?.id || null;
              await loadAxes();
              await loadCollaborators();
              showMsg("Eje agregado.");
            } catch (err) {
              showMsg(err.message || "No se pudo crear el eje.", true);
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
              codigo: axisCodeEl.value.trim(),
              lider_departamento: axisLeaderEl && axisLeaderEl.value ? axisLeaderEl.value.trim() : "",
              descripcion: axisDescEl.value.trim(),
              orden: Number(axis.orden || 1),
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
            const body = {
              codigo: "",
              nombre: "Nuevo objetivo",
              lider: "",
              descripcion: "",
            };
            try {
              const payload = await requestJson(`/api/strategic-axes/${axis.id}/objectives`, { method: "POST", body: JSON.stringify(body) });
              await loadAxes();
              selectedObjectiveId = payload.data?.id || selectedObjectiveId;
              renderAll();
              showMsg("Objetivo agregado.");
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

          Promise.all([loadDepartments(), loadAxes()]).then(loadCollaborators).catch((err) => {
            showMsg(err.message || "No se pudieron cargar los ejes.", true);
          });
        })();
      </script>
    </section>
""")


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
        axis = StrategicAxisConfig(
            nombre=nombre,
            codigo=(data.get("codigo") or "").strip(),
            lider_departamento=(data.get("lider_departamento") or "").strip(),
            descripcion=(data.get("descripcion") or "").strip(),
            orden=int(data.get("orden") or (max_order + 1)),
            is_active=True,
        )
        db.add(axis)
        db.commit()
        db.refresh(axis)
        return JSONResponse({"success": True, "data": _serialize_strategic_axis(axis)})
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
        axis.nombre = nombre
        axis.codigo = (data.get("codigo") or "").strip()
        axis.lider_departamento = (data.get("lider_departamento") or "").strip()
        axis.descripcion = (data.get("descripcion") or "").strip()
        axis.orden = int(data.get("orden") or axis.orden or 1)
        db.add(axis)
        db.commit()
        db.refresh(axis)
        return JSONResponse({"success": True, "data": _serialize_strategic_axis(axis)})
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
        max_order = (
            db.query(func.max(StrategicObjectiveConfig.orden))
            .filter(StrategicObjectiveConfig.eje_id == axis_id)
            .scalar()
            or 0
        )
        objective = StrategicObjectiveConfig(
            eje_id=axis_id,
            codigo=(data.get("codigo") or "").strip(),
            nombre=nombre,
            lider=(data.get("lider") or "").strip(),
            fecha_inicial=start_date,
            fecha_final=end_date,
            descripcion=(data.get("descripcion") or "").strip(),
            orden=int(data.get("orden") or (max_order + 1)),
            is_active=True,
        )
        db.add(objective)
        db.commit()
        db.refresh(objective)
        return JSONResponse({"success": True, "data": _serialize_strategic_objective(objective)})
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
        objective.codigo = (data.get("codigo") or "").strip()
        objective.nombre = nombre
        objective.lider = (data.get("lider") or "").strip()
        objective.fecha_inicial = start_date
        objective.fecha_final = end_date
        objective.descripcion = (data.get("descripcion") or "").strip()
        if data.get("orden") is not None:
            objective.orden = int(data.get("orden"))
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

        if _can_authorize_documents(request):
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
            descripcion=(data.get("descripcion") or "").strip(),
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
        activity.descripcion = (data.get("descripcion") or "").strip()
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
        process_owner = _resolve_process_owner_for_objective(objective, axis)
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
        assigned_by = session_username
        sub = POASubactivity(
            activity_id=activity.id,
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
        db.delete(sub)
        db.commit()
        return JSONResponse({"success": True})
    finally:
        db.close()


