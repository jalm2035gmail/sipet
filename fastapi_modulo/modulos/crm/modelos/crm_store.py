from fastapi_modulo.modulos.crm.servicios.actividad_service import (
    create_actividad,
    delete_actividad,
    list_actividades,
    update_actividad,
)
from fastapi_modulo.modulos.crm.servicios.campania_service import (
    add_contacto_campania,
    create_campania,
    list_campanias,
    list_contactos_campania,
    update_campania,
)
from fastapi_modulo.modulos.crm.servicios.contacto_service import (
    create_contacto,
    delete_contacto,
    get_contacto,
    list_contactos,
    update_contacto,
)
from fastapi_modulo.modulos.crm.servicios.dashboard_service import get_crm_resumen
from fastapi_modulo.modulos.crm.servicios.nota_service import create_nota, delete_nota, list_notas
from fastapi_modulo.modulos.crm.servicios.oportunidad_service import (
    create_oportunidad,
    delete_oportunidad,
    list_oportunidades,
    update_oportunidad,
)
