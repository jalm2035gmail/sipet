# Aplicaciones

Administración central de módulos SIPET.

## Funciones

- listar aplicaciones
- activar y desactivar módulos
- importar paquetes ZIP
- sincronizar el protocolo `__init__.py` y `__manifest__.py`
- auditar cumplimiento por módulo

## Protocolo de permisos por app

Cada módulo puede definir sus propios permisos sin modificar otro módulo.

Estructura mínima recomendada:

- `Seguridad/`
- `Seguridad/permisos.json`
- `__manifest__.py`

Ejemplo de `Seguridad/permisos.json`:

```json
{
  "app": "crm",
  "groups": [
    {
      "key": "crm_usuario",
      "name": "CRM Usuario",
      "permissions": [
        "crm.ver",
        "crm.contactos.ver"
      ]
    },
    {
      "key": "crm_admin",
      "name": "CRM Administrador",
      "permissions": [
        "crm.*"
      ]
    }
  ]
}
```

Declaración en `__manifest__.py`:

```python
"data": [
    "Seguridad/permisos.json",
]
```

Reglas:

- cada permiso debe usar prefijo del módulo: `mi_tablero.ver`, `crm.editar`, `activo_fijo.bajas.aprobar`
- los grupos y permisos viven dentro del propio módulo
- no declarar permisos de otro módulo en `Seguridad/`
- más adelante `Aplicaciones` leerá estos archivos para instalar y auditar permisos

## CSS oficial

Las pantallas backend de cada módulo deben usar el layout oficial y sus clases base.

Usar:

- `render_backend_page(...)`
- `backend_screen(...)`
- template base `base.html`

Clases oficiales recomendadas:

- `.content-section`
- `.content-section-head`
- `.content-section-kicker`
- `.content-section-title`
- `.content-section-body`
- `.subsection-grid`
- `.subsection-card`
- `.subsection-head`
- `.subsection-title`
- `.subsection-description`
- `.subsection-value`
- `.subsection-chip`

Si un módulo necesita CSS adicional:

- crear `static/css/<modulo>.css`
- declararlo en `__manifest__.py`
- usarlo solo para estilos propios del módulo
- no reescribir el layout global si no es estrictamente necesario
