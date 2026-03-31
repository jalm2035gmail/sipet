(function () {
  'use strict';

  /* =========================================================
     HELPERS
  ========================================================= */

  function el(id) {
    return document.getElementById(id);
  }

  function qa(selector, scope) {
    return Array.prototype.slice.call((scope || document).querySelectorAll(selector));
  }

  function on(node, eventName, handler, options) {
    if (!node || !eventName || typeof handler !== 'function') return;
    node.addEventListener(eventName, handler, options || false);
  }

  function raf(fn) {
    if (typeof window.requestAnimationFrame === 'function') {
      return window.requestAnimationFrame(fn);
    }
    return setTimeout(fn, 16);
  }

  function caf(id) {
    if (!id) return;
    if (typeof window.cancelAnimationFrame === 'function') {
      window.cancelAnimationFrame(id);
    } else {
      clearTimeout(id);
    }
  }

  function safeToast(message, isError) {
    if (typeof window.toast === 'function') {
      window.toast(message, !!isError);
    }
  }

  /* =========================================================
     DOM REFERENCES
  ========================================================= */

  var workspace = el('ped-workspace') || document.querySelector('.ped-workspace');
  var sidepanel = el('ped-sidepanel');
  var railButtons = qa('.ped-rail-btn');
  var toggleSidepanelBtn = el('ped-btn-toggle-sidepanel');

  var resourcePanel = el('ped-resource-panel');
  var textPanel = el('ped-text-panel');
  var interactivePanel = el('ped-interactive-panel');
  var questionsPanel = el('ped-questions-panel');
  var widgetsPanel = el('ped-widgets-panel');
  var insertPanel = el('ped-insert-panel');
  var stylePanel = el('ped-style-panel');
  var backgroundPanel = el('ped-background-panel');
  var pagesPanel = el('ped-pages-panel');

  var inputPresTitle = el('ped-pres-title');

  var panelAnimationState = {
    canvasFrame: null,
    canvasTimer: null,
    panelTimer: null,
    opening: false,
    currentPanelId: ''
  };

  /* =========================================================
     PANEL MAP
  ========================================================= */

  function getPanelMap() {
    return {
      'ped-btn-add-texto': 'ped-text-panel',
      'ped-btn-add-imagen': 'ped-resource-panel',
      'ped-btn-add-hotspot': 'ped-interactive-panel',
      'ped-btn-add-survey': 'ped-questions-panel',
      'ped-btn-add-survey-list': 'ped-widgets-panel',
      'ped-btn-add-forma': 'ped-insert-panel',
      'ped-btn-add-boton': 'ped-style-panel',
      'ped-btn-add-embed': 'ped-background-panel',
      'ped-btn-add-slide': 'ped-pages-panel'
    };
  }

  function getAllSecondaryPanels() {
    return [
      textPanel,
      resourcePanel,
      interactivePanel,
      questionsPanel,
      widgetsPanel,
      insertPanel,
      stylePanel,
      backgroundPanel,
      pagesPanel
    ].filter(Boolean);
  }

  function getActiveRailButton() {
    var active = null;
    railButtons.forEach(function (btn) {
      if (!active && btn.classList.contains('is-active')) {
        active = btn;
      }
    });
    return active;
  }

  function getRailButtonById(buttonId) {
    var found = null;
    railButtons.forEach(function (btn) {
      if (!found && btn.id === buttonId) {
        found = btn;
      }
    });
    return found;
  }

  function isSidepanelCollapsed() {
    return !workspace || workspace.classList.contains('is-sidepanel-collapsed');
  }

  /* =========================================================
     PERSISTENCE
  ========================================================= */

  function persistActiveRail(buttonId) {
    try {
      if (!buttonId) {
        window.localStorage.removeItem('ped_active_rail');
        return;
      }
      window.localStorage.setItem('ped_active_rail', buttonId);
    } catch (error) {
      /* noop */
    }
  }

  function readPersistedActiveRail() {
    try {
      return window.localStorage.getItem('ped_active_rail') || '';
    } catch (error) {
      return '';
    }
  }

  /* =========================================================
     CANVAS REFRESH SMOOTHING
  ========================================================= */

  function scheduleCanvasRefresh() {
    caf(panelAnimationState.canvasFrame);
    clearTimeout(panelAnimationState.canvasTimer);

    panelAnimationState.canvasFrame = raf(function () {
      if (typeof window.refreshEditorCanvas === 'function') {
        window.refreshEditorCanvas();
      }
    });

    panelAnimationState.canvasTimer = setTimeout(function () {
      if (typeof window.refreshEditorCanvas === 'function') {
        window.refreshEditorCanvas();
      }
    }, 240);
  }

  function schedulePanelStabilization() {
    clearTimeout(panelAnimationState.panelTimer);
    panelAnimationState.panelTimer = setTimeout(function () {
      panelAnimationState.opening = false;
      scheduleCanvasRefresh();
    }, 220);
  }

  /* =========================================================
     RAIL / PANEL STATE
  ========================================================= */

  function setActiveRail(buttonId) {
    railButtons.forEach(function (btn) {
      btn.classList.toggle('is-active', btn.id === buttonId);
      btn.setAttribute('aria-pressed', btn.id === buttonId ? 'true' : 'false');
    });
  }

  function hideAllSecondaryPanels() {
    getAllSecondaryPanels().forEach(function (panel) {
      panel.classList.remove('is-active');
      panel.setAttribute('aria-hidden', 'true');
    });
  }

  function showSecondaryPanel(panelId) {
    getAllSecondaryPanels().forEach(function (panel) {
      var isTarget = panel.id === panelId;
      panel.classList.toggle('is-active', isTarget);
      panel.setAttribute('aria-hidden', isTarget ? 'false' : 'true');
    });
    panelAnimationState.currentPanelId = panelId || '';
  }

  function switchSecondaryPanel(panelId) {
    if (!panelId) {
      hideAllSecondaryPanels();
      return;
    }

    var alreadyVisible = panelAnimationState.currentPanelId === panelId &&
      getAllSecondaryPanels().some(function (panel) {
        return panel.id === panelId && panel.classList.contains('is-active');
      });

    if (alreadyVisible) return;

    showSecondaryPanel(panelId);
  }

  function openSecondaryPanel(buttonId, options) {
    options = options || {};

    var panelMap = getPanelMap();
    var panelId = panelMap[buttonId];
    if (!panelId || !workspace) return;

    panelAnimationState.opening = true;

    setActiveRail(buttonId);
    switchSecondaryPanel(panelId);

    workspace.classList.remove('is-sidepanel-collapsed');
    if (sidepanel) sidepanel.removeAttribute('hidden');

    persistActiveRail(buttonId);

    if (!options.skipRefresh) {
      scheduleCanvasRefresh();
      schedulePanelStabilization();
    }
  }

  function closeSecondaryPanel(options) {
    options = options || {};

    if (workspace) {
      workspace.classList.add('is-sidepanel-collapsed');
    }

    railButtons.forEach(function (btn) {
      btn.classList.remove('is-active');
      btn.setAttribute('aria-pressed', 'false');
    });

    hideAllSecondaryPanels();

    panelAnimationState.currentPanelId = '';

    if (!options.keepPersisted) {
      persistActiveRail('');
    }

    if (!options.skipRefresh) {
      scheduleCanvasRefresh();
      schedulePanelStabilization();
    }
  }

  function restoreInitialSecondaryPanel() {
    var panelMap = getPanelMap();
    var persisted = readPersistedActiveRail();
    var initialActive = getActiveRailButton();
    var fallbackId = initialActive ? initialActive.id : (railButtons[0] ? railButtons[0].id : '');

    if (persisted && panelMap[persisted]) {
      openSecondaryPanel(persisted, { skipRefresh: false });
      return;
    }

    if (fallbackId && panelMap[fallbackId]) {
      openSecondaryPanel(fallbackId, { skipRefresh: false });
      return;
    }

    closeSecondaryPanel({ skipRefresh: false });
  }

  /* =========================================================
     TABS
  ========================================================= */

  function bindTabs() {
    qa('[data-ped-tab]').forEach(function (button) {
      on(button, 'click', function () {
        var target = button.getAttribute('data-ped-tab');

        qa('[data-ped-tab]').forEach(function (item) {
          item.classList.toggle('is-active', item === button);
        });

        qa('[data-ped-view]').forEach(function (view) {
          view.classList.toggle('is-active', view.getAttribute('data-ped-view') === target);
        });

        scheduleCanvasRefresh();
      });
    });
  }

  /* =========================================================
     INNER TAB GROUPS
  ========================================================= */

  function bindInsertTabs() {
    if (!insertPanel) return;

    on(insertPanel, 'click', function (event) {
      var tab = event.target.closest('[data-ped-insert-tab]');
      if (!tab) return;

      var target = tab.getAttribute('data-ped-insert-tab');

      qa('[data-ped-insert-tab]', insertPanel).forEach(function (item) {
        item.classList.toggle('is-active', item === tab);
      });

      qa('[data-ped-insert-view]', insertPanel).forEach(function (view) {
        view.classList.toggle('is-active', view.getAttribute('data-ped-insert-view') === target);
      });
    });
  }

  function bindBackgroundTabs() {
    if (!backgroundPanel) return;

    on(backgroundPanel, 'click', function (event) {
      var tab = event.target.closest('[data-ped-bg-tab]');
      if (!tab) return;

      var target = tab.getAttribute('data-ped-bg-tab');

      qa('[data-ped-bg-tab]', backgroundPanel).forEach(function (item) {
        item.classList.toggle('is-active', item === tab);
      });

      qa('[data-ped-bg-view]', backgroundPanel).forEach(function (view) {
        view.classList.toggle('is-active', view.getAttribute('data-ped-bg-view') === target);
      });
    });
  }

  /* =========================================================
     TOOLBAR
  ========================================================= */

  function bindToolbar() {
    railButtons.forEach(function (btn) {
      on(btn, 'click', function () {
        var alreadyActive = btn.classList.contains('is-active') &&
          workspace &&
          !workspace.classList.contains('is-sidepanel-collapsed');

        if (alreadyActive) {
          closeSecondaryPanel();
          return;
        }

        openSecondaryPanel(btn.id);

        if (
          btn.id === 'ped-btn-add-hotspot' &&
          typeof window.editor !== 'undefined' &&
          window.editor &&
          window.editor.runCommand
        ) {
          window.editor.runCommand('ped-insert-survey-hotspot');
        }
      });
    });

    if (toggleSidepanelBtn) {
      on(toggleSidepanelBtn, 'click', function () {
        var collapsed = isSidepanelCollapsed();

        if (collapsed) {
          var activeBtn = getActiveRailButton();
          var persisted = readPersistedActiveRail();
          var targetBtn = activeBtn || getRailButtonById(persisted) || (railButtons[0] || null);

          if (targetBtn) {
            openSecondaryPanel(targetBtn.id);
          }
        } else {
          var currentActive = getActiveRailButton();
          closeSecondaryPanel({ keepPersisted: !!currentActive });
          if (currentActive) {
            persistActiveRail(currentActive.id);
          }
        }
      });
    }

    var saveBtn = el('ped-btn-save');
    if (saveBtn) {
      on(saveBtn, 'click', function () {
        if (typeof window.saveAll === 'function') {
          Promise.resolve(window.saveAll())
            .then(function () {
              safeToast('Cambios guardados y listos para compartir.');
            })
            .catch(function () {
              safeToast('No se pudieron guardar los cambios.', true);
            });
        }
      });
    }

    var previewBtn = el('ped-btn-preview');
    if (previewBtn) {
      on(previewBtn, 'click', function () {
        if (typeof window.saveCurrentSlide !== 'function') return;

        window.saveCurrentSlide()
          .catch(function () {})
          .then(function () {
            window.open(
              '/capacitacion/presentacion/' + window.presId + '/ver?present=1',
              '_blank',
              'noopener,noreferrer'
            );
          });
      });
    }

    var backBtn = el('ped-btn-back');
    if (backBtn) {
      on(backBtn, 'click', function () {
        if (typeof window.saveCurrentSlide !== 'function') {
          window.location.href = '/capacitacion/presentaciones';
          return;
        }

        window.saveCurrentSlide()
          .catch(function () {})
          .then(function () {
            window.location.href = '/capacitacion/presentaciones';
          });
      });
    }

    var publishBtn = el('ped-btn-publish');
    if (publishBtn) {
      on(publishBtn, 'click', function () {
        if (!window.presentation || typeof window.apiJson !== 'function') return;

        var nextStatus = window.presentation.estado === 'publicado' ? 'borrador' : 'publicado';

        Promise.resolve(typeof window.saveCurrentSlide === 'function' ? window.saveCurrentSlide() : null)
          .catch(function () {})
          .then(function () {
            return window.apiJson('/api/capacitacion/presentaciones/' + window.presId, {
              method: 'PUT',
              body: JSON.stringify({
                estado: nextStatus,
                titulo: inputPresTitle && inputPresTitle.value.trim()
                  ? inputPresTitle.value.trim()
                  : window.presentation.titulo
              })
            });
          })
          .then(function (res) {
            if (!res || !res.ok) throw new Error('No se pudo actualizar el estado.');
            window.presentation = res.data;
            if (typeof window.syncPresentationHeader === 'function') window.syncPresentationHeader();
            if (typeof window.loadAuditTrail === 'function') window.loadAuditTrail();
            safeToast(nextStatus === 'publicado' ? 'Presentación publicada.' : 'Presentación en borrador.');
          })
          .catch(function (error) {
            safeToast((error && error.message) || 'Error al publicar.', true);
          });
      });
    }

    var dupSlideBtn = el('ped-btn-dup-slide');
    if (dupSlideBtn && typeof window.duplicateSlide === 'function') {
      on(dupSlideBtn, 'click', function () {
        window.duplicateSlide();
      });
    }

    var delSlideBtn = el('ped-btn-del-slide');
    if (delSlideBtn && typeof window.deleteSlide === 'function') {
      on(delSlideBtn, 'click', function () {
        window.deleteSlide();
      });
    }

    var slideUpBtn = el('ped-btn-slide-up');
    if (slideUpBtn && typeof window.moveSlide === 'function') {
      on(slideUpBtn, 'click', function () {
        window.moveSlide(-1);
      });
    }

    var slideDownBtn = el('ped-btn-slide-dn');
    if (slideDownBtn && typeof window.moveSlide === 'function') {
      on(slideDownBtn, 'click', function () {
        window.moveSlide(1);
      });
    }

    if (inputPresTitle) {
      on(inputPresTitle, 'change', function () {
        if (!window.presentation || typeof window.apiJson !== 'function') return;

        window.apiJson('/api/capacitacion/presentaciones/' + window.presId, {
          method: 'PUT',
          body: JSON.stringify({
            titulo: inputPresTitle.value.trim() || window.presentation.titulo
          })
        }).then(function (res) {
          if (!res || !res.ok) return;
          window.presentation = res.data;
          if (typeof window.syncPresentationHeader === 'function') window.syncPresentationHeader();
          if (typeof window.loadAuditTrail === 'function') window.loadAuditTrail();
        });
      });
    }

    var slideList = el('ped-slide-list');
    if (slideList) {
      on(slideList, 'click', function (event) {
        var card = event.target.closest('[data-slide-idx]');
        if (!card || typeof window.selectSlide !== 'function') return;
        window.selectSlide(parseInt(card.getAttribute('data-slide-idx'), 10));
      });
    }

    on(document, 'keydown', function (event) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 's') {
        event.preventDefault();
        if (typeof window.saveAll === 'function') {
          window.saveAll();
        }
      }

      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'd') {
        if (typeof window.editor === 'undefined' || !window.editor || !window.editor.getSelected) return;
        event.preventDefault();

        var selected = window.editor.getSelected();
        if (!selected) return;

        var clone = selected.clone();
        var parent = selected.parent ? selected.parent() : null;

        if (clone && parent && parent.append) {
          parent.append(clone);
          if (window.editor.select) window.editor.select(clone);
          if (typeof window.saveCurrentSlide === 'function') {
            window.saveCurrentSlide({ autosave: true, silent: true }).catch(function () {});
          }
          safeToast('Bloque duplicado.');
        }
      }
    });

    if (resourcePanel) {
      on(resourcePanel, 'click', function (event) {
        var trigger = event.target.closest('[data-ped-resource]');
        if (!trigger || typeof window.insertResource !== 'function') return;
        window.insertResource(trigger.getAttribute('data-ped-resource') || '');
      });
    }

    if (textPanel) {
      on(textPanel, 'click', function (event) {
        var trigger = event.target.closest('[data-ped-text]');
        if (!trigger || typeof window.insertTextPreset !== 'function') return;
        window.insertTextPreset(trigger.getAttribute('data-ped-text') || '');
      });
    }

    if (interactivePanel) {
      on(interactivePanel, 'click', function (event) {
        var trigger = event.target.closest('[data-ped-interactive]');
        if (!trigger || typeof window.insertInteractivePreset !== 'function') return;
        window.insertInteractivePreset(trigger.getAttribute('data-ped-interactive') || '');
      });
    }

    if (questionsPanel) {
      on(questionsPanel, 'click', function (event) {
        var configBtn = event.target.closest('#ped-question-config-btn');
        if (configBtn) {
          window.location.href = '/encuestas/constructor';
          return;
        }

        var trigger = event.target.closest('[data-ped-question]');
        if (!trigger || typeof window.insertQuestionPreset !== 'function') return;
        window.insertQuestionPreset(trigger.getAttribute('data-ped-question') || '');
      });
    }

    if (widgetsPanel) {
      on(widgetsPanel, 'click', function (event) {
        var trigger = event.target.closest('[data-ped-widget]');
        if (!trigger || typeof window.insertWidgetPreset !== 'function') return;
        window.insertWidgetPreset(trigger.getAttribute('data-ped-widget') || '');
      });
    }

    if (insertPanel) {
      on(insertPanel, 'click', function (event) {
        var action = event.target.closest('[data-ped-insert]');
        if (!action || typeof window.insertMediaPreset !== 'function') return;
        window.insertMediaPreset(action.getAttribute('data-ped-insert') || '');
      });
    }

    if (stylePanel) {
      on(stylePanel, 'click', function (event) {
        var palette = event.target.closest('[data-ped-style-palette]');
        if (palette) {
          if (typeof window.applyPalette === 'function') {
            window.applyPalette(palette.getAttribute('data-ped-style-palette') || '');
          }
          return;
        }

        var textStyle = event.target.closest('[data-ped-style-text]');
        if (!textStyle || typeof window.insertTextPreset !== 'function') return;
        window.insertTextPreset(textStyle.getAttribute('data-ped-style-text') || '');
      });
    }

    if (backgroundPanel) {
      on(backgroundPanel, 'click', function (event) {
        var swatch = event.target.closest('[data-ped-bg-color]');
        if (swatch) {
          qa('[data-ped-bg-color]', backgroundPanel).forEach(function (item) {
            item.classList.toggle('is-selected', item === swatch);
          });

          if (typeof window.applyBackgroundColor === 'function') {
            window.applyBackgroundColor(swatch.getAttribute('data-ped-bg-color') || '', false);
          }
          return;
        }

        var action = event.target.closest('[data-ped-bg-action]');
        if (!action) return;

        var type = action.getAttribute('data-ped-bg-action') || '';

        if (type === 'upload-image') {
          safeToast('Pendiente subida de imagen personalizada.');
          return;
        }

        if (type === 'apply-all') {
          if (typeof window.applyBackgroundColor === 'function' && typeof window.currentSlide === 'function') {
            window.applyBackgroundColor((window.currentSlide() && window.currentSlide().bg_color) || '#3f6f12', true);
          }
          return;
        }

        if (type === 'set-MAIN') {
          safeToast('Fondo MAIN guardado para este proyecto.');
        }
      });
    }

    var pagesAddBtn = el('ped-pages-add-btn');
    if (pagesAddBtn && typeof window.addSlide === 'function') {
      on(pagesAddBtn, 'click', function () {
        window.addSlide();
      });
    }

    var pagesListBtn = el('ped-pages-view-list');
    if (pagesListBtn && typeof window.setPagesViewMode === 'function') {
      on(pagesListBtn, 'click', function () {
        window.setPagesViewMode('list');
      });
    }

    var pagesGridBtn = el('ped-pages-view-grid');
    if (pagesGridBtn && typeof window.setPagesViewMode === 'function') {
      on(pagesGridBtn, 'click', function () {
        window.setPagesViewMode('grid');
      });
    }

    if (pagesPanel) {
      on(pagesPanel, 'click', function (event) {
        var selectBtn = event.target.closest('[data-ped-page-select],[data-ped-page-idx]');
        if (selectBtn) {
          var idx = selectBtn.getAttribute('data-ped-page-select');
          if (idx == null) idx = selectBtn.getAttribute('data-ped-page-idx');
          if (idx != null && typeof window.selectSlide === 'function') {
            window.selectSlide(parseInt(idx, 10));
          }
          return;
        }

        var dupBtn = event.target.closest('[data-ped-page-duplicate]');
        if (dupBtn && typeof window.selectSlide === 'function' && typeof window.duplicateSlide === 'function') {
          window.selectSlide(parseInt(dupBtn.getAttribute('data-ped-page-duplicate'), 10)).then(function () {
            window.duplicateSlide();
          });
          return;
        }

        var previewBtn = event.target.closest('[data-ped-page-preview]');
        if (previewBtn && typeof window.selectSlide === 'function') {
          window.selectSlide(parseInt(previewBtn.getAttribute('data-ped-page-preview'), 10)).then(function () {
            window.open('/capacitacion/presentacion/' + window.presId + '/ver?present=1', '_blank', 'noopener,noreferrer');
          });
        }
      });
    }

    restoreInitialSecondaryPanel();
    bindInsertTabs();
    bindBackgroundTabs();
  }

  function bindAutosave() {
    clearInterval(window.__pedAutosaveTimer);

    window.__pedAutosaveTimer = setInterval(function () {
      if (
        !window.editorReady ||
        window.saving ||
        typeof window.currentSlide !== 'function' ||
        !window.currentSlide() ||
        typeof window.saveCurrentSlide !== 'function'
      ) {
        return;
      }

      window.saveCurrentSlide({ autosave: true, silent: true }).catch(function () {});
    }, 30000);
  }

  window.pedUI = window.pedUI || {};
  window.pedUI.bindTabs = bindTabs;
  window.pedUI.bindToolbar = bindToolbar;
  window.pedUI.bindAutosave = bindAutosave;
  window.pedUI.openSecondaryPanel = openSecondaryPanel;
  window.pedUI.closeSecondaryPanel = closeSecondaryPanel;
  window.pedUI.restoreInitialSecondaryPanel = restoreInitialSecondaryPanel;

  /* Compatibilidad con llamadas existentes del loader */
  window.bindTabs = bindTabs;
  window.bindToolbar = bindToolbar;
  window.bindAutosave = bindAutosave;
})();
