# Deploy

Estructura del directorio:

- `targets/`: scripts de despliegue reales por entorno o instalación.
- `aliases/`: wrappers compatibles que redirigen a un target existente.

Scripts actuales:

- `targets/deploy-avancoop.sh`
- `targets/deploy-polo.sh`
- `aliases/deploy-polotitlan.sh` -> `targets/deploy-polo.sh`
- `aliases/deploy-sipet.sh` -> `targets/deploy-polo.sh`

Notas de sincronizacion:

- El deploy excluye `fastapi_modulo/modulos/`.
- Los modulos se importan y administran por dominio de forma separada.
