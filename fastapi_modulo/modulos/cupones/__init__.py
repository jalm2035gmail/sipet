"""
cupones_fidelizacion
====================
Módulo de cupones de descuento y planes de fidelización multi-tienda.

Uso simplificado con facades:
    from cupones_fidelizacion import CuponFacade, FidelizacionFacade

Uso directo de servicios:
    from cupones_fidelizacion.multitienda.tenant import TenantService
    from cupones_fidelizacion.cupones.generador import CuponGenerador
    from cupones_fidelizacion.fidelizacion.configurador import PlanFidelizacionService
"""

__version__ = "1.0.0"
__author__ = "Tu Empresa"

from cupones_fidelizacion.facade import CuponFacade, FidelizacionFacade

__all__ = ["CuponFacade", "FidelizacionFacade"]
