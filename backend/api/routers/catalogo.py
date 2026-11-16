"""Explorador del catalogo limpio con busqueda y paginacion."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from backend.api.deps import obtener_datastore
from backend.api.schemas import RespuestaCatalogo
from backend.services.datastore import DataStore

router = APIRouter(tags=["Catalogo"])


@router.get("/catalogo", response_model=RespuestaCatalogo, summary="Buscar titulos del catalogo")
def catalogo(
    q: str | None = Query(None, max_length=120, description="Busca en titulo, elenco, director y pais"),
    tipo: str | None = Query(None, description="Movie, TV Show u Otro"),
    pagina: int = Query(1, ge=1),
    tamano: int = Query(25, ge=1, le=100),
    datos: DataStore = Depends(obtener_datastore),
) -> dict:
    return datos.catalogo(consulta=q, tipo=tipo, pagina=pagina, tamano=tamano)
