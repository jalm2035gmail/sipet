(function () {
  if (window.SIPETOrgChartLoader) return;

  var loaderPromise = null;

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      if (document.querySelector('script[src="' + src + '"]')) {
        resolve();
        return;
      }
      var script = document.createElement("script");
      script.src = src;
      script.async = true;
      script.onload = function () { resolve(); };
      script.onerror = function () { reject(new Error("No se pudo cargar " + src)); };
      document.head.appendChild(script);
    });
  }

  async function ensure() {
    if (window.d3 && window.d3.OrgChart) return true;
    if (!loaderPromise) {
      loaderPromise = (async function () {
        await loadScript("/static/vendor/d3.min.js");
        await loadScript("/static/vendor/d3-flextree.min.js");
        await loadScript("/static/vendor/d3-org-chart.min.js");
        return true;
      })().catch(function () {
        return false;
      });
    }
    var result = await loaderPromise;
    return result !== false && !!(window.d3 && window.d3.OrgChart);
  }

  window.SIPETOrgChartLoader = {
    ensure: ensure
  };
})();
