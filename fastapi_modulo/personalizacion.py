from fastapi import APIRouter
from fastapi_modulo.modulos.personalizacion.personalizar import router as personalizar_router

personalizacion_router = APIRouter()
personalizacion_router.include_router(personalizar_router)

# Aquí puedes agregar tus endpoints de personalización
