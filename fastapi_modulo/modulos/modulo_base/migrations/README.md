Alembic es el mecanismo principal para cambios de esquema en modulos reales.

Reglas:
- `migrations/versions/` guarda revisiones por modulo.
- `bootstrap.py` solo debe encargarse de seeds ligeros o bootstrap de datos.
- `create_all()` queda limitado a desarrollo y pruebas rapidas.
- En produccion, los modulos con `uses_migrations=True` deben aplicar Alembic antes de iniciar.
