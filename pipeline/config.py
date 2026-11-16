"""Rutas y constantes compartidas por scripts, pipeline y backend."""

from __future__ import annotations

from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

DIR_DATOS = RAIZ_PROYECTO / "datos"
DIR_RAW = DIR_DATOS / "raw"
DIR_CLEAN = DIR_DATOS / "clean"
DIR_RESULTADOS = DIR_DATOS / "resultados"

# Entradas y salidas oficiales del trabajo
RUTA_ORIGINAL = DIR_RAW / "netflix_titles.csv"
RUTA_LIMPIA = DIR_CLEAN / "netflix_clean.csv"
RUTA_MAPREDUCE = DIR_RESULTADOS / "mapreduce_actores.csv"

# Resultados derivados que consume el dashboard
RUTA_ACTORES_SPARK = DIR_RESULTADOS / "actores_pyspark.csv"
RUTA_PAISES = DIR_RESULTADOS / "duracion_pais.csv"
RUTA_TIPOS = DIR_RESULTADOS / "titulos_por_tipo.csv"
RUTA_METRICAS = DIR_RESULTADOS / "metricas_limpieza.json"
RUTA_VERIFICACION = DIR_RESULTADOS / "verificacion.json"

COLUMNAS_ORIGINALES = [
    "show_id",
    "type",
    "title",
    "director",
    "cast",
    "country",
    "date_added",
    "release_year",
    "rating",
    "duration",
    "listed_in",
    "description",
]

COLUMNAS_LIMPIAS = COLUMNAS_ORIGINALES + ["duration_min"]

TIPOS_OFICIALES = ("Movie", "TV Show")


def asegurar_directorios() -> None:
    """Crea los directorios de datos si no existen."""
    for directorio in (DIR_RAW, DIR_CLEAN, DIR_RESULTADOS):
        directorio.mkdir(parents=True, exist_ok=True)
