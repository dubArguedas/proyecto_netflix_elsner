"""Pipeline de datos del proyecto Netflix.

Modulos:
    config      Rutas y constantes compartidas.
    limpieza    Reto 1 - limpieza con Pandas.
    actores     Reto 2/3B - conteo de titulos por actor.
    analisis    Reto 3C/4 - duraciones por pais y comparaciones.
"""

from pipeline.config import (  # noqa: F401
    COLUMNAS_LIMPIAS,
    COLUMNAS_ORIGINALES,
    DIR_DATOS,
    DIR_RESULTADOS,
    RAIZ_PROYECTO,
    RUTA_LIMPIA,
    RUTA_MAPREDUCE,
    RUTA_ORIGINAL,
)
