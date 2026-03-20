(function () {
  var root = document.getElementById("dashboard-layout-editor");
  if (!root || !window.grapesjs) {
    return;
  }

  function parseLayout() {
    try {
      return JSON.parse(root.getAttribute("data-layout") || '{"widgets":[]}');
    } catch (error) {
      return { widgets: [] };
    }
  }

  function buildMarkup(layout) {
    var widgets = Array.isArray(layout.widgets) ? layout.widgets : [];
    if (!widgets.length) {
      widgets = [{ type: "apps", x: 0, y: 0, w: 2, h: 1 }];
    }
    return widgets.map(function (widget) {
      return (
        '<section class="dashboard-block" data-widget-type="' + String(widget.type || "widget") + '"' +
        ' data-x="' + String(widget.x || 0) + '"' +
        ' data-y="' + String(widget.y || 0) + '"' +
        ' data-w="' + String(widget.w || 2) + '"' +
        ' data-h="' + String(widget.h || 1) + '"' +
        ' style="padding:20px;border:1px solid rgba(15,23,42,.08);border-radius:16px;background:linear-gradient(180deg,#fff,#f8fafc);margin:12px;">' +
        '<strong style="display:block;font-size:18px;color:#0f172a;">' + String(widget.type || "widget") + "</strong>" +
        '<span style="display:block;margin-top:8px;color:#64748b;">Widget personalizable</span>' +
        "</section>"
      );
    }).join("");
  }

  function extractLayout(editor) {
    var components = editor.getWrapper().components().models || [];
    return {
      widgets: components.map(function (component, index) {
        var attrs = component.getAttributes();
        return {
          type: attrs["data-widget-type"] || "widget",
          x: Number(attrs["data-x"] || index),
          y: Number(attrs["data-y"] || 0),
          w: Number(attrs["data-w"] || 2),
          h: Number(attrs["data-h"] || 1)
        };
      })
    };
  }

  var editor = window.grapesjs.init({
    container: "#dashboard-layout-editor",
    fromElement: false,
    storageManager: false,
    height: "320px",
    panels: { defaults: [] }
  });

  editor.setComponents(buildMarkup(parseLayout()));

  var saveButton = document.getElementById("dashboard-layout-save");
  if (!saveButton) {
    return;
  }

  saveButton.addEventListener("click", function () {
    var layout = extractLayout(editor);
    fetch("/api/dashboard/layout", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(layout)
    }).then(function () {
      root.setAttribute("data-layout", JSON.stringify(layout));
    });
  });
})();
