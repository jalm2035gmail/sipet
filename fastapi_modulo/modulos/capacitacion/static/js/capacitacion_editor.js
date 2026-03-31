/* capacitacion_editor.js — Loader del editor modular */
(function () {
  'use strict';

  var root = document.getElementById('ped-root');
  if (!root) return;

  if (window.__pedEditorBootstrapped) return;
  window.__pedEditorBootstrapped = true;

  var presId = parseInt(root.getAttribute('data-pres-id') || '0', 10);
  var ASSET_VERSION = '20260327b';
  var BASE_PATH = '/capacitacion/assets/js/editor/';

  var files = [
    'editor-core.js?v=' + ASSET_VERSION,
    'editor-widgets.js?v=' + ASSET_VERSION,
    'editor-background.js?v=' + ASSET_VERSION,
    'editor-surveys.js?v=' + ASSET_VERSION,
    'editor-canvas.js?v=' + ASSET_VERSION,
    'editor-slides.js?v=' + ASSET_VERSION,
    'editor-ui.js?v=' + ASSET_VERSION
  ];

  function showFatal(message) {
    if (typeof window.toast === 'function') {
      window.toast(message, true);
      return;
    }
    var toastNode = document.getElementById('ped-toast');
    if (toastNode) {
      toastNode.textContent = message || 'No se pudo cargar el editor.';
      toastNode.classList.add('show', 'error');
    }
  }

  function ensureGlobals() {
    window.presId = presId;

    if (typeof window.presentation === 'undefined') window.presentation = null;
    if (!Array.isArray(window.slides)) window.slides = [];
    if (!Array.isArray(window.liveSurveys)) window.liveSurveys = [];
    if (!window.surveyAnalytics || typeof window.surveyAnalytics !== 'object') {
      window.surveyAnalytics = {};
    }
    if (typeof window.currentSlideIdx === 'undefined') window.currentSlideIdx = -1;
    if (typeof window.editorReady === 'undefined') window.editorReady = false;
    if (typeof window.saving === 'undefined') window.saving = false;
    if (typeof window.pagesViewMode === 'undefined') window.pagesViewMode = 'list';

    window.inputPresTitle = window.inputPresTitle || document.getElementById('ped-pres-title');
  }

  function requireFunctions(names) {
    var missing = names.filter(function (name) {
      return typeof window[name] !== 'function';
    });
    if (missing.length) {
      throw new Error('Faltan funciones del editor: ' + missing.join(', '));
    }
  }

  function withTimeout(promise, timeoutMs, fallbackValue) {
    return new Promise(function (resolve) {
      var settled = false;
      var timer = setTimeout(function () {
        if (settled) return;
        settled = true;
        resolve(fallbackValue);
      }, timeoutMs);

      Promise.resolve(promise)
        .then(function (value) {
          if (settled) return;
          settled = true;
          clearTimeout(timer);
          resolve(value);
        })
        .catch(function () {
          if (settled) return;
          settled = true;
          clearTimeout(timer);
          resolve(fallbackValue);
        });
    });
  }

  function bootstrap() {
    try {
      ensureGlobals();

      if (window.editorBootstrapError) {
        showFatal(window.editorBootstrapError);
        return;
      }

      requireFunctions([
        'apiJson',
        'toast',
        'bindTabs',
        'bindToolbar',
        'initEditor',
        'selectSlide',
        'renderSlideList',
        'saveCurrentSlide'
      ]);

      window.syncPresentationHeader = function () {
        if (!window.presentation) return;

        if (window.inputPresTitle) {
          window.inputPresTitle.value = window.presentation.titulo || 'Presentación';
        }

        var publishBtn = window.el ? window.el('ped-btn-publish') : document.getElementById('ped-btn-publish');
        if (publishBtn) {
          publishBtn.textContent = window.presentation.estado === 'publicado'
            ? 'Despublicar'
            : 'Publicar';
        }
      };

      window.saveAll = function () {
        if (window.saving) return Promise.resolve();
        return window.saveCurrentSlide().catch(function () {});
      };

      window.loadData = function () {
        return Promise.all([
          window.apiJson('/api/capacitacion/presentaciones/' + window.presId),
          window.apiJson('/api/capacitacion/presentaciones/' + window.presId + '/diapositivas')
        ]).then(function (results) {
          var presentationRes = results[0];
          var slidesRes = results[1];

          if (!presentationRes || !presentationRes.ok) {
            throw new Error('No se pudo cargar la presentación.');
          }

          window.presentation = presentationRes.data || null;
          window.slides = slidesRes && slidesRes.ok && Array.isArray(slidesRes.data) ? slidesRes.data : [];
          window.liveSurveys = [];

          if (!window.slides.length) {
            throw new Error('La presentación no tiene diapositivas.');
          }

          return withTimeout(
            window.apiJson('/api/capacitacion/presentaciones/' + window.presId + '/encuestas-live'),
            4000,
            { ok: false, data: [] }
          ).then(function (surveysRes) {
            window.liveSurveys = surveysRes && surveysRes.ok && Array.isArray(surveysRes.data) ? surveysRes.data : [];
            return typeof window.loadSurveyAnalytics === 'function'
              ? withTimeout(window.loadSurveyAnalytics(), 4000, null).then(function () {
                  if (!window.surveyAnalytics || typeof window.surveyAnalytics !== 'object') {
                    window.surveyAnalytics = {};
                  }
                })
              : Promise.resolve();
          }).then(function () {
            if (typeof window.syncPresentationHeader === 'function') {
              window.syncPresentationHeader();
            }

            if (typeof window.renderSlideList === 'function') {
              window.renderSlideList();
            }

            return window.selectSlide(0).then(function () {
              if (typeof window.refreshSurveyPreviews === 'function') {
                window.refreshSurveyPreviews();
              }
              if (typeof window.loadAuditTrail === 'function') {
                return window.loadAuditTrail();
              }
              return null;
            });
          });
        });
      };

      if (typeof window.bindBackgroundInputs === 'function') {
        window.bindBackgroundInputs();
      }

      window.bindTabs();
      window.initEditor();
      window.bindToolbar();

      if (typeof window.bindAutosave === 'function') {
        window.bindAutosave();
      }

      window.loadData().catch(function (error) {
        showFatal((error && error.message) || 'Error al cargar el editor.');
      });
    } catch (error) {
      showFatal((error && error.message) || 'No se pudo inicializar el editor.');
    }
  }

  function loadSequential(index) {
    if (index >= files.length) {
      bootstrap();
      return;
    }

    var src = BASE_PATH + files[index];

    if (document.querySelector('script[data-ped-module-src="' + src + '"]')) {
      loadSequential(index + 1);
      return;
    }

    var script = document.createElement('script');
    script.src = src;
    script.defer = true;
    script.async = false;
    script.setAttribute('data-ped-module-src', src);

    script.onload = function () {
      loadSequential(index + 1);
    };

    script.onerror = function () {
      showFatal('No se pudo cargar el módulo: ' + files[index]);
    };

    document.body.appendChild(script);
  }

  loadSequential(0);
})();
