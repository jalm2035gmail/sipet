# Fases de migración del módulo Presupuesto

## 1. Preparación y planeación

- ✅ Crear la carpeta fastapi_modulo/modulos/presupuesto y los archivos presupuesto.py, presupuesto.html, presupuesto.css.
- ✅ Documentar rutas, dependencias y puntos de integración (ya realizado en separar presupuesto.md).
- ✅ Identificar todo el código relevante en main.py, base.html **y strategic_planning/backend/app/api/v1/endpoints/poa.py** (renderizado, lógica, JS, CSS, endpoints, lectura/escritura de presupuesto.txt, y endpoint de descarga de plantilla CSV).

## 2. Extracción de vistas y estilos

- ✅ Mover el HTML de la vista presupuesto a presupuesto.html (usando Jinja2 o similar).
- ✅ Mover los estilos embebidos a presupuesto.css.
- ✅ Reemplazar en main.py/base.html el bloque de presupuesto por una inclusión de plantilla.

## 3. Modularización de lógica backend

- ✅ Mover la función/endpoint de presupuesto a presupuesto.py.
- ✅ Adaptar la función para que use la plantilla presupuesto.html y los estilos presupuesto.css.
- ✅ Registrar el router de presupuesto en main.py y eliminar el endpoint duplicado.

## 4. Refactorización de JS

- ✅ Mover el JS específico de presupuesto a un bloque <script> en presupuesto.html.
- ✅ Asegurar que la funcionalidad de mostrar/ocultar columna, edición y guardado siga funcionando.


## 5. Integración y pruebas

- ✅ Actualizar main.py/base.html para consumir el nuevo módulo (si aplica).
- ✅ Probar la vista, edición, guardado y exportación/importación de presupuesto.
- ✅ Validar que no haya dependencias rotas ni duplicidad de código.


## 6. Limpieza y documentación

- ✅ Eliminar el código migrado de main.py y base.html.
- ✅ Actualizar separar presupuesto.md con la nueva arquitectura.
- ✅ Documentar cualquier cambio en rutas, endpoints o dependencias.

---

# Relación de Presupuesto con poa.py y main.py

## 1. Archivo main.py
- La ruta `/proyectando/presupuesto` está definida en `main.py`.
- Esta función genera la página de presupuesto, mostrando una tabla editable con los rubros y montos leídos desde `presupuesto.txt`.
- Incluye botones para importar/exportar presupuesto y, ahora, para descargar la plantilla CSV.
- Toda la lógica de renderizado, lectura y guardado de presupuesto está embebida en este archivo, mezclada con otras vistas y funcionalidades.

## 2. Archivo poa.py
- El archivo `poa.py` define endpoints relacionados con el POA (Plan Operativo Anual), como la creación de actividades y la obtención de datos para el Gantt.
- Se agregó el endpoint `/poas/descargar-plantilla-presupuesto` para descargar la plantilla de importación de presupuesto.
- Aunque el endpoint de descarga está en `poa.py`, la lógica de presupuesto (carga, edición, guardado) sigue en `main.py`.

## 3. Relación y dependencias
- El presupuesto es una parte fundamental del POA, ya que cada actividad puede tener un presupuesto asociado.
- Actualmente, la gestión de presupuesto está acoplada a la vista y lógica de `main.py`, mientras que la API de descarga de plantilla está en `poa.py`.
- No existe un módulo independiente para presupuesto: no hay modelos, servicios ni rutas dedicadas exclusivamente a presupuesto.
- Para separar el módulo de presupuesto, será necesario:
  - Extraer la lógica de lectura, guardado y validación de presupuesto de `main.py`.
  - Crear modelos/schemas para presupuesto.
  - Definir endpoints RESTful para CRUD de presupuesto en un archivo dedicado (por ejemplo, `presupuesto.py`).
  - Unificar la descarga de plantilla y la importación bajo el nuevo módulo.

## 4. Siguiente paso sugerido
- Crear un paquete/módulo `presupuesto` con:
  - Modelos y schemas.
  - Servicios para lógica de negocio.
  - Endpoints para API REST.
  - Plantillas y vistas separadas.
