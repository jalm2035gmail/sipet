// Registro de texto editable para widgets SIPET en GrapesJS.
// Este archivo replica el criterio usado por /static/js/sipet-widgets.js
// para no mantener dos comportamientos distintos.

if (window.grapesjs) {
  grapesjs.plugins.add('sipet-widgets', function(editor) {
    var dc = editor.DomComponents;
    var TEXT_TAGS = {
      A: true,
      BUTTON: true,
      DIV: true,
      H1: true,
      H2: true,
      H3: true,
      H4: true,
      H5: true,
      H6: true,
      LABEL: true,
      LI: true,
      P: true,
      SMALL: true,
      SPAN: true,
      STRONG: true,
    };
    var SKIP_TAGS = {
      IMG: true,
      INPUT: true,
      IFRAME: true,
      OPTION: true,
      PATH: true,
      SCRIPT: true,
      SELECT: true,
      STYLE: true,
      SVG: true,
      TEXTAREA: true,
      VIDEO: true,
    };

    dc.addType('sipet-widget-text', {
      model: {
        defaults: {
          tagName: 'div',
          editable: true,
          textable: true,
          selectable: true,
          hoverable: true,
          highlightable: true,
          layerable: true,
          copyable: true,
          draggable: true,
          droppable: false,
        },
      },
      isComponent: function(el) {
        return el && el.classList && el.classList.contains('sipet-editable-text')
          ? { type: 'sipet-widget-text' }
          : false;
      },
    });

    function hasDirectText(el) {
      if (!el || !el.childNodes) return false;
      for (var i = 0; i < el.childNodes.length; i++) {
        var node = el.childNodes[i];
        if (node && node.nodeType === 3 && node.textContent && node.textContent.trim()) {
          return true;
        }
      }
      return false;
    }

    function markEditableText(component) {
      if (!component) return;
      var el = component.getEl ? component.getEl() : null;
      if (el && el.nodeType === 1) {
        var tag = el.tagName ? String(el.tagName).toUpperCase() : '';
        if (!SKIP_TAGS[tag] && ((el.classList && el.classList.contains('sipet-editable-text')) || (TEXT_TAGS[tag] && hasDirectText(el)))) {
          if (el.classList && !el.classList.contains('sipet-editable-text')) {
            el.classList.add('sipet-editable-text');
          }
          var attrs = component.getAttributes ? component.getAttributes() : {};
          if (!attrs.class || attrs.class.indexOf('sipet-editable-text') === -1) {
            var nextClass = (attrs.class || '').trim();
            attrs.class = (nextClass ? nextClass + ' ' : '') + 'sipet-editable-text';
            component.setAttributes(attrs);
          }
          component.set({
            editable: true,
            textable: true,
            selectable: true,
            hoverable: true,
            highlightable: true,
            layerable: true,
            copyable: true,
            draggable: true,
            droppable: false,
          });
        }
      }
      if (!component.components) return;
      var children = component.components();
      if (!children || !children.length) return;
      for (var i = 0; i < children.length; i++) {
        var child = children.at ? children.at(i) : children[i];
        if (child) markEditableText(child);
      }
    }

    function normalizeEditableText(root) {
      markEditableText(root || editor.getWrapper());
    }

    editor.on('load', function() {
      normalizeEditableText();
    });
    editor.on('component:add', function(component) {
      normalizeEditableText(component);
    });
  });
}
