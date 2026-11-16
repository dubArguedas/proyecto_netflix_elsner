"""Punto de entrada del backend FastAPI.

Ejecucion:
    uvicorn backend.main:app --reload --port 8000
    (o simplemente: python run.py)

Documentacion interactiva: http://127.0.0.1:8000/docs
Dashboard:                http://127.0.0.1:8000/
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api import router as api_router
from backend.core.config import settings
from backend.services.datastore import datastore

registro = logging.getLogger("netflix.api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    registro.info("Cargando netflix_clean.csv y calculando analisis ...")
    datastore.cargar()
    registro.info(
        "Listo: %s titulos, %s actores, %s paises",
        len(datastore.df),
        len(datastore.actores),
        len(datastore.paises),
    )
    yield
    registro.info("Servicio detenido")


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=settings.descripcion,
    lifespan=ciclo_de_vida,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/api", include_in_schema=False)
def raiz_api() -> JSONResponse:
    return JSONResponse(
        {
            "servicio": settings.app_name,
            "version": settings.version,
            "documentacion": "/docs",
            "dashboard": "/",
        }
    )


# El frontend se sirve como archivos estaticos; el backend no depende de el.
if settings.dir_frontend.exists():
    app.mount(
        "/",
        StaticFiles(directory=settings.dir_frontend, html=True),
        name="frontend",
    )
