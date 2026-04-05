# Módulo Subastas

Base funcional para Python + FastAPI enfocada en:
- subastas
- lotes
- postores
- pujas
- adjudicaciones
- pagos
- dashboard
- bitácora

## Estructura
- `controladores/subastas.py`: endpoints y bootstrap local de FastAPI/SQLite.
- `modelos/db_models.py`: modelos SQLAlchemy.
- `modelos/schemas.py`: validaciones Pydantic.
- `modelos/store.py`: reglas de negocio.
- `vistas/subastas.html`: panel visual básico.
- `static/js/subastas.js`: interacciones del panel.
- `static/css/subastas.css`: estilos.
- `tests/`: pruebas básicas.

## Nota
Este módulo es un **MVP técnico**. Antes de producción conviene fortalecer:
- autenticación/autorización real
- concurrencia robusta para pujas simultáneas
- websocket o canal en tiempo real
- manejo de archivos para fotos/documentos
- pagos integrados
- integración con usuarios y negocios del ecosistema principal
