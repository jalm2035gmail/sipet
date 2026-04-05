(function () {
  const root = document.getElementById("enc-response-root");
  if (!root) return;

  function parseBootstrap() {
    try {
      if (window.__ENCUESTA_RESPONSE_BOOTSTRAP) {
        return window.__ENCUESTA_RESPONSE_BOOTSTRAP;
      }
      return JSON.parse(root.dataset.encResponseBootstrap || "{}");
    } catch (error) {
      console.warn("encuestas response bootstrap invalido", error);
      return {};
    }
  }

  const state = {
    session: parseBootstrap(),
    currentStep: 0,
    answers: {},
    timerId: null,
    answeredMessageTimerId: null,
    reviewPayload: null,
    reviewMode: "chart",
    livePageResults: {},
    sectionResultsVisibility: {},
  };
  const searchParams = new URLSearchParams(window.location.search || "");
  const presentMode = searchParams.get("present") === "1";
  let presentationFullscreenRequested = false;
  const apiMAIN = state.session.access_mode === "public" ? "/api/public/encuestas" : "/api/encuestas";

  const startScreen = document.getElementById("enc-response-start");
  const formScreen = document.getElementById("enc-response-form-screen");
  const closedScreen = document.getElementById("enc-response-closed");
  const titleNode = document.getElementById("enc-response-title");
  const descriptionNode = document.getElementById("enc-response-description");
  const headerHtmlNode = document.getElementById("enc-response-header-html");
  const footerHtmlNode = document.getElementById("enc-response-footer-html");
  const orientationWrap = document.getElementById("enc-response-orientation");
  const orientationVerticalButton = document.getElementById("enc-response-orientation-vertical");
  const orientationHorizontalButton = document.getElementById("enc-response-orientation-horizontal");
  const startCopy = document.getElementById("enc-response-start-copy");
  const startMeta = document.getElementById("enc-response-start-meta");
  const eval360Meta = document.getElementById("enc-response-360-meta");
  const startButton = document.getElementById("enc-response-start-btn");
  const progressBar = document.getElementById("enc-response-progress-bar");
  const progressText = document.getElementById("enc-response-progress-text");
  const stepsNode = document.getElementById("enc-response-steps");
  const messageNode = document.getElementById("enc-response-message");
  const stepLabelNode = document.getElementById("enc-response-step-label");
  const sectionTitleNode = document.getElementById("enc-response-section-title");
  const sectionDescriptionNode = document.getElementById("enc-response-section-description");
  const questionsNode = document.getElementById("enc-response-questions");
  const formCard = document.getElementById("enc-response-form-card");
  const prevButton = document.getElementById("enc-response-prev");
  const saveButton = document.getElementById("enc-response-save");
  const nextButton = document.getElementById("enc-response-next");
  const submitButton = document.getElementById("enc-response-submit");
  const presentationNav = document.getElementById("enc-response-presentation-nav");
  const presentationPrevButton = document.getElementById("enc-response-presentation-prev");
  const presentationNextButton = document.getElementById("enc-response-presentation-next");
  const presentationFullscreenButton = document.getElementById("enc-response-presentation-fullscreen");
  const presentationSubmitButton = document.getElementById("enc-response-presentation-submit");
  const formNode = document.getElementById("enc-response-form");
  const closedCopy = document.getElementById("enc-response-closed-copy");
  const closedScore = document.getElementById("enc-response-closed-score");
  const reviewToggleButton = document.getElementById("enc-response-review-toggle");
  const reviewNode = document.getElementById("enc-response-review");
  const reviewModeWrap = document.getElementById("enc-response-review-mode");
  const reviewChartButton = document.getElementById("enc-response-review-chart");
  const reviewDataButton = document.getElementById("enc-response-review-data");
  const quizCard = document.getElementById("enc-response-quiz-card");
  const attemptsMeta = document.getElementById("enc-response-attempts-meta");
  const timerWrap = document.getElementById("enc-response-timer-wrap");
  const timerNode = document.getElementById("enc-response-timer");
  const ORIENTATION_STORAGE_KEY = "encuestas_mobile_orientation";

  function quiz() {
    return state.session.quiz || {};
  }

  function publicationRules() {
    const instance = state.session.instance || {};
    return instance.publication_rules_json || {};
  }

  function liveSettings() {
    const instance = state.session.instance || {};
    return instance.settings_json || {};
  }

  function evaluation360() {
    return state.session.evaluation_360 || {};
  }

  function isRegisteredAccess() {
    return String(state.session.access_mode || "").trim().toLowerCase() !== "public";
  }

  function fetchJSON(url, options) {
    return fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options,
    }).then(async (response) => {
      const text = await response.text();
      const data = text ? JSON.parse(text) : null;
      if (!response.ok) {
        const detail = data && data.detail ? data.detail : data;
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
      }
      return data;
    });
  }

  function setMessage(message, isError) {
    messageNode.textContent = message || "";
    messageNode.style.color = isError ? "#991b1b" : "";
  }

  function sections() {
    return Array.isArray(state.session.sections) ? state.session.sections : [];
  }

  function presentationPages() {
    const rules = publicationRules();
    if (Array.isArray(rules.presentation_pages) && rules.presentation_pages.length) {
      return rules.presentation_pages;
    }
    const settings = liveSettings();
    return Array.isArray(settings.live_pages) ? settings.live_pages : [];
  }

  function isPresentationMode() {
    const rulesMode = String(publicationRules().response_mode || "standard").trim().toLowerCase();
    const liveMode = String(liveSettings().live_mode || "").trim().toLowerCase();
    return (rulesMode === "presentation" || liveMode === "presentation")
      && presentationPages().length > 0;
  }

  function isLivePresentationLocked() {
    const settings = liveSettings();
    return isPresentationMode()
      && String(settings.live_status || "").trim().toLowerCase() === "running"
      && String(settings.live_mode || "").trim().toLowerCase() === "presentation";
  }

  function currentOrientation() {
    return state.mobileOrientation || "horizontal";
  }

  function applyOrientation() {
    const orientation = currentOrientation();
    root.classList.toggle("is-mobile-vertical", orientation === "vertical");
    root.classList.toggle("is-mobile-horizontal", orientation !== "vertical");
    if (orientationVerticalButton) orientationVerticalButton.classList.toggle("is-primary", orientation === "vertical");
    if (orientationHorizontalButton) orientationHorizontalButton.classList.toggle("is-primary", orientation !== "vertical");
  }

  function contentItems() {
    return isPresentationMode() ? presentationPages() : sections();
  }

  function pageShowsTitle(page) {
    return page && page.show_title != null ? page.show_title !== false && String(page.show_title) !== "false" : true;
  }

  function findQuestionById(questionId) {
    const numericId = Number(questionId);
    for (const section of sections()) {
      const found = (section.questions || []).find((question) => Number(question.id) === numericId);
      if (found) return found;
    }
    return null;
  }

  function responseData() {
    return state.session.response || {};
  }

  async function loadResponseReview() {
    if (!isRegisteredAccess() || !responseData().id) return null;
    if (state.reviewPayload) return state.reviewPayload;
    state.reviewPayload = await fetchJSON(`/api/encuestas/respuestas/${responseData().id}/review`);
    return state.reviewPayload;
  }

  function isSubmitted() {
    return responseData().status === "submitted";
  }

  function refreshAnswersFromSession() {
    state.answers = { ...(responseData().answers_json || {}) };
  }

  function showScreen(mode) {
    startScreen.classList.toggle("is-active", mode === "start");
    formScreen.classList.toggle("is-active", mode === "form");
    closedScreen.classList.toggle("is-active", mode === "closed");
  }

  function presentationTarget() {
    return formScreen || formCard || questionsNode || document.documentElement;
  }

  function requestPresentationFullscreen() {
    const target = presentationTarget();
    if (!target || document.fullscreenElement || !target.requestFullscreen) return Promise.resolve();
    return target.requestFullscreen().catch(() => {});
  }

  function togglePresentationFullscreen() {
    if (document.fullscreenElement) {
      return document.exitFullscreen ? document.exitFullscreen().catch(() => {}) : Promise.resolve();
    }
    return requestPresentationFullscreen();
  }

  function maybeEnterPresentationFullscreen(force) {
    if (!isPresentationMode()) return;
    if (!force && !presentMode) return;
    if (!force && presentationFullscreenRequested) return;
    presentationFullscreenRequested = true;
    window.setTimeout(() => {
      requestPresentationFullscreen();
    }, 120);
  }

  function formatDate(value) {
    if (!value) return "Sin fecha";
    return String(value).replace("T", " ").slice(0, 16);
  }

  function updateChrome() {
    const instance = state.session.instance || {};
    const rules = publicationRules();
    const presentationActive = isPresentationMode();
    titleNode.textContent = instance.nombre || "Encuesta";
    descriptionNode.textContent = instance.descripcion || "Responde cada sección y guarda tu progreso cuando lo necesites.";
    root.classList.toggle("is-presentation-mode", presentationActive);
    if (document.body) {
      document.body.classList.toggle("enc-response-presentation-page", presentationActive);
      document.body.classList.toggle("enc-response-presentation-screen", presentationActive && presentMode);
    }
    if (orientationWrap) orientationWrap.hidden = !presentationActive;
    if (presentationNav) presentationNav.hidden = !presentationActive;
    if (presentationFullscreenButton) {
      presentationFullscreenButton.hidden = !presentationActive;
      presentationFullscreenButton.textContent = document.fullscreenElement ? "Salir de pantalla completa" : "Pantalla completa";
    }
    applyOrientation();
    if (formCard) formCard.classList.toggle("is-presentation-stage", presentationActive);
    if (headerHtmlNode) {
      headerHtmlNode.hidden = !String(rules.header_html || "").trim();
      headerHtmlNode.innerHTML = String(rules.header_html || "");
    }
    if (footerHtmlNode) {
      footerHtmlNode.hidden = !String(rules.footer_html || "").trim();
      footerHtmlNode.innerHTML = String(rules.footer_html || "");
    }
    progressBar.style.width = `${responseData().completion_pct || 0}%`;
    progressText.textContent = `${responseData().completion_pct || 0}%`;
    const quizState = quiz();
    if (quizState.is_quiz) {
      quizCard.style.display = "";
      attemptsMeta.innerHTML = [
        `<div><strong>Intento:</strong> ${quizState.current_attempt_number || 1} / ${quizState.max_attempts || 1}</div>`,
        `<div><strong>Estrategia:</strong> ${quizState.attempt_strategy === "last" ? "Último intento" : "Mejor intento"}</div>`,
        quizState.passing_score != null ? `<div><strong>Puntaje aprobatorio:</strong> ${quizState.passing_score}</div>` : "",
      ].filter(Boolean).join("");
      timerWrap.style.display = quizState.timer_seconds ? "" : "none";
    } else {
      quizCard.style.display = "none";
    }
  }

  function syncPresentationRulesFromLive(data) {
    if (!data || data.presentation_mode !== true) return;
    const instance = state.session.instance || {};
    const rules = { ...(instance.publication_rules_json || {}) };
    const livePages = Array.isArray(data.pages) ? data.pages : [];
    const currentPages = Array.isArray(rules.presentation_pages) ? rules.presentation_pages : [];
    let changed = false;

    if (String(rules.response_mode || "").trim().toLowerCase() !== "presentation") {
      rules.response_mode = "presentation";
      changed = true;
    }
    if (livePages.length && JSON.stringify(currentPages) !== JSON.stringify(livePages)) {
      rules.presentation_pages = livePages;
      changed = true;
    }
    if (!changed) return;

    instance.publication_rules_json = rules;
    state.session.instance = instance;
    updateChrome();
    renderSteps();
  }

  function renderStartScreen() {
    const response = responseData();
    const instance = state.session.instance || {};
    const evalState = evaluation360();
    const modeText = state.session.access_mode === "public" ? "enlace público" : "acceso autenticado";
    startCopy.textContent = response.status === "submitted"
      ? "Esta encuesta ya fue enviada. Puedes revisar el estado final a continuación."
      : "Responde la encuesta por secciones. Puedes avanzar, volver y guardar borrador antes de enviarla.";
    if (quiz().is_quiz) {
      startCopy.textContent = response.status === "submitted" && quiz().can_retry
        ? "Tu último intento ya fue enviado. Se habilitó un nuevo intento para continuar con el quiz."
        : `${startCopy.textContent} Este quiz controla intentos y puede incluir límite de tiempo.`;
    }
    startMeta.innerHTML = [
      `<div><strong>Acceso:</strong> ${modeText}</div>`,
      `<div><strong>Disponibilidad:</strong> ${formatDate(instance.schedule_start_at)} a ${formatDate(instance.schedule_end_at)}</div>`,
      response.last_saved_at ? `<div><strong>Último guardado:</strong> ${formatDate(response.last_saved_at)}</div>` : "",
      state.session.draft_exists ? "<div><strong>Borrador detectado:</strong> retomaremos tus respuestas guardadas.</div>" : "",
      quiz().is_quiz ? `<div><strong>Intentos usados:</strong> ${quiz().attempts_used || 0} de ${quiz().max_attempts || 1}</div>` : "",
      quiz().remaining_attempts > 0 ? `<div><strong>Intentos restantes después de este:</strong> ${quiz().remaining_attempts}</div>` : "",
    ].filter(Boolean).join("");
    startButton.textContent = response.status === "submitted"
      ? "Ver cierre"
      : state.session.draft_exists
        ? "Continuar borrador"
        : "Comenzar";
    if (evalState.is_360 && evalState.current && eval360Meta) {
      eval360Meta.style.display = "";
      eval360Meta.innerHTML = [
        `<div><strong>Evaluando a:</strong> ${escapeHtml(evalState.current.evaluatee_name_snapshot || evalState.current.evaluatee_key || "")}</div>`,
        `<div><strong>Relación:</strong> ${escapeHtml(evalState.current.relationship_type || "sin dato")}</div>`,
        `<div><strong>Progreso 360:</strong> ${evalState.completed || 0} de ${evalState.total || 0} relaciones completadas</div>`,
      ].join("");
    } else if (eval360Meta) {
      eval360Meta.style.display = "none";
      eval360Meta.innerHTML = "";
    }
  }

  function formatDuration(totalSeconds) {
    const safe = Math.max(0, Number(totalSeconds) || 0);
    const minutes = String(Math.floor(safe / 60)).padStart(2, "0");
    const seconds = String(safe % 60).padStart(2, "0");
    return `${minutes}:${seconds}`;
  }

  function stopTimer() {
    if (state.timerId) {
      window.clearInterval(state.timerId);
      state.timerId = null;
    }
  }

  async function forceSubmitByTimer() {
    stopTimer();
    try {
      await submitSurvey();
    } catch (error) {
      setMessage(error.message, true);
      renderClosedScreen();
      showScreen("closed");
    }
  }

  function startTimer() {
    stopTimer();
    const quizState = quiz();
    const startedAt = responseData().started_at;
    if (!quizState.is_quiz || !quizState.timer_seconds || !startedAt || isSubmitted()) {
      if (timerNode) timerNode.textContent = "00:00";
      return;
    }
    const deadline = new Date(startedAt).getTime() + (Number(quizState.timer_seconds) * 1000);
    const tick = () => {
      const remaining = Math.max(0, Math.floor((deadline - Date.now()) / 1000));
      timerNode.textContent = formatDuration(remaining);
      if (remaining <= 0) {
        forceSubmitByTimer();
      }
    };
    tick();
    state.timerId = window.setInterval(tick, 1000);
  }

  function renderSteps() {
    const items = contentItems();
    stepsNode.innerHTML = items.map((section, index) => {
      const current = index === state.currentStep ? "is-current" : "";
      const sectionQuestions = isPresentationMode()
        ? (
          Array.isArray(section.layout_sections) && section.layout_sections.length
            ? section.layout_sections.flatMap((item) =>
              String(item.type || "") === "question"
                ? (Array.isArray(item.question_ids) ? item.question_ids : [item.question_id]).map((questionId) => findQuestionById(questionId)).filter(Boolean)
                : []
            )
            : (section.blocks || []).filter((block) => String(block.type || "") === "question").map((block) => findQuestionById(block.question_id)).filter(Boolean)
        )
        : (section.questions || []);
      const answered = sectionQuestions.filter((question) => hasAnswer(question.id)).length;
      return `
        <button type="button" class="enc-response-step ${current}" data-enc-step="${index}">
          <span>${index + 1}. ${section.titulo || section.title || ("Página " + (index + 1))}</span>
          <small>${answered}/${sectionQuestions.length} respondidas</small>
        </button>
      `;
    }).join("");
  }

  function hasAnswer(questionId) {
    const value = state.answers[String(questionId)];
    if (Array.isArray(value)) return value.length > 0;
    return value !== null && value !== undefined && String(value).trim() !== "";
  }

  function isQuestionLocked(question) {
    return isSubmitted();
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function fileMeta(questionId) {
    const value = state.answers[String(questionId)];
    return value && typeof value === "object" ? value : {};
  }

  function matrixValue(questionId, rowKey) {
    const value = state.answers[String(questionId)];
    if (!value || typeof value !== "object" || Array.isArray(value)) return "";
    return String(value[rowKey] || "");
  }

  function rankingValue(questionId) {
    const value = state.answers[String(questionId)];
    return Array.isArray(value) ? value : [];
  }

  function renderMatrix(question, mode) {
    const rows = Array.isArray(question.options) ? question.options : [];
    const columns = Array.isArray((question.config_json || {}).columns) ? question.config_json.columns : [];
    const leftLabel = escapeHtml((question.config_json || {}).left_label || "");
    const rightLabel = escapeHtml((question.config_json || {}).right_label || "");
    const locked = isQuestionLocked(question);
    return `
      <div class="enc-response-matrix">
        ${leftLabel || rightLabel ? `<div class="enc-question-meta">${leftLabel}${leftLabel && rightLabel ? " / " : ""}${rightLabel}</div>` : ""}
        <table class="enc-table">
          <thead>
            <tr>
              <th>Ítem</th>
              ${columns.map((column) => `<th>${escapeHtml(column.label)}</th>`).join("")}
            </tr>
          </thead>
          <tbody>
            ${rows.map((row) => `
              <tr>
                <td>${escapeHtml(row.label)}</td>
                ${columns.map((column) => `
                  <td>
                    <input
                      type="radio"
                      name="enc-matrix-${question.id}-${escapeHtml(row.value)}"
                      data-enc-matrix="${question.id}"
                      data-row="${escapeHtml(row.value)}"
                      value="${escapeHtml(column.value)}"
                      ${matrixValue(question.id, row.value) === String(column.value) ? "checked" : ""}
                      ${locked ? "disabled" : ""}
                    >
                  </td>
                `).join("")}
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;
  }

  function renderRanking(question) {
    const current = rankingValue(question.id);
    const options = Array.isArray(question.options) ? question.options : [];
    const locked = isQuestionLocked(question);
    const ranked = current.map((value) => options.find((option) => String(option.value) === String(value))).filter(Boolean);
    const available = options.filter((option) => !current.includes(option.value));
    const all = ranked.concat(available);
    return `
      <div class="enc-response-ranking" data-enc-ranking="${question.id}">
        ${all.map((option, index) => {
          const isRanked = index < ranked.length;
          return `
            <div class="enc-question-meta" style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
              <span style="min-width:24px;font-weight:700;">${isRanked ? index + 1 : "-"}</span>
              <span style="flex:1;">${escapeHtml(option.label)}</span>
              <button type="button" class="enc-mini-btn" data-enc-rank-up="${question.id}" data-value="${escapeHtml(option.value)}" ${locked ? "disabled" : ""}>↑</button>
              <button type="button" class="enc-mini-btn" data-enc-rank-down="${question.id}" data-value="${escapeHtml(option.value)}" ${locked ? "disabled" : ""}>↓</button>
            </div>
          `;
        }).join("")}
      </div>
    `;
  }

  function renderQuestion(question) {
    const value = state.answers[String(question.id)];
    const required = question.is_required ? '<span class="enc-response-required">*</span>' : "";
    const options = Array.isArray(question.options) ? question.options : [];
    const locked = isQuestionLocked(question);
    const disabledAttr = locked ? "disabled" : "";
    const readonlyAttr = locked ? "readonly" : "";
    let fieldHtml = "";
    if (question.question_type === "long_text") {
      fieldHtml = `<textarea class="enc-input enc-textarea" data-enc-question="${question.id}" rows="5" ${readonlyAttr}>${escapeHtml(value || "")}</textarea>`;
    } else if (["short_text", "word_cloud"].includes(question.question_type)) {
      fieldHtml = `<input class="enc-input" data-enc-question="${question.id}" type="text" value="${escapeHtml(value || "")}" ${readonlyAttr}>`;
    } else if (question.question_type === "multiple_choice") {
      fieldHtml = options.map((option) => {
        const checked = Array.isArray(value) && value.includes(option.value) ? "checked" : "";
        return `<label class="enc-preview-choice"><input type="checkbox" data-enc-question="${question.id}" value="${escapeHtml(option.value)}" ${checked} ${disabledAttr}> <span>${escapeHtml(option.label)}</span></label>`;
      }).join("");
    } else if (question.question_type === "ranking") {
      fieldHtml = renderRanking(question);
    } else if (["matrix", "likert_scale", "semantic_differential"].includes(question.question_type)) {
      fieldHtml = renderMatrix(question, question.question_type);
    } else if (["single_choice", "live_poll_single_choice", "yes_no", "true_false", "quiz_single_choice", "dropdown", "image_choice"].includes(question.question_type)) {
      if (question.question_type === "dropdown") {
        fieldHtml = `
          <select class="enc-input enc-select" data-enc-question="${question.id}" ${disabledAttr}>
            <option value="">Selecciona una opción</option>
            ${options.map((option) => `<option value="${escapeHtml(option.value)}" ${String(value || "") === String(option.value) ? "selected" : ""}>${escapeHtml(option.label)}</option>`).join("")}
          </select>
        `;
      } else if (question.question_type === "image_choice") {
        fieldHtml = `<div class="enc-response-image-choice">${options.map((option) => {
          const checked = String(value || "") === String(option.value) ? "checked" : "";
          return `<label class="enc-preview-choice" style="display:flex;align-items:center;gap:12px;padding:12px;border:1px solid rgba(15,23,42,0.1);border-radius:14px;"><input type="radio" name="enc-question-${question.id}" data-enc-question="${question.id}" value="${escapeHtml(option.value)}" ${checked} ${disabledAttr}> <span>${escapeHtml(option.label)}</span></label>`;
        }).join("")}</div>`;
      } else {
      fieldHtml = options.map((option) => {
        const checked = String(value || "") === String(option.value) ? "checked" : "";
        return `<label class="enc-preview-choice"><input type="radio" name="enc-question-${question.id}" data-enc-question="${question.id}" value="${escapeHtml(option.value)}" ${checked} ${disabledAttr}> <span>${escapeHtml(option.label)}</span></label>`;
      }).join("");
      }
    } else if (["scale_1_5", "live_scale_1_5", "nps_0_10"].includes(question.question_type)) {
      fieldHtml = `<div class="enc-response-scale">${options.map((option) => {
        const active = String(value || "") === String(option.value) ? "is-active" : "";
        return `<button type="button" class="enc-preview-scale ${active}" data-enc-scale="${question.id}" data-value="${escapeHtml(option.value)}" ${disabledAttr}>${escapeHtml(option.label)}</button>`;
      }).join("")}</div>`;
    } else if (question.question_type === "slider") {
      const config = question.config_json || {};
      const currentValue = value == null || value === "" ? String(config.min ?? 0) : String(value);
      fieldHtml = `
        <div>
          <input class="enc-input" data-enc-question="${question.id}" type="range" min="${escapeHtml(config.min ?? 0)}" max="${escapeHtml(config.max ?? 10)}" step="${escapeHtml(config.step ?? 1)}" value="${escapeHtml(currentValue)}" ${disabledAttr}>
          <div class="enc-question-meta">${escapeHtml(config.min_label || "Mínimo")} · <strong>${escapeHtml(currentValue)}</strong> · ${escapeHtml(config.max_label || "Máximo")}</div>
        </div>
      `;
    } else if (question.question_type === "date") {
      fieldHtml = `<input class="enc-input" data-enc-question="${question.id}" type="date" value="${escapeHtml(value || "")}" ${disabledAttr}>`;
    } else if (question.question_type === "time") {
      fieldHtml = `<input class="enc-input" data-enc-question="${question.id}" type="time" value="${escapeHtml(value || "")}" ${disabledAttr}>`;
    } else if (question.question_type === "file_upload") {
      const file = fileMeta(question.id);
      fieldHtml = `
        <div>
          <input class="enc-input" data-enc-file="${question.id}" type="file" accept="${escapeHtml((question.config_json || {}).accept || '*/*')}" ${disabledAttr}>
          <div class="enc-question-meta">${file.name ? `Archivo seleccionado: ${escapeHtml(file.name)}` : "Sin archivo seleccionado."}</div>
        </div>
      `;
    } else {
      fieldHtml = `<input class="enc-input" data-enc-question="${question.id}" type="text" value="${escapeHtml(value || "")}" ${readonlyAttr}>`;
    }
    return `
      <article class="enc-preview-question enc-response-question">
        <h4>${escapeHtml(question.titulo)} ${required}</h4>
        <p>${escapeHtml(question.descripcion || "")}</p>
        <div class="enc-preview-field">${fieldHtml}</div>
        ${locked ? '<p class="enc-response-question-answered">Pregunta respondida</p>' : ''}
      </article>
    `;
  }

  function renderPresentationBlock(block) {
    const widthClass = String(block.width || "full") === "half" ? "is-half" : "is-full";
    if (String(block.type || "") === "question") {
      const question = findQuestionById(block.question_id);
      if (!question) {
        return `<div class="enc-presentation-item ${widthClass}"><div class="enc-placeholder">Pregunta no disponible.</div></div>`;
      }
      return `<div class="enc-presentation-item ${widthClass}">${renderQuestion(question)}</div>`;
    }
    if (String(block.type || "") === "image") {
      return `<div class="enc-presentation-item ${widthClass}">${renderImageSection(block)}</div>`;
    }
    return `<div class="enc-presentation-item ${widthClass}"><article class="enc-card enc-response-card enc-response-richtext">${renderEmbeddedSectionHtml(block)}</article></div>`;
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
      const bodyClass = body && body.className ? ` class="${escapeHtml(body.className)}"` : "";
      const bodyStyle = body && body.getAttribute("style") ? ` style="${escapeHtml(body.getAttribute("style"))}"` : "";
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
    const inputEffect = escapeHtml(String((section && section.js_input_effect) || "none"));
    const highlightEffect = escapeHtml(String((section && section.js_highlight_effect) || "none"));
    const outputEffect = escapeHtml(String((section && section.js_output_effect) || "none"));
    const inputCode = jsInput ? escapeHtml(encodeURIComponent(jsInput)) : "";
    const highlightCode = jsHighlight ? escapeHtml(encodeURIComponent(jsHighlight)) : "";
    const outputCode = jsOutput ? escapeHtml(encodeURIComponent(jsOutput)) : "";
    return `<div class="enc-embedded-runtime" data-enc-js-input-effect="${inputEffect}" data-enc-js-highlight-effect="${highlightEffect}" data-enc-js-output-effect="${outputEffect}" data-enc-js-input="${inputCode}" data-enc-js-highlight="${highlightCode}" data-enc-js-output="${outputCode}">${normalized.css ? `<style>${normalized.css}</style>` : ""}${normalized.html}</div>`;
  }

  function renderImageSection(section) {
    const imageUrl = escapeHtml(section.image_url || "");
    const imageFit = escapeHtml(section.image_fit || "cover");
    const imageAlt = escapeHtml(section.image_alt || "");
    if (!imageUrl) return '<div class="enc-placeholder">Imagen no configurada.</div>';
    return `<div class="enc-presentation-image-surface" style="background-image:url('${imageUrl}');background-size:${imageFit};background-position:center;background-repeat:no-repeat;"><img class="enc-presentation-image ${imageFit === "contain" ? "is-contain" : "is-cover"}" src="${imageUrl}" alt="${imageAlt}"></div>`;
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
          console.warn("encuestas js entrada invalido", error);
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
              console.warn("encuestas js destacar invalido", error);
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
            console.warn("encuestas js salida invalido", error);
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

  function renderPresentationLayoutSection(section, page) {
    const type = String((section && section.type) || "html");
    if (type === "question") {
      const questions = (Array.isArray(section.question_ids) ? section.question_ids : [section.question_id])
        .map((questionId) => findQuestionById(questionId))
        .filter(Boolean);
      if (!questions.length) return `<article class="enc-presentation-layout-slot"><div class="enc-placeholder">Pregunta no disponible.</div></article>`;
      const firstQuestionId = questions[0] ? String(questions[0].id) : "";
      const resultsMap = state.livePageResults || {};
      const sectionResult = firstQuestionId ? resultsMap[firstQuestionId] : null;
      const totalResponses = sectionResult && sectionResult.total_responses != null ? Number(sectionResult.total_responses) : 0;
      const isOpen = Boolean(firstQuestionId && state.sectionResultsVisibility[firstQuestionId]);
      return `
        <article class="enc-presentation-layout-slot">
          <div class="enc-presentation-question-tools">
            <span class="enc-presentation-question-count"><span data-enc-animate-count="${totalResponses}" data-enc-count-singular=" respuesta" data-enc-count-plural=" respuestas">0 respuestas</span></span>
            ${firstQuestionId ? `<button type="button" class="enc-presentation-eye" data-enc-toggle-section-results="${firstQuestionId}" aria-label="${isOpen ? "Ocultar respuestas" : "Ver respuestas"}" title="${isOpen ? "Ocultar respuestas" : "Ver respuestas"}">${isOpen ? "🙈" : "👁"}</button>` : ""}
          </div>
          ${questions.map((question) => renderQuestion(question)).join("")}
          ${isOpen ? renderPresentationSectionResults(questions) : ""}
        </article>
      `;
    }
    if (type === "image") {
      return `<article class="enc-presentation-layout-slot">${renderImageSection(section)}</article>`;
    }
    const html = renderEmbeddedSectionHtml(section);
    return `<article class="enc-presentation-layout-slot">${html ? `<article class="enc-card enc-response-card enc-response-richtext">${html}</article>` : `<div class="enc-placeholder">Sección vacía.</div>`}</article>`;
  }

  function renderPresentationSectionResults(questions) {
    const blocks = questions.map((question) => {
      const result = (state.livePageResults || {})[String(question.id)];
      if (!result) return "";
      const total = Number(result.total_responses || 0);
      let body = `<p class="enc-presentation-results-total"><em><span data-enc-animate-count="${total}" data-enc-count-singular=" respuesta" data-enc-count-plural=" respuestas">0 respuestas</span></em></p>`;
      if (question.options && question.options.length) {
        body += renderPresentationResultOptions(question, result);
      } else if (result.texts && result.texts.length) {
        body += `<div class="enc-presentation-results-list">${result.texts.slice(0, 5).map((text) => `<div class="enc-presentation-results-item"><span>${escapeHtml(text)}</span></div>`).join("")}</div>`;
      }
      return `<div class="enc-presentation-results-card"><h5>${escapeHtml(question.titulo || "")}</h5>${body}</div>`;
    }).filter(Boolean).join("");
    return blocks ? `<div class="enc-presentation-section-results">${blocks}</div>` : "";
  }

  function resultChartType(question) {
    const type = String((((question || {}).config_json || {}).result_chart_type) || "bar").trim().toLowerCase();
    return ["bar", "donut", "list"].includes(type) ? type : "bar";
  }

  function resultPalette(index) {
    const colors = ["#2563eb", "#14b8a6", "#f97316", "#8b5cf6", "#e11d48", "#f59e0b"];
    return colors[index % colors.length];
  }

  function renderPresentationResultOptions(question, result) {
    const options = Array.isArray(question.options) ? question.options : [];
    const counts = result.counts || {};
    const total = Number(result.total_responses || 0);
    const entries = options.map((option, index) => {
      const count = Number(counts[String(option.value)] || 0);
      const percent = total > 0 ? Math.round((count / total) * 100) : 0;
      return {
        label: option.label || String(option.value),
        count,
        percent,
        color: resultPalette(index),
      };
    });
    const chartType = resultChartType(question);
    if (chartType === "list") {
      return `<div class="enc-presentation-results-list is-list">${entries.map((entry) => `
        <div class="enc-presentation-results-item is-list">
          <span>${escapeHtml(entry.label)}</span>
          <strong><span data-enc-animate-count="${entry.count}">0</span> <small>${entry.percent}%</small></strong>
        </div>
      `).join("")}</div>`;
    }
    if (chartType === "donut") {
      let offset = 0;
      const stops = entries.map((entry) => {
        const start = offset;
        offset += entry.percent;
        return `${entry.color} ${start}% ${offset}%`;
      });
      const donut = stops.length ? stops.join(", ") : "#e5e7eb 0% 100%";
      return `
        <div class="enc-presentation-results-donut-wrap">
          <div class="enc-presentation-results-donut" style="background:conic-gradient(${donut});">
            <div class="enc-presentation-results-donut-core">
              <strong data-enc-animate-count="${total}">0</strong>
              <span>respuestas</span>
            </div>
          </div>
          <div class="enc-presentation-results-legend">${entries.map((entry) => `
            <div class="enc-presentation-results-legend-item">
              <span class="enc-presentation-results-swatch" style="background:${entry.color};"></span>
              <span>${escapeHtml(entry.label)}</span>
              <strong><span data-enc-animate-count="${entry.count}">0</span> <small>${entry.percent}%</small></strong>
            </div>
          `).join("")}</div>
        </div>
      `;
    }
    const maxCount = Math.max(...entries.map((entry) => entry.count), 1);
    return `<div class="enc-presentation-results-list">${entries.map((entry) => {
      const width = Math.round((entry.count / maxCount) * 100);
      return `
        <div class="enc-presentation-results-item is-chart">
          <div class="enc-presentation-results-copy">
            <span>${escapeHtml(entry.label)}</span>
            <strong><span data-enc-animate-count="${entry.count}">0</span> <small>${entry.percent}%</small></strong>
          </div>
          <div class="enc-presentation-results-bar"><span data-enc-animate-width="${width}" style="width:0%;background:${entry.color};"></span></div>
        </div>
      `;
    }).join("")}</div>`;
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

  function renderPresentationPage(page) {
    const bgLayers = [];
    const title = String((page && page.title) || "").trim();
    const showTitle = pageShowsTitle(page);
    const footerText = String((page && page.footer_text) || "").trim();
    if (page && page.bg_image_url) {
      bgLayers.push(`linear-gradient(180deg, rgba(15,23,42,0.08), rgba(15,23,42,0.14)), url("${escapeHtml(page.bg_image_url)}") center / cover`);
    }
    bgLayers.push(escapeHtml((page && page.bg_color) || "#ffffff"));
    const layoutSections = Array.isArray(page && page.layout_sections) ? page.layout_sections : [];
    const sectionCount = Number(page && page.section_count) === 4 ? 4 : Number(page && page.section_count) === 2 ? 2 : 1;
    if (layoutSections.length) {
      return `
        <div class="enc-presentation-stage">
          <div class="enc-presentation-stage-ratio">
            <div class="enc-presentation-stage-canvas" style="background:${bgLayers.join(", ")};">
              <div class="enc-presentation-layout">
                ${showTitle && title ? `<header class="enc-presentation-layout-header"><h1>${escapeHtml(title)}</h1></header>` : ""}
                <div class="enc-presentation-layout-body is-sections-${sectionCount}">
                  ${layoutSections.map((section) => renderPresentationLayoutSection(section, page)).join("")}
                </div>
                ${footerText ? `<footer class="enc-presentation-layout-footer" style="background:${escapeHtml((page && page.footer_color) || "#0f172a")};"><span>${escapeHtml(footerText)}</span></footer>` : ""}
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

  function renderCurrentStep() {
    const items = contentItems();
    const current = items[state.currentStep];
    if (!current) {
      questionsNode.innerHTML = '<div class="enc-placeholder">No hay contenido disponible.</div>';
      return;
    }
    stepLabelNode.textContent = `Paso ${state.currentStep + 1} de ${items.length}`;
    sectionTitleNode.textContent = current.titulo || current.title || `Página ${state.currentStep + 1}`;
    sectionDescriptionNode.textContent = current.descripcion || current.description || "";
    if (isPresentationMode()) {
      sectionTitleNode.hidden = !pageShowsTitle(current);
      sectionDescriptionNode.hidden = !pageShowsTitle(current) || !(current.descripcion || current.description);
    } else {
      sectionTitleNode.hidden = false;
      sectionDescriptionNode.hidden = !(current.descripcion || current.description);
    }
    questionsNode.innerHTML = isPresentationMode()
      ? renderPresentationPage(current)
      : (current.questions || []).map(renderQuestion).join("");
    hydrateEmbeddedRuntime(questionsNode);
    animatePresentationResultBars(questionsNode);
    const liveLocked = isLivePresentationLocked();
    prevButton.style.display = state.currentStep === 0 ? "none" : "";
    nextButton.style.display = state.currentStep >= items.length - 1 ? "none" : "";
    submitButton.style.display = state.currentStep >= items.length - 1 ? "" : "none";
    prevButton.disabled = liveLocked;
    nextButton.disabled = liveLocked;
    submitButton.disabled = false;
    if (presentationPrevButton) {
      presentationPrevButton.hidden = !isPresentationMode() || state.currentStep === 0;
      presentationPrevButton.disabled = liveLocked;
    }
    if (presentationNextButton) {
      presentationNextButton.hidden = !isPresentationMode() || state.currentStep >= items.length - 1;
      presentationNextButton.disabled = liveLocked;
    }
    if (presentationSubmitButton) {
      presentationSubmitButton.hidden = !isPresentationMode() || state.currentStep < items.length - 1 || isSubmitted();
      presentationSubmitButton.disabled = false;
    }
    stepsNode.querySelectorAll("[data-enc-step]").forEach((button) => {
      button.disabled = liveLocked;
    });
  }

  function validateCurrentStep() {
    const current = contentItems()[state.currentStep];
    if (!current) return true;
    const questionList = isPresentationMode()
      ? (
        Array.isArray(current.layout_sections) && current.layout_sections.length
          ? current.layout_sections.flatMap((section) =>
            String(section.type || "") === "question"
              ? (Array.isArray(section.question_ids) ? section.question_ids : [section.question_id]).map((questionId) => findQuestionById(questionId)).filter(Boolean)
              : []
          )
          : (current.blocks || []).filter((block) => String(block.type || "") === "question").map((block) => findQuestionById(block.question_id)).filter(Boolean)
      )
      : (current.questions || []);
    for (const question of questionList) {
      if (!question.is_required) continue;
      if (!hasAnswer(question.id)) {
        setMessage(`La pregunta "${question.titulo}" es obligatoria.`, true);
        return false;
      }
    }
    setMessage("", false);
    return true;
  }

  function collectCurrentInputs() {
    questionsNode.querySelectorAll("[data-enc-question]").forEach((node) => {
      const questionId = String(node.dataset.encQuestion);
      if (node.type === "checkbox") {
        const group = Array.from(questionsNode.querySelectorAll(`[data-enc-question="${questionId}"]`));
        state.answers[questionId] = group.filter((item) => item.checked).map((item) => item.value);
      } else if (node.type === "radio") {
        if (node.checked) state.answers[questionId] = node.value;
        else if (!questionsNode.querySelector(`[data-enc-question="${questionId}"]:checked`)) state.answers[questionId] = "";
      } else {
        state.answers[questionId] = node.value;
      }
    });
    questionsNode.querySelectorAll("[data-enc-matrix]").forEach((node) => {
      const questionId = String(node.dataset.encMatrix);
      const row = String(node.dataset.row);
      if (!state.answers[questionId] || typeof state.answers[questionId] !== "object" || Array.isArray(state.answers[questionId])) {
        state.answers[questionId] = {};
      }
      if (node.checked) state.answers[questionId][row] = node.value;
    });
  }

  async function saveDraft(message) {
    collectCurrentInputs();
    const payload = await fetchJSON(`${apiMAIN}/respuestas/${responseData().id}/save`, {
      method: "PUT",
      body: JSON.stringify({ answers: state.answers }),
    });
    state.session = payload;
    refreshAnswersFromSession();
    updateChrome();
    renderSteps();
    renderCurrentStep();
    startTimer();
    setMessage(message || "Borrador guardado.", false);
  }

  async function submitSurvey(options) {
    const stayOnPage = Boolean(options && options.stayOnPage);
    collectCurrentInputs();
    const payload = await fetchJSON(`${apiMAIN}/respuestas/${responseData().id}/submit`, {
      method: "POST",
      body: JSON.stringify({ answers: state.answers }),
    });
    state.session = payload;
    refreshAnswersFromSession();
    updateChrome();
    stopTimer();
    if (stayOnPage) {
      renderSteps();
      renderCurrentStep();
      setMessage("Respuesta enviada", false);
      return;
    }
    renderClosedScreen();
    showScreen("closed");
  }

  function renderClosedScreen() {
    const response = responseData();
    const metrics = response.metrics_json || {};
    closedCopy.textContent = response.status === "submitted"
      ? `Tu respuesta fue enviada el ${formatDate(response.submitted_at)}. Gracias por completar la encuesta.`
      : "La captura ya no está disponible.";
    closedScore.textContent = quiz().is_quiz
      ? [
          response.total_score != null ? `Puntaje: ${response.total_score}.` : "",
          metrics.evaluation_status ? `Resultado: ${metrics.evaluation_status}.` : "",
          quiz().best_attempt && quiz().attempt_strategy === "best"
            ? `Mejor intento registrado: ${quiz().best_attempt.score_value}.`
            : "",
        ].filter(Boolean).join(" ")
      : "";
    if (reviewToggleButton) {
      const hasAnswers = Object.keys(response.answers_json || {}).length > 0;
      reviewToggleButton.hidden = !(isRegisteredAccess() && hasAnswers);
      reviewToggleButton.textContent = reviewNode && !reviewNode.hidden ? "Ocultar respuestas" : "Ver respuestas";
    }
    if (reviewModeWrap) reviewModeWrap.hidden = reviewNode ? reviewNode.hidden : true;
    if (reviewNode && reviewNode.hidden === false) {
      renderResponseReview();
    }
  }

  function navigatePrev() {
    if (isLivePresentationLocked()) {
      showLiveNavigationLockedMessage();
      return;
    }
    collectCurrentInputs();
    if (state.currentStep > 0) {
      state.currentStep -= 1;
      renderSteps();
      renderCurrentStep();
    }
  }

  function isEditableTarget(target) {
    if (!(target instanceof Element)) return false;
    if (target.closest('input, textarea, select, [contenteditable="true"]')) return true;
    return false;
  }

  function showAnsweredFeedback() {
    setMessage("Pregunta respondida", false);
    window.clearTimeout(state.answeredMessageTimerId);
    state.answeredMessageTimerId = window.setTimeout(() => {
      if (messageNode.textContent === "Pregunta respondida") {
        setMessage("", false);
      }
    }, 1800);
  }

  function showLiveNavigationLockedMessage() {
    setMessage("La sesión en vivo está controlada por el presentador.", false);
  }

  function finalizeQuestionAnswer(questionId) {
    if (!hasAnswer(questionId)) return;
    renderSteps();
    renderCurrentStep();
    showAnsweredFeedback();
  }

  async function navigateNext() {
    if (isLivePresentationLocked()) {
      showLiveNavigationLockedMessage();
      return;
    }
    collectCurrentInputs();
    if (!validateCurrentStep()) return;
    await saveDraft("Progreso guardado.");
    if (state.currentStep < contentItems().length - 1) {
      state.currentStep += 1;
      renderSteps();
      renderCurrentStep();
    }
  }

  function renderResponseReview() {
    if (!reviewNode) return;
    const payload = state.reviewPayload || { questions: [] };
    const questions = Array.isArray(payload.questions) ? payload.questions : [];
    if (!questions.length) {
      reviewNode.hidden = true;
      if (reviewModeWrap) reviewModeWrap.hidden = true;
      return;
    }
    reviewNode.hidden = false;
    if (reviewModeWrap) reviewModeWrap.hidden = false;
    if (reviewChartButton) reviewChartButton.classList.toggle("is-primary", state.reviewMode === "chart");
    if (reviewDataButton) reviewDataButton.classList.toggle("is-primary", state.reviewMode === "data");
    reviewNode.innerHTML = questions.map((question) => `
      <article class="enc-response-review-item">
        <strong>${escapeHtml(question.titulo || "Pregunta")}</strong>
        <p>${escapeHtml(question.descripcion || "")}</p>
        ${state.reviewMode === "chart" ? renderReviewChart(question) : renderReviewData(question)}
      </article>
    `).join("");
  }

  function renderReviewChart(question) {
    const counts = question.counts || {};
    const options = Array.isArray(question.options) ? question.options : [];
    const entries = options.length
      ? options.map((option) => ({
          label: option.label || String(option.value),
          count: counts[String(option.value)] || 0,
        }))
      : Object.entries(counts).map(([label, count]) => ({ label, count }));
    if (entries.length) {
      const max = Math.max(...entries.map((entry) => entry.count), 1);
      return `<div class="enc-response-review-bars">${entries.map((entry) => `
        <div class="enc-response-review-bar-row">
          <span>${escapeHtml(entry.label)}</span>
          <div class="enc-response-review-bar-track"><div class="enc-response-review-bar-fill" style="width:${Math.round((entry.count / max) * 100)}%"></div></div>
          <strong>${entry.count}</strong>
        </div>
      `).join("")}</div>`;
    }
    const texts = Array.isArray(question.texts) ? question.texts : [];
    if (texts.length) {
      return `<div class="enc-response-review-cloud">${texts.map((text) => `<span class="enc-pill is-draft">${escapeHtml(text)}</span>`).join("")}</div>`;
    }
    return '<p class="enc-question-meta">Sin datos para graficar.</p>';
  }

  function renderReviewData(question) {
    const counts = question.counts || {};
    const rows = Array.isArray(question.data_rows) ? question.data_rows : [];
    const options = Array.isArray(question.options) ? question.options : [];
    if (options.length || Object.keys(counts).length) {
      const entries = options.length
        ? options.map((option) => ({
            label: option.label || String(option.value),
            count: counts[String(option.value)] || 0,
          }))
        : Object.entries(counts).map(([label, count]) => ({ label, count }));
      return `<div class="enc-stack">${entries.map((entry) => `<div class="enc-question-meta"><strong>${escapeHtml(entry.label)}:</strong> ${entry.count}</div>`).join("")}</div>`;
    }
    if (rows.length) {
      return `<div class="enc-stack">${rows.slice(0, 20).map((row) => `<div class="enc-question-meta">${escapeHtml(String(row))}</div>`).join("")}</div>`;
    }
    return '<p class="enc-question-meta">Sin datos disponibles.</p>';
  }

  function bindEvents() {
    startButton.addEventListener("click", () => {
      if (isSubmitted()) {
        renderClosedScreen();
        showScreen("closed");
        return;
      }
      showScreen("form");
      renderCurrentStep();
      maybeEnterPresentationFullscreen(true);
      startTimer();
    });

    prevButton.addEventListener("click", async () => {
      navigatePrev();
    });

    nextButton.addEventListener("click", async () => {
      await navigateNext();
    });

    if (presentationPrevButton) {
      presentationPrevButton.addEventListener("click", async () => {
        navigatePrev();
      });
    }

    if (presentationNextButton) {
      presentationNextButton.addEventListener("click", async () => {
        try {
          await navigateNext();
        } catch (error) {
            setMessage(error.message, true);
        }
      });
    }

    if (presentationFullscreenButton) {
      presentationFullscreenButton.addEventListener("click", async () => {
        await togglePresentationFullscreen();
        updateChrome();
      });
    }

    if (presentationSubmitButton) {
      presentationSubmitButton.addEventListener("click", async () => {
        try {
          if (!validateCurrentStep()) return;
          await submitSurvey({ stayOnPage: true });
        } catch (error) {
          setMessage(error.message, true);
        }
      });
    }

    document.addEventListener("fullscreenchange", function () {
      updateChrome();
    });

    document.addEventListener("keydown", async (event) => {
      if (!isPresentationMode()) return;
      if (!formScreen.classList.contains("is-active")) return;
      if (isSubmitted()) return;
      if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
      if (isEditableTarget(event.target)) return;
      if (isLivePresentationLocked()) {
        if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
          event.preventDefault();
          showLiveNavigationLockedMessage();
        }
        return;
      }

      if (event.key === "ArrowLeft") {
        event.preventDefault();
        navigatePrev();
        return;
      }

      if (event.key === "ArrowRight") {
        event.preventDefault();
        try {
          await navigateNext();
        } catch (error) {
          setMessage(error.message, true);
        }
      }
    });

    saveButton.addEventListener("click", async () => {
      try {
        await saveDraft("Progreso guardado.");
      } catch (error) {
        setMessage(error.message, true);
      }
    });

    formNode.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        if (!validateCurrentStep()) return;
        await submitSurvey({ stayOnPage: isPresentationMode() });
      } catch (error) {
        setMessage(error.message, true);
      }
    });

    if (reviewToggleButton) {
      reviewToggleButton.addEventListener("click", async function () {
        if (!reviewNode) return;
        const willShow = reviewNode.hidden;
        if (willShow) {
          try {
            await loadResponseReview();
          } catch (error) {
            setMessage(error.message, true);
            return;
          }
          renderResponseReview();
          reviewNode.hidden = false;
          if (reviewModeWrap) reviewModeWrap.hidden = false;
        } else {
          reviewNode.hidden = true;
          if (reviewModeWrap) reviewModeWrap.hidden = true;
        }
        reviewToggleButton.textContent = willShow ? "Ocultar respuestas" : "Ver respuestas";
      });
    }

    if (reviewChartButton) {
      reviewChartButton.addEventListener("click", function () {
        state.reviewMode = "chart";
        renderResponseReview();
      });
    }

    if (reviewDataButton) {
      reviewDataButton.addEventListener("click", function () {
        state.reviewMode = "data";
        renderResponseReview();
      });
    }

    questionsNode.addEventListener("click", function (event) {
      const button = event.target.closest("[data-enc-toggle-section-results]");
      if (!button) return;
      const questionId = String(button.dataset.encToggleSectionResults || "");
      if (!questionId) return;
      state.sectionResultsVisibility[questionId] = !state.sectionResultsVisibility[questionId];
      renderCurrentStep();
    });

    stepsNode.addEventListener("click", async (event) => {
      const button = event.target.closest("[data-enc-step]");
      if (!button) return;
      if (isLivePresentationLocked()) {
        showLiveNavigationLockedMessage();
        return;
      }
      collectCurrentInputs();
      state.currentStep = Number(button.dataset.encStep);
      renderSteps();
      renderCurrentStep();
    });

    questionsNode.addEventListener("click", (event) => {
      const button = event.target.closest("[data-enc-scale]");
      if (!button) return;
      const questionId = String(button.dataset.encScale);
      if (hasAnswer(questionId)) return;
      state.answers[questionId] = button.dataset.value;
      finalizeQuestionAnswer(questionId);
    });

    questionsNode.addEventListener("click", (event) => {
      const upButton = event.target.closest("[data-enc-rank-up]");
      const downButton = event.target.closest("[data-enc-rank-down]");
      if (!upButton && !downButton) return;
      const button = upButton || downButton;
      const questionId = String(button.dataset.encRankUp || button.dataset.encRankDown);
      if (hasAnswer(questionId)) return;
      const value = String(button.dataset.value || "");
      const current = rankingValue(questionId);
      const ordered = current.slice();
      const currentIndex = ordered.indexOf(value);
      if (currentIndex === -1) {
        ordered.push(value);
      } else {
        const nextIndex = upButton ? currentIndex - 1 : currentIndex + 1;
        if (nextIndex < 0 || nextIndex >= ordered.length) return;
        const temp = ordered[currentIndex];
        ordered[currentIndex] = ordered[nextIndex];
        ordered[nextIndex] = temp;
      }
      state.answers[questionId] = ordered;
      finalizeQuestionAnswer(questionId);
    });

    questionsNode.addEventListener("change", (event) => {
      const input = event.target.closest("[data-enc-question], [data-enc-matrix]");
      if (!input) return;
      if (input.dataset.encQuestion) {
        const questionId = String(input.dataset.encQuestion);
        if (input.type === "checkbox") {
          const group = Array.from(questionsNode.querySelectorAll(`[data-enc-question="${questionId}"]`));
          state.answers[questionId] = group.filter((item) => item.checked).map((item) => item.value);
        } else if (input.type === "radio") {
          if (input.checked) state.answers[questionId] = input.value;
        } else {
          state.answers[questionId] = input.value;
        }
        finalizeQuestionAnswer(questionId);
        return;
      }
      if (input.dataset.encMatrix) {
        const questionId = String(input.dataset.encMatrix);
        const row = String(input.dataset.row);
        if (!state.answers[questionId] || typeof state.answers[questionId] !== "object" || Array.isArray(state.answers[questionId])) {
          state.answers[questionId] = {};
        }
        if (input.checked) {
          state.answers[questionId][row] = input.value;
        }
        finalizeQuestionAnswer(questionId);
      }
    });

    questionsNode.addEventListener("change", async (event) => {
      const input = event.target.closest("[data-enc-file]");
      if (!input || !input.files || !input.files[0]) return;
      const questionId = String(input.dataset.encFile);
      const file = input.files[0];
      const reader = new FileReader();
      reader.onload = () => {
        state.answers[questionId] = {
          name: file.name,
          type: file.type,
          size: file.size,
          data_url: typeof reader.result === "string" ? reader.result : "",
        };
        finalizeQuestionAnswer(questionId);
      };
      reader.readAsDataURL(file);
    });
  }

  function applyImageLayout() {
    const instance = state.session.instance || {};
    const rules = instance.publication_rules_json || {};
    const imgUrl = (rules.image_url || "").trim();
    const imgPos = (rules.image_position || "").trim();
    if (!imgUrl || !imgPos) return;
    root.setAttribute("data-enc-img-pos", imgPos);
    if (imgPos === "background") {
      root.style.setProperty("--enc-response-bg-img", `url("${imgUrl}")`);
    } else if (imgPos === "col-left" || imgPos === "col-right") {
      const colImg = document.getElementById("enc-response-col-img");
      if (colImg) {
        colImg.style.backgroundImage = `url("${imgUrl}")`;
        colImg.removeAttribute("hidden");
      }
    } else if (imgPos === "box") {
      const boxImg = document.getElementById("enc-response-box-img");
      const boxImgEl = document.getElementById("enc-response-box-img-el");
      if (boxImg && boxImgEl) {
        boxImgEl.src = imgUrl;
        boxImg.removeAttribute("hidden");
      }
    }
  }

  function initialize() {
    state.mobileOrientation = window.localStorage.getItem(ORIENTATION_STORAGE_KEY) || "horizontal";
    if (window.matchMedia && window.matchMedia("(max-width: 860px)").matches) {
      state.mobileOrientation = "horizontal";
      window.localStorage.setItem(ORIENTATION_STORAGE_KEY, state.mobileOrientation);
    }
    if (isPresentationMode()) {
      const livePageIndex = Number(liveSettings().live_current_page_index);
      if (Number.isInteger(livePageIndex) && livePageIndex >= 0) {
        state.currentStep = Math.min(livePageIndex, Math.max(0, contentItems().length - 1));
      }
    }
    applyImageLayout();
    refreshAnswersFromSession();
    updateChrome();
    renderStartScreen();
    renderSteps();
    if (isSubmitted()) {
      renderClosedScreen();
    }
    bindEvents();
    if (orientationVerticalButton) {
      orientationVerticalButton.addEventListener("click", function () {
        state.mobileOrientation = "vertical";
        window.localStorage.setItem(ORIENTATION_STORAGE_KEY, state.mobileOrientation);
        applyOrientation();
      });
    }
    if (orientationHorizontalButton) {
      orientationHorizontalButton.addEventListener("click", function () {
        state.mobileOrientation = "horizontal";
        window.localStorage.setItem(ORIENTATION_STORAGE_KEY, state.mobileOrientation);
        applyOrientation();
      });
    }
    initLiveMode();
  }

  // ---------------------------------------------------------------------------
  // Live mode — audience polling
  // ---------------------------------------------------------------------------

  function initLiveMode() {
    const instance = state.session.instance || {};
    const settings = instance.settings_json || {};
    const liveStatus = settings.live_status || "idle";
    const hasPresentationPages = Array.isArray(presentationPages()) && presentationPages().length > 0;
    const rulesMode = String(publicationRules().response_mode || "standard").trim().toLowerCase();

    // Only activate live mode if the session is already running when the page
    // loads, or if the instance is live-enabled (may start later).
    const liveEnabled =
      liveStatus === "running" ||
      (rulesMode === "presentation" && hasPresentationPages) ||
      settings.live_enabled === true ||
      settings.presentation_mode === "mentimeter" ||
      settings.live_session_enabled === true;

    if (!liveEnabled) return;

    // Build the live polling URL based on access mode
    const accessMode = (state.session.access_mode || "").trim();
    const publicToken = (state.session.public_link_token || instance.public_link_token || "").trim();
    const instanceId = instance.id;

    let liveUrl = null;
    if (accessMode === "public" && publicToken) {
      liveUrl = `/api/public/encuestas/${publicToken}/live/status`;
    } else if (instanceId) {
      liveUrl = `/api/encuestas/campanas/${instanceId}/live/audience`;
    }

    if (!liveUrl) return;

    // Live state
    const live = {
      status: liveStatus,
      currentQuestionId: settings.live_current_question_id || null,
      currentPageIndex: settings.live_current_page_index || 0,
      pollTimer: null,
      banner: null,
    };

    // Inject live banner into the form screen
    const liveBanner = document.createElement("div");
    liveBanner.id = "enc-live-banner";
    liveBanner.className = "enc-live-banner";
    liveBanner.setAttribute("aria-live", "polite");
    liveBanner.innerHTML = `
      <span class="enc-live-dot"></span>
      <span id="enc-live-banner-text">Sesión en vivo activa</span>
      <span id="enc-live-q-label" class="enc-live-q-label"></span>
    `;
    formScreen.insertBefore(liveBanner, formScreen.firstChild);
    live.banner = liveBanner;

    // Inject live banner styles
    const style = document.createElement("style");
    style.textContent = `
      .enc-live-banner {
        display: flex; align-items: center; gap: 8px;
        padding: 8px 16px; margin-bottom: 12px;
        background: #dcfce7; border: 1px solid #bbf7d0; border-radius: 8px;
        font-size: 13px; color: #166534; font-weight: 500;
      }
      .enc-live-dot {
        width: 8px; height: 8px; border-radius: 50%; background: #22c55e;
        animation: enc-live-pulse 1.2s ease-in-out infinite;
        flex-shrink: 0;
      }
      @keyframes enc-live-pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50%       { opacity: 0.5; transform: scale(0.85); }
      }
      .enc-live-q-label {
        margin-left: auto; font-size: 12px; opacity: 0.8;
      }
      .enc-live-banner.is-waiting {
        background: #fef9c3; border-color: #fde68a; color: #92400e;
      }
      .enc-live-banner.is-waiting .enc-live-dot { background: #eab308; }
      .enc-live-banner.is-ended {
        background: #f3f4f6; border-color: #e5e7eb; color: #6b7280;
      }
      .enc-live-banner.is-ended .enc-live-dot { background: #9ca3af; animation: none; }
      .enc-live-highlight {
        outline: 3px solid #22c55e !important;
        outline-offset: 4px;
        border-radius: 10px;
        transition: outline 0.3s ease;
      }
    `;
    document.head.appendChild(style);

    function updateBanner(status, label) {
      liveBanner.classList.remove("is-waiting", "is-ended");
      const textEl = document.getElementById("enc-live-banner-text");
      const labelEl = document.getElementById("enc-live-q-label");
      if (status === "running") {
        textEl.textContent = "Sesión en vivo activa";
        labelEl.textContent = label || "";
      } else if (status === "ended") {
        liveBanner.classList.add("is-ended");
        textEl.textContent = "Sesión en vivo finalizada";
        labelEl.textContent = "";
      } else {
        liveBanner.classList.add("is-waiting");
        textEl.textContent = "Esperando inicio de sesión en vivo...";
        labelEl.textContent = "";
      }
    }

    function navigateToQuestion(questionId, pageIndex) {
      if (isPresentationMode() && Number.isInteger(pageIndex) && pageIndex >= 0) {
        if (state.currentStep !== pageIndex) {
          collectCurrentInputs();
          state.currentStep = pageIndex;
          renderSteps();
          renderCurrentStep();
        }
        return;
      }
      if (!questionId) return;
      const items = contentItems();
      for (let sIdx = 0; sIdx < items.length; sIdx++) {
        const sec = items[sIdx];
        const questions = isPresentationMode()
          ? (
            Array.isArray(sec.layout_sections) && sec.layout_sections.length
              ? sec.layout_sections.flatMap((section) =>
                String(section.type || "") === "question"
                  ? (Array.isArray(section.question_ids) ? section.question_ids : [section.question_id]).map((questionId) => findQuestionById(questionId)).filter(Boolean)
                  : []
              )
              : (sec.blocks || []).filter((block) => String(block.type || "") === "question").map((block) => findQuestionById(block.question_id)).filter(Boolean)
          )
          : (sec.questions || []);
        const found = questions.some(q => q.id === questionId);
        if (found) {
          if (state.currentStep !== sIdx) {
            collectCurrentInputs();
            state.currentStep = sIdx;
            renderSteps();
            renderCurrentStep();
          }
          // Highlight the specific question element
          setTimeout(() => {
            const el = questionsNode.querySelector(`[data-enc-question="${questionId}"], [data-enc-scale="${questionId}"]`);
            const article = el ? el.closest("article") : null;
            if (article) {
              // Remove previous highlights
              questionsNode.querySelectorAll(".enc-live-highlight").forEach(n => n.classList.remove("enc-live-highlight"));
              article.classList.add("enc-live-highlight");
              article.scrollIntoView({ behavior: "smooth", block: "center" });
            }
          }, 50);
          return;
        }
      }
    }

    async function pollLiveStatus() {
      try {
        const data = await fetchJSON(liveUrl);
        syncPresentationRulesFromLive(data);
        const newStatus = data.live_status || "idle";
        const newQId = data.live_current_question_id || null;
        const newPageIndex = Number.isInteger(data.live_current_page_index) ? data.live_current_page_index : null;
        const currentQ = data.current_question || null;
        const currentPage = data.current_page || null;
        state.livePageResults = data.current_page_results || {};

        const statusChanged = newStatus !== live.status;
        const questionChanged = newQId !== live.currentQuestionId;
        const pageChanged = newPageIndex !== null && newPageIndex !== live.currentPageIndex;

        live.status = newStatus;
        live.currentQuestionId = newQId;
        if (newPageIndex !== null) live.currentPageIndex = newPageIndex;
        if (state.session.instance) {
          state.session.instance.settings_json = {
            ...(state.session.instance.settings_json || {}),
            live_status: newStatus,
            live_mode: data.live_mode || (state.session.instance.settings_json || {}).live_mode,
            live_current_page_index: newPageIndex != null ? newPageIndex : (state.session.instance.settings_json || {}).live_current_page_index,
            live_current_question_id: newQId,
          };
        }

        updateBanner(
          newStatus,
          isPresentationMode()
            ? (currentPage && pageShowsTitle(currentPage) ? `Lámina activa: ${currentPage.title || currentPage.titulo || ""}` : "")
            : (currentQ ? `Pregunta activa: ${currentQ.titulo}` : "")
        );

        if (newStatus === "running") {
          // If we're on the start screen, auto-advance to form
          if (!formScreen.classList.contains("is-active") && !isSubmitted()) {
            showScreen("form");
            renderCurrentStep();
          }
          if (isPresentationMode()) {
            maybeEnterPresentationFullscreen(false);
          }
          if (
            (isPresentationMode() && (statusChanged || pageChanged || questionChanged))
            || (!isPresentationMode() && questionChanged && newQId)
          ) {
            navigateToQuestion(newQId, newPageIndex);
          }
        }

        if (newStatus === "ended") {
          stopLivePoll();
        }
      } catch (_) {
        // Silently ignore transient poll failures
      }
    }

    function startLivePoll() {
      if (live.pollTimer) return;
      live.pollTimer = setInterval(pollLiveStatus, 2500);
      pollLiveStatus(); // immediate first poll
    }

    function stopLivePoll() {
      if (live.pollTimer) {
        clearInterval(live.pollTimer);
        live.pollTimer = null;
      }
    }

    // Show banner and start polling
    updateBanner(liveStatus, null);
    startLivePoll();
  }

  initialize();
})();
