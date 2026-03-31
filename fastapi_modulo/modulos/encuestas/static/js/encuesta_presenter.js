/**
 * encuesta_presenter.js
 * Control panel for live survey sessions.
 */
(function () {
  "use strict";

  /* -------------------------------------------------------------------------
   * Bootstrap
   * ---------------------------------------------------------------------- */
  const bootstrap = window.__PRESENTER_BOOTSTRAP || {};
  const instanceId = bootstrap.instance_id;
  const tenantId = bootstrap.tenant_id;

  /* -------------------------------------------------------------------------
   * DOM refs
   * ---------------------------------------------------------------------- */
  const root = document.getElementById("enc-presenter-root");
  if (!root) return;

  const titleEl = document.getElementById("enc-pres-title");
  const statusBadge = document.getElementById("enc-pres-status-badge");
  const btnStart = document.getElementById("enc-pres-btn-start");
  const btnStartCenter = document.getElementById("enc-pres-btn-start-center");
  const btnStop = document.getElementById("enc-pres-btn-stop");
  const btnCopyToken = document.getElementById("enc-pres-btn-copy-token");
  const questionList = document.getElementById("enc-pres-question-list");
  const sidebarLabel = document.getElementById("enc-pres-sidebar-label");
  const accessModeSelect = document.getElementById("enc-pres-access-mode");
  const accessHelp = document.getElementById("enc-pres-access-help");

  const idleMsg = document.getElementById("enc-pres-idle-message");
  const activePanel = document.getElementById("enc-pres-active-panel");
  const endedMsg = document.getElementById("enc-pres-ended-message");

  const qIndexEl = document.getElementById("enc-pres-q-index");
  const qTypeEl = document.getElementById("enc-pres-q-type");
  const qTituloEl = document.getElementById("enc-pres-q-titulo");
  const qDescEl = document.getElementById("enc-pres-q-desc");
  const pageStage = document.getElementById("enc-pres-page-stage");

  const btnPrev = document.getElementById("enc-pres-btn-prev");
  const btnNext = document.getElementById("enc-pres-btn-next");
  const btnToggleResults = document.getElementById("enc-pres-btn-toggle-results");
  const resultsPanel = document.getElementById("enc-pres-results-panel");
  const btnResultsChart = document.getElementById("enc-pres-btn-results-chart");
  const btnResultsData = document.getElementById("enc-pres-btn-results-data");
  const btnResultsFullscreen = document.getElementById("enc-pres-btn-results-fullscreen");

  /* -------------------------------------------------------------------------
   * State
   * ---------------------------------------------------------------------- */
  let presenterToken = "";
  let liveStatus = "idle";       // idle | running | ended
  let items = [];                // ordered list from API (pages or questions)
  let questions = [];
  let currentQIdx = 0;
  let showResults = true;
  let presentationMode = false;
  let livePageResults = {};
  let sectionResultsVisibility = {};
  let resultsViewMode = "chart";
  let pollTimer = null;
  const POLL_INTERVAL = 2500;

  /* -------------------------------------------------------------------------
   * Init
   * ---------------------------------------------------------------------- */
  if (bootstrap.instance && bootstrap.instance.nombre) {
    titleEl.textContent = bootstrap.instance.nombre;
  }
  if (bootstrap.instance && bootstrap.instance.audience_mode && accessModeSelect) {
    accessModeSelect.value = String(bootstrap.instance.audience_mode).trim().toLowerCase() === "internal" ? "internal" : "public_link";
    updateAccessHelp();
  }

  // Try to restore presenter token from sessionStorage
  const storedToken = sessionStorage.getItem(`pres_token_${instanceId}`);
  if (storedToken) {
    presenterToken = storedToken;
    fetchPresenterStatus();
  }

  /* -------------------------------------------------------------------------
   * API helpers
   * ---------------------------------------------------------------------- */
  async function apiPost(path, body) {
    const resp = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(body),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || resp.statusText);
    }
    return resp.json();
  }

  async function apiGet(path) {
    const resp = await fetch(path, { credentials: "same-origin" });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || resp.statusText);
    }
    return resp.json();
  }

  async function apiPatch(path, body) {
    const resp = await fetch(path, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(body),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || resp.statusText);
    }
    return resp.json();
  }

  /* -------------------------------------------------------------------------
   * Session control
   * ---------------------------------------------------------------------- */
  async function startSession() {
    try {
      const state = await apiPost(
        `/api/encuestas/campanas/${instanceId}/live/start`,
        {}
      );
      presenterToken = state.presenter_token || "";
      sessionStorage.setItem(`pres_token_${instanceId}`, presenterToken);
      applyState(state);
    } catch (e) {
      alert("Error al iniciar sesión: " + e.message);
    }
  }

  async function stopSession() {
    if (!confirm("¿Finalizar la sesión en vivo?")) return;
    try {
      sessionStorage.removeItem(`pres_token_${instanceId}`);
      presenterToken = "";
      const state = await apiPost(
        `/api/encuestas/campanas/${instanceId}/live/stop`,
        {}
      );
      applyState(state);
    } catch (e) {
      alert("Error al finalizar sesión: " + e.message);
    }
  }

  async function setQuestion(questionId) {
    if (!presenterToken) return;
    try {
      const state = await apiPost(
        `/api/encuestas/campanas/${instanceId}/live/question`,
        {
          question_id: questionId,
          presenter_token: presenterToken,
          show_results: showResults,
        }
      );
      applyState(state);
    } catch (e) {
      alert("Error al cambiar pregunta: " + e.message);
    }
  }

  async function setPage(pageIndex) {
    if (!presenterToken) return;
    try {
      const state = await apiPost(
        `/api/encuestas/campanas/${instanceId}/live/page`,
        {
          page_index: pageIndex,
          presenter_token: presenterToken,
          show_results: showResults,
        }
      );
      applyState(state);
    } catch (e) {
      alert("Error al cambiar lámina: " + e.message);
    }
  }

  async function fetchPresenterStatus() {
    try {
      const state = await apiGet(
        `/api/encuestas/campanas/${instanceId}/live/status`
      );
      applyState(state);
    } catch (_) {
      // Silently ignore poll failures
    }
  }

  /* -------------------------------------------------------------------------
   * State application
   * ---------------------------------------------------------------------- */
  function applyState(state) {
    liveStatus = state.live_status || "idle";
    presentationMode = state.presentation_mode === true || state.live_mode === "presentation";
    currentQIdx = presentationMode
      ? (state.live_current_page_index || 0)
      : (state.live_current_question_index || 0);
    showResults = state.live_show_results !== false;

    if (presentationMode) {
      items = Array.isArray(state.pages) ? state.pages : [];
    } else if (state.questions && state.questions.length) {
      items = state.questions;
    }
    if (Array.isArray(state.questions)) {
      questions = state.questions;
    }
    livePageResults = state.current_page_results || {};

    if (sidebarLabel) sidebarLabel.textContent = presentationMode ? "Láminas" : "Preguntas";
    renderHeader();
    renderQuestionList();
    renderCenterPanel();
    renderResults(state.current_results || null);

    // Start/stop polling
    if (liveStatus === "running") {
      startPolling();
    } else {
      stopPolling();
    }
  }

  function renderHeader() {
    const labels = { idle: "Inactiva", running: "En vivo", ended: "Finalizada" };
    statusBadge.textContent = labels[liveStatus] || liveStatus;
    statusBadge.className = `enc-presenter-badge enc-pres-badge-${liveStatus}`;

    if (liveStatus === "idle" || liveStatus === "ended") {
      btnStart.hidden = false;
      btnStop.hidden = true;
      btnCopyToken.hidden = true;
    } else {
      btnStart.hidden = true;
      btnStop.hidden = false;
      btnCopyToken.hidden = false;
    }
  }

  function renderResultsModeButtons() {
    if (btnResultsChart) btnResultsChart.classList.toggle("is-primary", resultsViewMode === "chart");
    if (btnResultsData) btnResultsData.classList.toggle("is-primary", resultsViewMode === "data");
  }

  function renderQuestionList() {
    questionList.innerHTML = "";
    items.forEach((item, idx) => {
      const li = document.createElement("li");
      li.className = "enc-pres-q-item" + (idx === currentQIdx ? " is-active" : "");
      li.dataset.idx = idx;
      li.innerHTML = `
        <span class="enc-pres-q-num">${idx + 1}</span>
        <span class="enc-pres-q-text">${escHtml(item.title || item.titulo || `Lámina ${idx + 1}`)}</span>
      `;
      if (liveStatus === "running") {
        li.style.cursor = "pointer";
        li.addEventListener("click", () => {
          if (presentationMode) setPage(idx);
          else if (item.id) setQuestion(item.id);
        });
      }
      questionList.appendChild(li);
    });
  }

  function renderCenterPanel() {
    idleMsg.hidden = liveStatus !== "idle";
    endedMsg.hidden = liveStatus !== "ended";
    activePanel.hidden = liveStatus !== "running";

    if (liveStatus !== "running" || !items.length) return;

    const current = items[currentQIdx];
    if (!current) return;

    qIndexEl.textContent = presentationMode
      ? `Lámina ${currentQIdx + 1} / ${items.length}`
      : `Pregunta ${currentQIdx + 1} / ${items.length}`;
    qTypeEl.textContent = presentationMode ? "presentation" : (current.question_type || "");
    qTituloEl.textContent = current.title || current.titulo || "";
    qDescEl.textContent = current.description || current.descripcion || "";
    qDescEl.hidden = !(current.description || current.descripcion);
    if (pageStage) {
      pageStage.hidden = !presentationMode;
      pageStage.classList.toggle("is-presentation-mode", presentationMode);
      if (presentationMode) {
        pageStage.innerHTML = renderPresentationPage(current);
        hydrateEmbeddedRuntime(pageStage);
        animatePresentationResultBars(pageStage);
      }
      else pageStage.innerHTML = "";
    }

    btnPrev.disabled = currentQIdx === 0;
    btnNext.disabled = currentQIdx === items.length - 1;

    btnToggleResults.textContent = showResults ? "Ocultar resultados" : "Mostrar resultados";
  }

  function renderPresentationBlock(block) {
    const widthClass = String(block.width || "full") === "half" ? "is-half" : "is-full";
    if (String(block.type || "") === "question") {
      const question = questions.find((item) => Number(item.id) === Number(block.question_id));
      if (!question) return `<div class="enc-presentation-item ${widthClass}"><div class="enc-placeholder">Pregunta no disponible.</div></div>`;
      return `<div class="enc-presentation-item ${widthClass}"><article class="enc-card"><h4>${escHtml(question.titulo || "")}</h4><p class="enc-question-meta">${escHtml(question.descripcion || "")}</p></article></div>`;
    }
    if (String(block.type || "") === "image") {
      return `<div class="enc-presentation-item ${widthClass}">${renderImageSection(block)}</div>`;
    }
    return `<div class="enc-presentation-item ${widthClass}"><article class="enc-card enc-response-richtext">${renderEmbeddedSectionHtml(block)}</article></div>`;
  }

  function normalizeEmbeddedContent(rawHtml, rawCss) {
    const html = String(rawHtml || "").trim();
    const css = String(rawCss || "").trim();
    if (!html) return { html: "", css };
    if (!/(<!doctype|<html\b|<body\b|<head\b)/i.test(html)) return { html, css };
    try {
      const doc = new DOMParser().parseFromString(html, "text/html");
      const body = doc.body;
      const bodyContent = body ? body.innerHTML.trim() : "";
      const extractedCss = Array.from(doc.head ? doc.head.querySelectorAll("style") : [])
        .map((node) => node.textContent || "")
        .join("\n")
        .trim();
      const bodyClass = body && body.className ? ` class="${escHtml(body.className)}"` : "";
      const bodyStyle = body && body.getAttribute("style") ? ` style="${escHtml(body.getAttribute("style"))}"` : "";
      if (!bodyContent) return { html, css: css || extractedCss };
      return {
        html: `<div${bodyClass}${bodyStyle}>${bodyContent}</div>`,
        css: css || extractedCss,
      };
    } catch (_error) {
      return { html, css };
    }
  }

  function renderEmbeddedSectionHtml(section) {
    const normalized = normalizeEmbeddedContent(section && section.html, section && section.css);
    const jsInput = String((section && section.js_input) || "").trim();
    const jsHighlight = String((section && section.js_highlight) || "").trim();
    const jsOutput = String((section && section.js_output) || "").trim();
    const inputEffect = escHtml(String((section && section.js_input_effect) || "none"));
    const highlightEffect = escHtml(String((section && section.js_highlight_effect) || "none"));
    const outputEffect = escHtml(String((section && section.js_output_effect) || "none"));
    const inputCode = jsInput ? escHtml(encodeURIComponent(jsInput)) : "";
    const highlightCode = jsHighlight ? escHtml(encodeURIComponent(jsHighlight)) : "";
    const outputCode = jsOutput ? escHtml(encodeURIComponent(jsOutput)) : "";
    return `<div class="enc-embedded-runtime" data-enc-js-input-effect="${inputEffect}" data-enc-js-highlight-effect="${highlightEffect}" data-enc-js-output-effect="${outputEffect}" data-enc-js-input="${inputCode}" data-enc-js-highlight="${highlightCode}" data-enc-js-output="${outputCode}">${normalized.css ? `<style>${normalized.css}</style>` : ""}${normalized.html}</div>`;
  }

  function renderImageSection(section) {
    const imageUrl = escHtml(section.image_url || "");
    const imageFit = escHtml(section.image_fit || "cover");
    const imageAlt = escHtml(section.image_alt || "");
    if (!imageUrl) return '<div class="enc-placeholder">Imagen no configurada.</div>';
    return `<div class="enc-presentation-image-surface" role="img" aria-label="${imageAlt}" style="background-image:url('${imageUrl}');background-size:${imageFit};background-position:center;background-repeat:no-repeat;"></div>`;
  }

  function runEmbeddedEffect(node, effectName) {
    if (!(node instanceof HTMLElement) || !node.animate) return;
    const effect = String(effectName || "none");
    if (effect === "none") return;
    const animations = {
      fade_in: { keyframes: [{ opacity: 0 }, { opacity: 1 }], options: { duration: 360, easing: "ease-out", fill: "both" } },
      slide_up: { keyframes: [{ opacity: 0, transform: "translateY(32px)" }, { opacity: 1, transform: "translateY(0)" }], options: { duration: 420, easing: "cubic-bezier(.2,.8,.2,1)", fill: "both" } },
      slide_left: { keyframes: [{ opacity: 0, transform: "translateX(40px)" }, { opacity: 1, transform: "translateX(0)" }], options: { duration: 420, easing: "cubic-bezier(.2,.8,.2,1)", fill: "both" } },
      zoom_in: { keyframes: [{ opacity: 0, transform: "scale(.9)" }, { opacity: 1, transform: "scale(1)" }], options: { duration: 320, easing: "ease-out", fill: "both" } },
      bounce_in: { keyframes: [{ opacity: 0, transform: "scale(.82)" }, { opacity: 1, transform: "scale(1.04)" }, { opacity: 1, transform: "scale(1)" }], options: { duration: 520, easing: "ease-out", fill: "both" } },
      pulse: { keyframes: [{ transform: "scale(1)" }, { transform: "scale(1.03)" }, { transform: "scale(1)" }], options: { duration: 260, easing: "ease-in-out" } },
      pop: { keyframes: [{ transform: "scale(1)" }, { transform: "scale(1.08)" }, { transform: "scale(1)" }], options: { duration: 220, easing: "ease-out" } },
      shake: { keyframes: [{ transform: "translateX(0)" }, { transform: "translateX(-6px)" }, { transform: "translateX(6px)" }, { transform: "translateX(-4px)" }, { transform: "translateX(0)" }], options: { duration: 280, easing: "ease-in-out" } },
      highlight: { keyframes: [{ boxShadow: "0 0 0 rgba(59,130,246,0)" }, { boxShadow: "0 0 0 8px rgba(59,130,246,.18)" }, { boxShadow: "0 0 0 rgba(59,130,246,0)" }], options: { duration: 520, easing: "ease-out" } },
      flip: { keyframes: [{ transform: "rotateY(0deg)" }, { transform: "rotateY(14deg)" }, { transform: "rotateY(0deg)" }], options: { duration: 340, easing: "ease-in-out" } },
    };
    const config = animations[effect];
    if (!config) return;
    node.animate(config.keyframes, config.options);
  }

  function hydrateEmbeddedRuntime(scope) {
    if (!scope) return;
    scope.querySelectorAll(".enc-embedded-runtime").forEach((node) => {
      if (!(node instanceof HTMLElement)) return;
      const inputCode = node.dataset.encJsInput ? decodeURIComponent(node.dataset.encJsInput) : "";
      const highlightCode = node.dataset.encJsHighlight ? decodeURIComponent(node.dataset.encJsHighlight) : "";
      const outputCode = node.dataset.encJsOutput ? decodeURIComponent(node.dataset.encJsOutput) : "";
      const inputEffect = node.dataset.encJsInputEffect || "none";
      const highlightEffect = node.dataset.encJsHighlightEffect || "none";
      const outputEffect = node.dataset.encJsOutputEffect || "none";
      if (inputCode && node.dataset.encJsInputRan !== "1") {
        node.dataset.encJsInputRan = "1";
        try {
          new Function("root", inputCode)(node);
        } catch (error) {
          console.warn("encuestas presenter js entrada invalido", error);
        }
      }
      if (node.dataset.encJsEntryEffectRan !== "1") {
        node.dataset.encJsEntryEffectRan = "1";
        runEmbeddedEffect(node, inputEffect);
      }
      if ((highlightCode || highlightEffect !== "none") && node.dataset.encJsHighlightBound !== "1") {
        node.dataset.encJsHighlightBound = "1";
        const highlightHandler = function (event) {
          const target = event.target;
          if (!(target instanceof Element)) return;
          if (!target.closest("p,span,h1,h2,h3,h4,h5,h6,li,a,strong,em,small,div")) return;
          if (target.closest("img,svg,canvas,video")) return;
          runEmbeddedEffect(node, highlightEffect);
          if (highlightCode) {
            try {
              new Function("root", "event", highlightCode)(node, event);
            } catch (error) {
              console.warn("encuestas presenter js destacar invalido", error);
            }
          }
        };
        node.addEventListener("mouseover", highlightHandler);
        node.addEventListener("focusin", highlightHandler);
      }
      if (outputCode && node.dataset.encJsOutputBound !== "1") {
        node.dataset.encJsOutputBound = "1";
        node.addEventListener("click", function (event) {
          const target = event.target;
          if (!(target instanceof Element)) return;
          if (!target.closest("p,span,h1,h2,h3,h4,h5,h6,li,a,strong,em,small,div")) return;
          if (target.closest("img,svg,canvas,video")) return;
          runEmbeddedEffect(node, outputEffect);
          try {
            new Function("root", "event", outputCode)(node, event);
          } catch (error) {
            console.warn("encuestas presenter js salida invalido", error);
          }
        });
      } else if (outputCode === "" && outputEffect !== "none" && node.dataset.encJsOutputBound !== "1") {
        node.dataset.encJsOutputBound = "1";
        node.addEventListener("click", function (event) {
          const target = event.target;
          if (!(target instanceof Element)) return;
          if (!target.closest("p,span,h1,h2,h3,h4,h5,h6,li,a,strong,em,small,div")) return;
          if (target.closest("img,svg,canvas,video")) return;
          runEmbeddedEffect(node, outputEffect);
        });
      }
    });
  }

  function renderPresentationSectionResults(selectedQuestions) {
    const blocks = selectedQuestions.map((question) => {
      const result = livePageResults[String(question.id)];
      if (!result) return "";
      const total = Number(result.total_responses || 0);
      let body = `<p class="enc-presentation-results-total"><em><span data-enc-animate-count="${total}" data-enc-count-singular=" respuesta" data-enc-count-plural=" respuestas">0 respuestas</span></em></p>`;
      if (question.options && question.options.length) {
        const maxCount = Math.max(...question.options.map((option) => Number((result.counts || {})[String(option.value)] || 0)), 1);
        body += `<div class="enc-presentation-results-list">${question.options.map((option) => {
          const count = Number((result.counts || {})[String(option.value)] || 0);
          const width = Math.round((count / maxCount) * 100);
          return `
            <div class="enc-presentation-results-item is-chart">
              <div class="enc-presentation-results-copy">
                <span>${escHtml(option.label || String(option.value))}</span>
                <strong data-enc-animate-count="${count}">0</strong>
              </div>
              <div class="enc-presentation-results-bar"><span data-enc-animate-width="${width}" style="width:0%"></span></div>
            </div>
          `;
        }).join("")}</div>`;
      } else if (result.texts && result.texts.length) {
        body += `<div class="enc-presentation-results-list">${result.texts.slice(0, 5).map((text) => `<div class="enc-presentation-results-item"><span>${escHtml(text)}</span></div>`).join("")}</div>`;
      }
      return `<div class="enc-presentation-results-card"><h5>${escHtml(question.titulo || "")}</h5>${body}</div>`;
    }).filter(Boolean).join("");
    return blocks ? `<div class="enc-presentation-section-results">${blocks}</div>` : "";
  }

  function animatePresentationResultBars(scope) {
    if (!scope) return;
    scope.querySelectorAll("[data-enc-animate-count]").forEach((node) => {
      const targetCount = Number(node.getAttribute("data-enc-animate-count") || 0);
      const singularSuffix = String(node.getAttribute("data-enc-count-singular") || "");
      const pluralSuffix = String(node.getAttribute("data-enc-count-plural") || singularSuffix);
      const durationMs = 520;
      const startTime = performance.now();
      const setValue = (value) => {
        const rounded = Math.round(value);
        const suffix = rounded === 1 ? singularSuffix : pluralSuffix;
        node.textContent = `${rounded}${suffix}`;
      };
      setValue(0);
      const step = (now) => {
        const progress = Math.min(1, (now - startTime) / durationMs);
        const value = targetCount * progress;
        setValue(value);
        if (progress < 1) {
          requestAnimationFrame(step);
        } else {
          setValue(targetCount);
        }
      };
      requestAnimationFrame(step);
    });
    scope.querySelectorAll("[data-enc-animate-width]").forEach((node) => {
      const targetWidth = Number(node.getAttribute("data-enc-animate-width") || 0);
      node.style.width = "0%";
      requestAnimationFrame(() => {
        node.style.width = `${Math.max(0, Math.min(100, targetWidth))}%`;
      });
    });
  }

  function renderPresentationLayoutSection(section) {
    const type = String((section && section.type) || "html");
    if (type === "question") {
      const selectedQuestions = (Array.isArray(section.question_ids) ? section.question_ids : [section.question_id])
        .map((questionId) => questions.find((item) => Number(item.id) === Number(questionId)))
        .filter(Boolean);
      if (!selectedQuestions.length) return `<article class="enc-presentation-layout-slot"><div class="enc-placeholder">Pregunta no disponible.</div></article>`;
      const firstQuestionId = selectedQuestions[0] ? String(selectedQuestions[0].id) : "";
      const sectionResult = firstQuestionId ? livePageResults[firstQuestionId] : null;
      const totalResponses = sectionResult && sectionResult.total_responses != null ? Number(sectionResult.total_responses) : 0;
      const isOpen = Boolean(firstQuestionId && sectionResultsVisibility[firstQuestionId]);
      return `
        <article class="enc-presentation-layout-slot">
          <div class="enc-presentation-question-tools">
            <span class="enc-presentation-question-count"><span data-enc-animate-count="${totalResponses}" data-enc-count-singular=" respuesta" data-enc-count-plural=" respuestas">0 respuestas</span></span>
            ${firstQuestionId ? `<button type="button" class="enc-presentation-eye" data-enc-toggle-section-results="${firstQuestionId}" aria-label="${isOpen ? "Ocultar respuestas" : "Ver respuestas"}" title="${isOpen ? "Ocultar respuestas" : "Ver respuestas"}">${isOpen ? "🙈" : "👁"}</button>` : ""}
          </div>
          ${selectedQuestions.map((question) => `<article class="enc-card"><h4>${escHtml(question.titulo || "")}</h4><p class="enc-question-meta">${escHtml(question.descripcion || "")}</p></article>`).join("")}
          ${isOpen ? renderPresentationSectionResults(selectedQuestions) : ""}
        </article>
      `;
    }
    if (type === "image") {
      return `<article class="enc-presentation-layout-slot">${renderImageSection(section)}</article>`;
    }
    const html = renderEmbeddedSectionHtml(section);
    return `<article class="enc-presentation-layout-slot">${html ? `<article class="enc-card enc-response-richtext">${html}</article>` : `<div class="enc-placeholder">Sección vacía.</div>`}</article>`;
  }

  function renderPresentationPage(page) {
    const bgLayers = [];
    const title = String((page && page.title) || "").trim();
    const footerText = String((page && page.footer_text) || "").trim();
    if (page && page.bg_image_url) {
      bgLayers.push(`linear-gradient(180deg, rgba(15,23,42,0.08), rgba(15,23,42,0.14)), url("${escHtml(page.bg_image_url)}") center / cover`);
    }
    bgLayers.push(escHtml((page && page.bg_color) || "#ffffff"));
    const layoutSections = Array.isArray(page && page.layout_sections) ? page.layout_sections : [];
    const sectionCount = Number(page && page.section_count) === 4 ? 4 : Number(page && page.section_count) === 2 ? 2 : 1;
    if (layoutSections.length) {
      return `
        <div class="enc-presentation-stage">
          <div class="enc-presentation-stage-ratio">
            <div class="enc-presentation-stage-canvas" style="background:${bgLayers.join(", ")};">
              <div class="enc-presentation-layout">
                ${title ? `<header class="enc-presentation-layout-header"><h1>${escHtml(title)}</h1></header>` : ""}
                <div class="enc-presentation-layout-body is-sections-${sectionCount}">
                  ${layoutSections.map((section) => renderPresentationLayoutSection(section)).join("")}
                </div>
                ${footerText ? `<footer class="enc-presentation-layout-footer" style="background:${escHtml((page && page.footer_color) || "#0f172a")};"><span>${escHtml(footerText)}</span></footer>` : ""}
              </div>
            </div>
          </div>
        </div>
      `;
    }
    return `
      <div class="enc-presentation-stage">
        <div class="enc-presentation-stage-ratio">
          <div class="enc-presentation-stage-canvas" style="background:${bgLayers.join(", ")};">
            <div class="enc-presentation-grid">${(page.blocks || []).map(renderPresentationBlock).join("")}</div>
          </div>
        </div>
      </div>
    `;
  }

  function renderResults(results) {
    if (!results || liveStatus !== "running") {
      resultsPanel.innerHTML = '<p class="enc-pres-results-waiting enc-muted">Esperando respuestas...</p>';
      renderResultsModeButtons();
      return;
    }

    const total = results.total_responses || 0;
    const counts = results.counts || {};
    const texts = results.texts || [];
    const q = presentationMode
      ? questions.find((item) => Number(item.id) === Number(results.question_id))
      : items[currentQIdx];

    let html = `<p class="enc-pres-results-total"><strong>${total}</strong> respuesta${total !== 1 ? "s" : ""}</p>`;

    if (presentationMode && !results.question_id) {
      resultsPanel.innerHTML = '<p class="enc-pres-results-waiting enc-muted">Esta lámina no tiene una pregunta asociada para mostrar resultados.</p>';
      renderResultsModeButtons();
      return;
    }

    if (q && q.options && q.options.length) {
      if (resultsViewMode === "data") {
        html += '<div class="enc-pres-data-list">';
        q.options.forEach(opt => {
          const count = counts[String(opt.value)] || 0;
          const pctTotal = total > 0 ? Math.round((count / total) * 100) : 0;
          html += `
            <div class="enc-pres-data-row">
              <span>${escHtml(opt.label || String(opt.value))}</span>
              <strong>${count}</strong>
              <small>${pctTotal}%</small>
            </div>`;
        });
        html += "</div>";
      } else {
        const maxCount = Math.max(...q.options.map(o => counts[String(o.value)] || 0), 1);
        html += '<ul class="enc-pres-bar-list">';
        q.options.forEach(opt => {
          const count = counts[String(opt.value)] || 0;
          const pct = Math.round((count / maxCount) * 100);
          const pctTotal = total > 0 ? Math.round((count / total) * 100) : 0;
          html += `
            <li class="enc-pres-bar-item">
              <span class="enc-pres-bar-label">${escHtml(opt.label || String(opt.value))}</span>
              <div class="enc-pres-bar-track">
                <div class="enc-pres-bar-fill" style="width:${pct}%"></div>
              </div>
              <span class="enc-pres-bar-count">${count} <small>(${pctTotal}%)</small></span>
            </li>`;
        });
        html += "</ul>";
      }
    } else if (texts.length) {
      html += '<ul class="enc-pres-text-list">';
      texts.slice(0, 10).forEach(t => {
        html += `<li class="enc-pres-text-item">${escHtml(t)}</li>`;
      });
      html += "</ul>";
    }

    resultsPanel.innerHTML = html;
    renderResultsModeButtons();
  }

  async function toggleResultsFullscreen() {
    const presentationTarget = pageStage ? pageStage.querySelector(".enc-presentation-stage") : null;
    const target = presentationMode && presentationTarget
      ? presentationTarget
      : (resultsPanel && resultsPanel.parentElement ? resultsPanel.parentElement : resultsPanel);
    if (!target) return;
    if (document.fullscreenElement) {
      await document.exitFullscreen();
      return;
    }
    if (target.requestFullscreen) {
      await target.requestFullscreen();
    }
  }

  /* -------------------------------------------------------------------------
   * Polling
   * ---------------------------------------------------------------------- */
  function startPolling() {
    if (pollTimer) return;
    pollTimer = setInterval(fetchPresenterStatus, POLL_INTERVAL);
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  /* -------------------------------------------------------------------------
   * Event listeners
   * ---------------------------------------------------------------------- */
  [btnStart, btnStartCenter].forEach(btn => {
    if (btn) btn.addEventListener("click", startSession);
  });

  btnStop && btnStop.addEventListener("click", stopSession);

  btnCopyToken && btnCopyToken.addEventListener("click", () => {
    if (!presenterToken) return;
    navigator.clipboard.writeText(presenterToken).then(() => {
      btnCopyToken.textContent = "¡Copiado!";
      setTimeout(() => (btnCopyToken.textContent = "Copiar token"), 2000);
    });
  });

  btnPrev && btnPrev.addEventListener("click", () => {
    if (currentQIdx > 0 && items[currentQIdx - 1]) {
      if (presentationMode) setPage(currentQIdx - 1);
      else setQuestion(items[currentQIdx - 1].id);
    }
  });

  btnNext && btnNext.addEventListener("click", () => {
    if (currentQIdx < items.length - 1 && items[currentQIdx + 1]) {
      if (presentationMode) setPage(currentQIdx + 1);
      else setQuestion(items[currentQIdx + 1].id);
    }
  });

  btnToggleResults && btnToggleResults.addEventListener("click", async () => {
    showResults = !showResults;
    if (presenterToken && items[currentQIdx]) {
      if (presentationMode) await setPage(currentQIdx);
      else await setQuestion(items[currentQIdx].id);
    }
  });

  btnResultsChart && btnResultsChart.addEventListener("click", function () {
    resultsViewMode = "chart";
    renderResultsModeButtons();
    if (liveStatus === "running") fetchPresenterStatus();
  });

  btnResultsData && btnResultsData.addEventListener("click", function () {
    resultsViewMode = "data";
    renderResultsModeButtons();
    if (liveStatus === "running") fetchPresenterStatus();
  });

  btnResultsFullscreen && btnResultsFullscreen.addEventListener("click", async function () {
    try {
      await toggleResultsFullscreen();
    } catch (error) {
      alert("No se pudo abrir en pantalla completa: " + error.message);
    }
  });

  pageStage && pageStage.addEventListener("click", function (event) {
    const button = event.target.closest("[data-enc-toggle-section-results]");
    if (!button) return;
    const questionId = String(button.dataset.encToggleSectionResults || "");
    if (!questionId) return;
    sectionResultsVisibility[questionId] = !sectionResultsVisibility[questionId];
    renderCenterPanel();
  });

  function updateAccessHelp() {
    if (!accessModeSelect || !accessHelp) return;
    accessHelp.textContent = accessModeSelect.value === "internal"
      ? "Solo podrán entrar participantes autenticados."
      : "Comparte el vínculo público de la encuesta para una reunión abierta.";
  }

  accessModeSelect && accessModeSelect.addEventListener("change", async () => {
    updateAccessHelp();
    try {
      await apiPatch(`/api/encuestas/campanas/${instanceId}/draft`, {
        audience_mode: accessModeSelect.value,
        is_public_link_enabled: accessModeSelect.value === "public_link",
      });
    } catch (e) {
      alert("Error al actualizar el acceso: " + e.message);
    }
  });

  /* -------------------------------------------------------------------------
   * Utilities
   * ---------------------------------------------------------------------- */
  function escHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /* -------------------------------------------------------------------------
   * Inject presenter-specific styles
   * ---------------------------------------------------------------------- */
  const style = document.createElement("style");
  style.textContent = `
    .enc-presenter-root { display: flex; flex-direction: column; height: 100%; min-height: 0; }
    .enc-presenter-header {
      display: flex; align-items: center; justify-content: space-between;
      padding: 12px 20px; border-bottom: 1px solid var(--enc-line, #e5e7eb);
      background: var(--enc-surface, #fff); gap: 12px; flex-shrink: 0;
    }
    .enc-presenter-header-left { display: flex; align-items: center; gap: 12px; }
    .enc-presenter-header-right { display: flex; align-items: center; gap: 8px; }
    .enc-presenter-title { font-size: 16px; font-weight: 600; }
    .enc-presenter-badge {
      font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 999px;
      background: var(--enc-muted-bg, #f3f4f6); color: var(--enc-muted, #6b7280);
    }
    .enc-pres-badge-running { background: #dcfce7; color: #166534; }
    .enc-pres-badge-ended   { background: #f3f4f6; color: #6b7280; }
    .enc-presenter-body {
      display: grid; grid-template-columns: 220px 1fr 280px;
      flex: 1; min-height: 0; overflow: hidden;
    }
    .enc-presenter-sidebar, .enc-presenter-results {
      border-right: 1px solid var(--enc-line, #e5e7eb); overflow-y: auto;
      padding: 16px 12px; display: flex; flex-direction: column; gap: 8px;
    }
    .enc-presenter-access { padding: 12px; display: grid; gap: 10px; }
    .enc-presenter-results { border-right: none; border-left: 1px solid var(--enc-line, #e5e7eb); }
    .enc-pres-results-head { display: grid; gap: 8px; }
    .enc-pres-results-controls { display: flex; flex-wrap: wrap; gap: 8px; }
    .enc-presenter-center { padding: 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 20px; }
    .enc-pres-state-msg {
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      gap: 16px; height: 100%; text-align: center; color: var(--enc-muted, #6b7280);
    }
    .enc-pres-state-icon { font-size: 48px; }
    .enc-pres-question-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 4px; }
    .enc-pres-q-item {
      display: grid; grid-template-columns: 24px 1fr; gap: 8px; align-items: start;
      padding: 8px; border-radius: 8px; transition: background 0.15s;
    }
    .enc-pres-q-item:hover { background: var(--enc-hover, #f9fafb); }
    .enc-pres-q-item.is-active { background: var(--enc-accent-bg, #eff6ff); }
    .enc-pres-q-num {
      width: 24px; height: 24px; border-radius: 50%; background: var(--enc-line, #e5e7eb);
      display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 600; flex-shrink: 0;
    }
    .enc-pres-q-item.is-active .enc-pres-q-num { background: var(--enc-accent, #3b82f6); color: #fff; }
    .enc-pres-q-text { font-size: 13px; line-height: 1.4; }
    .enc-pres-current-question { padding: 24px; }
    .enc-pres-question-meta { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
    .enc-pres-q-counter { font-size: 13px; color: var(--enc-muted, #6b7280); }
    .enc-pres-q-type-badge {
      font-size: 11px; padding: 2px 8px; border-radius: 4px;
      background: var(--enc-muted-bg, #f3f4f6); color: var(--enc-muted, #6b7280);
    }
    .enc-pres-q-titulo { font-size: 20px; font-weight: 600; margin: 0 0 8px; }
    .enc-pres-q-desc { font-size: 14px; color: var(--enc-muted, #6b7280); margin: 0; }
    .enc-pres-nav-buttons { display: flex; align-items: center; gap: 8px; }
    .enc-pres-nav-buttons .enc-button:first-child { margin-right: auto; }
    .enc-pres-page-stage.is-presentation-mode {
      padding: 0;
      border: none;
      background: transparent;
      box-shadow: none;
      overflow: hidden;
      min-height: min(70vh, 860px);
    }
    .enc-pres-page-stage.is-presentation-mode .enc-presentation-stage {
      height: 100%;
    }
    .enc-pres-page-stage.is-presentation-mode .enc-presentation-stage-ratio {
      min-height: min(70vh, 860px);
    }
    .enc-pres-results-total { font-size: 14px; margin: 0 0 12px; }
    .enc-pres-bar-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
    .enc-pres-bar-item { display: flex; flex-direction: column; gap: 4px; }
    .enc-pres-bar-label { font-size: 13px; font-weight: 500; }
    .enc-pres-bar-track { height: 12px; border-radius: 6px; background: var(--enc-line, #e5e7eb); overflow: hidden; }
    .enc-pres-bar-fill { height: 100%; background: var(--enc-accent, #3b82f6); border-radius: 6px; transition: width 0.5s ease; }
    .enc-pres-bar-count { font-size: 12px; color: var(--enc-muted, #6b7280); }
    .enc-pres-text-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
    .enc-pres-text-item {
      font-size: 13px; padding: 6px 10px; background: var(--enc-muted-bg, #f9fafb);
      border-radius: 6px; border-left: 3px solid var(--enc-accent, #3b82f6);
    }
    .enc-pres-data-list { display: grid; gap: 8px; }
    .enc-pres-data-row {
      display: grid; grid-template-columns: minmax(0, 1fr) auto auto; gap: 10px;
      align-items: center; padding: 8px 10px; border: 1px solid var(--enc-line, #e5e7eb); border-radius: 10px;
      background: var(--enc-surface, #fff); font-size: 13px;
    }
    .enc-pres-data-row small { color: var(--enc-muted, #6b7280); }
    .enc-presentation-question-tools {
      display: flex; align-items: center; justify-content: flex-end; gap: 10px; margin-bottom: 8px;
    }
    .enc-presentation-question-count {
      font-size: 12px; font-style: italic; color: var(--enc-muted, #6b7280);
    }
    .enc-presentation-eye {
      min-width: 34px; min-height: 34px; padding: 0 10px; border: 1px solid var(--enc-line, #e5e7eb);
      border-radius: 999px; background: var(--enc-surface, #fff); color: var(--enc-ink, #111827); cursor: pointer;
    }
    .enc-presentation-section-results { display: grid; gap: 10px; margin-top: 12px; }
    .enc-presentation-results-card {
      padding: 12px 14px; border: 1px solid var(--enc-line, #e5e7eb); border-radius: 14px; background: #fff;
    }
    .enc-presentation-results-card h5 { margin: 0 0 8px; font-size: 13px; }
    .enc-presentation-results-total { margin: 0 0 8px; color: var(--enc-muted, #6b7280); }
    .enc-presentation-results-list { display: grid; gap: 6px; }
    .enc-presentation-results-copy {
      display: flex; align-items: center; justify-content: space-between; gap: 12px;
    }
    .enc-presentation-results-bar {
      height: 8px; overflow: hidden; border-radius: 999px; background: var(--enc-line, #e5e7eb);
    }
    .enc-presentation-results-bar span {
      display: block; height: 100%; border-radius: inherit; background: var(--enc-accent, #3b82f6); transition: width 0.55s ease;
    }
    .enc-presentation-results-item {
      display: flex; align-items: center; justify-content: space-between; gap: 12px; font-size: 13px;
    }
    .enc-presentation-results-item.is-chart { display: grid; gap: 6px; }
    .enc-pres-results-waiting { font-size: 13px; }
    :fullscreen .enc-presenter-results,
    :fullscreen #enc-pres-results-panel {
      background: #fff;
    }
    :fullscreen.enc-presentation-stage {
      width: 100vw;
      height: 100vh;
      padding: 0;
      margin: 0;
      background: #000;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    :fullscreen.enc-presentation-stage .enc-presentation-stage-ratio {
      width: 100vw;
      height: 100vh;
      max-width: none;
      max-height: none;
      aspect-ratio: auto;
    }
    :fullscreen.enc-presentation-stage .enc-presentation-stage-canvas {
      width: 100%;
      height: 100%;
      border-radius: 0;
      box-shadow: none;
    }
    :fullscreen #enc-pres-results-panel {
      padding: 24px;
      overflow: auto;
    }
    :fullscreen .enc-pres-bar-label { font-size: 20px; }
    :fullscreen .enc-pres-bar-track { height: 18px; }
    :fullscreen .enc-pres-bar-count,
    :fullscreen .enc-pres-data-row,
    :fullscreen .enc-pres-text-item { font-size: 18px; }
    :fullscreen .enc-pres-results-total { font-size: 24px; }
    .enc-button-danger {
      background: #ef4444; color: #fff; border: none; border-radius: 8px;
      padding: 8px 16px; font-size: 14px; font-weight: 500; cursor: pointer;
    }
    .enc-button-danger:hover { background: #dc2626; }
  `;
  document.head.appendChild(style);

})();
