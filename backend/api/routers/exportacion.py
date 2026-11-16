"""Descarga de los CSV generados por el proyecto."""

from __future__ import annotations

import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from backend.api.deps import obtener_datastore
from backend.core.config import settings
from backend.services.datastore import DataStore
from pipeline.config import RAIZ_PROYECTO

router = APIRouter(tags=["Exportacion"])

NOMBRES = {
    "actores": "actores_pyspark.csv",
    "paises": "duracion_pais.csv",
    "tipos": "titulos_por_tipo.csv",
    "mapreduce": "mapreduce_actores.csv",
    "netflix_clean": "netflix_clean.csv",
}

ARCHIVOS = {
    "notebook": (RAIZ_PROYECTO / "databricks" / "03_analisis_netflix.ipynb", "application/x-ipynb+json"),
    "informe": (RAIZ_PROYECTO / "docs" / "Informe_Netflix_Elsner.pdf", "application/pdf"),
    "presentacion": (RAIZ_PROYECTO / "docs" / "Presentacion_Netflix_Grupo.pdf", "application/pdf"),
}


@router.get("/descargas/{recurso}", summary="Descarga el notebook, el informe o la presentacion")
def descargar(recurso: str) -> FileResponse:
    if recurso not in ARCHIVOS:
        raise HTTPException(
            status_code=404,
            detail=f"Archivo no disponible. Use: {', '.join(ARCHIVOS)}",
        )
    ruta, tipo = ARCHIVOS[recurso]
    if not ruta.exists():
        raise HTTPException(status_code=404, detail=f"El archivo {ruta.name} aun no se ha generado")
    return FileResponse(ruta, media_type=tipo, filename=ruta.name)


@router.get("/export/{recurso}.csv", summary="Descarga un CSV de resultados")
def exportar(recurso: str, datos: DataStore = Depends(obtener_datastore)) -> StreamingResponse:
    if recurso not in settings.recursos_exportables:
        raise HTTPException(
            status_code=404,
            detail=f"Recurso no disponible. Use: {', '.join(settings.recursos_exportables)}",
        )

    tabla = datos.exportar(recurso)
    if tabla is None or tabla.empty:
        raise HTTPException(status_code=404, detail=f"Sin datos para {recurso}")

    buffer = io.StringIO()
    tabla.to_csv(buffer, index=False)
    contenido = buffer.getvalue().encode("utf-8-sig")
    nombre = NOMBRES.get(recurso, f"{recurso}.csv")

    return StreamingResponse(
        iter([contenido]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )
