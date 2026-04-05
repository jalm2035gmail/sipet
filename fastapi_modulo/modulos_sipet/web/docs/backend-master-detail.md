# Backend Master Detail

Patron reusable para pantallas administrativas con:

- navegacion interna a la izquierda
- panel de trabajo a la derecha
- tabs verticales sin modal
- responsive a una sola columna

## Assets compartidos

Incluye estos archivos en la vista HTML del modulo:

```html
<link rel="stylesheet" href="/static/css/backend-master-detail.css" />
<script src="/static/js/backend-master-detail.js"></script>
```

## Estructura minima

```html
<div class="backend-master-detail js-backend-master-detail">
  <aside class="backend-master-detail__nav">
    <p class="backend-master-detail__nav-title">Configuracion</p>

    <div class="backend-master-detail__tabs" role="tablist" aria-orientation="vertical">
      <button
        class="backend-master-detail__tab active"
        id="tab-general"
        type="button"
        role="tab"
        aria-selected="true"
        aria-controls="panel-general"
      >
        <span class="backend-master-detail__tab-title">General</span>
        <span class="backend-master-detail__tab-copy">Datos base del modulo.</span>
      </button>

      <button
        class="backend-master-detail__tab"
        id="tab-ajustes"
        type="button"
        role="tab"
        aria-selected="false"
        aria-controls="panel-ajustes"
      >
        <span class="backend-master-detail__tab-title">Ajustes</span>
        <span class="backend-master-detail__tab-copy">Permisos, banderas y reglas.</span>
      </button>
    </div>
  </aside>

  <div class="backend-master-detail__content">
    <section
      class="backend-master-detail__panel"
      id="panel-general"
      role="tabpanel"
      aria-labelledby="tab-general"
    >
      ...
    </section>

    <section
      class="backend-master-detail__panel"
      id="panel-ajustes"
      role="tabpanel"
      aria-labelledby="tab-ajustes"
      hidden
    >
      ...
    </section>
  </div>
</div>
```

## Reglas

- Cada tab necesita `aria-controls` apuntando al `id` del panel.
- Cada panel necesita `aria-labelledby` apuntando al `id` del tab.
- Marca solo un tab como `active` al inicio.
- Los paneles inactivos deben arrancar con `hidden`.
- Usa este layout para configuracion, catalogos y vistas administrativas. No lo uses para drawers o flujos cortos de una sola accion.

## Compatibilidad

El inicializador tambien acepta clases antiguas de `notebook`, `notebook-tab` y `notebook-panel`, para migracion gradual.

## Recomendacion de uso

- Si el modulo ya tiene una lista y un formulario en la misma pantalla, conserva esa logica interna.
- Reemplaza solo la navegacion superior por este contenedor lateral.
- Mantene un boton de guardado siempre visible dentro del panel derecho.
