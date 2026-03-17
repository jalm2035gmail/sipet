# Arquitectura Multi-Tenant - Fase 0

## Modelo aprobado

- Patrón operativo: `1 app + N bases de datos`
- Framework web principal: `FastAPI`
- ORM estándar: `SQLAlchemy`
- Base de datos de producción: `PostgreSQL`
- Base de datos de desarrollo local: `SQLite`
- Caché preferente para resolución tenant-BD: `Redis`

## Tenant Key oficial

- Estrategia principal: `host`
- Ejemplo: `cliente1.midominio.com`
- Reglas:
  - solo minúsculas
  - sin espacios
  - el host es la identidad primaria del tenant
  - alias de dominio deben resolverse por registro administrativo central

## Convención de nombres de bases de datos

- Producción:
  - `{tenant_slug}_{environment}`
  - Ejemplo: `cliente1_midominio_com_prod`
- Desarrollo:
  - `sqlite:///{project_root}/{tenant_slug}_{environment}.db`

## Reglas de naming

- caracteres permitidos: `a-z`, `0-9`, `_`
- longitud máxima recomendada: `63`
- reemplazar `.`, `-` y espacios por `_`
- colapsar separadores repetidos
- no iniciar con número cuando se use como identificador lógico

## Base administrativa central

Se aprueba una base administrativa central para:

- registrar tenants
- registrar dominios y alias
- registrar estado operativo
- registrar base de datos asociada
- registrar apps instaladas por tenant
- registrar migraciones y auditoría de provisión

## Estrategia de resolución tenant -> base de datos

- Desarrollo inicial:
  - convención por host
  - soporte complementario por variables o archivo de mapeo
- Producción:
  - base administrativa central como fuente de verdad
  - Redis como caché de resolución

## Compatibilidad por ambiente

| Ambiente | Motor principal | Mapeo tenant-BD | Caché | Uso esperado |
| --- | --- | --- | --- | --- |
| local | SQLite | convención/archivo | opcional | desarrollo rápido |
| test | SQLite o PostgreSQL | archivo/fixtures | opcional | pruebas automatizadas |
| staging | PostgreSQL | BD administrativa central | Redis | validación previa |
| producción | PostgreSQL | BD administrativa central | Redis | operación oficial |

## Estructura objetivo

```text
fastapi_modulo/
├── core/
│   ├── tenant_settings.py
│   ├── tenant_types.py
│   └── ...
├── modulos/
├── templates/
└── ...
```

## Criterio de salida de Fase 0

La fase queda cerrada cuando:

- existe una definición única del tenant key
- existe una política oficial de motores por ambiente
- existe una convención oficial de nombres de bases de datos
- existe una matriz de compatibilidad por ambiente
- existe una base técnica mínima para que las siguientes fases codifiquen sobre un estándar único
