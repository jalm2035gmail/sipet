/**
 * sipet_dashboard.js — Panel de control SIPET.
 *
 * Expone:
 *   SipetDash.init()   — carga y renderiza los widgets del dashboard
 */
const SipetDash = (() => {
  const BASE = "/api/v2/pwa/sipet";

  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function pct(value, total) {
    if (!total) return 0;
    return Math.min(100, Math.round((value / total) * 100));
  }

  // ── Widgets ─────────────────────────────────────────────────────────────────

  function renderKpiCard(label, value, sub = "") {
    const card = el("div", "dash-kpi");
    card.appendChild(el("p", "dash-kpi-label", label));
    card.appendChild(el("span", "dash-kpi-value", String(value)));
    if (sub) card.appendChild(el("p", "dash-kpi-sub", sub));
    return card;
  }

  function renderProgressBar(value, max, label) {
    const wrap = el("div", "dash-progress-wrap");
    const header = el("div", "dash-progress-header");
    header.appendChild(el("span", "", label));
    header.appendChild(el("span", "dash-progress-pct", `${pct(value, max)}%`));
    wrap.appendChild(header);
    const bar = el("div", "dash-progress-bar");
    const fill = el("div", "dash-progress-fill");
    fill.style.width = `${pct(value, max)}%`;
    bar.appendChild(fill);
    wrap.appendChild(bar);
    return wrap;
  }

  // ── Activities list ──────────────────────────────────────────────────────────

  async function loadActivities(objectiveId) {
    const res = await apiFetch(`${BASE}/objectives/${objectiveId}/activities`);
    if (!res.ok) return [];
    return res.json();
  }

  function renderActivityRow(activity) {
    const row = el("div", `activity-row status-${activity.status}`);
    const left = el("div", "activity-left");
    left.appendChild(el("span", "activity-name", activity.name));
    left.appendChild(el("span", "activity-area", activity.area || ""));

    const right = el("div", "activity-right");
    const progress = el("span", "activity-progress", `${activity.progress}%`);
    right.appendChild(progress);

    const statusMap = {
      pending: "Pendiente", in_progress: "En progreso",
      completed: "Completada", approved: "Aprobada",
    };
    right.appendChild(el("span", "activity-status", statusMap[activity.status] || activity.status));

    row.append(left, right);

    row.addEventListener("click", () => {
      window.location.href = `/activities?id=${activity.id}`;
    });
    return row;
  }

  // ── Main init ────────────────────────────────────────────────────────────────

  async function init() {
    // 1. Dashboard summary
    const summaryContainer = document.getElementById("dash-summary");
    if (summaryContainer) {
      try {
        const res = await apiFetch(`${BASE}/dashboard`);
        if (res.ok) {
          const d = await res.json();
          summaryContainer.innerHTML = "";
          summaryContainer.appendChild(renderKpiCard("Planes", d.plans));
          summaryContainer.appendChild(renderKpiCard("Objetivos", d.objectives));
          summaryContainer.appendChild(renderKpiCard("KPIs", d.kpis));
          summaryContainer.appendChild(renderKpiCard("Actividades", d.activities,
            `${d.completed_activities} completadas · ${d.overdue_activities} vencidas`));
          summaryContainer.appendChild(renderKpiCard("Presupuesto ejecutado",
            `${d.execution_rate}%`,
            `$${d.executed_budget.toLocaleString()} / $${d.planned_budget.toLocaleString()}`));
        }
      } catch (_) { /* ignore */ }
    }

    // 2. Progress bars
    const progressContainer = document.getElementById("dash-progress");
    if (progressContainer) {
      try {
        const res = await apiFetch(`${BASE}/dashboard`);
        if (res.ok) {
          const d = await res.json();
          progressContainer.innerHTML = "";
          progressContainer.appendChild(
            renderProgressBar(d.completed_activities, d.activities, "Actividades completadas")
          );
          progressContainer.appendChild(
            renderProgressBar(d.average_progress, 100, "Avance promedio")
          );
          progressContainer.appendChild(
            renderProgressBar(d.executed_budget, d.planned_budget, "Ejecución presupuestal")
          );
        }
      } catch (_) { /* ignore */ }
    }

    // 3. Plans accordion (top 3)
    const plansContainer = document.getElementById("dash-plans");
    if (plansContainer) {
      try {
        const res = await apiFetch(`${BASE}/plans`);
        if (res.ok) {
          const plans = await res.json();
          plansContainer.innerHTML = "";
          for (const plan of plans.slice(0, 3)) {
            const block = el("details", "dash-plan");
            const summary = el("summary", "dash-plan-title", `${plan.code} · ${plan.name}`);
            block.appendChild(summary);
            block.appendChild(el("p", "dash-plan-org", plan.organization));

            // load objectives on expand
            block.addEventListener("toggle", async () => {
              if (!block.open || block.dataset.loaded) return;
              block.dataset.loaded = "1";
              const resO = await apiFetch(`${BASE}/plans/${plan.id}/objectives`);
              if (resO.ok) {
                const objs = await resO.json();
                objs.forEach((o) => {
                  const oEl = el("div", "dash-obj");
                  oEl.appendChild(el("span", "dash-obj-code", o.code));
                  oEl.appendChild(el("span", "dash-obj-title", o.title));
                  block.appendChild(oEl);
                });
              }
            });
            plansContainer.appendChild(block);
          }
        }
      } catch (_) { /* ignore */ }
    }
  }

  return { init, loadActivities, renderActivityRow };
})();

window.SipetDash = SipetDash;
