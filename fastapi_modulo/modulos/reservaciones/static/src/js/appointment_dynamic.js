/**
 * Módulo: reservaciones
 * Módulo JS de utilidades compartidas para el sistema de reservaciones.
 *
 * La lógica principal de cada vista vive en su propio bloque <script>
 * dentro del HTML correspondiente (reservaciones.html, calendario.html).
 *
 * Este archivo expone window.ResUtils con helpers reutilizables.
 */
(function () {
  'use strict';

  window.ResUtils = {

    /**
     * Escapa caracteres HTML para evitar XSS al insertar strings en el DOM.
     * @param {*} str
     * @returns {string}
     */
    escHtml: function (str) {
      if (str == null) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
    },

    /**
     * Convierte un string "HH:MM" a número flotante (ej. "09:30" → 9.5).
     * @param {string} timeStr
     * @returns {number}
     */
    timeToFloat: function (timeStr) {
      var parts = (timeStr || '00:00').split(':');
      var h = parseInt(parts[0], 10) || 0;
      var m = parseInt(parts[1], 10) || 0;
      return h + m / 60;
    },

    /**
     * Formatea un string ISO datetime a formato local es-MX.
     * @param {string} iso
     * @returns {string}
     */
    formatDatetime: function (iso) {
      if (!iso) return '–';
      try {
        var d = new Date(iso);
        return d.toLocaleString('es-MX', {
          day: '2-digit', month: '2-digit', year: 'numeric',
          hour: '2-digit', minute: '2-digit',
        });
      } catch (e) {
        return iso;
      }
    },

    /**
     * Realiza un fetch JSON con cabeceras estándar.
     * Lanza un Error con el mensaje del backend si el status no es OK.
     * @param {string} url
     * @param {RequestInit} [opts]
     * @returns {Promise<any>}
     */
    fetchJSON: async function (url, opts) {
      var options = Object.assign(
        { headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' } },
        opts || {}
      );
      var res = await fetch(url, options);
      if (!res.ok) {
        var detail = 'HTTP ' + res.status;
        try { var j = await res.json(); detail = j.detail || detail; } catch (e) {}
        throw new Error(detail);
      }
      return res.json();
    },

    /**
     * Devuelve el badge HTML de estado de una cita.
     * @param {string} state
     * @returns {string}
     */
    estadoBadge: function (state) {
      var labels = {
        draft:       'Solicitada',
        confirmed:   'Confirmada',
        in_progress: 'En Progreso',
        completed:   'Completada',
        cancelled:   'Cancelada',
        no_show:     'No Show',
      };
      var label = labels[state] || state;
      return '<span class="res-estado-badge res-badge-' + ResUtils.escHtml(state) + '">' + ResUtils.escHtml(label) + '</span>';
    },

  };

})();
