"""
excepciones.py
--------------
Jerarquía de excepciones del módulo.
"""


class ErrorModulo(Exception):
    """Base de todas las excepciones del módulo."""
    pass


# --- Multi-tienda ---
class TenantNoEncontrado(ErrorModulo):
    pass

class TenantInactivo(ErrorModulo):
    pass

class AccesoDenegado(ErrorModulo):
    """Intento de acceder a datos de otro tenant."""
    pass


# --- Cupones ---
class CuponNoEncontrado(ErrorModulo):
    pass

class CuponInvalido(ErrorModulo):
    pass

class CuponExpirado(CuponInvalido):
    pass

class CuponAgotado(CuponInvalido):
    pass

class CuponRevocado(CuponInvalido):
    pass

class CuponMontoInsuficiente(CuponInvalido):
    pass

class CuponNoAplicaProducto(CuponInvalido):
    pass

class CuponYaUsadoPorCliente(CuponInvalido):
    pass

class CodigoCuponDuplicado(ErrorModulo):
    pass


# --- Fidelización ---
class PlanNoConfigurado(ErrorModulo):
    pass

class CuentaNoEncontrada(ErrorModulo):
    pass

class PuntosInsuficientes(ErrorModulo):
    pass

class CanjeMinimNoAlcanzado(ErrorModulo):
    pass


# --- Antiabuso ---
class SospechaDeFraude(ErrorModulo):
    pass
