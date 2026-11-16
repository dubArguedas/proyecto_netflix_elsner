"""Reto 1 - Resultados de la limpieza."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from backend.api.deps import obtener_datastore
from backend.services.datastore import DataStore

router = APIRouter(tags=["Reto 1 - Limpieza"])


@router.get("/limpieza", summary="Tabla 1, nulos por columna y muestra del archivo limpio")
def limpieza(datos: DataStore = Depends(obtener_datastore)) -> dict[str, Any]:
    return datos.informe_limpieza()
