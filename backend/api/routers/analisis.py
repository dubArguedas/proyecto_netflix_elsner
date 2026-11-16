"""Analisis A, B y C del Reto 3."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from backend.api.deps import obtener_datastore
from backend.api.schemas import RespuestaActores, RespuestaPaises, RespuestaTipos
from backend.services.datastore import DataStore, registros

router = APIRouter(tags=["Reto 3 - Analisis"])


@router.get("/tipos", response_model=RespuestaTipos, summary="Analisis A - titulos por tipo")
def tipos(datos: DataStore = Depends(obtener_datastore)) -> dict:
    clasificado = datos.tipos[datos.tipos["tipo"].isin(["Movie", "TV Show"])]
    return {
        "total_titulos": int(len(datos.df)),
        "total_clasificado": int(clasificado["cantidad_titulos"].sum()),
        "registros": registros(datos.tipos),
    }


@router.get("/actores", response_model=RespuestaActores, summary="Analisis B - titulos por actor")
def actores(
    limite: int = Query(10, ge=1, le=5000, description="Cantidad de actores a devolver"),
    datos: DataStore = Depends(obtener_datastore),
) -> dict:
    return {
        "total_actores": int(len(datos.actores)),
        "limite": limite,
        "registros": registros(datos.actores.head(limite)),
    }


@router.get("/paises", response_model=RespuestaPaises, summary="Analisis C - duracion promedio por pais")
def paises(
    limite: int = Query(10, ge=1, le=5000, description="Cantidad de paises a devolver"),
    datos: DataStore = Depends(obtener_datastore),
) -> dict:
    base = datos.df[
        datos.df["type"].eq("Movie")
        & datos.df["duration_min"].notna()
        & (datos.df["duration_min"] > 0)
        & datos.df["country"].notna()
    ]
    return {
        "total_paises": int(len(datos.paises)),
        "peliculas_utilizadas": int(base["show_id"].nunique()),
        "registros": registros(datos.paises.head(limite)),
    }
