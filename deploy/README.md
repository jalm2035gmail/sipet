# Deploy

Estructura del directorio:

- `targets/`: scripts de despliegue reales por entorno o instalación.
- `aliases/`: wrappers compatibles que redirigen a un target existente.

Scripts actuales:

- `targets/bootstrap-sipet-server.sh`
- `targets/deploy-avancoop.sh`
- `targets/deploy-uprocach.sh`
- `targets/deploy-polo.sh`
- `aliases/deploy-polotitlan.sh` -> `targets/deploy-polo.sh`
- `aliases/deploy-uprocach.sh` -> `targets/deploy-uprocach.sh`

Notas de sincronizacion:

- El deploy excluye `fastapi_modulo/modulos/`.
- El deploy excluye los JSON legacy de `fastapi_modulo/modulos_sipet/frontend/` para no migrar contenido local de desarrollo a producción.
- `deploy-uprocach.sh` valida que `REMOTE_DIR/fastapi_modulo/modulos` ya exista en el servidor antes de continuar.
- Los modulos se importan y administran por dominio de forma separada.

Ejemplos:

- `SERVER=administrator@203.0.113.10 deploy/aliases/deploy-uprocach.sh`
- `SERVER=administrator@38.247.130.84 deploy/targets/deploy-avancoop.sh`
