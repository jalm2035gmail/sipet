(function () {
  const root = document.getElementById("enc-root");
  if (!root) return;

  const state = {
    bootstrap: parseBootstrapState(),
    campaigns: [],
    campaignView: "kanban",
    templates: [],
    builder: null,
    results: null,
    permissions: null,
    currentInstanceId: null,
    selectedSectionId: null,
    questionTypes: [],
    assignableUsers: [],
    chart: null,
    questionModalType: null,
    presentationEditor: null,
    draggingPresentationPageIndex: null,
    draggingPageBlockIndex: null,
    draggingLayoutSectionIndex: null,
  };

  const navButtons = Array.from(root.querySelectorAll("[data-enc-nav]"));
  const panels = Array.from(root.querySelectorAll("[data-enc-panel]"));
  const builderTabs = Array.from(root.querySelectorAll("[data-enc-builder-tab]"));
  const builderPanels = Array.from(root.querySelectorAll("[data-enc-builder-panel]"));
  const surveyTabs = Array.from(root.querySelectorAll("[data-enc-survey-tab]"));
  const surveyPanels = Array.from(root.querySelectorAll("[data-enc-survey-panel]"));
  const metricNodes = root.querySelectorAll("[data-enc-metric]");
  const _actionScope = root.closest(".enc-app-main") || root;
  const actionButtons = _actionScope.querySelectorAll("[data-enc-action]");

  const campaignsBody = document.getElementById("enc-campaigns-body");
  const campaignsKanban = document.getElementById("enc-campaigns-kanban");
  const campaignsListWrap = document.getElementById("enc-campaigns-list-wrap");
  const campaignsMsg = document.getElementById("enc-campaigns-msg");
  const campaignViewButtons = Array.from(root.querySelectorAll("[data-enc-campaign-view]"));
  const builderMsg = document.getElementById("enc-builder-msg");
  const builderSelect = document.getElementById("enc-builder-instance-select");
  const templateSelect = document.getElementById("enc-template-select");
  const resultsSelect = document.getElementById("enc-results-instance-select");
  const resultsMsg = document.getElementById("enc-results-msg");
  const resultsEmpty = document.getElementById("enc-results-empty");
  const resultsBody = document.getElementById("enc-results-body");
  const resultsResponsesCount = document.getElementById("enc-results-responses-count");
  const resultsCompletion = document.getElementById("enc-results-completion");
  const resultsNps = document.getElementById("enc-results-nps");
  const resultsScore = document.getElementById("enc-results-score");
  const resultsSegments = document.getElementById("enc-results-segments");
  const resultsQuestions = document.getElementById("enc-results-questions");
  const resultsResponsesBody = document.getElementById("enc-results-responses-body");
  const resultsChartNode = document.getElementById("enc-results-chart");
  const resultsComparison = document.getElementById("enc-results-comparison");
  const resultsExportCsv = document.getElementById("enc-results-export-csv");
  const resultsExportPdf = document.getElementById("enc-results-export-pdf");
  const resultsExportXlsx = document.getElementById("enc-results-export-xlsx");
  const resultsFilterDepartment = document.getElementById("enc-results-filter-department");
  const resultsFilterRole = document.getElementById("enc-results-filter-role");
  const resultsFilterCompany = document.getElementById("enc-results-filter-company");
  const resultsSegmentBy = document.getElementById("enc-results-segment-by");
  const sectionsList = document.getElementById("enc-sections-list");
  const questionsList = document.getElementById("enc-questions-list");
  const boardMsg = document.getElementById("enc-board-msg");
  const questionsEmpty = document.getElementById("enc-questions-empty");
  const previewRoot = document.getElementById("enc-preview-root");
  const validationBox = document.getElementById("enc-publish-validation");
  const publishCampaignButton = root.querySelector('[data-enc-action="publish-campaign"]');
  const closeCampaignButton = root.querySelector('[data-enc-action="close-campaign"]');
  const addStructureButton = root.querySelector('[data-enc-action="add-section"]');

  const generalForm = document.getElementById("enc-general-form");
  const audienceForm = document.getElementById("enc-audience-form");
  const rulesForm = document.getElementById("enc-rules-form");
  const publicationForm = document.getElementById("enc-publication-form");
  const surveyOptionsForm = document.getElementById("enc-survey-options-form");
  const surveyDescriptionForm = document.getElementById("enc-survey-description-form");
  const surveyInitialMessageForm = document.getElementById("enc-survey-initial-message-form");
  const surveyFinalMessageForm = document.getElementById("enc-survey-final-message-form");
  const surveyImagenForm = document.getElementById("enc-imagen-form");
  const editorImagenUrl = document.getElementById("enc-imagen-url");
  const imagenFileInput = document.getElementById("enc-imagen-file");
  const imagenUploadArea = document.getElementById("enc-imagen-upload-area");
  const imagenUploadPrompt = document.getElementById("enc-imagen-upload-prompt");
  const imagenUploadPreview = document.getElementById("enc-imagen-upload-preview");
  const imagenPreviewImg = document.getElementById("enc-imagen-preview-img");
  const imagenUploadClear = document.getElementById("enc-imagen-upload-clear");
  const imagenUploadMsg = document.getElementById("enc-imagen-upload-msg");
  const editorTitle = document.getElementById("enc-editor-title");
  const editorParticipaciones = document.getElementById("enc-editor-participaciones");
  const editorResponsable = document.getElementById("enc-editor-responsable");
  const editorRestringido = document.getElementById("enc-editor-restringido");
  const publicLinkSummary = document.getElementById("enc-public-link-summary");
  const publicLinkAnchor = document.getElementById("enc-public-link-anchor");
  const openPublicLink = document.getElementById("enc-open-public-link");
  const presenterLinkAnchor = document.getElementById("enc-presenter-link-anchor");
  const openPresenterLink = document.getElementById("enc-open-presenter-link");
  const surveyInstanceId = document.getElementById("enc-survey-instance-id");
  const surveyIntegrationToken = document.getElementById("enc-survey-integration-token");
  const editorAudienceMode = document.getElementById("enc-editor-audience-mode");
  const editorAnonymityMode = document.getElementById("enc-editor-anonymity-mode");
  const editorScoringMode = document.getElementById("enc-editor-scoring-mode");
  const editorPublicationMode = document.getElementById("enc-editor-publication-mode");
  const editorResponseMode = document.getElementById("enc-editor-response-mode");
  const editorDescription = document.getElementById("enc-editor-description");
  const editorHeaderHtml = document.getElementById("enc-editor-header-html");
  const editorFooterHtml = document.getElementById("enc-editor-footer-html");
  const insertHeaderImageButton = document.getElementById("enc-insert-header-image");
  const insertFooterImageButton = document.getElementById("enc-insert-footer-image");
  const presentationPagesNode = document.getElementById("enc-presentation-pages");
  const presentationAddPageButton = document.getElementById("enc-presentation-add-page");
  const presentationSaveButton = document.getElementById("enc-presentation-save");
  const editorInitialMessage = document.getElementById("enc-editor-initial-message");
  const editorFinalMessage = document.getElementById("enc-editor-final-message");
  const audienceModeInput = document.getElementById("enc-audience-mode");
  const publicLinkEnabledInput = document.getElementById("enc-public-link-enabled");
  const manualGroupsField = document.getElementById("enc-audience-manual-group");
  const manualGroupsList = document.getElementById("enc-manual-groups-list");
  const manualGroupAdd = document.getElementById("enc-manual-group-add");
  const questionModal = document.getElementById("enc-question-modal");
  const questionModalTitle = document.getElementById("enc-modal-question-title");
  const questionModalTypes = document.getElementById("enc-modal-question-types");
  const questionModalPreview = document.getElementById("enc-modal-question-preview");
  const questionModalOptions = document.getElementById("enc-modal-question-options");
  const questionModalDescription = document.getElementById("enc-modal-question-description");
  const questionModalRequired = document.getElementById("enc-modal-question-required");
  const questionModalSaveClose = document.getElementById("enc-modal-question-save-close");
  const questionModalSaveNew = document.getElementById("enc-modal-question-save-new");
  const questionModalTabs = Array.from(root.querySelectorAll("[data-enc-question-tab]"));
  const questionModalPanels = Array.from(root.querySelectorAll("[data-enc-question-panel]"));

  const optionsPopup = document.getElementById("enc-options-popup");
  const optionsPopupTitle = document.getElementById("enc-options-popup-title");
  const optionsPopupTextarea = document.getElementById("enc-options-popup-textarea");
  const optionsPopupConfirm = document.getElementById("enc-options-popup-confirm");
  const optionsPopupCancel = document.getElementById("enc-options-popup-cancel");
  const optionsPopupClose = document.getElementById("enc-options-popup-close");
  const optionsPopupBackdrop = document.getElementById("enc-options-popup-backdrop");

  const inlineOptionsPanel = document.getElementById("enc-modal-inline-options");
  const inlineOptionsLabel = document.getElementById("enc-modal-inline-options-label");
  const inlineOptionsTa = document.getElementById("enc-modal-inline-options-ta");
  const pageModal = document.getElementById("enc-page-modal");
  const pageTitleInput = document.getElementById("enc-page-title");
  const pageSectionCountInput = document.getElementById("enc-page-section-count");
  const pageDescriptionInput = document.getElementById("enc-page-description");
  const pageBgColorInput = document.getElementById("enc-page-bg-color");
  const pageBgImageInput = document.getElementById("enc-page-bg-image");
  const pageFooterTextInput = document.getElementById("enc-page-footer-text");
  const pageFooterColorInput = document.getElementById("enc-page-footer-color");
  const pageBlocksNode = document.getElementById("enc-page-blocks");
  const pagePreviewNode = document.getElementById("enc-page-preview");
  const pageSaveCloseButton = document.getElementById("enc-page-save-close");

  if (inlineOptionsTa) {
    inlineOptionsTa.addEventListener("input", function () {
      if (questionModalOptions) questionModalOptions.value = inlineOptionsTa.value;
      renderQuestionModalPreview();
    });
  }

  function parseBootstrapState() {
    try {
      return JSON.parse(root.dataset.encBootstrap || "{}");
    } catch (error) {
      console.warn("encuestas bootstrap invalido", error);
      return {};
    }
  }

  function setMessage(node, message, isError) {
    if (!node) return;
    node.textContent = message || "";
    node.style.color = isError ? "#991b1b" : "";
  }

  function selectedResultsFilters() {
    return {
      department: resultsFilterDepartment ? resultsFilterDepartment.value : "",
      role: resultsFilterRole ? resultsFilterRole.value : "",
      company: resultsFilterCompany ? resultsFilterCompany.value : "",
      segment_by: resultsSegmentBy ? resultsSegmentBy.value : "department",
    };
  }

  function fillResultsFilterSelect(node, values, placeholder, selectedValue) {
    if (!node) return;
    node.innerHTML = [`<option value="">${placeholder}</option>`]
      .concat((values || []).map((value) => `<option value="${value}" ${String(selectedValue) === String(value) ? "selected" : ""}>${value}</option>`))
      .join("");
  }

  function can(permission) {
    return !!(state.permissions && state.permissions[permission]);
  }

  async function fetchJSON(url, options) {
    const response = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (response.status === 204) return null;
    const text = await response.text();
    let data = null;
    if (text) {
      try {
        data = JSON.parse(text);
      } catch (_error) {
        data = text;
      }
    }
    if (!response.ok) {
      const detail = data && data.detail ? data.detail : data;
      throw new Error(
        typeof detail === "string"
          ? detail
          : (detail ? JSON.stringify(detail) : `HTTP ${response.status}`)
      );
    }
    return data;
  }

  function showPanel(panelId) {
    const targetPanel = panels.some((panel) => panel.dataset.encPanel === panelId) ? panelId : "dashboard";
    navButtons.forEach((button) => {
      button.classList.toggle("is-active", button.dataset.encNav === targetPanel);
    });
    panels.forEach((panel) => {
      panel.classList.toggle("is-active", panel.dataset.encPanel === targetPanel);
    });
  }

  function initialPanel() {
    const panel = String((state.bootstrap && state.bootstrap.current_panel) || "").trim();
    if (panel) return panel;
    const currentPath = window.location.pathname;
    if (currentPath.endsWith("/constructor")) return "constructor";
    if (currentPath.endsWith("/resultados")) return "resultados";
    if (currentPath.endsWith("/encuestas")) return "encuestas";
    return "dashboard";
  }

  function showBuilderTab(tabId) {
    builderTabs.forEach((button) => {
      button.classList.toggle("is-active", button.dataset.encBuilderTab === tabId);
    });
    builderPanels.forEach((panel) => {
      panel.classList.toggle("is-active", panel.dataset.encBuilderPanel === tabId);
    });
  }

  function showSurveyTab(tabId) {
    surveyTabs.forEach((button) => {
      button.classList.toggle("is-active", button.dataset.encSurveyTab === tabId);
    });
    surveyPanels.forEach((panel) => {
      panel.classList.toggle("is-active", panel.dataset.encSurveyPanel === tabId);
    });
  }

  function showQuestionModalTab(tabId) {
    questionModalTabs.forEach((button) => {
      button.classList.toggle("is-active", button.dataset.encQuestionTab === tabId);
    });
    questionModalPanels.forEach((panel) => {
      panel.classList.toggle("is-active", panel.dataset.encQuestionPanel === tabId);
    });
  }

  function isPublicLinkAudience(value) {
    return String(value || "").trim().toLowerCase() === "public_link";
  }

  function syncPublicLinkControls() {
    if (!publicLinkEnabledInput) return;
    const shouldEnable = isPublicLinkAudience(audienceModeInput ? audienceModeInput.value : "")
      || isPublicLinkAudience(editorAudienceMode ? editorAudienceMode.value : "");
    if (shouldEnable) {
      publicLinkEnabledInput.value = "true";
    }
  }

  function responseMode() {
    return String(
      (state.builder && state.builder.publication_rules_json && state.builder.publication_rules_json.response_mode)
      || "standard"
    ).trim().toLowerCase();
  }

  function normalizeSectionCount(value) {
    const safe = Number(value);
    if (safe === 2 || safe === 4) return safe;
    return 1;
  }

  const EMBEDDED_EFFECT_OPTIONS = [
    { value: "none", label: "Sin efecto" },
    { value: "fade_in", label: "Aparecer" },
    { value: "slide_up", label: "Subir" },
    { value: "slide_left", label: "Entrar lateral" },
    { value: "zoom_in", label: "Zoom" },
    { value: "bounce_in", label: "Rebote" },
  ];

  const EMBEDDED_CLICK_EFFECT_OPTIONS = [
    { value: "none", label: "Sin efecto" },
    { value: "pulse", label: "Pulso" },
    { value: "pop", label: "Pop" },
    { value: "shake", label: "Sacudir" },
    { value: "highlight", label: "Resaltar" },
    { value: "flip", label: "Giro" },
  ];

  const EMBEDDED_HIGHLIGHT_EFFECT_OPTIONS = [
    { value: "none", label: "Sin efecto" },
    { value: "highlight", label: "Resaltar" },
    { value: "pulse", label: "Pulso" },
    { value: "zoom_in", label: "Zoom" },
    { value: "shake", label: "Sacudir" },
  ];

  function renderEffectOptions(options, selectedValue) {
    return options.map((option) => `<option value="${option.value}" ${String(selectedValue || "none") === option.value ? "selected" : ""}>${option.label}</option>`).join("");
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

  function createPresentationSection(data) {
    const normalized = normalizeEmbeddedContent(data && data.html, data && data.css);
    const questionIds = Array.isArray(data && data.question_ids)
      ? data.question_ids.map((value) => Number(value)).filter((value) => Number.isFinite(value))
      : (data && data.question_id != null && data.question_id !== "" ? [Number(data.question_id)] : []);
    return {
      id: String((data && data.id) || `section_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`),
      type: String((data && data.type) || "html"),
      html: normalized.html,
      css: normalized.css,
      js_input: String((data && data.js_input) || ""),
      js_highlight: String((data && data.js_highlight) || ""),
      js_output: String((data && data.js_output) || ""),
      js_input_effect: String((data && data.js_input_effect) || "none"),
      js_highlight_effect: String((data && data.js_highlight_effect) || "none"),
      js_output_effect: String((data && data.js_output_effect) || "none"),
      image_url: String((data && data.image_url) || ""),
      image_alt: String((data && data.image_alt) || ""),
      image_fit: String((data && data.image_fit) || "cover"),
      question_id: questionIds.length ? questionIds[0] : null,
      question_ids: questionIds,
    };
  }

  function ensureLayoutSections(count, sections) {
    const safeCount = normalizeSectionCount(count);
    const source = Array.isArray(sections) ? sections.map(createPresentationSection).slice(0, safeCount) : [];
    while (source.length < safeCount) {
      source.push(createPresentationSection({ type: "html" }));
    }
    return source;
  }

  function legacyBlocksToLayoutSections(blocks, count) {
    const source = Array.isArray(blocks) ? blocks : [];
    return ensureLayoutSections(count || source.length || 1, source.map((block) => ({
      type: block.type,
      html: block.html,
      css: block.css,
      js_input: block.js_input,
      js_highlight: block.js_highlight,
      js_output: block.js_output,
      js_input_effect: block.js_input_effect,
      js_highlight_effect: block.js_highlight_effect,
      js_output_effect: block.js_output_effect,
      image_url: block.image_url,
      image_alt: block.image_alt,
      image_fit: block.image_fit,
      question_id: block.question_id,
      question_ids: block.question_id != null ? [block.question_id] : [],
    })));
  }

  function createPresentationPage(data) {
    const rawSectionCount = data && data.section_count;
    const legacyBlocks = Array.isArray(data && data.blocks) ? data.blocks.map(createPresentationBlock) : [];
    const sectionCount = rawSectionCount != null
      ? normalizeSectionCount(rawSectionCount)
      : normalizeSectionCount(legacyBlocks.length || 1);
    const layoutSections = Array.isArray(data && data.layout_sections)
      ? ensureLayoutSections(sectionCount, data.layout_sections)
      : legacyBlocks.length
        ? legacyBlocksToLayoutSections(legacyBlocks, sectionCount)
        : ensureLayoutSections(sectionCount || 1, []);
    return {
      id: String((data && data.id) || `page_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`),
      title: String((data && data.title) || "Nueva página"),
      description: String((data && data.description) || ""),
      bg_color: String((data && data.bg_color) || "#ffffff"),
      bg_image_url: String((data && data.bg_image_url) || ""),
      section_count: sectionCount || 1,
      layout_sections: layoutSections,
      footer_text: String((data && data.footer_text) || ""),
      footer_color: String((data && data.footer_color) || "#0f172a"),
      blocks: Array.isArray(data && data.blocks) ? data.blocks.map(createPresentationBlock) : [],
    };
  }

  function createPresentationBlock(data) {
    return {
      id: String((data && data.id) || `block_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`),
      type: String((data && data.type) || "html"),
      width: String((data && data.width) || "full"),
      html: String((data && data.html) || ""),
      css: String((data && data.css) || ""),
      js_input: String((data && data.js_input) || ""),
      js_highlight: String((data && data.js_highlight) || ""),
      js_output: String((data && data.js_output) || ""),
      js_input_effect: String((data && data.js_input_effect) || "none"),
      js_highlight_effect: String((data && data.js_highlight_effect) || "none"),
      js_output_effect: String((data && data.js_output_effect) || "none"),
      image_url: String((data && data.image_url) || ""),
      image_alt: String((data && data.image_alt) || ""),
      image_fit: String((data && data.image_fit) || "cover"),
      question_id: data && data.question_id != null ? Number(data.question_id) : null,
    };
  }

  function getPresentationPages() {
    const rules = (state.builder && state.builder.publication_rules_json) || {};
    return Array.isArray(rules.presentation_pages) ? rules.presentation_pages.map(createPresentationPage) : [];
  }

  function setPresentationPages(pages) {
    if (!state.builder) return;
    state.builder.publication_rules_json = {
      ...(state.builder.publication_rules_json || {}),
      presentation_pages: pages.map(createPresentationPage),
    };
  }

  function presentationTemplates() {
    return {
      hero: function () {
        return createPresentationPage({
          title: "Portada de encuesta",
          description: "Introduce el tema y prepara a la audiencia.",
          bg_color: "#f8fafc",
          blocks: [
            createPresentationBlock({
              type: "html",
              html: '<section style="padding:72px 68px;background:linear-gradient(135deg,#ff8a00 0%,#ffd166 42%,#22d3ee 100%);color:#081120;border-radius:28px;"><div style="max-width:520px;"><div style="font-size:12px;letter-spacing:.18em;text-transform:uppercase;font-weight:800;margin-bottom:18px;">Encuesta en vivo</div><h1 style="font-size:54px;line-height:.95;margin:0 0 16px;font-weight:800;">Abre la conversación</h1><p style="font-size:19px;line-height:1.55;margin:0;">Usa esta página para dar contexto, reglas o detonar la participación.</p></div></section>',
            }),
          ],
        });
      },
      split: function () {
        return createPresentationPage({
          title: "Idea principal",
          description: "Texto con apoyo visual en dos columnas.",
          bg_color: "#ffffff",
          blocks: [
            createPresentationBlock({
              type: "html",
              width: "half",
              html: '<section style="padding:52px 56px;background:#ffffff;border-radius:24px;"><h2 style="margin:0 0 10px;font-size:38px;">Explica una idea</h2><p style="margin:0;font-size:18px;line-height:1.7;color:#475569;">Usa este bloque para narrativa, instrucciones o contexto antes de mostrar la pregunta.</p></section>',
            }),
            createPresentationBlock({
              type: "image",
              width: "half",
              image_url: "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=1200&q=80",
              image_fit: "cover",
            }),
          ],
        });
      },
      stats: function () {
        return createPresentationPage({
          title: "Indicadores",
          description: "Muestra datos rápidos antes de la interacción.",
          bg_color: "#f8fafc",
          blocks: [
            createPresentationBlock({
              type: "html",
              html: '<section style="padding:42px 52px;background:#f8fafc;border-radius:24px;"><div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;"><div style="padding:22px;background:#fff;border-radius:20px;"><div style="font-size:13px;color:#64748b;">Cobertura</div><strong style="font-size:42px;">92%</strong></div><div style="padding:22px;background:#fff;border-radius:20px;"><div style="font-size:13px;color:#64748b;">Participación</div><strong style="font-size:42px;">4.8</strong></div><div style="padding:22px;background:#fff;border-radius:20px;"><div style="font-size:13px;color:#64748b;">NPS</div><strong style="font-size:42px;">67</strong></div></div></section>',
            }),
          ],
        });
      },
      "question-focus": function () {
        return createPresentationPage({
          title: "Pregunta destacada",
          description: "Combina introducción con la pregunta principal.",
          bg_color: "#ffffff",
          blocks: [
            createPresentationBlock({
              type: "html",
              html: '<section style="padding:40px 56px;border-radius:24px;background:#0f172a;color:#eff6ff;"><div style="font-size:12px;text-transform:uppercase;letter-spacing:.18em;opacity:.72;margin-bottom:12px;">Momento interactivo</div><h2 style="margin:0 0 12px;font-size:38px;">Prepara a la audiencia</h2><p style="margin:0;font-size:18px;line-height:1.65;color:rgba(255,255,255,.82);">Agrega debajo una pregunta de la encuesta para capturar respuestas en vivo.</p></section>',
            }),
            createPresentationBlock({
              type: "question",
              width: "full",
            }),
          ],
        });
      },
    };
  }

  function mergePresentationTemplate(templateKey) {
    const templates = presentationTemplates();
    const factory = templates[templateKey];
    if (!factory) return createPresentationPage({ blocks: [] });
    return factory();
  }

  function getAllBuilderQuestions() {
    const sections = (state.builder && state.builder.sections) || [];
    const rows = [];
    sections.forEach((section) => {
      (section.questions || []).forEach((question) => {
        rows.push({
          id: question.id,
          label: `${section.titulo || "Sección"} · ${question.titulo || "Pregunta"}`,
        });
      });
    });
    return rows;
  }

  function buildQuestionOptionsHtml(selectedId) {
    const options = ['<option value="">Selecciona una pregunta</option>'].concat(
      getAllBuilderQuestions().map((item) =>
        `<option value="${item.id}" ${String(selectedId) === String(item.id) ? "selected" : ""}>${escapeHtml(item.label)}</option>`
      )
    );
    return options.join("");
  }

  function buildQuestionCheckboxesHtml(selectedIds, sectionIndex) {
    const selected = new Set((Array.isArray(selectedIds) ? selectedIds : []).map((value) => String(value)));
    const items = getAllBuilderQuestions();
    if (!items.length) {
      return `
        <div class="enc-placeholder">
          <strong>No hay preguntas disponibles.</strong>
          <span>Crea primero una pregunta para poder agregarla a esta página.</span>
          <div class="enc-form-actions" style="margin-top:12px;">
            <button type="button" class="enc-button enc-button-secondary" data-enc-open-question-library="true">Crear pregunta ahora</button>
          </div>
        </div>
      `;
    }
    return items.map((item) => `
      <label class="enc-preview-choice">
        <input type="checkbox" data-enc-layout-section-question="${sectionIndex}" value="${item.id}" ${selected.has(String(item.id)) ? "checked" : ""}>
        <span>${escapeHtml(item.label)}</span>
      </label>
    `).join("");
  }

  function focusPresentationQuestionPicker(sectionIndex) {
    if (!pageBlocksNode) return;
    window.requestAnimationFrame(() => {
      const firstQuestion = pageBlocksNode.querySelector(`[data-enc-layout-section-question="${sectionIndex}"]`);
      const picker = pageBlocksNode.querySelector(".enc-page-question-picker");
      if (firstQuestion) {
        firstQuestion.focus();
        firstQuestion.scrollIntoView({ behavior: "smooth", block: "center" });
      } else if (picker) {
        picker.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    });
  }

  function renderPresentationBuilder() {
    if (!presentationPagesNode) return;
    const pages = getPresentationPages();
    if (!pages.length) {
      presentationPagesNode.innerHTML = '<div class="enc-placeholder">No hay páginas definidas. Agrega la primera.</div>';
      return;
    }
    presentationPagesNode.innerHTML = pages.map((page, pageIndex) => `
      <article class="enc-card enc-presentation-page" data-enc-presentation-page="${pageIndex}" draggable="true">
        <div class="enc-section-head">
          <div>
            <h3>Página ${pageIndex + 1}</h3>
            <p>${escapeHtml(page.description || "Define el contenido y distribución de esta página.")}</p>
          </div>
          <div class="enc-builder-toolbar">
            <button type="button" class="enc-button enc-button-secondary" data-enc-open-presentation-page="${pageIndex}">Editar página</button>
            <button type="button" class="enc-button enc-button-secondary" data-enc-remove-presentation-page="${pageIndex}">Eliminar página</button>
          </div>
        </div>
        <div class="enc-presentation-page-summary">
          <div class="enc-presentation-page-meta">
            <span class="enc-pill is-draft">${escapeHtml(page.title || `Página ${pageIndex + 1}`)}</span>
            <span class="enc-question-meta">${page.section_count || 1} sección(es)</span>
          </div>
          <div class="enc-presentation-page-live-preview">
            ${renderPresentationPageCanvas(page, true)}
          </div>
        </div>
      </article>
    `).join("");
  }

  function movePresentationPage(fromIndex, toIndex) {
    const pages = getPresentationPages();
    if (fromIndex < 0 || toIndex < 0 || fromIndex >= pages.length || toIndex >= pages.length || fromIndex === toIndex) return;
    const temp = pages[fromIndex];
    pages[fromIndex] = pages[toIndex];
    pages[toIndex] = temp;
    setPresentationPages(pages);
    renderPresentationBuilder();
    setMessage(builderMsg, "Orden de páginas actualizado.", false);
  }

  function presentationCanvasStyle(page) {
    const layers = [];
    if (page && page.bg_image_url) {
      layers.push(`linear-gradient(180deg, rgba(15,23,42,0.12), rgba(15,23,42,0.18)), url("${String(page.bg_image_url).replace(/"/g, '\\"')}") center / cover`);
    }
    layers.push(page && page.bg_color ? page.bg_color : "#ffffff");
    return `background:${layers.join(",")};`;
  }

  function renderLayoutSectionSummary(section) {
    const type = String((section && section.type) || "html");
    if (type === "question") {
      const labels = (Array.isArray(section.question_ids) ? section.question_ids : [])
        .map((questionId) => getAllBuilderQuestions().find((item) => Number(item.id) === Number(questionId)))
        .filter(Boolean)
        .map((item) => item.label);
      return `<div class="enc-presentation-mini-item"><strong>Preguntas</strong><span>${escapeHtml(labels.length ? labels.join(" · ") : "Selecciona una o varias preguntas")}</span></div>`;
    }
    if (type === "image") {
      return `<div class="enc-presentation-mini-item"><strong>Imagen</strong><span>${escapeHtml(section.image_url || "Sin URL")}</span></div>`;
    }
    const sanitizedHtml = String(section.html || "")
      .replace(/<style[\s\S]*?<\/style>/gi, " ")
      .replace(/<script[\s\S]*?<\/script>/gi, " ");
    const htmlText = sanitizedHtml.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
    const previewText = htmlText ? htmlText.slice(0, 140) : "Bloque visual HTML";
    return `<div class="enc-presentation-mini-item"><strong>HTML</strong><span>${escapeHtml(previewText)}${htmlText.length > 140 ? "..." : ""}</span></div>`;
  }

  function sectionGridClass(sectionCount) {
    return `is-sections-${normalizeSectionCount(sectionCount)}`;
  }

  function renderPresentationSectionPreview(section, sectionIndex, interactive) {
    const type = String((section && section.type) || "html");
    const isSelected = Boolean(
      interactive
      && state.presentationEditor
      && Number(state.presentationEditor.selectedSectionIndex) === Number(sectionIndex)
    );
    const attrs = interactive
      ? `data-enc-layout-section="${sectionIndex}" draggable="true"`
      : "";
    if (type === "question") {
      const labels = (Array.isArray(section.question_ids) ? section.question_ids : [])
        .map((questionId) => getAllBuilderQuestions().find((item) => Number(item.id) === Number(questionId)))
        .filter(Boolean)
        .map((item) => item.label);
      return `<article class="enc-presentation-layout-slot ${isSelected ? "is-selected" : ""}" ${attrs}><div class="enc-presentation-mini-item"><strong>Preguntas</strong><span>${escapeHtml(labels.length ? labels.join(" · ") : "Selecciona una o varias preguntas")}</span></div></article>`;
    }
    if (type === "image") {
      return `<article class="enc-presentation-layout-slot ${isSelected ? "is-selected" : ""}" ${attrs}>${renderImageSection(section)}</article>`;
    }
    const html = renderEmbeddedSectionHtml(section);
    return `<article class="enc-presentation-layout-slot ${isSelected ? "is-selected" : ""}" ${attrs}>${html ? `<article class="enc-card enc-response-richtext">${html}</article>` : `<div class="enc-placeholder">Haz clic para elegir contenido</div>`}</article>`;
  }

  function renderPresentationPageCanvas(page, compact) {
    const sections = ensureLayoutSections(page.section_count, page.layout_sections);
    const title = String((page && page.title) || "").trim();
    const footerText = String((page && page.footer_text) || "").trim();
    return `
      <div class="enc-presentation-stage ${compact ? "is-compact" : ""}">
        <div class="enc-presentation-stage-ratio">
          <div class="enc-presentation-stage-canvas" style="${presentationCanvasStyle(page)}">
            <div class="enc-presentation-layout">
              ${title ? `<header class="enc-presentation-layout-header"><h1>${escapeHtml(title)}</h1></header>` : ""}
              <div class="enc-presentation-layout-body ${sectionGridClass(page.section_count)}">
                ${sections.map((section, index) => renderPresentationSectionPreview(section, index, !compact)).join("")}
              </div>
              ${footerText ? `<footer class="enc-presentation-layout-footer" style="background:${escapeHtml(page.footer_color || "#0f172a")};"><span>${escapeHtml(footerText)}</span></footer>` : ""}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  function renderPresentationPagePreview(page) {
    if (!pagePreviewNode) return;
    pagePreviewNode.innerHTML = renderPresentationPageCanvas(page, false);
    hydrateEmbeddedRuntime(pagePreviewNode);
  }

  function syncPresentationEditorPage() {
    if (!state.presentationEditor) return null;
    const page = createPresentationPage({
      ...(state.presentationEditor.page || {}),
      title: pageTitleInput ? pageTitleInput.value : "",
      section_count: pageSectionCountInput ? normalizeSectionCount(pageSectionCountInput.value) : 1,
      description: pageDescriptionInput ? pageDescriptionInput.value : "",
      bg_color: pageBgColorInput ? pageBgColorInput.value : "#ffffff",
      bg_image_url: pageBgImageInput ? pageBgImageInput.value : "",
      footer_text: pageFooterTextInput ? pageFooterTextInput.value : "",
      footer_color: pageFooterColorInput ? pageFooterColorInput.value : "#0f172a",
    });
    page.layout_sections = ensureLayoutSections(page.section_count, page.layout_sections);
    state.presentationEditor.page = page;
    renderPresentationPagePreview(page);
    return page;
  }

  function renderPageBlocksEditor() {
    if (!pageBlocksNode || !state.presentationEditor) return;
    const page = state.presentationEditor.page || createPresentationPage({});
    const sectionIndex = Number(state.presentationEditor.selectedSectionIndex || 0);
    const sections = ensureLayoutSections(page.section_count, page.layout_sections);
    const section = sections[sectionIndex] || createPresentationSection({});
    pageBlocksNode.innerHTML = `
      <article class="enc-card enc-presentation-block">
        <div class="enc-builder-toolbar">
          <strong>Sección ${sectionIndex + 1} de ${page.section_count}</strong>
          <span class="enc-question-meta">Haz clic en otra sección del canvas para editarla.</span>
        </div>
        <div class="enc-form-grid">
          <label class="enc-field">
            <span>Tipo de contenido</span>
            <select class="enc-input enc-select" data-enc-layout-section-type="${sectionIndex}">
              <option value="html" ${section.type === "html" ? "selected" : ""}>HTML</option>
              <option value="image" ${section.type === "image" ? "selected" : ""}>Imagen</option>
              <option value="question" ${section.type === "question" ? "selected" : ""}>Pregunta</option>
            </select>
          </label>
          ${section.type === "question" ? `
            <label class="enc-field enc-field-span-2">
              <span>Preguntas</span>
              <div class="enc-page-question-picker">
                ${buildQuestionCheckboxesHtml(section.question_ids, sectionIndex)}
              </div>
            </label>
          ` : section.type === "image" ? `
            <label class="enc-field enc-field-span-2">
              <span>URL de imagen</span>
              <input class="enc-input" type="url" data-enc-layout-section-image-url="${sectionIndex}" value="${escapeHtml(section.image_url)}" placeholder="https://ejemplo.com/imagen.jpg">
            </label>
            <label class="enc-field">
              <span>Texto alternativo</span>
              <input class="enc-input" type="text" data-enc-layout-section-image-alt="${sectionIndex}" value="${escapeHtml(section.image_alt)}" placeholder="Descripción corta de la imagen">
            </label>
            <label class="enc-field">
              <span>Ajuste</span>
              <select class="enc-input enc-select" data-enc-layout-section-image-fit="${sectionIndex}">
                <option value="cover" ${section.image_fit === "cover" ? "selected" : ""}>Cubrir</option>
                <option value="contain" ${section.image_fit === "contain" ? "selected" : ""}>Contener</option>
              </select>
            </label>
          ` : `
            <label class="enc-field enc-field-span-2">
              <span>HTML</span>
              <textarea class="enc-input enc-textarea" data-enc-layout-section-html="${sectionIndex}" placeholder="<div>Contenido libre</div>">${escapeHtml(section.html)}</textarea>
            </label>
            <label class="enc-field enc-field-span-2">
              <span>CSS</span>
              <textarea class="enc-input enc-textarea" data-enc-layout-section-css="${sectionIndex}" placeholder=".bloque { color: #0f172a; }">${escapeHtml(section.css || "")}</textarea>
            </label>
            <label class="enc-field enc-field-span-2">
              <span>Efecto de entrada</span>
              <select class="enc-input enc-select" data-enc-layout-section-js-input-effect="${sectionIndex}">
                ${renderEffectOptions(EMBEDDED_EFFECT_OPTIONS, section.js_input_effect)}
              </select>
            </label>
            <label class="enc-field enc-field-span-2">
              <span>Efecto destacar</span>
              <select class="enc-input enc-select" data-enc-layout-section-js-highlight-effect="${sectionIndex}">
                ${renderEffectOptions(EMBEDDED_HIGHLIGHT_EFFECT_OPTIONS, section.js_highlight_effect)}
              </select>
            </label>
            <label class="enc-field enc-field-span-2">
              <span>Efecto de salida</span>
              <select class="enc-input enc-select" data-enc-layout-section-js-output-effect="${sectionIndex}">
                ${renderEffectOptions(EMBEDDED_CLICK_EFFECT_OPTIONS, section.js_output_effect)}
              </select>
            </label>
            <label class="enc-field enc-field-span-2">
              <span>JS Entrada</span>
              <textarea class="enc-input enc-textarea" data-enc-layout-section-js-input="${sectionIndex}" placeholder="console.log('entrada');">${escapeHtml(section.js_input || "")}</textarea>
            </label>
            <label class="enc-field enc-field-span-2">
              <span>JS Destacar</span>
              <textarea class="enc-input enc-textarea" data-enc-layout-section-js-highlight="${sectionIndex}" placeholder="root.classList.add('resaltado');">${escapeHtml(section.js_highlight || "")}</textarea>
            </label>
            <label class="enc-field enc-field-span-2">
              <span>JS Salida</span>
              <textarea class="enc-input enc-textarea" data-enc-layout-section-js-output="${sectionIndex}" placeholder="console.log('salida');">${escapeHtml(section.js_output || "")}</textarea>
            </label>
            <div class="enc-form-actions enc-field-span-2">
              <button type="button" class="enc-button enc-button-secondary" data-enc-layout-section-insert-image="${sectionIndex}">Insertar imagen</button>
            </div>
          `}
        </div>
      </article>
    `;
    renderPresentationPagePreview(page);
  }

  function collectLayoutSectionsFromModal() {
    if (!state.presentationEditor) return [];
    const page = state.presentationEditor.page || createPresentationPage({});
    const sections = ensureLayoutSections(page.section_count, page.layout_sections);
    const sectionIndex = Number(state.presentationEditor.selectedSectionIndex || 0);
    const section = createPresentationSection(sections[sectionIndex] || {});
    const typeNode = pageBlocksNode ? pageBlocksNode.querySelector(`[data-enc-layout-section-type="${sectionIndex}"]`) : null;
    const htmlNode = pageBlocksNode ? pageBlocksNode.querySelector(`[data-enc-layout-section-html="${sectionIndex}"]`) : null;
    const cssNode = pageBlocksNode ? pageBlocksNode.querySelector(`[data-enc-layout-section-css="${sectionIndex}"]`) : null;
    const jsInputEffectNode = pageBlocksNode ? pageBlocksNode.querySelector(`[data-enc-layout-section-js-input-effect="${sectionIndex}"]`) : null;
    const jsHighlightEffectNode = pageBlocksNode ? pageBlocksNode.querySelector(`[data-enc-layout-section-js-highlight-effect="${sectionIndex}"]`) : null;
    const jsOutputEffectNode = pageBlocksNode ? pageBlocksNode.querySelector(`[data-enc-layout-section-js-output-effect="${sectionIndex}"]`) : null;
    const jsInputNode = pageBlocksNode ? pageBlocksNode.querySelector(`[data-enc-layout-section-js-input="${sectionIndex}"]`) : null;
    const jsHighlightNode = pageBlocksNode ? pageBlocksNode.querySelector(`[data-enc-layout-section-js-highlight="${sectionIndex}"]`) : null;
    const jsOutputNode = pageBlocksNode ? pageBlocksNode.querySelector(`[data-enc-layout-section-js-output="${sectionIndex}"]`) : null;
    const questionNodes = pageBlocksNode ? Array.from(pageBlocksNode.querySelectorAll(`[data-enc-layout-section-question="${sectionIndex}"]`)) : [];
    const imageUrlNode = pageBlocksNode ? pageBlocksNode.querySelector(`[data-enc-layout-section-image-url="${sectionIndex}"]`) : null;
    const imageAltNode = pageBlocksNode ? pageBlocksNode.querySelector(`[data-enc-layout-section-image-alt="${sectionIndex}"]`) : null;
    const imageFitNode = pageBlocksNode ? pageBlocksNode.querySelector(`[data-enc-layout-section-image-fit="${sectionIndex}"]`) : null;
    section.type = typeNode ? typeNode.value : section.type;
    const normalized = normalizeEmbeddedContent(htmlNode ? htmlNode.value : section.html, cssNode ? cssNode.value : section.css);
    section.html = normalized.html;
    section.css = normalized.css;
    section.js_input = jsInputNode ? jsInputNode.value : section.js_input;
    section.js_highlight = jsHighlightNode ? jsHighlightNode.value : section.js_highlight;
    section.js_output = jsOutputNode ? jsOutputNode.value : section.js_output;
    section.js_input_effect = jsInputEffectNode ? jsInputEffectNode.value : section.js_input_effect;
    section.js_highlight_effect = jsHighlightEffectNode ? jsHighlightEffectNode.value : section.js_highlight_effect;
    section.js_output_effect = jsOutputEffectNode ? jsOutputEffectNode.value : section.js_output_effect;
    section.question_ids = questionNodes.filter((node) => node.checked).map((node) => Number(node.value)).filter((value) => Number.isFinite(value));
    section.question_id = section.question_ids.length ? section.question_ids[0] : null;
    section.image_url = imageUrlNode ? imageUrlNode.value : section.image_url;
    section.image_alt = imageAltNode ? imageAltNode.value : section.image_alt;
    section.image_fit = imageFitNode ? imageFitNode.value : section.image_fit;
    sections[sectionIndex] = section;
    return sections;
  }

  function updatePresentationEditorPage() {
    if (!state.presentationEditor) return;
    const page = syncPresentationEditorPage() || createPresentationPage({});
    page.layout_sections = collectLayoutSectionsFromModal();
    state.presentationEditor.page = createPresentationPage(page);
    renderPresentationPagePreview(state.presentationEditor.page);
  }

  function moveLayoutSection(fromIndex, toIndex) {
    if (!state.presentationEditor) return;
    updatePresentationEditorPage();
    const sections = ensureLayoutSections(state.presentationEditor.page.section_count, state.presentationEditor.page.layout_sections);
    if (fromIndex < 0 || toIndex < 0 || fromIndex >= sections.length || toIndex >= sections.length || fromIndex === toIndex) return;
    const temp = sections[fromIndex];
    sections[fromIndex] = sections[toIndex];
    sections[toIndex] = temp;
    state.presentationEditor.page.layout_sections = sections;
    state.presentationEditor.selectedSectionIndex = toIndex;
    renderPageBlocksEditor();
  }

  function appendHtmlBlockFromPaste(rawHtml, rawText) {
    if (!state.presentationEditor) return;
    const html = String(rawHtml || "").trim();
    const text = String(rawText || "").trim();
    if (!html && !text) return;
    updatePresentationEditorPage();
    const sections = ensureLayoutSections(state.presentationEditor.page.section_count, state.presentationEditor.page.layout_sections);
    const targetIndex = Number(state.presentationEditor.selectedSectionIndex || 0);
    sections[targetIndex] = createPresentationSection({
      ...(sections[targetIndex] || {}),
      type: "html",
      ...normalizeEmbeddedContent(html || `<section style="padding:24px;"><p>${escapeHtml(text)}</p></section>`, ""),
      js_input: "",
      js_highlight: "",
      js_output: "",
      js_input_effect: "none",
      js_highlight_effect: "none",
      js_output_effect: "none",
    });
    state.presentationEditor.page.layout_sections = sections;
    renderPageBlocksEditor();
    setMessage(builderMsg, "Contenido pegado en la sección seleccionada.", false);
  }

  function openPresentationPageBuilder(pageIndex) {
    if (!pageModal) return;
    const pages = getPresentationPages();
    const page = pages[pageIndex];
    if (!page) return;
    state.presentationEditor = {
      pageIndex,
      page: createPresentationPage(page),
      selectedSectionIndex: 0,
    };
    if (pageTitleInput) pageTitleInput.value = state.presentationEditor.page.title || "";
    if (pageSectionCountInput) pageSectionCountInput.value = String(state.presentationEditor.page.section_count || 1);
    if (pageDescriptionInput) pageDescriptionInput.value = state.presentationEditor.page.description || "";
    if (pageBgColorInput) pageBgColorInput.value = state.presentationEditor.page.bg_color || "#ffffff";
    if (pageBgImageInput) pageBgImageInput.value = state.presentationEditor.page.bg_image_url || "";
    if (pageFooterTextInput) pageFooterTextInput.value = state.presentationEditor.page.footer_text || "";
    if (pageFooterColorInput) pageFooterColorInput.value = state.presentationEditor.page.footer_color || "#0f172a";
    renderPageBlocksEditor();
    pageModal.hidden = false;
    document.body.style.overflow = "hidden";
    if (pagePreviewNode) pagePreviewNode.focus();
  }

  function closePresentationPageBuilder() {
    if (!pageModal) return;
    pageModal.hidden = true;
    state.presentationEditor = null;
    document.body.style.overflow = "";
  }

  function persistPresentationEditorPage() {
    if (!state.presentationEditor) return;
    updatePresentationEditorPage();
    const pages = getPresentationPages();
    pages[state.presentationEditor.pageIndex] = createPresentationPage(state.presentationEditor.page);
    setPresentationPages(pages);
    renderPresentationBuilder();
  }

  function addPresentationPage() {
    const pages = getPresentationPages();
    pages.push(createPresentationPage({
      title: "Nueva página",
      section_count: 1,
      layout_sections: [],
      footer_text: "",
      footer_color: "#0f172a",
    }));
    setPresentationPages(pages);
    showSurveyTab("presentation");
    renderPresentationBuilder();
    setMessage(builderMsg, "Página agregada. Ahora puedes construir su contenido.", false);
    openPresentationPageBuilder(pages.length - 1);
  }

  function collectPresentationPagesFromEditor() {
    return getPresentationPages();
  }

  async function savePresentationPages() {
    const pages = getPresentationPages();
    await saveDraft(
      {
        publication_rules_json: {
          ...(state.builder && state.builder.publication_rules_json ? state.builder.publication_rules_json : {}),
          presentation_pages: pages,
        },
      },
      "Presentación guardada."
    );
  }

  function paintMetrics() {
    const metrics = state.bootstrap.metrics || {};
    metricNodes.forEach((node) => {
      const key = node.dataset.encMetric;
      const value = metrics[key];
      if (value == null) return;
      node.textContent = key === "completion_rate" ? `${value}%` : String(value);
    });
  }

  function formatDateForInput(value) {
    if (!value) return "";
    return String(value).slice(0, 16);
  }

  function formatDateLabel(value) {
    if (!value) return "Pendiente";
    return value.replace("T", " ").slice(0, 16);
  }

  function statusPill(status) {
    if (status === "published") return '<span class="enc-pill is-live">Publicada</span>';
    if (status === "closed") return '<span class="enc-pill is-planned">Cerrada</span>';
    return '<span class="enc-pill is-draft">Borrador</span>';
  }

  function parseOptionsText(rawText, type) {
    if (type === "yes_no") {
      return [
        { label: "Sí", value: "yes", orden: 1 },
        { label: "No", value: "no", orden: 2 },
      ];
    }
    if (type === "true_false") {
      return [
        { label: "Verdadero", value: "true", orden: 1 },
        { label: "Falso", value: "false", orden: 2 },
      ];
    }
    if (type === "scale_1_5" || type === "live_scale_1_5") {
      return [1, 2, 3, 4, 5].map((value) => ({ label: String(value), value: String(value), orden: value }));
    }
    if (type === "nps_0_10") {
      return Array.from({ length: 11 }, (_, index) => ({
        label: String(index),
        value: String(index),
        orden: index + 1,
      }));
    }
    return String(rawText || "")
      .split(",")
      .map((part) => part.trim())
      .filter(Boolean)
      .map((label, index) => ({ label, value: label.toLowerCase().replace(/\s+/g, "_"), orden: index + 1 }));
  }

  function typeSupportsOptions(type) {
    return [
      "single_choice",
      "live_poll_single_choice",
      "multiple_choice",
      "yes_no",
      "scale_1_5",
      "live_scale_1_5",
      "nps_0_10",
      "quiz_single_choice",
      "ranking",
      "matrix",
      "likert_scale",
      "semantic_differential",
      "dropdown",
      "image_choice",
      "true_false",
    ].includes(type);
  }

  function defaultOptionsText(type) {
    if (type === "yes_no") return "Sí\nNo";
    if (type === "true_false") return "Verdadero\nFalso";
    if (type === "scale_1_5" || type === "live_scale_1_5") return "1\n2\n3\n4\n5";
    if (type === "nps_0_10") return "0\n1\n2\n3\n4\n5\n6\n7\n8\n9\n10";
    if (type === "likert_scale") return "Totalmente en desacuerdo\nEn desacuerdo\nNeutral\nDe acuerdo\nTotalmente de acuerdo";
    if (type === "semantic_differential") return "Muy negativo\nNegativo\nNeutral\nPositivo\nMuy positivo";
    if (type === "matrix") return "Fila 1\nFila 2\nFila 3";
    return "";
  }

  function getQuestionTypeKeys() {
    return (state.questionTypes || []).map((item) => item.key);
  }

  function questionTypeLabel(key) {
    const labels = {
      short_text: "Texto corto",
      long_text: "Texto largo",
      word_cloud: "Nube de palabras",
      single_choice: "Opción única",
      live_poll_single_choice: "Encuesta en vivo de opción única",
      multiple_choice: "Selección múltiple",
      yes_no: "Sí / No",
      scale_1_5: "Escala del 1 al 5",
      live_scale_1_5: "Escala en vivo del 1 al 5",
      nps_0_10: "NPS del 0 al 10",
      quiz_single_choice: "Quiz de opción única",
      ranking: "Ordenamiento / Priorización",
      matrix: "Matriz de valoraciones",
      likert_scale: "Escala de Likert",
      semantic_differential: "Diferencial semántico",
      date: "Fecha",
      time: "Hora",
      dropdown: "Lista desplegable",
      file_upload: "Carga de archivos",
      slider: "Control deslizante",
      image_choice: "Selección con imágenes",
      true_false: "Verdadero / Falso",
    };
    return labels[key] || key;
  }

  function questionTypePromptLabel() {
    const items = (state.questionTypes || []).map((item) => `${questionTypeLabel(item.key)}\n${item.key}`);
    return items.join("\n\n");
  }

  async function pickQuestionType() {
    const items = (state.questionTypes || []).map((item) => {
      const icon = ({
        short_text: "⌶",
        long_text: "≣",
        word_cloud: "◌",
        single_choice: "◉",
        live_poll_single_choice: "◉",
        multiple_choice: "☑",
        yes_no: "↔",
        scale_1_5: "◔",
        live_scale_1_5: "◔",
        nps_0_10: "◒",
        quiz_single_choice: "✦",
        ranking: "⇅",
        matrix: "▦",
        likert_scale: "☷",
        semantic_differential: "⟷",
        date: "◷",
        time: "◔",
        dropdown: "▾",
        file_upload: "⤴",
        slider: "⎯",
        image_choice: "▥",
        true_false: "✓",
      })[item.key] || "•";
      return `
        <button type="button" class="enc-type-picker-item" data-enc-type-choice="${item.key}">
          <span class="enc-type-picker-icon" aria-hidden="true">${icon}</span>
          <span class="enc-type-picker-copy">
            <strong>${questionTypeLabel(item.key)}</strong>
            <small>${item.key}</small>
          </span>
        </button>
      `;
    }).join("");
    const container = document.createElement("div");
    container.className = "enc-type-picker";
    container.innerHTML = `
      <div class="enc-type-picker-head">
        <p class="enc-sidebar-label">Tipo de pregunta</p>
        <div class="enc-type-picker-list">${items}</div>
      </div>
    `;
    const anchor = builderMsg || root;
    anchor.innerHTML = "";
    anchor.appendChild(container);
    setMessage("", false);
    return await new Promise((resolve) => {
      container.addEventListener("click", (event) => {
        const button = event.target.closest("[data-enc-type-choice]");
        if (!button) return;
        resolve(String(button.dataset.encTypeChoice || ""));
      }, { once: true });
    });
  }

  function parseQuestionModalOptions(type) {
    if (!typeSupportsOptions(type)) return [];
    return parseOptionsText(
      String((questionModalOptions && questionModalOptions.value) || "")
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean)
        .join(", "),
      type
    );
  }

  function fillSurveyEditor() {
    const builder = state.builder;
    if (!builder) return;
    const settings = builder.settings_json || {};
    const publicationRules = builder.publication_rules_json || {};
    if (editorTitle) editorTitle.value = builder.nombre || "";
    if (editorParticipaciones) editorParticipaciones.textContent = String(builder.responses_count || 0);
    if (editorResponsable) {
      editorResponsable.textContent = builder.created_by_name || builder.owner_name || builder.responsable || "SIPET";
    }
    if (editorRestringido) {
      const labels = {
        internal: "Personal interno",
        mixed: "Audiencia mixta",
        public_link: "Enlace público",
      };
      editorRestringido.textContent = labels[builder.audience_mode] || "Todos los participantes autorizados";
    }
    if (editorAudienceMode) editorAudienceMode.value = builder.audience_mode || "internal";
    if (editorAnonymityMode) editorAnonymityMode.value = builder.anonymity_mode || "identified";
    if (editorScoringMode) editorScoringMode.value = settings.scoring_mode || "none";
    if (editorPublicationMode) editorPublicationMode.value = builder.publication_mode || "manual";
    if (editorResponseMode) editorResponseMode.value = publicationRules.response_mode || "standard";
    if (addStructureButton) {
      addStructureButton.textContent = publicationRules.response_mode === "presentation"
        ? "+ Agregar página"
        : "+ Agregar sección";
    }
    if (editorDescription) editorDescription.value = builder.descripcion || "";
    if (editorHeaderHtml) editorHeaderHtml.value = publicationRules.header_html || "";
    if (editorFooterHtml) editorFooterHtml.value = publicationRules.footer_html || "";
    if (editorInitialMessage) editorInitialMessage.value = publicationRules.initial_message || "";
    if (editorFinalMessage) editorFinalMessage.value = publicationRules.final_message || "";
    if (editorImagenUrl) editorImagenUrl.value = publicationRules.image_url || "";
    renderPublicLinkSummary(builder);
    renderPresentationBuilder();
    const imgPosRadio = document.querySelector(`[name="enc-image-position"][value="${publicationRules.image_position || "background"}"]`);
    if (imgPosRadio) imgPosRadio.checked = true;
  }

  function renderQuestionModalPreview() {
    if (!questionModalPreview) return;
    const type = state.questionModalType || (state.questionTypes[0] && state.questionTypes[0].key) || "short_text";
    const title = String((questionModalTitle && questionModalTitle.value) || "").trim() || "¿Cuál es tu pregunta?";
    const options = parseQuestionModalOptions(type).slice(0, 5);
    let body = '<div class="enc-input">respuesta</div>';
    if (["single_choice", "live_poll_single_choice", "quiz_single_choice", "yes_no", "true_false", "dropdown", "image_choice"].includes(type)) {
      const source = options.length ? options : parseOptionsText("", type);
      body = source.slice(0, 3).map((option, index) => `<div class="enc-question-meta">${index === 1 ? "◉" : "○"} ${option.label}</div>`).join("");
    } else if (["multiple_choice", "ranking"].includes(type)) {
      const source = options.length ? options : [{ label: "opción 1" }, { label: "opción 2" }, { label: "opción 3" }];
      body = source.slice(0, 3).map((option, index) => `<div class="enc-question-meta">${index === 0 ? "☑" : "☐"} ${option.label}</div>`).join("");
    } else if (["scale_1_5", "live_scale_1_5", "nps_0_10", "slider", "likert_scale", "semantic_differential", "matrix"].includes(type)) {
      const source = options.length ? options : [{ label: "1" }, { label: "2" }, { label: "3" }, { label: "4" }, { label: "5" }];
      body = `<div class="enc-builder-toolbar">${source.slice(0, 5).map((option) => `<span class="enc-pill is-draft">${option.label}</span>`).join("")}</div>`;
    }
    questionModalPreview.innerHTML = `
      <strong>${title}</strong>
      <p class="enc-question-meta">${questionTypeLabel(type)}</p>
      ${body}
    `;
  }

  function renderQuestionModalTypeList() {
    if (!questionModalTypes) return;
    if (!state.questionModalType) {
      state.questionModalType = state.questionTypes[0] ? state.questionTypes[0].key : "short_text";
    }
    questionModalTypes.innerHTML = (state.questionTypes || []).map((item) => `
      <button type="button" class="enc-question-type-chip ${state.questionModalType === item.key ? "is-active" : ""}" data-enc-modal-type="${item.key}">
        <input type="radio" name="enc-modal-type" ${state.questionModalType === item.key ? "checked" : ""} tabindex="-1">
        <span class="enc-question-type-chip-copy">
          <strong>${questionTypeLabel(item.key)}</strong>
          <small>${item.key}</small>
        </span>
      </button>
    `).join("");
    const supportsOpts = typeSupportsOptions(state.questionModalType);
    if (questionModalOptions) {
      if (supportsOpts) {
        questionModalOptions.disabled = false;
        if (!questionModalOptions.value.trim()) {
          questionModalOptions.value = defaultOptionsText(state.questionModalType);
        }
      } else {
        questionModalOptions.disabled = true;
        questionModalOptions.value = "";
      }
    }
    if (inlineOptionsPanel) {
      inlineOptionsPanel.hidden = !supportsOpts;
      if (supportsOpts) {
        if (inlineOptionsLabel) {
          inlineOptionsLabel.textContent = `Alternativas — ${questionTypeLabel(state.questionModalType)}`;
        }
        if (inlineOptionsTa) {
          inlineOptionsTa.value = (questionModalOptions && questionModalOptions.value) || defaultOptionsText(state.questionModalType);
        }
      }
    }
    if (questionModalPreview) questionModalPreview.hidden = supportsOpts;
    renderQuestionModalPreview();
  }

  function resetQuestionModal() {
    state.questionModalType = state.questionTypes[0] ? state.questionTypes[0].key : "short_text";
    if (questionModalTitle) questionModalTitle.value = "";
    if (questionModalDescription) questionModalDescription.value = "";
    if (questionModalRequired) questionModalRequired.value = "false";
    if (questionModalOptions) questionModalOptions.value = defaultOptionsText(state.questionModalType);
    if (inlineOptionsTa) inlineOptionsTa.value = defaultOptionsText(state.questionModalType);
    showQuestionModalTab("answers");
    renderQuestionModalTypeList();
  }

  function openQuestionModal() {
    if (!questionModal) return;
    resetQuestionModal();
    questionModal.hidden = false;
    document.body.style.overflow = "hidden";
    if (questionModalTitle) questionModalTitle.focus();
  }

  function closeQuestionModal() {
    if (!questionModal) return;
    questionModal.hidden = true;
    document.body.style.overflow = "";
  }

  function openOptionsPopup(type) {
    if (!optionsPopup || !optionsPopupTextarea) return;
    const existing = questionModalOptions ? questionModalOptions.value.trim() : "";
    optionsPopupTextarea.value = existing || defaultOptionsText(type) || "";
    if (optionsPopupTitle) {
      optionsPopupTitle.textContent = `Alternativas — ${questionTypeLabel(type)}`;
    }
    optionsPopup.hidden = false;
    optionsPopupTextarea.focus();
  }

  function closeOptionsPopup() {
    if (!optionsPopup) return;
    optionsPopup.hidden = true;
  }

  function confirmOptionsPopup() {
    if (questionModalOptions && optionsPopupTextarea) {
      questionModalOptions.value = optionsPopupTextarea.value;
    }
    closeOptionsPopup();
    renderQuestionModalPreview();
  }

  if (optionsPopupConfirm) optionsPopupConfirm.addEventListener("click", confirmOptionsPopup);
  if (optionsPopupCancel) optionsPopupCancel.addEventListener("click", closeOptionsPopup);
  if (optionsPopupClose) optionsPopupClose.addEventListener("click", closeOptionsPopup);
  if (optionsPopupBackdrop) optionsPopupBackdrop.addEventListener("click", closeOptionsPopup);
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    if (optionsPopup && !optionsPopup.hidden) {
      closeOptionsPopup();
      return;
    }
    if (pageModal && !pageModal.hidden) {
      closePresentationPageBuilder();
      return;
    }
    if (questionModal && !questionModal.hidden) {
      closeQuestionModal();
    }
  });

  function parseCsvValues(rawText) {
    return String(rawText || "")
      .split(",")
      .map((part) => part.trim())
      .filter(Boolean);
  }

  function stringifyManualGroups(groups) {
    if (!Array.isArray(groups) || !groups.length) return "";
    return JSON.stringify(groups, null, 2);
  }

  function normalizeManualGroups(groups) {
    if (!Array.isArray(groups)) return [];
    return groups
      .map(function (group) {
        const members = Array.isArray(group && group.members) ? group.members : [];
        return {
          name: String(group && group.name || "").trim(),
          description: String(group && group.description || "").trim(),
          members: members
            .map(function (member) {
              return {
                user_id: String(member && member.user_id || "").trim(),
                nombre: String(member && member.nombre || "").trim(),
                role: String(member && member.role || "").trim(),
                department: String(member && member.department || "").trim(),
              };
            })
            .filter(function (member) {
              return member.user_id || member.nombre || member.role || member.department;
            }),
        };
      })
      .filter(function (group) {
        return group.name || group.description || group.members.length;
      });
  }

  function parseManualGroups(rawText) {
    const text = String(rawText || "").trim();
    if (!text) return [];
    const parsed = JSON.parse(text);
    if (Array.isArray(parsed)) return normalizeManualGroups(parsed);
    return normalizeManualGroups([parsed]);
  }

  function createManualMember(member) {
    return {
      user_id: String(member && member.user_id || "").trim(),
      nombre: String(member && member.nombre || "").trim(),
      role: String(member && member.role || "").trim(),
      department: String(member && member.department || "").trim(),
    };
  }

  function createManualGroup(group) {
    const normalizedMembers = Array.isArray(group && group.members) && group.members.length
      ? group.members.map(createManualMember)
      : [createManualMember({})];
    return {
      name: String(group && group.name || "").trim(),
      description: String(group && group.description || "").trim(),
      members: normalizedMembers,
    };
  }

  function readManualGroupsFromEditor() {
    if (!manualGroupsList) {
      return parseManualGroups(manualGroupsField ? manualGroupsField.value : "");
    }
    const groups = Array.from(manualGroupsList.querySelectorAll("[data-enc-manual-group]"))
      .map(function (groupNode) {
        const group = {
          name: String((groupNode.querySelector("[data-enc-manual-group-name]") || {}).value || "").trim(),
          description: String((groupNode.querySelector("[data-enc-manual-group-description]") || {}).value || "").trim(),
          members: Array.from(groupNode.querySelectorAll("[data-enc-manual-member]")).map(function (memberNode) {
            return {
              user_id: String((memberNode.querySelector("[data-enc-member-user-id]") || {}).value || "").trim(),
              nombre: String((memberNode.querySelector("[data-enc-member-name]") || {}).value || "").trim(),
              role: String((memberNode.querySelector("[data-enc-member-role]") || {}).value || "").trim(),
              department: String((memberNode.querySelector("[data-enc-member-department]") || {}).value || "").trim(),
            };
          }),
        };
        return group;
      });
    return normalizeManualGroups(groups);
  }

  function syncManualGroupsField() {
    if (!manualGroupsField) return;
    manualGroupsField.value = stringifyManualGroups(readManualGroupsFromEditor());
  }

  function renderManualGroupsEditor(groups) {
    if (!manualGroupsList) return;
    const normalizedGroups = Array.isArray(groups) && groups.length
      ? normalizeManualGroups(groups).map(createManualGroup)
      : [];
    manualGroupsList.innerHTML = normalizedGroups.length
      ? normalizedGroups.map(function (group, groupIndex) {
          return `
            <section class="enc-manual-group-card" data-enc-manual-group="${groupIndex}">
              <div class="enc-manual-group-head">
                <strong>Grupo ${groupIndex + 1}</strong>
                <button type="button" class="enc-mini-btn" data-enc-remove-group="${groupIndex}">Quitar grupo</button>
              </div>
              <div class="enc-manual-group-grid">
                <label class="enc-field">
                  <span>Nombre del grupo</span>
                  <input data-enc-manual-group-name class="enc-input" type="text" value="${escapeHtml(group.name)}" placeholder="Grupo especial">
                </label>
                <label class="enc-field">
                  <span>Descripción</span>
                  <input data-enc-manual-group-description class="enc-input" type="text" value="${escapeHtml(group.description)}" placeholder="Grupo manual de encuesta">
                </label>
              </div>
              <div class="enc-manual-members">
                ${group.members.map(function (member, memberIndex) {
                  return `
                    <div class="enc-manual-member-row" data-enc-manual-member="${memberIndex}">
                      <input data-enc-member-user-id class="enc-input" type="text" value="${escapeHtml(member.user_id)}" placeholder="user_id">
                      <input data-enc-member-name class="enc-input" type="text" value="${escapeHtml(member.nombre)}" placeholder="Nombre">
                      <input data-enc-member-role class="enc-input" type="text" value="${escapeHtml(member.role)}" placeholder="Rol">
                      <input data-enc-member-department class="enc-input" type="text" value="${escapeHtml(member.department)}" placeholder="Departamento">
                      <button type="button" class="enc-mini-btn" data-enc-remove-member="${memberIndex}">Quitar</button>
                    </div>
                  `;
                }).join("")}
              </div>
              <div class="enc-manual-groups-actions">
                <button type="button" class="enc-mini-btn is-primary" data-enc-add-member="${groupIndex}">Agregar miembro</button>
              </div>
            </section>
          `;
        }).join("")
      : '<div class="enc-placeholder">No hay grupos manuales. Agrega uno para materializar miembros específicos.</div>';
    syncManualGroupsField();
  }

  function ensureManualGroupsEditor() {
    renderManualGroupsEditor(parseManualGroups(manualGroupsField ? manualGroupsField.value : ""));
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function getPublicSurveyUrl(builder) {
    if (!builder) return "";
    const token = String(builder.public_link_token || "").trim();
    const isPublic = Boolean(builder.is_public_link_enabled) || isPublicLinkAudience(builder.audience_mode);
    const isPublished = ["published", "scheduled"].includes(String(builder.status || "").trim().toLowerCase());
    if (!token || !isPublic || !isPublished) return "";
    return `${window.location.origin}/api/public/encuestas/${encodeURIComponent(token)}`;
  }

  function getPresenterUrl(builder) {
    if (!builder || builder.id == null) return "";
    return `${window.location.origin}/encuestas/presentador/${encodeURIComponent(builder.id)}`;
  }

  async function copyText(text) {
    if (!text) return;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text);
      return;
    }
    const temp = document.createElement("textarea");
    temp.value = text;
    temp.setAttribute("readonly", "readonly");
    temp.style.position = "absolute";
    temp.style.left = "-9999px";
    document.body.appendChild(temp);
    temp.select();
    document.execCommand("copy");
    document.body.removeChild(temp);
  }

  function appendHtmlImage(textarea, imageUrl) {
    if (!textarea || !imageUrl) return;
    const snippet = `<img src="${imageUrl}" alt="" style="max-width:100%;height:auto;border-radius:16px;">`;
    const current = String(textarea.value || "").trim();
    textarea.value = current ? `${current}\n${snippet}` : snippet;
  }

  async function uploadSurveyImageFile(file) {
    if (!state.currentInstanceId) {
      throw new Error("Selecciona una campaña primero.");
    }
    if (!file) {
      throw new Error("Selecciona una imagen.");
    }
    const formData = new FormData();
    formData.append("file", file);
    const resp = await fetch(
      `/api/encuestas/campanas/${state.currentInstanceId}/upload-image`,
      { method: "POST", body: formData, credentials: "same-origin" }
    );
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || resp.statusText);
    }
    return resp.json();
  }

  async function promptAndInsertHtmlImage(targetTextarea) {
    if (!targetTextarea) return;
    if (!state.currentInstanceId) {
      throw new Error("Selecciona una campaña primero.");
    }
    const picker = document.createElement("input");
    picker.type = "file";
    picker.accept = "image/jpeg,image/png,image/gif,image/webp,image/svg+xml";
    const file = await new Promise((resolve) => {
      picker.addEventListener("change", function () {
        resolve(picker.files && picker.files[0] ? picker.files[0] : null);
      }, { once: true });
      picker.click();
    });
    if (!file) return;
    setMessage(builderMsg, "Subiendo imagen...", false);
    const data = await uploadSurveyImageFile(file);
    appendHtmlImage(targetTextarea, data.url || "");
    setMessage(builderMsg, "Imagen insertada en el HTML. Guarda el contenido para aplicarla.", false);
  }

  function renderPublicLinkSummary(builder) {
    if (!publicLinkSummary || !publicLinkAnchor || !surveyInstanceId || !surveyIntegrationToken) return;
    const publicUrl = getPublicSurveyUrl(builder);
    const presenterUrl = getPresenterUrl(builder);
    const instanceId = builder && builder.id != null ? String(builder.id) : "";
    const integrationToken = String((builder && builder.settings_json && builder.settings_json.live_integration_token) || "").trim();
    if (!publicUrl && !presenterUrl && !instanceId && !integrationToken) {
      publicLinkSummary.hidden = true;
      publicLinkAnchor.textContent = "";
      publicLinkAnchor.removeAttribute("href");
      if (openPublicLink) openPublicLink.hidden = true;
      if (presenterLinkAnchor) {
        presenterLinkAnchor.textContent = "";
        presenterLinkAnchor.removeAttribute("href");
      }
      if (openPresenterLink) openPresenterLink.hidden = true;
      surveyInstanceId.textContent = "";
      surveyIntegrationToken.textContent = "";
      return;
    }
    publicLinkSummary.hidden = false;
    surveyInstanceId.textContent = instanceId || "Sin ID";
    surveyIntegrationToken.textContent = integrationToken || "Sin token";
    const status = String((builder && builder.status) || "").trim().toLowerCase();
    const publicLinkHint = ["published", "scheduled"].includes(status)
      ? "Habilita el enlace público para abrir la encuesta interactiva."
      : "Publica la encuesta para habilitar el acceso público.";
    publicLinkAnchor.href = publicUrl || "#";
    publicLinkAnchor.textContent = publicUrl || publicLinkHint;
    publicLinkAnchor.title = publicUrl || "";
    if (openPublicLink) {
      openPublicLink.href = publicUrl || "#";
      openPublicLink.hidden = !publicUrl;
    }
    if (presenterLinkAnchor) {
      presenterLinkAnchor.href = presenterUrl || "#";
      presenterLinkAnchor.textContent = presenterUrl || "Disponible al guardar la encuesta.";
      presenterLinkAnchor.title = presenterUrl || "";
    }
    if (openPresenterLink) {
      openPresenterLink.href = presenterUrl || "#";
      openPresenterLink.hidden = !presenterUrl;
    }
  }

  function getCurrentSection() {
    const sections = (state.builder && state.builder.sections) || [];
    return sections.find((section) => section.id === state.selectedSectionId) || null;
  }

  function renderCampaigns() {
    if (campaignsBody) {
      if (!state.campaigns.length) {
        campaignsBody.innerHTML = '<tr><td colspan="5">No hay campañas registradas.</td></tr>';
      } else {
        campaignsBody.innerHTML = state.campaigns
          .map(
            (campaign) => `
              <tr>
                <td>${campaign.nombre}</td>
                <td>${statusPill(campaign.status)}</td>
                <td>${campaign.audience_mode || "internal"}</td>
                <td>${formatDateLabel(campaign.published_at || campaign.schedule_start_at)}</td>
                <td>
                  ${can("manage_surveys") ? `<button type="button" class="enc-mini-btn is-primary" data-enc-open-builder="${campaign.id}">Constructor</button>` : ""}
                  ${can("view_results_summary") ? `<button type="button" class="enc-mini-btn" data-enc-open-results="${campaign.id}">Resultados</button>` : ""}
                </td>
              </tr>
            `
          )
          .join("");
      }
    }
    if (!campaignsKanban) return;
    if (!state.campaigns.length) {
      campaignsKanban.innerHTML = '<div class="enc-campaign-board-empty">No hay campañas registradas.</div>';
      return;
    }
    campaignsKanban.innerHTML = state.campaigns
      .map(
        (campaign) => `
          <article class="enc-campaign-board-card">
            <div class="enc-campaign-board-head">
              <div>
                <strong>${campaign.nombre}</strong>
                <p>${campaign.descripcion || "Campaña lista para gestión y seguimiento."}</p>
              </div>
              ${statusPill(campaign.status)}
            </div>
            <div class="enc-campaign-board-meta">
              <div class="enc-campaign-board-meta-item">
                <span>Audiencia</span>
                <strong>${campaign.audience_mode || "internal"}</strong>
              </div>
              <div class="enc-campaign-board-meta-item">
                <span>Publicación</span>
                <strong>${formatDateLabel(campaign.published_at || campaign.schedule_start_at)}</strong>
              </div>
            </div>
            <div class="enc-campaign-board-actions">
              ${can("manage_surveys") ? `<button type="button" class="enc-mini-btn is-primary" data-enc-open-builder="${campaign.id}">Constructor</button>` : ""}
              ${can("view_results_summary") ? `<button type="button" class="enc-mini-btn" data-enc-open-results="${campaign.id}">Resultados</button>` : ""}
            </div>
          </article>
        `
      )
      .join("");
  }

  function renderCampaignView() {
    const currentView = state.campaignView || "kanban";
    campaignViewButtons.forEach((button) => {
      const view = String(button.dataset.encCampaignView || "");
      const isActive = view === currentView;
      button.classList.toggle("is-active", isActive);
      if (button.classList.contains("is-disabled")) return;
      button.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
    if (campaignsKanban) campaignsKanban.hidden = currentView !== "kanban";
    if (campaignsListWrap) campaignsListWrap.hidden = currentView !== "list";
  }

  function renderBuilderSelect() {
    if (!builderSelect) return;
    const selected = state.currentInstanceId ? String(state.currentInstanceId) : "";
    builderSelect.innerHTML = ['<option value="">Selecciona una campaña</option>']
      .concat(
        state.campaigns.map(
          (campaign) => `<option value="${campaign.id}" ${selected === String(campaign.id) ? "selected" : ""}>${campaign.nombre}</option>`
        )
      )
      .join("");
    if (resultsSelect) {
      resultsSelect.innerHTML = builderSelect.innerHTML;
    }
  }

  function renderTemplateSelect() {
    if (!templateSelect) return;
    templateSelect.innerHTML = ['<option value="">Usar plantilla</option>']
      .concat(
        state.templates.map(
          (template) => `<option value="${template.id}">${template.nombre}</option>`
        )
      )
      .join("");
  }

  function applyPermissionsUI() {
    root.querySelectorAll('[data-enc-action="new-survey"], [data-enc-action="add-section"], [data-enc-action="add-question"], [data-enc-action="publish-campaign"], [data-enc-action="close-campaign"]').forEach((node) => {
      node.style.display = can("manage_surveys") ? "" : "none";
    });
    root.querySelectorAll('[data-enc-action="create-from-template"], [data-enc-action="save-as-template"]').forEach((node) => {
      node.style.display = can("manage_surveys") ? "" : "none";
    });
    if (builderSelect) builderSelect.disabled = !can("manage_surveys");
    if (templateSelect) templateSelect.disabled = !can("manage_surveys");
    if (resultsExportCsv) resultsExportCsv.style.display = can("export_sensitive_results") ? "" : "none";
    if (resultsExportPdf) resultsExportPdf.style.display = can("export_sensitive_results") ? "" : "none";
    if (resultsExportXlsx) resultsExportXlsx.style.display = can("export_sensitive_results") ? "" : "none";
  }

  function segmentSummaryRows() {
    if (!state.results || !state.results.segment_report) return [];
    return ["department", "role", "company"]
      .flatMap((key) => (state.results.segment_report[key] || []).slice(0, 3));
  }

  function renderResultsChart() {
    if (!resultsChartNode || !state.results || !window.Chart) return;
    const summary = state.results.summary || {};
    if (state.chart) {
      state.chart.destroy();
    }
    state.chart = new window.Chart(resultsChartNode, {
      type: "bar",
      data: {
        labels: ["Finalización", "NPS", "CSAT", "CES", "Quiz"],
        datasets: [
          {
            label: "Indicadores",
            data: [
              summary.completion_pct_avg || 0,
              summary.nps_score || 0,
              summary.csat_score || 0,
              summary.ces_score || 0,
              summary.quiz_approval_pct || 0,
            ],
            backgroundColor: ["#2b6c4f", "#1d4ed8", "#0f766e", "#c2410c", "#7c3aed"],
            borderRadius: 10,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } },
      },
    });
  }

  function renderComparison() {
    if (!resultsComparison || !state.results) return;
    const rows = state.results.comparison_report || [];
    resultsComparison.innerHTML = rows.length
      ? rows.map((row) => `
          <article class="enc-section-card">
            <strong>${row.segment}</strong>
            <p class="enc-section-meta">
              ${row.responses} respuesta(s) · Finalización ${row.completion_pct_avg ?? 0}% · Score ${row.total_score_avg ?? "N/A"} · NPS ${row.nps_score ?? "N/A"} · CSAT ${row.csat_score ?? "N/A"} · CES ${row.ces_score ?? "N/A"}
            </p>
          </article>
        `).join("")
      : '<div class="enc-placeholder">No hay comparativos disponibles para el filtro actual.</div>';
  }

  function syncResultsFilters() {
    if (!state.results) return;
    const available = state.results.available_filters || {};
    const applied = state.results.applied_filters || {};
    fillResultsFilterSelect(resultsFilterDepartment, available.departments || [], "Todos los departamentos", applied.department || "");
    fillResultsFilterSelect(resultsFilterRole, available.roles || [], "Todos los roles", applied.role || "");
    fillResultsFilterSelect(resultsFilterCompany, available.companies || [], "Todas las empresas", applied.company || "");
    if (resultsSegmentBy) {
      resultsSegmentBy.value = applied.segment_by || "department";
    }
  }

  function renderResults() {
    if (!resultsBody || !resultsEmpty) return;
    const data = state.results;
    if (!data) {
      resultsBody.hidden = true;
      resultsEmpty.hidden = false;
      return;
    }
    const summary = data.summary || {};
    resultsBody.hidden = false;
    resultsEmpty.hidden = true;
    resultsResponsesCount.textContent = String(summary.responses_count || 0);
    resultsCompletion.textContent = `${summary.completion_pct_avg || 0}%`;
    resultsNps.textContent = String(summary.nps_score ?? 0);
    resultsScore.textContent = String(summary.total_score_avg ?? 0);
    const filters = selectedResultsFilters();
    const query = new URLSearchParams();
    if (filters.department) query.set("department", filters.department);
    if (filters.role) query.set("role", filters.role);
    if (filters.company) query.set("company", filters.company);
    if (filters.segment_by) query.set("segment_by", filters.segment_by);
    const suffix = query.toString() ? `?${query.toString()}` : "";
    if (resultsExportCsv) {
      resultsExportCsv.href = `/api/encuestas/campanas/${data.instance.id}/export.csv${suffix}`;
    }
    if (resultsExportPdf) {
      resultsExportPdf.href = `/api/encuestas/campanas/${data.instance.id}/export.pdf${suffix}`;
    }
    if (resultsExportXlsx) {
      resultsExportXlsx.href = `/api/encuestas/campanas/${data.instance.id}/export.xlsx${suffix}`;
    }
    resultsSegments.innerHTML = segmentSummaryRows().length
      ? segmentSummaryRows().map((item) => `
          <article class="enc-section-card">
            <strong>${item.label}: ${item.segment}</strong>
            <p class="enc-section-meta">${item.responses} respuesta(s) · Finalización ${item.completion_pct_avg ?? 0}% · Score ${item.score_avg ?? "N/A"}</p>
          </article>
        `).join("")
      : '<div class="enc-placeholder">No hay segmentos con respuestas enviadas.</div>';
    resultsQuestions.innerHTML = (data.question_report || []).length
      ? data.question_report.map((item) => {
          const options = (item.options || []).length
            ? `<div class="enc-question-meta">${item.options.map((option) => `${option.label}: ${option.count}`).join(" · ")}</div>`
            : `<div class="enc-question-meta">${(item.sample_answers || []).join(" · ") || "Sin muestras"}</div>`;
          return `
            <article class="enc-question-card">
              <strong>${item.section_title} · ${item.question_title}</strong>
              <p class="enc-question-meta">${questionTypeLabel(item.question_type)} · ${item.responses_count} respuesta(s) · Score ${item.avg_score ?? "N/A"}</p>
              ${options}
            </article>
          `;
        }).join("")
      : '<div class="enc-placeholder">No hay respuestas enviadas para generar reporte.</div>';
    resultsResponsesBody.innerHTML = (data.responses_table || []).length
      ? data.responses_table.map((row) => `
          <tr>
            <td>${row.respondent_name}</td>
            <td>${row.role || "Sin dato"}</td>
            <td>${row.department || "Sin dato"}</td>
            <td>${row.status}</td>
            <td>${row.total_score ?? "N/A"}</td>
            <td>${formatDateLabel(row.submitted_at)}</td>
          </tr>
        `).join("")
      : '<tr><td colspan="6">Sin respuestas enviadas.</td></tr>';
    syncResultsFilters();
    renderComparison();
    renderResultsChart();
  }

  function fillBuilderForms() {
    const builder = state.builder;
    if (!builder) return;
    const settings = builder.settings_json || {};
    document.getElementById("enc-general-nombre").value = builder.nombre || "";
    document.getElementById("enc-general-descripcion").value = builder.descripcion || "";
    document.getElementById("enc-general-publication-mode").value = builder.publication_mode || "manual";
    document.getElementById("enc-general-start-at").value = formatDateForInput(builder.schedule_start_at);
    document.getElementById("enc-general-end-at").value = formatDateForInput(builder.schedule_end_at);
    if (audienceModeInput) audienceModeInput.value = builder.audience_mode || "internal";
    document.getElementById("enc-audience-source-app").value = builder.source_app || "";
    document.getElementById("enc-audience-assignment-type").value = settings.assignment_type || "user";
    document.getElementById("enc-audience-values").value = Array.isArray(settings.assignment_values)
      ? settings.assignment_values.join(", ")
      : "";
    document.getElementById("enc-audience-group-note").value = settings.audience_note || "";
    if (manualGroupsField) manualGroupsField.value = stringifyManualGroups(settings.manual_groups);
    renderManualGroupsEditor(settings.manual_groups);
    document.getElementById("enc-rules-anonymity-mode").value = builder.anonymity_mode || "identified";
    document.getElementById("enc-rules-scoring-mode").value = settings.scoring_mode || "none";
    document.getElementById("enc-rules-json").value = JSON.stringify(builder.publication_rules_json || {}, null, 2);
    if (publicLinkEnabledInput) {
      publicLinkEnabledInput.value = builder.is_public_link_enabled || isPublicLinkAudience(builder.audience_mode) ? "true" : "false";
    }
    document.getElementById("enc-public-link-token").value = builder.public_link_token || "";
    document.getElementById("enc-publication-due-at").value = formatDateForInput(settings.assignment_due_at);
    syncPublicLinkControls();
  }

  function renderSections() {
    if (!sectionsList) return;
    const sections = (state.builder && state.builder.sections) || [];
    if (!sections.length) {
      sectionsList.innerHTML = '<div class="enc-placeholder">Aún no hay secciones. Agrega la primera.</div>';
      questionsList.innerHTML = "";
      questionsEmpty.style.display = "";
      return;
    }
    if (!state.selectedSectionId || !sections.some((section) => section.id === state.selectedSectionId)) {
      state.selectedSectionId = sections[0].id;
    }
    sectionsList.innerHTML = sections
      .map((section, index) => {
        const activeClass = section.id === state.selectedSectionId ? "is-active" : "";
        return `
          <article class="enc-section-card ${activeClass}" data-enc-section-id="${section.id}">
            <strong>${index + 1}. ${section.titulo}</strong>
            <p class="enc-section-meta">${section.descripcion || "Sin descripción"} · ${section.questions.length} pregunta(s)</p>
            <div class="enc-section-actions">
              <button type="button" class="enc-mini-btn" data-enc-select-section="${section.id}">Abrir</button>
              <button type="button" class="enc-mini-btn" data-enc-edit-section="${section.id}">Editar</button>
              <button type="button" class="enc-mini-btn" data-enc-section-up="${section.id}">Subir</button>
              <button type="button" class="enc-mini-btn" data-enc-section-down="${section.id}">Bajar</button>
            </div>
          </article>
        `;
      })
      .join("");
    renderQuestions();
  }

  function renderQuestions() {
    const section = getCurrentSection();
    if (!section) {
      questionsList.innerHTML = "";
      questionsEmpty.style.display = "";
      return;
    }
    questionsEmpty.style.display = "none";
    questionsList.innerHTML = (section.questions || [])
      .map(
        (question, index) => `
          <article class="enc-question-card">
            <strong>${index + 1}. ${question.titulo}</strong>
            <p class="enc-question-meta">${questionTypeLabel(question.question_type)} · ${question.is_required ? "Obligatoria" : "Opcional"}</p>
            <div class="enc-question-actions">
              <button type="button" class="enc-mini-btn" data-enc-edit-question="${question.id}">Editar</button>
              <button type="button" class="enc-mini-btn" data-enc-duplicate-question="${question.id}">Duplicar</button>
              <button type="button" class="enc-mini-btn" data-enc-question-up="${question.id}">Subir</button>
              <button type="button" class="enc-mini-btn" data-enc-question-down="${question.id}">Bajar</button>
            </div>
          </article>
        `
      )
      .join("");
  }

  function renderValidation() {
    if (publishCampaignButton) publishCampaignButton.disabled = !state.currentInstanceId;
    if (closeCampaignButton) closeCampaignButton.disabled = !state.currentInstanceId;
    if (!validationBox) return;
    const validation = (state.builder && state.builder.publish_validation) || null;
    if (!validation) {
      validationBox.className = "enc-validation-box";
      validationBox.textContent = "Selecciona una campaña para evaluar su publicación.";
      return;
    }
    validationBox.className = `enc-validation-box ${validation.ok ? "is-ok" : "is-error"}`;
    validationBox.innerHTML = validation.ok
      ? "La encuesta cumple las validaciones mínimas para publicación."
      : `<strong>Faltantes:</strong><ul>${validation.errors.map((error) => `<li>${error}</li>`).join("")}</ul>`;
  }

  async function loadPreview() {
    if (!state.currentInstanceId || !previewRoot) return;
    const preview = await fetchJSON(`/api/encuestas/campanas/${state.currentInstanceId}/preview`);
    previewRoot.innerHTML = preview.html;
  }

  async function loadCampaigns(focusBuilder) {
    state.campaigns = await fetchJSON("/api/encuestas/campanas");
    renderCampaigns();
    renderBuilderSelect();
    const shouldAutoloadBuilder = !state.currentInstanceId && state.campaigns.length;
    if ((focusBuilder || shouldAutoloadBuilder) && state.campaigns.length) {
      const candidate = state.currentInstanceId || state.campaigns[0].id;
      await loadBuilder(candidate);
      if (focusBuilder) showPanel("constructor");
      return;
    }
    renderValidation();
  }

  async function loadQuestionTypes() {
    state.questionTypes = await fetchJSON("/api/encuestas/question-types");
  }

  async function loadTemplates() {
    state.templates = await fetchJSON("/api/encuestas/templates");
    renderTemplateSelect();
  }

  async function loadPermissions() {
    state.permissions = await fetchJSON("/api/encuestas/permissions");
    applyPermissionsUI();
  }

  async function loadAssignableUsers() {
    state.assignableUsers = await fetchJSON("/api/encuestas/assignable-users");
  }

  async function loadBuilder(instanceId) {
    if (!instanceId) return;
    state.currentInstanceId = Number(instanceId);
    state.builder = await fetchJSON(`/api/encuestas/campanas/${instanceId}/builder`);
    if (!state.selectedSectionId && state.builder.sections && state.builder.sections.length) {
      state.selectedSectionId = state.builder.sections[0].id;
    }
    fillBuilderForms();
    fillSurveyEditor();
    renderSections();
    renderValidation();
    await loadPreview();
  }

  async function ensureChartLibrary() {
    if (window.Chart) return;
    await new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "/static/vendor/chart.umd.min.js";
      script.onload = resolve;
      script.onerror = reject;
      document.body.appendChild(script);
    });
  }

  async function loadResults(instanceId) {
    if (!instanceId) return;
    await ensureChartLibrary();
    const filters = selectedResultsFilters();
    const query = new URLSearchParams();
    if (filters.department) query.set("department", filters.department);
    if (filters.role) query.set("role", filters.role);
    if (filters.company) query.set("company", filters.company);
    if (filters.segment_by) query.set("segment_by", filters.segment_by);
    state.results = await fetchJSON(`/api/encuestas/campanas/${instanceId}/analytics?${query.toString()}`);
    if (state.results && state.results.permissions) {
      state.permissions = { ...state.permissions, ...state.results.permissions };
      applyPermissionsUI();
    }
    renderResults();
  }

  async function createCampaign() {
    const timestamp = new Date().toISOString().slice(0, 16).replace("T", " ");
    const nombre = window.prompt("Nombre de la nueva campaña", `Nueva encuesta ${timestamp}`);
    if (!nombre) return;
    const campaign = await fetchJSON("/api/encuestas/campanas", {
      method: "POST",
      body: JSON.stringify({ nombre }),
    });
    state.currentInstanceId = campaign.id;
    state.selectedSectionId = null;
    await loadCampaigns(true);
    setMessage(campaignsMsg, "Campaña creada.");
  }

  async function createCampaignFromTemplate() {
    if (!templateSelect || !templateSelect.value) {
      setMessage(builderMsg, "Selecciona una plantilla primero.", true);
      return;
    }
    const template = (state.templates || []).find((item) => String(item.id) === String(templateSelect.value));
    const nombre = window.prompt("Nombre de la campaña", template ? template.nombre : "Nueva encuesta");
    if (!nombre) return;
    const campaign = await fetchJSON("/api/encuestas/campanas", {
      method: "POST",
      body: JSON.stringify({ nombre, template_id: Number(templateSelect.value) }),
    });
    state.currentInstanceId = campaign.id;
    state.selectedSectionId = null;
    await loadCampaigns(true);
    setMessage(builderMsg, "Campaña creada desde plantilla.");
  }

  async function saveAsTemplate() {
    if (!state.currentInstanceId || !state.builder) {
      setMessage(builderMsg, "Selecciona una campaña primero.", true);
      return;
    }
    const nombre = window.prompt("Nombre de la plantilla", state.builder.nombre || "Nueva plantilla");
    if (!nombre) return;
    const slug = window.prompt("Slug de la plantilla", nombre.toLowerCase().replace(/\s+/g, "-"));
    if (!slug) return;
    await fetchJSON(`/api/encuestas/campanas/${state.currentInstanceId}/save-template`, {
      method: "POST",
      body: JSON.stringify({
        nombre,
        slug,
        descripcion: state.builder.descripcion || "",
      }),
    });
    await loadTemplates();
    setMessage(builderMsg, "Plantilla guardada.");
  }

  async function saveDraft(payload, message) {
    if (!state.currentInstanceId) {
      setMessage(builderMsg, "Selecciona una campaña primero.", true);
      return;
    }
    await fetchJSON(`/api/encuestas/campanas/${state.currentInstanceId}/draft`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    await loadCampaigns(false);
    await loadBuilder(state.currentInstanceId);
    setMessage(builderMsg, message || "Cambios guardados.");
  }

  async function addSection() {
    if (!state.currentInstanceId) {
      setMessage(boardMsg, "Selecciona una campaña en el desplegable de arriba.", true);
      setMessage(builderMsg, "Selecciona una campaña primero.", true);
      return;
    }
    setMessage(boardMsg, "", false);
    const titulo = window.prompt("Título de la sección", "Nueva sección");
    if (!titulo) return;
    await fetchJSON(`/api/encuestas/campanas/${state.currentInstanceId}/sections`, {
      method: "POST",
      body: JSON.stringify({ titulo }),
    });
    await loadBuilder(state.currentInstanceId);
    setMessage(builderMsg, "Sección agregada.");
  }

  async function editSection(sectionId) {
    const section = ((state.builder && state.builder.sections) || []).find((item) => item.id === sectionId);
    if (!section) return;
    const titulo = window.prompt("Editar título de la sección", section.titulo || "");
    if (!titulo) return;
    const descripcion = window.prompt("Descripción de la sección", section.descripcion || "");
    await fetchJSON(`/api/encuestas/campanas/${state.currentInstanceId}/sections/${sectionId}`, {
      method: "PATCH",
      body: JSON.stringify({ titulo, descripcion }),
    });
    await loadBuilder(state.currentInstanceId);
    setMessage(builderMsg, "Sección actualizada.");
  }

  async function reorderSection(sectionId, direction) {
    const sections = (state.builder && state.builder.sections) || [];
    const index = sections.findIndex((item) => item.id === sectionId);
    const swapIndex = index + direction;
    if (index < 0 || swapIndex < 0 || swapIndex >= sections.length) return;
    const ids = sections.map((item) => item.id);
    const temp = ids[index];
    ids[index] = ids[swapIndex];
    ids[swapIndex] = temp;
    await fetchJSON(`/api/encuestas/campanas/${state.currentInstanceId}/sections/reorder`, {
      method: "POST",
      body: JSON.stringify({ ids }),
    });
    await loadBuilder(state.currentInstanceId);
  }

  async function addQuestion() {
    const section = getCurrentSection();
    if (!state.currentInstanceId) {
      setMessage(boardMsg, "Selecciona una campaña en el desplegable de arriba.", true);
      setMessage(builderMsg, "Selecciona una campaña primero.", true);
      return;
    }
    if (!section) {
      setMessage(boardMsg, "Primero crea y selecciona una sección.", true);
      setMessage(builderMsg, "Selecciona una sección primero.", true);
      return;
    }
    setMessage(boardMsg, "", false);
    openQuestionModal();
  }

  async function saveQuestionFromModal(keepOpen) {
    const section = getCurrentSection();
    if (!state.currentInstanceId || !section) {
      setMessage(builderMsg, "Selecciona una sección primero.", true);
      return;
    }
    const titulo = String((questionModalTitle && questionModalTitle.value) || "").trim();
    if (!titulo) {
      throw new Error("Escribe la pregunta.");
    }
    const type = state.questionModalType || "";
    if (!getQuestionTypeKeys().includes(type)) {
      throw new Error("Selecciona un tipo de pregunta válido.");
    }
    await fetchJSON(`/api/encuestas/campanas/${state.currentInstanceId}/sections/${section.id}/questions`, {
      method: "POST",
      body: JSON.stringify({
        titulo,
        descripcion: String((questionModalDescription && questionModalDescription.value) || "").trim(),
        question_type: type,
        is_required: String((questionModalRequired && questionModalRequired.value) || "false") === "true",
        options: parseQuestionModalOptions(type),
      }),
    });
    await loadBuilder(state.currentInstanceId);
    setMessage(builderMsg, "Pregunta agregada.");
    if (keepOpen) {
      resetQuestionModal();
      return;
    }
    closeQuestionModal();
  }

  async function editQuestion(questionId) {
    const section = getCurrentSection();
    const question = section && (section.questions || []).find((item) => item.id === questionId);
    if (!question) return;
    const titulo = window.prompt("Editar pregunta", question.titulo || "");
    if (!titulo) return;
    const descripcion = window.prompt("Descripción", question.descripcion || "");
    const optionsText = ["single_choice", "live_poll_single_choice", "multiple_choice", "yes_no", "scale_1_5", "live_scale_1_5", "nps_0_10", "quiz_single_choice", "ranking", "matrix", "likert_scale", "semantic_differential", "dropdown", "image_choice", "true_false"].includes(question.question_type)
      ? window.prompt(
          "Opciones separadas por coma",
          (question.options || []).map((option) => option.label).join(", ")
        )
      : null;
    const payload = {
      titulo,
      descripcion,
      options: optionsText === null ? undefined : parseOptionsText(optionsText, question.question_type),
    };
    await fetchJSON(`/api/encuestas/campanas/${state.currentInstanceId}/questions/${questionId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
    await loadBuilder(state.currentInstanceId);
    setMessage(builderMsg, "Pregunta actualizada.");
  }

  async function duplicateQuestion(questionId) {
    await fetchJSON(`/api/encuestas/campanas/${state.currentInstanceId}/questions/${questionId}/duplicate`, {
      method: "POST",
    });
    await loadBuilder(state.currentInstanceId);
    setMessage(builderMsg, "Pregunta duplicada.");
  }

  async function reorderQuestion(questionId, direction) {
    const section = getCurrentSection();
    if (!section) return;
    const ids = (section.questions || []).map((item) => item.id);
    const index = ids.indexOf(questionId);
    const swapIndex = index + direction;
    if (index < 0 || swapIndex < 0 || swapIndex >= ids.length) return;
    const temp = ids[index];
    ids[index] = ids[swapIndex];
    ids[swapIndex] = temp;
    await fetchJSON(`/api/encuestas/campanas/${state.currentInstanceId}/sections/${section.id}/questions/reorder`, {
      method: "POST",
      body: JSON.stringify({ ids }),
    });
    await loadBuilder(state.currentInstanceId);
  }

  async function publishCampaign() {
    if (!state.currentInstanceId) return;
    await fetchJSON(`/api/encuestas/campanas/${state.currentInstanceId}/publish`, { method: "POST" });
    await loadCampaigns(false);
    await loadBuilder(state.currentInstanceId);
    setMessage(builderMsg, "Encuesta publicada.");
  }

  async function closeCampaign() {
    if (!state.currentInstanceId) return;
    await fetchJSON(`/api/encuestas/campanas/${state.currentInstanceId}/close`, { method: "POST" });
    await loadCampaigns(false);
    await loadBuilder(state.currentInstanceId);
    setMessage(builderMsg, "Encuesta cerrada.");
  }

  function bindNavigation() {
    navButtons.forEach((button) => {
      button.addEventListener("click", function () {
        showPanel(button.dataset.encNav);
      });
    });
    campaignViewButtons.forEach((button) => {
      button.addEventListener("click", function () {
        const view = String(button.dataset.encCampaignView || "");
        if (!view || view === "activities" || button.classList.contains("is-disabled")) return;
        state.campaignView = view;
        renderCampaignView();
      });
    });
    builderTabs.forEach((button) => {
      button.addEventListener("click", function () {
        showBuilderTab(button.dataset.encBuilderTab);
      });
    });
    surveyTabs.forEach((button) => {
      button.addEventListener("click", function () {
        showSurveyTab(button.dataset.encSurveyTab);
      });
    });
    questionModalTabs.forEach((button) => {
      button.addEventListener("click", function () {
        showQuestionModalTab(button.dataset.encQuestionTab);
      });
    });
  }

  function bindActions() {
    actionButtons.forEach((button) => {
      button.addEventListener("click", async function () {
        try {
          const action = button.dataset.encAction;
          if (action === "open-builder") {
            await loadCampaigns(true);
            showPanel("constructor");
            return;
          }
          if (action === "new-survey") {
            await createCampaign();
            showPanel("constructor");
            return;
          }
          if (action === "create-from-template") {
            await createCampaignFromTemplate();
            showPanel("constructor");
            return;
          }
          if (action === "save-as-template") {
            await saveAsTemplate();
            return;
          }
          if (action === "refresh-builder") {
            if (state.currentInstanceId) await loadBuilder(state.currentInstanceId);
            return;
          }
          if (action === "refresh-results") {
            const targetId = resultsSelect && resultsSelect.value ? resultsSelect.value : state.currentInstanceId;
            if (targetId) await loadResults(targetId);
            return;
          }
          if (action === "add-section") {
            if (responseMode() === "presentation") {
              addPresentationPage();
            } else {
              await addSection();
            }
            return;
          }
          if (action === "add-question") {
            await addQuestion();
            return;
          }
          if (action === "publish-campaign") {
            await publishCampaign();
            return;
          }
          if (action === "close-campaign") {
            await closeCampaign();
          }
        } catch (error) {
          setMessage(builderMsg, error.message, true);
        }
      });
    });

    root.addEventListener("click", async function (event) {
      const closer = event.target.closest("[data-enc-close-modal]");
      if (closer) {
        if (closer.dataset.encCloseModal === "question") {
          closeQuestionModal();
          return;
        }
        if (closer.dataset.encCloseModal === "page") {
          closePresentationPageBuilder();
          return;
        }
      }
      const target = event.target.closest("button");
      if (!target) return;
      try {
        if (target.dataset.encModalType) {
          state.questionModalType = String(target.dataset.encModalType);
          if (questionModalOptions) {
            questionModalOptions.value = defaultOptionsText(state.questionModalType);
          }
          renderQuestionModalTypeList();
        } else if (target.dataset.encOpenBuilder) {
          showPanel("constructor");
          await loadBuilder(target.dataset.encOpenBuilder);
          renderBuilderSelect();
        } else if (target.dataset.encOpenResults) {
          showPanel("resultados");
          if (resultsSelect) resultsSelect.value = String(target.dataset.encOpenResults);
          await loadResults(target.dataset.encOpenResults);
        } else if (target.dataset.encSelectSection) {
          state.selectedSectionId = Number(target.dataset.encSelectSection);
          renderSections();
        } else if (target.dataset.encEditSection) {
          await editSection(Number(target.dataset.encEditSection));
        } else if (target.dataset.encSectionUp) {
          await reorderSection(Number(target.dataset.encSectionUp), -1);
        } else if (target.dataset.encSectionDown) {
          await reorderSection(Number(target.dataset.encSectionDown), 1);
        } else if (target.dataset.encEditQuestion) {
          await editQuestion(Number(target.dataset.encEditQuestion));
        } else if (target.dataset.encDuplicateQuestion) {
          await duplicateQuestion(Number(target.dataset.encDuplicateQuestion));
        } else if (target.dataset.encQuestionUp) {
          await reorderQuestion(Number(target.dataset.encQuestionUp), -1);
        } else if (target.dataset.encQuestionDown) {
          await reorderQuestion(Number(target.dataset.encQuestionDown), 1);
        } else if (target.dataset.encOpenPresentationPage !== undefined) {
          openPresentationPageBuilder(Number(target.dataset.encOpenPresentationPage));
        } else if (target.dataset.encPageTemplate) {
          if (!state.presentationEditor) throw new Error("Abre una página primero.");
          state.presentationEditor.page = mergePresentationTemplate(String(target.dataset.encPageTemplate));
          if (pageTitleInput) pageTitleInput.value = state.presentationEditor.page.title || "";
          if (pageSectionCountInput) pageSectionCountInput.value = String(state.presentationEditor.page.section_count || 1);
          if (pageDescriptionInput) pageDescriptionInput.value = state.presentationEditor.page.description || "";
          if (pageBgColorInput) pageBgColorInput.value = state.presentationEditor.page.bg_color || "#ffffff";
          if (pageBgImageInput) pageBgImageInput.value = state.presentationEditor.page.bg_image_url || "";
          if (pageFooterTextInput) pageFooterTextInput.value = state.presentationEditor.page.footer_text || "";
          if (pageFooterColorInput) pageFooterColorInput.value = state.presentationEditor.page.footer_color || "#0f172a";
          state.presentationEditor.selectedSectionIndex = 0;
          renderPageBlocksEditor();
        } else if (target.dataset.encLayoutSectionInsertImage !== undefined) {
          const index = Number(target.dataset.encLayoutSectionInsertImage);
          const area = pageBlocksNode
            ? pageBlocksNode.querySelector(`[data-enc-layout-section-html="${index}"]`)
            : null;
          if (!area) throw new Error("No se encontró la sección HTML para insertar la imagen.");
          await promptAndInsertHtmlImage(area);
          updatePresentationEditorPage();
        } else if (target.dataset.encPageBlock) {
          if (!state.presentationEditor) throw new Error("Abre una página primero.");
          const type = String(target.dataset.encPageBlock || "html");
          const availableQuestions = getAllBuilderQuestions();
          if (type === "question" && !availableQuestions.length) {
            closePresentationPageBuilder();
            showSurveyTab("questions");
            if (!getCurrentSection()) {
              const firstSection = ((state.builder && state.builder.sections) || [])[0];
              if (firstSection) {
                state.selectedSectionId = Number(firstSection.id);
                renderSections();
              }
            }
            if (!getCurrentSection()) {
              setMessage(builderMsg, "Primero crea una sección y luego una pregunta.", true);
              return;
            }
            await addQuestion();
            setMessage(builderMsg, "Crea la pregunta y luego podrás seleccionarla en la página.", false);
            return;
          }
          const sectionIndex = Number(state.presentationEditor.selectedSectionIndex || 0);
          updatePresentationEditorPage();
          const sections = ensureLayoutSections(state.presentationEditor.page.section_count, state.presentationEditor.page.layout_sections);
          sections[sectionIndex] = createPresentationSection({
            ...(sections[sectionIndex] || {}),
            type,
            image_fit: "cover",
          });
          state.presentationEditor.page.layout_sections = sections;
          renderPageBlocksEditor();
          if (type === "question") {
            focusPresentationQuestionPicker(sectionIndex);
          }
        } else if (target.dataset.encOpenQuestionLibrary !== undefined) {
          closePresentationPageBuilder();
          showSurveyTab("questions");
          if (!getCurrentSection()) {
            const firstSection = ((state.builder && state.builder.sections) || [])[0];
            if (firstSection) {
              state.selectedSectionId = Number(firstSection.id);
              renderSections();
            }
          }
          if (!getCurrentSection()) {
            setMessage(builderMsg, "Primero crea una sección y luego una pregunta.", true);
            return;
          }
          await addQuestion();
          setMessage(builderMsg, "Crea la pregunta y luego vuelve a la página para seleccionarla.", false);
        } else if (target.dataset.encRemovePresentationPage !== undefined) {
          const pages = getPresentationPages();
          pages.splice(Number(target.dataset.encRemovePresentationPage), 1);
          setPresentationPages(pages);
          renderPresentationBuilder();
        } else if (target.dataset.encCopyInstanceId !== undefined) {
          const instanceId = state.builder && state.builder.id != null ? String(state.builder.id) : "";
          if (!instanceId) throw new Error("La encuesta no tiene ID disponible.");
          await copyText(instanceId);
          setMessage(builderMsg, "ID de encuesta copiado.");
        } else if (target.dataset.encCopyIntegrationToken !== undefined) {
          const integrationToken = String((state.builder && state.builder.settings_json && state.builder.settings_json.live_integration_token) || "").trim();
          if (!integrationToken) throw new Error("La encuesta no tiene token de integración disponible.");
          await copyText(integrationToken);
          setMessage(builderMsg, "Token de integración copiado.");
        } else if (target.dataset.encCopyPublicLink !== undefined) {
          const publicUrl = getPublicSurveyUrl(state.builder);
          if (!publicUrl) throw new Error("La encuesta no tiene enlace publico disponible.");
          await copyText(publicUrl);
          setMessage(builderMsg, "Enlace publico copiado.");
        } else if (target.dataset.encCopyPresenterLink !== undefined) {
          const presenterUrl = getPresenterUrl(state.builder);
          if (!presenterUrl) throw new Error("La encuesta no tiene panel en vivo disponible.");
          await copyText(presenterUrl);
          setMessage(builderMsg, "Acceso al panel en vivo copiado.");
        }
      } catch (error) {
        setMessage(builderMsg, error.message, true);
      }
    });

    if (questionModalSaveClose) {
      questionModalSaveClose.addEventListener("click", async function () {
        try {
          await saveQuestionFromModal(false);
        } catch (error) {
          setMessage(builderMsg, error.message, true);
        }
      });
    }

    if (questionModalSaveNew) {
      questionModalSaveNew.addEventListener("click", async function () {
        try {
          await saveQuestionFromModal(true);
        } catch (error) {
          setMessage(builderMsg, error.message, true);
        }
      });
    }

    if (questionModalTitle) {
      questionModalTitle.addEventListener("input", renderQuestionModalPreview);
    }
    if (questionModalOptions) {
      questionModalOptions.addEventListener("input", renderQuestionModalPreview);
    }

    [pageTitleInput, pageSectionCountInput, pageDescriptionInput, pageBgColorInput, pageBgImageInput, pageFooterTextInput, pageFooterColorInput].forEach((node) => {
      if (!node) return;
      node.addEventListener("input", function () {
        if (node === pageSectionCountInput && state.presentationEditor) {
          const page = syncPresentationEditorPage();
          page.layout_sections = ensureLayoutSections(page.section_count, page.layout_sections);
          state.presentationEditor.page = createPresentationPage(page);
          const maxIndex = Math.max(0, state.presentationEditor.page.section_count - 1);
          state.presentationEditor.selectedSectionIndex = Math.min(Number(state.presentationEditor.selectedSectionIndex || 0), maxIndex);
          renderPageBlocksEditor();
          return;
        }
        syncPresentationEditorPage();
      });
    });

    if (pageBlocksNode) {
      pageBlocksNode.addEventListener("input", function () {
        updatePresentationEditorPage();
      });
      pageBlocksNode.addEventListener("change", function () {
        updatePresentationEditorPage();
      });
    }

    if (presentationPagesNode) {
      presentationPagesNode.addEventListener("dragstart", function (event) {
        const pageNode = event.target.closest("[data-enc-presentation-page]");
        if (!pageNode) return;
        state.draggingPresentationPageIndex = Number(pageNode.dataset.encPresentationPage);
        pageNode.classList.add("is-dragging");
        if (event.dataTransfer) {
          event.dataTransfer.effectAllowed = "move";
          event.dataTransfer.setData("text/plain", String(state.draggingPresentationPageIndex));
        }
      });
      presentationPagesNode.addEventListener("dragend", function () {
        state.draggingPresentationPageIndex = null;
        presentationPagesNode.querySelectorAll(".is-dragging").forEach((node) => node.classList.remove("is-dragging"));
        presentationPagesNode.querySelectorAll(".is-drop-target").forEach((node) => node.classList.remove("is-drop-target"));
      });
      presentationPagesNode.addEventListener("dragover", function (event) {
        if (state.draggingPresentationPageIndex == null) return;
        event.preventDefault();
        const pageNode = event.target.closest("[data-enc-presentation-page]");
        presentationPagesNode.querySelectorAll(".is-drop-target").forEach((node) => node.classList.remove("is-drop-target"));
        if (pageNode) pageNode.classList.add("is-drop-target");
      });
      presentationPagesNode.addEventListener("dragleave", function (event) {
        const related = event.relatedTarget;
        if (related && presentationPagesNode.contains(related)) return;
        presentationPagesNode.querySelectorAll(".is-drop-target").forEach((node) => node.classList.remove("is-drop-target"));
      });
      presentationPagesNode.addEventListener("drop", function (event) {
        if (state.draggingPresentationPageIndex == null) return;
        event.preventDefault();
        const pageNode = event.target.closest("[data-enc-presentation-page]");
        presentationPagesNode.querySelectorAll(".is-drop-target").forEach((node) => node.classList.remove("is-drop-target"));
        if (!pageNode) return;
        movePresentationPage(Number(state.draggingPresentationPageIndex), Number(pageNode.dataset.encPresentationPage));
      });
    }

    if (pageSaveCloseButton) {
      pageSaveCloseButton.addEventListener("click", async function () {
        try {
          persistPresentationEditorPage();
          await savePresentationPages();
          closePresentationPageBuilder();
          setMessage(builderMsg, "Página actualizada en el constructor.", false);
        } catch (error) {
          setMessage(builderMsg, error.message, true);
        }
      });
    }

    if (pagePreviewNode) {
      pagePreviewNode.addEventListener("click", function (event) {
        const sectionNode = event.target.closest("[data-enc-layout-section]");
        if (!sectionNode || !state.presentationEditor) return;
        updatePresentationEditorPage();
        state.presentationEditor.selectedSectionIndex = Number(sectionNode.dataset.encLayoutSection);
        renderPageBlocksEditor();
      });
      pagePreviewNode.addEventListener("dragstart", function (event) {
        const sectionNode = event.target.closest("[data-enc-layout-section]");
        if (!sectionNode || !state.presentationEditor) return;
        state.draggingLayoutSectionIndex = Number(sectionNode.dataset.encLayoutSection);
        sectionNode.classList.add("is-dragging");
        if (event.dataTransfer) {
          event.dataTransfer.effectAllowed = "move";
          event.dataTransfer.setData("text/plain", String(state.draggingLayoutSectionIndex));
        }
      });
      pagePreviewNode.addEventListener("dragend", function () {
        state.draggingLayoutSectionIndex = null;
        pagePreviewNode.querySelectorAll(".is-dragging").forEach((node) => node.classList.remove("is-dragging"));
        pagePreviewNode.querySelectorAll(".is-drop-target").forEach((node) => node.classList.remove("is-drop-target"));
        pagePreviewNode.classList.remove("is-drop-target");
      });
      pagePreviewNode.addEventListener("dragover", function (event) {
        if (state.draggingLayoutSectionIndex == null) return;
        event.preventDefault();
        const sectionNode = event.target.closest("[data-enc-layout-section]");
        pagePreviewNode.querySelectorAll(".is-drop-target").forEach((node) => node.classList.remove("is-drop-target"));
        if (sectionNode) sectionNode.classList.add("is-drop-target");
        else pagePreviewNode.classList.add("is-drop-target");
      });
      pagePreviewNode.addEventListener("dragleave", function () {
        pagePreviewNode.classList.remove("is-drop-target");
      });
      pagePreviewNode.addEventListener("drop", function (event) {
        if (state.draggingLayoutSectionIndex == null || !state.presentationEditor) return;
        event.preventDefault();
        pagePreviewNode.classList.remove("is-drop-target");
        const sectionNode = event.target.closest("[data-enc-layout-section]");
        if (!sectionNode) return;
        moveLayoutSection(Number(state.draggingLayoutSectionIndex), Number(sectionNode.dataset.encLayoutSection));
      });
      pagePreviewNode.addEventListener("paste", function (event) {
        if (!state.presentationEditor) return;
        const clipboard = event.clipboardData;
        if (!clipboard) return;
        const html = clipboard.getData("text/html");
        const text = clipboard.getData("text/plain");
        if (!html && !text) return;
        event.preventDefault();
        appendHtmlBlockFromPaste(html, text);
      });
    }

    if (pageModal) {
      pageModal.addEventListener("paste", function (event) {
        if (!state.presentationEditor) return;
        const target = event.target;
        if (
          target instanceof HTMLTextAreaElement
          || target instanceof HTMLInputElement
          || target instanceof HTMLSelectElement
          || (target instanceof HTMLElement && target.isContentEditable)
        ) {
          return;
        }
        const clipboard = event.clipboardData;
        if (!clipboard) return;
        const html = clipboard.getData("text/html");
        const text = clipboard.getData("text/plain");
        if (!html && !text) return;
        event.preventDefault();
        appendHtmlBlockFromPaste(html, text);
      });
    }
  }

  function bindForms() {
    ensureManualGroupsEditor();

    builderSelect.addEventListener("change", async function () {
      if (!builderSelect.value) return;
      await loadBuilder(builderSelect.value);
    });

    generalForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      try {
        await saveDraft(
          {
            nombre: document.getElementById("enc-general-nombre").value,
            descripcion: document.getElementById("enc-general-descripcion").value,
            publication_mode: document.getElementById("enc-general-publication-mode").value,
            schedule_start_at: document.getElementById("enc-general-start-at").value || null,
            schedule_end_at: document.getElementById("enc-general-end-at").value || null,
          },
          "Datos generales guardados."
        );
      } catch (error) {
        setMessage(builderMsg, error.message, true);
      }
    });

    audienceForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      try {
        syncPublicLinkControls();
        const assignmentType = document.getElementById("enc-audience-assignment-type").value;
        const assignmentValues = parseCsvValues(document.getElementById("enc-audience-values").value);
        const manualGroups = readManualGroupsFromEditor();
        const nextSettings = {
          ...(state.builder && state.builder.settings_json ? state.builder.settings_json : {}),
          audience_note: document.getElementById("enc-audience-group-note").value,
          assignment_type: assignmentType,
          assignment_values: assignmentValues,
          manual_groups: manualGroups,
        };
        await saveDraft(
          {
            audience_mode: audienceModeInput ? audienceModeInput.value : "internal",
            source_app: document.getElementById("enc-audience-source-app").value,
            settings_json: nextSettings,
          },
          "Audiencia MAIN guardada."
        );
        await fetchJSON(`/api/encuestas/campanas/${state.currentInstanceId}/assignments/sync`, {
          method: "POST",
          body: JSON.stringify({
            assignments: assignmentValues.length ? [{ type: assignmentType, values: assignmentValues }] : [],
            manual_groups: manualGroups,
            due_at: nextSettings.assignment_due_at || null,
          }),
        });
        await loadBuilder(state.currentInstanceId);
        setMessage(builderMsg, "Audiencia guardada y materializada.");
      } catch (error) {
        setMessage(builderMsg, error.message, true);
      }
    });

    rulesForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      try {
        const rulesText = document.getElementById("enc-rules-json").value.trim();
        const publicationRules = rulesText ? JSON.parse(rulesText) : {};
        await saveDraft(
          {
            anonymity_mode: document.getElementById("enc-rules-anonymity-mode").value,
            settings_json: {
              ...(state.builder && state.builder.settings_json ? state.builder.settings_json : {}),
              scoring_mode: document.getElementById("enc-rules-scoring-mode").value,
            },
            publication_rules_json: publicationRules,
          },
          "Reglas guardadas."
        );
      } catch (error) {
        setMessage(builderMsg, error.message || "JSON inválido en reglas.", true);
      }
    });

    publicationForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      try {
        syncPublicLinkControls();
        const nextSettings = {
          ...(state.builder && state.builder.settings_json ? state.builder.settings_json : {}),
          assignment_due_at: document.getElementById("enc-publication-due-at").value || null,
        };
        await saveDraft(
          {
            is_public_link_enabled: publicLinkEnabledInput ? publicLinkEnabledInput.value === "true" : false,
            public_link_token: document.getElementById("enc-public-link-token").value,
            settings_json: nextSettings,
          },
          "Configuración de publicación guardada."
        );
      } catch (error) {
        setMessage(builderMsg, error.message, true);
      }
    });

    if (surveyOptionsForm) {
      surveyOptionsForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        try {
          syncPublicLinkControls();
          await saveDraft(
            {
              audience_mode: editorAudienceMode ? editorAudienceMode.value : "internal",
              anonymity_mode: editorAnonymityMode ? editorAnonymityMode.value : "identified",
              publication_mode: editorPublicationMode ? editorPublicationMode.value : "manual",
              publication_rules_json: {
                ...(state.builder && state.builder.publication_rules_json ? state.builder.publication_rules_json : {}),
                response_mode: editorResponseMode ? editorResponseMode.value : "standard",
              },
              settings_json: {
                ...(state.builder && state.builder.settings_json ? state.builder.settings_json : {}),
                scoring_mode: editorScoringMode ? editorScoringMode.value : "none",
              },
            },
            "Opciones guardadas."
          );
        } catch (error) {
          setMessage(builderMsg, error.message, true);
        }
      });
    }

    if (audienceModeInput) audienceModeInput.addEventListener("change", syncPublicLinkControls);
    if (editorAudienceMode) editorAudienceMode.addEventListener("change", syncPublicLinkControls);
    if (manualGroupAdd) {
      manualGroupAdd.addEventListener("click", function () {
        const groups = readManualGroupsFromEditor();
        groups.push(createManualGroup({}));
        renderManualGroupsEditor(groups);
      });
    }
    if (manualGroupsList) {
      manualGroupsList.addEventListener("input", syncManualGroupsField);
      manualGroupsList.addEventListener("click", function (event) {
        const addMemberButton = event.target.closest("[data-enc-add-member]");
        if (addMemberButton) {
          const groups = readManualGroupsFromEditor();
          const groupIndex = Number(addMemberButton.getAttribute("data-enc-add-member"));
          if (groups[groupIndex]) {
            groups[groupIndex].members.push(createManualMember({}));
            renderManualGroupsEditor(groups);
          }
          return;
        }
        const removeMemberButton = event.target.closest("[data-enc-remove-member]");
        if (removeMemberButton) {
          const groupNode = event.target.closest("[data-enc-manual-group]");
          const groupIndex = Number(groupNode ? groupNode.getAttribute("data-enc-manual-group") : -1);
          const memberIndex = Number(removeMemberButton.getAttribute("data-enc-remove-member"));
          const groups = readManualGroupsFromEditor();
          if (groups[groupIndex]) {
            groups[groupIndex].members.splice(memberIndex, 1);
            if (!groups[groupIndex].members.length) groups[groupIndex].members.push(createManualMember({}));
            renderManualGroupsEditor(groups);
          }
          return;
        }
        const removeGroupButton = event.target.closest("[data-enc-remove-group]");
        if (removeGroupButton) {
          const groupIndex = Number(removeGroupButton.getAttribute("data-enc-remove-group"));
          const groups = readManualGroupsFromEditor();
          groups.splice(groupIndex, 1);
          renderManualGroupsEditor(groups);
        }
      });
    }

    if (insertHeaderImageButton) {
      insertHeaderImageButton.addEventListener("click", async function () {
        try {
          await promptAndInsertHtmlImage(editorHeaderHtml);
        } catch (error) {
          setMessage(builderMsg, error.message, true);
        }
      });
    }

    if (insertFooterImageButton) {
      insertFooterImageButton.addEventListener("click", async function () {
        try {
          await promptAndInsertHtmlImage(editorFooterHtml);
        } catch (error) {
          setMessage(builderMsg, error.message, true);
        }
      });
    }

    if (presentationAddPageButton) {
      presentationAddPageButton.addEventListener("click", function () {
        addPresentationPage();
      });
    }

    if (presentationSaveButton) {
      presentationSaveButton.addEventListener("click", async function () {
        try {
          await savePresentationPages();
        } catch (error) {
          setMessage(builderMsg, error.message, true);
        }
      });
    }

    if (surveyDescriptionForm) {
      surveyDescriptionForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        try {
          await saveDraft(
            {
              nombre: editorTitle ? editorTitle.value : "",
              descripcion: editorDescription ? editorDescription.value : "",
              publication_rules_json: {
                ...(state.builder && state.builder.publication_rules_json ? state.builder.publication_rules_json : {}),
                header_html: editorHeaderHtml ? editorHeaderHtml.value : "",
                footer_html: editorFooterHtml ? editorFooterHtml.value : "",
              },
            },
            "Contenido guardado."
          );
        } catch (error) {
          setMessage(builderMsg, error.message, true);
        }
      });
    }

    if (surveyInitialMessageForm) {
      surveyInitialMessageForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        try {
          await saveDraft(
            {
              publication_rules_json: {
                ...(state.builder && state.builder.publication_rules_json ? state.builder.publication_rules_json : {}),
                initial_message: editorInitialMessage ? editorInitialMessage.value : "",
              },
            },
            "Mensaje inicial guardado."
          );
        } catch (error) {
          setMessage(builderMsg, error.message, true);
        }
      });
    }

    if (surveyFinalMessageForm) {
      surveyFinalMessageForm.addEventListener("submit", async function (event) {
        event.preventDefault();
        try {
          await saveDraft(
            {
              publication_rules_json: {
                ...(state.builder && state.builder.publication_rules_json ? state.builder.publication_rules_json : {}),
                final_message: editorFinalMessage ? editorFinalMessage.value : "",
              },
            },
            "Mensaje final guardado."
          );
        } catch (error) {
          setMessage(builderMsg, error.message, true);
        }
      });
    }
    if (surveyImagenForm) {
      // File preview on selection
      if (imagenFileInput) {
        imagenFileInput.addEventListener("change", function () {
          const file = imagenFileInput.files && imagenFileInput.files[0];
          if (!file) return;
          _showImagePreview(file);
        });
      }
      // Drag-and-drop on upload area
      if (imagenUploadArea) {
        imagenUploadArea.addEventListener("dragover", function (e) {
          e.preventDefault();
          imagenUploadArea.classList.add("is-dragover");
        });
        imagenUploadArea.addEventListener("dragleave", function () {
          imagenUploadArea.classList.remove("is-dragover");
        });
        imagenUploadArea.addEventListener("drop", function (e) {
          e.preventDefault();
          imagenUploadArea.classList.remove("is-dragover");
          const file = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
          if (file) {
            const dt = new DataTransfer();
            dt.items.add(file);
            imagenFileInput.files = dt.files;
            _showImagePreview(file);
          }
        });
      }
      // Clear button
      if (imagenUploadClear) {
        imagenUploadClear.addEventListener("click", function () {
          if (imagenFileInput) imagenFileInput.value = "";
          if (imagenUploadPrompt) imagenUploadPrompt.hidden = false;
          if (imagenUploadPreview) imagenUploadPreview.hidden = true;
          if (imagenUploadMsg) imagenUploadMsg.hidden = true;
        });
      }

      surveyImagenForm.addEventListener("submit", async function (e) {
        e.preventDefault();
        if (!state.currentInstanceId) {
          setMessage(builderMsg, "Selecciona una campaña primero.", true);
          return;
        }
        const checkedPos = document.querySelector('[name="enc-image-position"]:checked');
        let imageUrl = editorImagenUrl ? editorImagenUrl.value.trim() : "";

        // If a file is selected, upload it first
        const file = imagenFileInput && imagenFileInput.files && imagenFileInput.files[0];
        if (file) {
          if (imagenUploadMsg) { imagenUploadMsg.textContent = "Subiendo imagen..."; imagenUploadMsg.hidden = false; }
          try {
            const formData = new FormData();
            formData.append("file", file);
            const resp = await fetch(
              `/api/encuestas/campanas/${state.currentInstanceId}/upload-image`,
              { method: "POST", body: formData, credentials: "same-origin" }
            );
            if (!resp.ok) {
              const err = await resp.json().catch(() => ({ detail: resp.statusText }));
              throw new Error(err.detail || resp.statusText);
            }
            const data = await resp.json();
            imageUrl = data.url || imageUrl;
            if (editorImagenUrl) editorImagenUrl.value = imageUrl;
            if (imagenUploadMsg) { imagenUploadMsg.textContent = "Imagen subida correctamente."; }
            if (imagenFileInput) imagenFileInput.value = "";
          } catch (uploadErr) {
            if (imagenUploadMsg) { imagenUploadMsg.textContent = "Error al subir: " + uploadErr.message; imagenUploadMsg.hidden = false; }
            setMessage(builderMsg, uploadErr.message, true);
            return;
          }
        }

        try {
          await saveDraft(
            {
              publication_rules_json: {
                ...(state.builder && state.builder.publication_rules_json ? state.builder.publication_rules_json : {}),
                image_url: imageUrl,
                image_position: checkedPos ? checkedPos.value : "background",
              },
            },
            "Imagen guardada."
          );
        } catch (error) {
          setMessage(builderMsg, error.message, true);
        }
      });
    }

    function _showImagePreview(file) {
      if (!imagenPreviewImg || !imagenUploadPrompt || !imagenUploadPreview) return;
      const reader = new FileReader();
      reader.onload = function (ev) {
        imagenPreviewImg.src = ev.target.result;
        imagenUploadPrompt.hidden = true;
        imagenUploadPreview.hidden = false;
        if (imagenUploadMsg) imagenUploadMsg.hidden = true;
      };
      reader.readAsDataURL(file);
    }
  }

  function bindResultsFilters() {
    [resultsFilterDepartment, resultsFilterRole, resultsFilterCompany, resultsSegmentBy].forEach((node) => {
      if (!node) return;
      node.addEventListener("change", async function () {
        const targetId = resultsSelect && resultsSelect.value ? resultsSelect.value : state.currentInstanceId;
        if (!targetId) return;
        try {
          await loadResults(targetId);
          setMessage(resultsMsg, "Resultados filtrados.");
        } catch (error) {
          setMessage(resultsMsg, error.message, true);
        }
      });
    });
    if (resultsSelect) {
      resultsSelect.addEventListener("change", async function () {
        if (!resultsSelect.value) return;
        try {
          await loadResults(resultsSelect.value);
          setMessage(resultsMsg, "");
        } catch (error) {
          setMessage(resultsMsg, error.message, true);
        }
      });
    }
  }

  async function initialize() {
    paintMetrics();
    showPanel(initialPanel());
    renderCampaignView();
    bindNavigation();
    bindActions();
    bindForms();
    bindResultsFilters();
    await loadPermissions();
    await loadQuestionTypes();
    await loadTemplates();
    if (can("manage_surveys")) {
      await loadAssignableUsers();
    }
    await loadCampaigns(false);
    renderCampaigns();
    renderBuilderSelect();
    renderResults();
  }

  initialize().catch((error) => {
    setMessage(builderMsg, error.message, true);
    setMessage(campaignsMsg, error.message, true);
  });
})();
