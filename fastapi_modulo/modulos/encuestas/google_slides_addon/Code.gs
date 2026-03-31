/**
 * Encuestas en vivo — Google Slides Add-on
 *
 * Permite al presentador controlar una sesión en vivo desde
 * una barra lateral mientras avanza su presentación.
 *
 * Configuración (guardar en Propiedades del Script):
 *   SIPET_BASE_URL   — URL base de la API
 *   SIPET_INSTANCE_ID — ID de la SurveyInstance
 *   SIPET_INTEGRATION_TOKEN — Token de integración de la encuesta
 *   SIPET_PRESENTER_TOKEN — Token generado al iniciar la sesión
 */

// ---------------------------------------------------------------------------
// Entry points requeridos por el manifest
// ---------------------------------------------------------------------------

function onSlidesHomepage(e) {
  return buildHomepageCard();
}

function onFileScopeGranted(e) {
  return buildHomepageCard();
}

function onOpen(e) {
  SlidesApp.getUi()
    .createAddonMenu()
    .addItem("Abrir panel", "openSidebar")
    .addToUi();
}

function onInstall(e) {
  onOpen(e);
}

// ---------------------------------------------------------------------------
// Sidebar principal
// ---------------------------------------------------------------------------

function openSidebar() {
  var html = HtmlService.createHtmlOutputFromFile("Sidebar")
    .setTitle("Encuestas en vivo")
    .setWidth(320);
  SlidesApp.getUi().showSidebar(html);
}

// ---------------------------------------------------------------------------
// Tarjeta de inicio
// ---------------------------------------------------------------------------

function buildHomepageCard() {
  var card = CardService.newCardBuilder()
    .setHeader(
      CardService.newCardHeader()
        .setTitle("Encuestas en vivo")
        .setSubtitle("Controla preguntas durante tu presentación")
    );

  var section = CardService.newCardSection();
  section.addWidget(
    CardService.newTextParagraph().setText(
      "Abre la barra lateral para controlar las preguntas en vivo mientras presentas."
    )
  );
  section.addWidget(
    CardService.newTextButton()
      .setText("Abrir panel de control")
      .setOnClickAction(CardService.newAction().setFunctionName("openSidebar"))
  );

  card.addSection(section);
  return card.build();
}

// ---------------------------------------------------------------------------
// Configuración persistida
// ---------------------------------------------------------------------------

function normalizeBaseUrl(value) {
  return String(value || "").trim().replace(/\/+$/, "");
}

function getConfig() {
  var props = PropertiesService.getScriptProperties();
  return {
    baseUrl: props.getProperty("SIPET_BASE_URL") || "",
    instanceId: props.getProperty("SIPET_INSTANCE_ID") || "",
    integrationToken: props.getProperty("SIPET_INTEGRATION_TOKEN") || "",
    presenterToken: props.getProperty("SIPET_PRESENTER_TOKEN") || ""
  };
}

function saveConfig(baseUrl, instanceId, integrationToken, presenterToken) {
  var props = PropertiesService.getScriptProperties();
  props.setProperty("SIPET_BASE_URL", normalizeBaseUrl(baseUrl));
  props.setProperty("SIPET_INSTANCE_ID", (instanceId || "").trim());
  props.setProperty("SIPET_INTEGRATION_TOKEN", (integrationToken || "").trim());
  props.setProperty("SIPET_PRESENTER_TOKEN", (presenterToken || "").trim());
  return { ok: true };
}

// ---------------------------------------------------------------------------
// Helpers de API
// ---------------------------------------------------------------------------

function buildApiHeaders(cfg, includeJsonContentType) {
  var headers = {
    "Accept": "application/json"
  };
  if (includeJsonContentType) {
    headers["Content-Type"] = "application/json";
  }
  if (cfg && cfg.integrationToken) {
    headers["X-Encuestas-Integration-Token"] = cfg.integrationToken;
  }
  return headers;
}

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

function fetchLiveStatus() {
  var cfg = getConfig();
  if (!cfg.baseUrl || !cfg.instanceId || !cfg.integrationToken) {
    return { error: "Configura la URL base, el ID de encuesta y el token de integración primero." };
  }

  var url = cfg.baseUrl + "/api/encuestas/campanas/" + cfg.instanceId + "/live/status";
  try {
    var resp = UrlFetchApp.fetch(url, {
      method: "GET",
      muteHttpExceptions: true,
      headers: buildApiHeaders(cfg, false),
      followRedirects: false
    });

    var code = resp.getResponseCode();
    var body = resp.getContentText();

    if (code !== 200) {
      return { error: "HTTP " + code + ": " + body.slice(0, 300) };
    }

    return JSON.parse(body);
  } catch (e) {
    return { error: e.message };
  }
}

function startLiveSession() {
  var cfg = getConfig();
  if (!cfg.baseUrl || !cfg.instanceId || !cfg.integrationToken) {
    return { error: "Configura la URL base, el ID de encuesta y el token de integración primero." };
  }

  var url = cfg.baseUrl + "/api/encuestas/campanas/" + cfg.instanceId + "/live/start";
  try {
    var resp = UrlFetchApp.fetch(url, {
      method: "POST",
      muteHttpExceptions: true,
      headers: buildApiHeaders(cfg, true),
      payload: "{}",
      followRedirects: false
    });

    var code = resp.getResponseCode();
    var body = resp.getContentText();

    if (code !== 200) {
      return { error: "HTTP " + code + ": " + body.slice(0, 300) };
    }

    var state = JSON.parse(body);

    if (state.presenter_token) {
      PropertiesService.getScriptProperties().setProperty(
        "SIPET_PRESENTER_TOKEN",
        state.presenter_token
      );
    }

    return state;
  } catch (e) {
    return { error: e.message };
  }
}

function stopLiveSession() {
  var cfg = getConfig();
  if (!cfg.baseUrl || !cfg.instanceId || !cfg.integrationToken) {
    return { error: "Configuración incompleta." };
  }

  var url = cfg.baseUrl + "/api/encuestas/campanas/" + cfg.instanceId + "/live/stop";
  try {
    var resp = UrlFetchApp.fetch(url, {
      method: "POST",
      muteHttpExceptions: true,
      headers: buildApiHeaders(cfg, true),
      payload: "{}",
      followRedirects: false
    });

    var code = resp.getResponseCode();
    var body = resp.getContentText();

    if (code !== 200) {
      return { error: "HTTP " + code + ": " + body.slice(0, 300) };
    }

    return JSON.parse(body);
  } catch (e) {
    return { error: e.message };
  }
}

function setLiveQuestion(questionId, showResults) {
  var cfg = getConfig();
  if (!cfg.baseUrl || !cfg.instanceId || !cfg.integrationToken || !cfg.presenterToken) {
    return { error: "Configuración incompleta (faltan token de integración o token de presentador)." };
  }

  var url = cfg.baseUrl + "/api/encuestas/campanas/" + cfg.instanceId + "/live/question";
  var payload = JSON.stringify({
    question_id: parseInt(questionId, 10),
    presenter_token: cfg.presenterToken,
    show_results: showResults !== false
  });

  try {
    var resp = UrlFetchApp.fetch(url, {
      method: "POST",
      muteHttpExceptions: true,
      headers: buildApiHeaders(cfg, true),
      payload: payload,
      followRedirects: false
    });

    var code = resp.getResponseCode();
    var body = resp.getContentText();

    if (code !== 200) {
      return { error: "HTTP " + code + ": " + body.slice(0, 300) };
    }

    return JSON.parse(body);
  } catch (e) {
    return { error: e.message };
  }
}
