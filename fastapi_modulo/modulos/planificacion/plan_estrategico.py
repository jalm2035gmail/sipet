# plan_estrategico.py
"""
Lógica backend para el plan estratégico.
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/plan-estrategico")
def obtener_plan_estrategico():
    """Devuelve datos del plan estratégico."""
    # TODO: Implementar lógica real
    return {"plan_estrategico": []}
