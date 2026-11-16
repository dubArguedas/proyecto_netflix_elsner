"""Rutas de la API organizadas por area del proyecto."""

from fastapi import APIRouter

from backend.api.routers import (
    analisis,
    catalogo,
    exportacion,
    limpieza,
    overview,
    verificacion,
)

router = APIRouter(prefix="/api")
router.include_router(overview.router)
router.include_router(limpieza.router)
router.include_router(analisis.router)
router.include_router(verificacion.router)
router.include_router(catalogo.router)
router.include_router(exportacion.router)
