# poa.py
"""
Lógica backend para el POA.
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/poa")
def obtener_poa():
    """Devuelve datos del POA."""
    # TODO: Implementar lógica real
    return {"poa": []}
