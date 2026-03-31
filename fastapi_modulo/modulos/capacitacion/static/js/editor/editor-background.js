'use strict';

/* =========================================================
   HELPERS
========================================================= */

function getCurrentEditor() {
  return (typeof window.editor !== 'undefined' && window.editor) ? window.editor : null;
}

function getSlidesCollection() {
  return Array.isArray(window.slides) ? window.slides : [];
}

function getActiveSlide() {
  return typeof window.currentSlide === 'function' ? window.currentSlide() : null;
}

function syncBackgroundSwatches(color) {
  var panel = document.getElementById('ped-background-panel');
  if (!panel) return;

  Array.prototype.slice.call(panel.querySelectorAll('[data-ped-bg-color]')).forEach(function (item) {
    var swatchColor = item.getAttribute('data-ped-bg-color');
    var isSelected = !!color && swatchColor === color;
    item.classList.toggle('is-selected', isSelected);
  });
}

/* =========================================================
   PREVIEW
========================================================= */

function updateBackgroundPreview(color, imageUrl) {
  var preview = el('ped-bg-preview');
  if (!preview) return;

  preview.style.backgroundColor = color || '#3f6f12';

  if (imageUrl) {
    preview.style.backgroundImage = 'url(' + imageUrl + ')';
    preview.style.backgroundSize = 'cover';
    preview.style.backgroundPosition = 'center';
    preview.style.backgroundRepeat = 'no-repeat';
  } else {
    preview.style.backgroundImage = 'none';
    preview.style.backgroundSize = '';
    preview.style.backgroundPosition = '';
    preview.style.backgroundRepeat = '';
  }
}

/* =========================================================
   PALETAS
========================================================= */

function applyPalette(kind) {
  var paletteMap = {
    'creation-1': ['#e89a6d', '#65a620', '#3f6f12'],
    'creation-2': ['#65a620', '#e89a6d', '#ffffff'],
    'creation-3': ['#3f6f12', '#c79f66', '#ffffff'],
    'combo-1': ['#e8e95d', '#63b28e', '#16647d'],
    'combo-2': ['#ecdbac', '#e39b6e', '#bf4343'],
    'combo-3': ['#eed27b', '#6eb1d8', '#1d5f96'],
    'combo-4': ['#ece76e', '#edc84f', '#5462f0'],
    'combo-5': ['#dbe870', '#ebefef', '#0f1d59'],
    'combo-6': ['#bbe885', '#d57183', '#8e1010'],
    'brand-kit': ['#e89a6d', '#3f6f12', '#ffffff']
  };

  if (kind === 'brand-add') {
    if (typeof window.toast === 'function') {
      window.toast('Pendiente conectar colores personalizados de la marca.');
    }
    return;
  }

  var palette = paletteMap[kind];
  var editorInstance = getCurrentEditor();

  if (!palette || !editorInstance) return;

  var selected = editorInstance.getSelected && editorInstance.getSelected();

  if (selected && selected.addStyle) {
    selected.addStyle({
      color: palette[2] || '#111827',
      background: palette[0],
      borderColor: palette[1] || palette[0]
    });

    if (typeof window.toast === 'function') {
      window.toast('Paleta aplicada al elemento seleccionado.');
    }

    if (typeof window.saveCurrentSlide === 'function') {
      window.saveCurrentSlide({ autosave: true, silent: true }).catch(function () {});
    }

    return;
  }

  var slide = getActiveSlide();
  if (!slide) return;

  slide.bg_color = palette[1] || palette[0];

  if (typeof window.inputSlideBgColor !== 'undefined' && window.inputSlideBgColor) {
    window.inputSlideBgColor.value = slide.bg_color;
  }

  if (typeof window.paintEditorBackground === 'function') {
    window.paintEditorBackground(slide);
  }

  if (typeof window.renderSlideList === 'function') {
    window.renderSlideList();
  }

  updateBackgroundPreview(slide.bg_color, slide.bg_image_url || '');
  syncBackgroundSwatches(slide.bg_color);

  if (typeof window.toast === 'function') {
    window.toast('Paleta aplicada a la diapositiva.');
  }

  if (typeof window.saveCurrentSlide === 'function') {
    window.saveCurrentSlide({ autosave: true, silent: true }).catch(function () {});
  }
}

/* =========================================================
   COLOR DE FONDO
========================================================= */

function applyBackgroundColor(color, applyAll) {
  if (color === 'custom' || color === 'palette') {
    if (typeof window.inputSlideBgColor !== 'undefined' && window.inputSlideBgColor) {
      window.inputSlideBgColor.click();
    }
    return;
  }

  if (!color) return;

  if (applyAll) {
    var slides = getSlidesCollection();
    if (!slides.length) return;

    slides.forEach(function (slide) {
      slide.bg_color = color;
    });

    if (typeof window.inputSlideBgColor !== 'undefined' && window.inputSlideBgColor) {
      window.inputSlideBgColor.value = color;
    }

    if (typeof window.renderSlideList === 'function') {
      window.renderSlideList();
    }

    var activeAll = getActiveSlide();
    if (activeAll && typeof window.paintEditorBackground === 'function') {
      window.paintEditorBackground(activeAll);
    }

    updateBackgroundPreview(color, activeAll && activeAll.bg_image_url ? activeAll.bg_image_url : '');
    syncBackgroundSwatches(color);

    if (typeof window.toast === 'function') {
      window.toast('Fondo aplicado a todas las páginas.');
    }

    if (typeof window.saveCurrentSlide === 'function') {
      window.saveCurrentSlide({ autosave: true, silent: true }).catch(function () {});
    }

    return;
  }

  var slide = getActiveSlide();
  if (!slide) return;

  slide.bg_color = color;

  if (typeof window.inputSlideBgColor !== 'undefined' && window.inputSlideBgColor) {
    window.inputSlideBgColor.value = color;
  }

  if (typeof window.paintEditorBackground === 'function') {
    window.paintEditorBackground(slide);
  }

  if (typeof window.renderSlideList === 'function') {
    window.renderSlideList();
  }

  updateBackgroundPreview(color, slide.bg_image_url || '');
  syncBackgroundSwatches(color);

  if (typeof window.toast === 'function') {
    window.toast('Fondo aplicado a la diapositiva.');
  }

  if (typeof window.saveCurrentSlide === 'function') {
    window.saveCurrentSlide({ autosave: true, silent: true }).catch(function () {});
  }
}

/* =========================================================
   IMAGEN DE FONDO
========================================================= */

function applyBackgroundImage(imageUrl, applyAll) {
  if (!imageUrl) return;

  if (applyAll) {
    var slides = getSlidesCollection();
    if (!slides.length) return;

    slides.forEach(function (slide) {
      slide.bg_image_url = imageUrl;
    });

    var activeAll = getActiveSlide();
    if (activeAll && typeof window.paintEditorBackground === 'function') {
      window.paintEditorBackground(activeAll);
      updateBackgroundPreview(activeAll.bg_color || '#3f6f12', imageUrl);
    }

    if (typeof window.renderSlideList === 'function') {
      window.renderSlideList();
    }

    if (typeof window.toast === 'function') {
      window.toast('Imagen de fondo aplicada a todas las páginas.');
    }

    if (typeof window.saveCurrentSlide === 'function') {
      window.saveCurrentSlide({ autosave: true, silent: true }).catch(function () {});
    }

    return;
  }

  var slide = getActiveSlide();
  if (!slide) return;

  slide.bg_image_url = imageUrl;

  if (typeof window.paintEditorBackground === 'function') {
    window.paintEditorBackground(slide);
  }

  if (typeof window.renderSlideList === 'function') {
    window.renderSlideList();
  }

  updateBackgroundPreview(slide.bg_color || '#3f6f12', imageUrl);

  if (typeof window.toast === 'function') {
    window.toast('Imagen de fondo aplicada a la diapositiva.');
  }

  if (typeof window.saveCurrentSlide === 'function') {
    window.saveCurrentSlide({ autosave: true, silent: true }).catch(function () {});
  }
}

function clearBackgroundImage(applyAll) {
  if (applyAll) {
    var slides = getSlidesCollection();
    if (!slides.length) return;

    slides.forEach(function (slide) {
      slide.bg_image_url = '';
    });

    var activeAll = getActiveSlide();
    if (activeAll && typeof window.paintEditorBackground === 'function') {
      window.paintEditorBackground(activeAll);
      updateBackgroundPreview(activeAll.bg_color || '#3f6f12', '');
    }

    if (typeof window.renderSlideList === 'function') {
      window.renderSlideList();
    }

    if (typeof window.toast === 'function') {
      window.toast('Imagen de fondo eliminada de todas las páginas.');
    }

    if (typeof window.saveCurrentSlide === 'function') {
      window.saveCurrentSlide({ autosave: true, silent: true }).catch(function () {});
    }

    return;
  }

  var slide = getActiveSlide();
  if (!slide) return;

  slide.bg_image_url = '';

  if (typeof window.paintEditorBackground === 'function') {
    window.paintEditorBackground(slide);
  }

  if (typeof window.renderSlideList === 'function') {
    window.renderSlideList();
  }

  updateBackgroundPreview(slide.bg_color || '#3f6f12', '');

  if (typeof window.toast === 'function') {
    window.toast('Imagen de fondo eliminada de la diapositiva.');
  }

  if (typeof window.saveCurrentSlide === 'function') {
    window.saveCurrentSlide({ autosave: true, silent: true }).catch(function () {});
  }
}

/* =========================================================
   SINCRONIZACIÓN UI
========================================================= */

function syncBackgroundControls(slide) {
  slide = slide || getActiveSlide();
  if (!slide) return;

  if (typeof window.inputSlideBgColor !== 'undefined' && window.inputSlideBgColor) {
    window.inputSlideBgColor.value = slide.bg_color || '#ffffff';
  }

  if (typeof window.inputSlideBgImage !== 'undefined' && window.inputSlideBgImage) {
    window.inputSlideBgImage.value = slide.bg_image_url || '';
  }

  updateBackgroundPreview(slide.bg_color || '#3f6f12', slide.bg_image_url || '');
  syncBackgroundSwatches(slide.bg_color || '');
}

/* =========================================================
   EXPOSICIÓN GLOBAL
========================================================= */

window.updateBackgroundPreview = updateBackgroundPreview;
window.applyPalette = applyPalette;
window.applyBackgroundColor = applyBackgroundColor;
window.applyBackgroundImage = applyBackgroundImage;
window.clearBackgroundImage = clearBackgroundImage;
window.syncBackgroundControls = syncBackgroundControls;
