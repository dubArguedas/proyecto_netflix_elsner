"""Verificacion: tablas 3, 4 y 5 y detalle de MapReduce."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from backend.api.deps import obtener_datastore
from backend.services.datastore import DataStore, registros
from pipeline.actores import separar_actores
from pipeline.config import RUTA_MAPREDUCE

router = APIRouter(tags=["Verificacion"])


@router.get("/verificacion", summary="Tablas 3, 4 y 5 del informe")
def verificacion(datos: DataStore = Depends(obtener_datastore)) -> dict[str, Any]:
    return datos.verificacion


@router.get("/mapreduce", summary="Resultado de Hadoop y los diez primeros actores")
def mapreduce(
    limite: int = Query(10, ge=1, le=1000),
    datos: DataStore = Depends(obtener_datastore),
) -> dict[str, Any]:
    return {
        "disponible": not datos.mapreduce.empty,
        "archivo": RUTA_MAPREDUCE.name,
        "total_actores": int(len(datos.mapreduce)),
        "pares_actor_titulo": int(
            datos.df["cast"].map(lambda valor: len(separar_actores(valor))).sum()
        ),
        "registros": registros(datos.mapreduce.head(limite)),
        "top_10": registros(datos.mapreduce.head(10)),
        "comparacion": datos.verificacion.get("comparacion_actores"),
    }
