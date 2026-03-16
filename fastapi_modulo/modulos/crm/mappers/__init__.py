from fastapi_modulo.modulos.crm.mappers.actividad_mapper import actividad_to_dict
from fastapi_modulo.modulos.crm.mappers.campania_mapper import campania_to_dict
from fastapi_modulo.modulos.crm.mappers.contacto_campania_mapper import contacto_campania_to_dict
from fastapi_modulo.modulos.crm.mappers.contacto_mapper import contacto_to_dict
from fastapi_modulo.modulos.crm.mappers.evento_mapper import evento_to_dict
from fastapi_modulo.modulos.crm.mappers.nota_mapper import nota_to_dict
from fastapi_modulo.modulos.crm.mappers.oportunidad_mapper import oportunidad_to_dict

__all__ = [
    "actividad_to_dict",
    "campania_to_dict",
    "contacto_campania_to_dict",
    "contacto_to_dict",
    "evento_to_dict",
    "nota_to_dict",
    "oportunidad_to_dict",
]
