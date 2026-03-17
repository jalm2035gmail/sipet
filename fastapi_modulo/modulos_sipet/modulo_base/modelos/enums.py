from enum import Enum


class ModuloBaseEstado(str, Enum):
    BORRADOR = "borrador"
    ACTIVO = "activo"
    INACTIVO = "inactivo"
