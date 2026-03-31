'use strict';

/* =========================================================
   HELPERS
========================================================= */

function getSlidesSafe() {
  return Array.isArray(window.slides) ? window.slides : [];
}

function getCurrentSlideSafe() {
  return typeof window.currentSlide === 'function' ? window.currentSlide() : null;
}

function ensurePagesViewMode() {
  if (window.pagesViewMode !== 'grid') {
    window.pagesViewMode = 'list';
  }
  return window.pagesViewMode;
}

function getSlideThumbStyle(slide, fallback) {
  fallback = fallback || '#476f16';
  var bgColor = (slide && slide.bg_color) || fallback;
  var bgImage = slide && slide.bg_image_url ? slide.bg_image_url : '';
  var style = 'background:' + bgColor + ';';
  if (bgImage) {
    style += 'background-image:url(' + bgImage + ');background-size:cover;background-position:center;';
  }
  return style;
}

function escapeHtmlLocal(value) {
  if (typeof window.esc === 'function') return window.esc(value);
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/* =========================================================
   FORMULARIO DE SLIDE
========================================================= */

function applySlideForm(slide) {
  if (!slide) return;

  if (typeof window.inputSlideTitle !== 'undefined' && window.inputSlideTitle) {
    window.inputSlideTitle.value = slide.titulo || '';
  }

  if (typeof window.inputSlideBgColor !== 'undefined' && window.inputSlideBgColor) {
    window.inputSlideBgColor.value = slide.bg_color || '#ffffff';
  }

  if (typeof window.inputSlideBgImage !== 'undefined' && window.inputSlideBgImage) {
    window.inputSlideBgImage.value = slide.bg_image_url || '';
  }

  if (typeof window.inputSlideNotes !== 'undefined' && window.inputSlideNotes) {
    window.inputSlideNotes.value = slide.notas || '';
  }

  if (typeof window.slideStatus !== 'undefined' && window.slideStatus) {
    window.slideStatus.textContent = slide.titulo || ('Diapositiva ' + (window.currentSlideIdx + 1));
  }

  if (typeof window.syncBackgroundControls === 'function') {
    window.syncBackgroundControls(slide);
  } else if (typeof window.updateBackgroundPreview === 'function') {
    window.updateBackgroundPreview(slide.bg_color || '#3f6f12', slide.bg_image_url || '');
  }
}

/* =========================================================
   PANEL DE PÁGINAS
========================================================= */

function renderPagesPanel() {
  var pagesList = el('ped-pages-list');
  if (!pagesList) return;

  var slides = getSlidesSafe();
  var currentIdx = typeof window.currentSlideIdx === 'number' ? window.currentSlideIdx : -1;
  var mode = ensurePagesViewMode();

  pagesList.classList.toggle('is-grid', mode === 'grid');

  if (!slides.length) {
    pagesList.innerHTML = '<div class="ped-empty">No hay páginas disponibles.</div>';
    return;
  }

  pagesList.innerHTML = slides.map(function (slide, index) {
    var title = escapeHtmlLocal(slide.titulo || ('Diapositiva ' + (index + 1)));
    var activeClass = index === currentIdx ? ' is-active' : '';
    var thumbStyle = getSlideThumbStyle(slide, '#d1d5db');

    return (
      '<button class="ped-page-card' + activeClass + '" type="button" data-ped-page-idx="' + index + '">' +
        '<div class="ped-page-row">' +
          '<div class="ped-page-thumb" data-ped-page-select="' + index + '" style="' + thumbStyle + '"></div>' +
          '<div class="ped-page-actions">' +
            '<button class="ped-page-icon" type="button" data-ped-page-select="' + index + '" title="Abrir">↗</button>' +
            '<button class="ped-page-icon" type="button" data-ped-page-duplicate="' + index + '" title="Duplicar">⧉</button>' +
            '<button class="ped-page-icon" type="button" data-ped-page-preview="' + index + '" title="Presentar">▶</button>' +
          '</div>' +
        '</div>' +
        '<div class="ped-page-meta">' +
          '<strong>' + (index + 1) + '.</strong>' +
          '<span>' + title + '</span>' +
        '</div>' +
      '</button>'
    );
  }).join('');
}

function setPagesViewMode(mode) {
  window.pagesViewMode = mode === 'grid' ? 'grid' : 'list';

  var listBtn = el('ped-pages-view-list');
  var gridBtn = el('ped-pages-view-grid');

  if (listBtn) listBtn.classList.toggle('is-active', window.pagesViewMode === 'list');
  if (gridBtn) gridBtn.classList.toggle('is-active', window.pagesViewMode === 'grid');

  renderPagesPanel();
}

/* =========================================================
   FOOTER / LISTA DE SLIDES
========================================================= */

function renderSlideList() {
  var host = el('ped-slide-list');
  if (!host) return;

  var slides = getSlidesSafe();
  var currentIdx = typeof window.currentSlideIdx === 'number' ? window.currentSlideIdx : -1;

  if (!slides.length) {
    host.innerHTML = '<div class="ped-empty">Sin diapositivas.</div>';
    renderPagesPanel();
    return;
  }

  host.innerHTML = slides.map(function (slide, index) {
    var title = escapeHtmlLocal(slide.titulo || ('Diapositiva ' + (index + 1)));
    var meta = slide.bg_image_url ? 'Imagen' : (slide.bg_color || '#ffffff');
    var activeClass = index === currentIdx ? ' active' : '';
    var thumbStyle = getSlideThumbStyle(slide, '#476f16');

    return (
      '<button class="ped-slide-thumb' + activeClass + '" type="button" data-slide-idx="' + index + '" style="' + thumbStyle + '">' +
        '<span class="ped-slide-thumb-num">' + (index + 1) + '</span>' +
        '<div class="ped-slide-thumb-title">' + title + '</div>' +
        '<div class="ped-slide-thumb-meta">' + escapeHtmlLocal(meta) + '</div>' +
      '</button>'
    );
  }).join('');

  renderPagesPanel();
}

/* =========================================================
   CARGA EN EL EDITOR
========================================================= */

function loadSlideIntoEditor(slide) {
  if (!slide || !window.editorReady || !window.editor) return;

  applySlideForm(slide);

  var payload = typeof window.grapesElementFromSlide === 'function'
    ? window.grapesElementFromSlide(slide)
    : null;

  var project = payload && payload.contenido_json ? payload.contenido_json : null;

  try {
    if (window.editor.DomComponents && window.editor.DomComponents.clear) {
      window.editor.DomComponents.clear();
    }
    if (window.editor.CssComposer && window.editor.CssComposer.clear) {
      window.editor.CssComposer.clear();
    }

    if (project && project.project && window.editor.loadProjectData) {
      window.editor.loadProjectData(project.project);
    } else if (project && (project.html || project.css)) {
      if (window.editor.setComponents) window.editor.setComponents(project.html || '');
      if (window.editor.setStyle) window.editor.setStyle(project.css || '');
    } else {
      var legacyHtml = typeof window.legacyElementsToHtml === 'function'
        ? window.legacyElementsToHtml(slide.elementos || [])
        : '';
      if (window.editor.setComponents) window.editor.setComponents(legacyHtml);
      if (window.editor.setStyle) window.editor.setStyle('');
    }

    setTimeout(function () {
      if (typeof window.refreshSurveyPreviews === 'function') {
        window.refreshSurveyPreviews();
      }
      if (typeof window.renderWidgetConfig === 'function') {
        window.renderWidgetConfig();
      }
      if (typeof window.refreshEditorCanvas === 'function') {
        window.refreshEditorCanvas();
      }
      if (typeof window.paintEditorBackground === 'function') {
        window.paintEditorBackground(slide);
      }
    }, 80);
  } catch (error) {
    if (typeof window.toast === 'function') {
      window.toast('No se pudo cargar la diapositiva en el editor.', true);
    }
  }
}

/* =========================================================
   EXTRACCIÓN DE PROYECTO
========================================================= */

function extractProjectPayload() {
  if (!window.editor) {
    return {
      html: '',
      css: '',
      project: null,
      responsive_mode: window.currentViewportMode || 'desktop',
      saved_at: new Date().toISOString()
    };
  }

  return {
    html: window.editor.getHtml ? window.editor.getHtml() : '',
    css: window.editor.getCss ? window.editor.getCss() : '',
    project: window.editor.getProjectData ? window.editor.getProjectData() : null,
    responsive_mode: window.currentViewportMode || 'desktop',
    saved_at: new Date().toISOString()
  };
}

/* =========================================================
   GUARDADO
========================================================= */

function saveCurrentSlide(options) {
  options = options || {};

  var slide = getCurrentSlideSafe();
  if (!slide || !window.editorReady) return Promise.resolve();

  var title = (
    (typeof window.inputSlideTitle !== 'undefined' && window.inputSlideTitle && window.inputSlideTitle.value) || ''
  ).trim() || ('Diapositiva ' + (window.currentSlideIdx + 1));

  var bgColor = (
    (typeof window.inputSlideBgColor !== 'undefined' && window.inputSlideBgColor && window.inputSlideBgColor.value) || '#ffffff'
  );

  var bgImage = (
    (typeof window.inputSlideBgImage !== 'undefined' && window.inputSlideBgImage && window.inputSlideBgImage.value) || ''
  ).trim();

  var notes = (
    (typeof window.inputSlideNotes !== 'undefined' && window.inputSlideNotes && window.inputSlideNotes.value) || ''
  ).trim();

  slide.titulo = title;
  slide.bg_color = bgColor;
  slide.bg_image_url = bgImage;
  slide.notas = notes;

  var payload = extractProjectPayload();
  window.saving = true;

  return window.apiJson('/api/capacitacion/diapositivas/' + slide.id, {
    method: 'PUT',
    body: JSON.stringify({
      titulo: title,
      bg_color: bgColor,
      bg_image_url: bgImage,
      notas: notes
    })
  }).then(function (res) {
    if (!res || !res.ok) throw new Error('No se pudo guardar la diapositiva.');

    return window.apiJson('/api/capacitacion/diapositivas/' + slide.id + '/elementos', {
      method: 'PUT',
      body: JSON.stringify({
        elementos: [{
          tipo: 'grapes',
          contenido_json: payload,
          animation_json: slide.animation_json || {},
          pos_x: 0,
          pos_y: 0,
          width: 100,
          height: 100,
          z_index: 1
        }],
        autosave: !!options.autosave
      })
    });
  }).then(function (res) {
    window.saving = false;
    if (!res || !res.ok) throw new Error('No se pudo guardar el contenido.');

    slide.elementos = [{
      tipo: 'grapes',
      contenido_json: payload,
      animation_json: slide.animation_json || {},
      pos_x: 0,
      pos_y: 0,
      width: 100,
      height: 100,
      z_index: 1
    }];

    renderSlideList();

    if (typeof window.loadAuditTrail === 'function') {
      window.loadAuditTrail();
    }

    if (!options.silent && typeof window.toast === 'function') {
      window.toast(options.autosave ? 'Auto guardado.' : 'Slide guardada.');
    }

    return res;
  }).catch(function (error) {
    window.saving = false;
    if (!options.silent && typeof window.toast === 'function') {
      window.toast((error && error.message) || 'Error al guardar.', true);
    }
    throw error;
  });
}

/* =========================================================
   SELECCIÓN DE SLIDE
========================================================= */

function selectSlide(index) {
  var slides = getSlidesSafe();
  if (!slides.length) return Promise.resolve();

  index = clamp(index, 0, slides.length - 1);

  if (index === window.currentSlideIdx && getCurrentSlideSafe()) {
    return Promise.resolve();
  }

  function activate() {
    window.currentSlideIdx = index;
    renderSlideList();
    loadSlideIntoEditor(getCurrentSlideSafe());
  }

  if (window.currentSlideIdx >= 0) {
    return saveCurrentSlide({ silent: true })
      .catch(function () {})
      .then(function () {
        activate();
      });
  }

  activate();
  return Promise.resolve();
}

/* =========================================================
   CRUD DE SLIDES
========================================================= */

function addSlide() {
  return saveCurrentSlide({ silent: true })
    .catch(function () {})
    .then(function () {
      return window.apiJson('/api/capacitacion/presentaciones/' + window.presId + '/diapositivas', {
        method: 'POST',
        body: JSON.stringify({
          titulo: 'Nueva diapositiva',
          bg_color: '#ffffff'
        })
      });
    })
    .then(function (res) {
      if (!res || !res.ok) throw new Error('No se pudo crear la diapositiva.');

      getSlidesSafe().push(res.data);

      return selectSlide(getSlidesSafe().length - 1).then(function () {
        if (typeof window.loadAuditTrail === 'function') {
          return window.loadAuditTrail();
        }
        return null;
      });
    })
    .catch(function (error) {
      if (typeof window.toast === 'function') {
        window.toast((error && error.message) || 'Error al crear diapositiva.', true);
      }
    });
}

function duplicateSlide() {
  var slide = getCurrentSlideSafe();
  if (!slide) return Promise.resolve();

  return saveCurrentSlide({ silent: true })
    .catch(function () {})
    .then(function () {
      return window.apiJson('/api/capacitacion/diapositivas/' + slide.id + '/duplicar', {
        method: 'POST'
      });
    })
    .then(function (res) {
      if (!res || !res.ok) throw new Error('No se pudo duplicar la diapositiva.');

      getSlidesSafe().splice(window.currentSlideIdx + 1, 0, res.data);

      return selectSlide(window.currentSlideIdx + 1).then(function () {
        if (typeof window.loadAuditTrail === 'function') {
          return window.loadAuditTrail();
        }
        return null;
      });
    })
    .catch(function (error) {
      if (typeof window.toast === 'function') {
        window.toast((error && error.message) || 'Error al duplicar.', true);
      }
    });
}

function deleteSlide() {
  var slides = getSlidesSafe();
  var slide = getCurrentSlideSafe();

  if (!slide || slides.length <= 1) {
    if (typeof window.toast === 'function') {
      window.toast('La presentación debe conservar al menos una diapositiva.', true);
    }
    return Promise.resolve();
  }

  if (!window.confirm('¿Eliminar esta diapositiva?')) {
    return Promise.resolve();
  }

  return window.apiJson('/api/capacitacion/diapositivas/' + slide.id, {
    method: 'DELETE'
  }).then(function (res) {
    if (!res || !res.ok) throw new Error('No se pudo eliminar la diapositiva.');

    slides.splice(window.currentSlideIdx, 1);
    var targetIndex = Math.max(0, window.currentSlideIdx - 1);

    window.currentSlideIdx = -1;
    return selectSlide(targetIndex).then(function () {
      if (typeof window.loadAuditTrail === 'function') {
        return window.loadAuditTrail();
      }
      return null;
    });
  }).catch(function (error) {
    if (typeof window.toast === 'function') {
      window.toast((error && error.message) || 'Error al eliminar.', true);
    }
  });
}

function moveSlide(direction) {
  var slides = getSlidesSafe();
  if (!slides.length) return Promise.resolve();

  var newIndex = window.currentSlideIdx + direction;
  if (newIndex < 0 || newIndex >= slides.length) return Promise.resolve();

  return saveCurrentSlide({ silent: true })
    .catch(function () {})
    .then(function () {
      var tmp = slides[window.currentSlideIdx];
      slides[window.currentSlideIdx] = slides[newIndex];
      slides[newIndex] = tmp;
      window.currentSlideIdx = newIndex;

      renderSlideList();

      return window.apiJson('/api/capacitacion/presentaciones/' + window.presId + '/reordenar', {
        method: 'PUT',
        body: JSON.stringify({
          orden_ids: slides.map(function (slide) { return slide.id; })
        })
      });
    })
    .then(function (res) {
      if (res && !res.ok) {
        throw new Error('No se pudo reordenar la presentación.');
      }

      loadSlideIntoEditor(getCurrentSlideSafe());

      if (typeof window.loadAuditTrail === 'function') {
        return window.loadAuditTrail();
      }
      return null;
    })
    .catch(function (error) {
      if (typeof window.toast === 'function') {
        window.toast((error && error.message) || 'Error al mover la diapositiva.', true);
      }
    });
}

/* =========================================================
   EXPOSICIÓN GLOBAL
========================================================= */

window.setPagesViewMode = setPagesViewMode;
window.applySlideForm = applySlideForm;
window.renderPagesPanel = renderPagesPanel;
window.renderSlideList = renderSlideList;
window.loadSlideIntoEditor = loadSlideIntoEditor;
window.extractProjectPayload = extractProjectPayload;
window.saveCurrentSlide = saveCurrentSlide;
window.selectSlide = selectSlide;
window.addSlide = addSlide;
window.duplicateSlide = duplicateSlide;
window.deleteSlide = deleteSlide;
window.moveSlide = moveSlide;
