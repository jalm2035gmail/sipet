(function () {
  function initContainer(container) {
    if (!container || container.__backendMasterDetailReady) return;
    var tabs = container.querySelectorAll(".backend-master-detail__tab, .notebook-tab");
    var panels = container.querySelectorAll(".backend-master-detail__panel, .notebook-panel");
    if (!tabs.length || !panels.length) return;

    function openTab(tab) {
      var panelId = tab.getAttribute("aria-controls");
      tabs.forEach(function (item) {
        item.classList.remove("active");
        item.setAttribute("aria-selected", "false");
      });
      panels.forEach(function (panel) {
        panel.hidden = true;
      });
      tab.classList.add("active");
      tab.setAttribute("aria-selected", "true");
      if (!panelId) return;
      var targetPanel = container.querySelector("#" + panelId);
      if (targetPanel) {
        targetPanel.hidden = false;
      }
    }

    tabs.forEach(function (tab) {
      tab.addEventListener("click", function (event) {
        event.preventDefault();
        openTab(tab);
      });
    });

    var activeTab = container.querySelector(".backend-master-detail__tab.active, .notebook-tab.active") || tabs[0];
    if (activeTab) {
      openTab(activeTab);
    }
    container.__backendMasterDetailReady = true;
  }

  function initBackendMasterDetail(root) {
    var scope = root && root.querySelectorAll ? root : document;
    scope.querySelectorAll(".js-backend-master-detail, [data-backend-master-detail], .notebook").forEach(initContainer);
  }

  window.initBackendMasterDetail = initBackendMasterDetail;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initBackendMasterDetail(document);
    });
  } else {
    initBackendMasterDetail(document);
  }
})();
