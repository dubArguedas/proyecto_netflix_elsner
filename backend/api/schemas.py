"""Modelos de respuesta documentados en /docs (OpenAPI)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Salud(BaseModel):
    estado: str = Field(examples=["ok"])
    version: str
    registros_limpios: int
    actores_mapreduce: int
    mapreduce_disponible: bool
    archivo_limpio: str | None


class TipoItem(BaseModel):
    tipo: str = Field(examples=["Movie"])
    cantidad_titulos: int
    porcentaje: float | None = None


class RespuestaTipos(BaseModel):
    total_titulos: int
    total_clasificado: int
    registros: list[TipoItem]


class ActorItem(BaseModel):
    actor: str
    cantidad_titulos: int


class RespuestaActores(BaseModel):
    total_actores: int
    limite: int
    registros: list[ActorItem]


class PaisItem(BaseModel):
    pais: str
    cantidad_peliculas: int
    duracion_promedio_min: float


class RespuestaPaises(BaseModel):
    total_paises: int
    peliculas_utilizadas: int
    registros: list[PaisItem]


class IndicadorLimpieza(BaseModel):
    indicador: str
    valor: int | None


class ColumnaNulo(BaseModel):
    columna: str
    nulos: int
    porcentaje: float


class ItemCatalogo(BaseModel):
    show_id: str
    type: str | None = None
    title: str | None = None
    director: str | None = None
    country: str | None = None
    release_year: int | None = None
    rating: str | None = None
    duration_min: int | None = None


class RespuestaCatalogo(BaseModel):
    total: int
    pagina: int
    tamano: int
    paginas: int
    registros: list[ItemCatalogo]


class ErrorApi(BaseModel):
    detalle: str
    ayuda: Any | None = None
