"""Estado del servicio y resumen ejecutivo."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from backend.api.deps import obtener_datastore
from backend.api.schemas import Salud
from backend.core.config import settings
from backend.services.datastore import DataStore
from pipeline.config import RUTA_LIMPIA

router = APIRouter(tags=["Resumen"])


@router.get("/health", response_model=Salud, summary="Estado del servicio")
def salud(datos: DataStore = Depends(obtener_datastore)) -> dict[str, Any]:
    return {
        "estado": "ok",
        "version": settings.version,
        "registros_limpios": int(len(datos.df)),
        "actores_mapreduce": int(len(datos.mapreduce)),
        "mapreduce_disponible": not datos.mapreduce.empty,
        "archivo_limpio": RUTA_LIMPIA.name if RUTA_LIMPIA.exists() else None,
    }


@router.get("/resumen", summary="KPIs, distribuciones y calidad del dato")
def resumen(datos: DataStore = Depends(obtener_datastore)) -> dict[str, Any]:
    return datos.resumen()
