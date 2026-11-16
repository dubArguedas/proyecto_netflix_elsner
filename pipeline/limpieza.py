"""Reto 1 - Limpieza del catalogo de Netflix con Pandas.

El orden de las operaciones es exactamente el que exige el enunciado:

    1. Eliminar espacios al inicio y al final de los campos de texto.
    2. Sustituir saltos de linea y tabulaciones por espacios.
    3. Convertir textos vacios en valores nulos.
    4. Eliminar filas completamente duplicadas.
    5. Eliminar registros sin show_id.
    6. Si un show_id se repite, conservar la primera aparicion.
    7. Convertir date_added a dd/mm/aaaa (vacio si no se puede interpretar).
    8. Crear duration_min solo para type == "Movie".
    9. Conservar las columnas originales y agregar duration_min al final.
   10. Mantener los datos desconocidos como nulos.
   11. Guardar en UTF-8, con cabecera, separado por comas y sin indice.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from pipeline.config import (
    COLUMNAS_LIMPIAS,
    COLUMNAS_ORIGINALES,
    RUTA_LIMPIA,
    RUTA_METRICAS,
    RUTA_ORIGINAL,
    asegurar_directorios,
)

# El catalogo usa fechas en ingles ("September 25, 2021"). Se traducen de forma
# explicita para que el resultado no dependa del idioma del sistema operativo.
MESES_EN = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12, "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}

PATRON_FECHA_INGLES = r"^\s*([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(\d{4})\s*$"
PATRON_FECHA_ISO = r"^\s*(\d{4})-(\d{1,2})-(\d{1,2})\s*$"
PATRON_FECHA_DMY = r"^\s*(\d{1,2})/(\d{1,2})/(\d{4})\s*$"


def leer_original(ruta: Path | str = RUTA_ORIGINAL) -> pd.DataFrame:
    """Lee netflix_titles.csv forzando todas las columnas de texto a string."""
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontro el archivo original: {ruta}\n"
            "Descarguelo de Kaggle (netflix-shows) y guardelo en datos/raw/."
        )

    df = pd.read_csv(ruta, dtype=str, keep_default_na=False, na_values=[""])
    faltantes = [c for c in COLUMNAS_ORIGINALES if c not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas obligatorias en {ruta.name}: {faltantes}")

    return df[COLUMNAS_ORIGINALES].copy()


def _fecha_valida(anio: int, mes: int, dia: int) -> bool:
    """Valida una fecha sin depender del locale del sistema."""
    try:
        datetime(anio, mes, dia)
    except ValueError:
        return False
    return True


def _limpiar_texto(serie: pd.Series) -> pd.Series:
    """Pasos 1 a 3 del enunciado sobre una columna de texto."""
    limpia = serie.astype("string").str.strip()                       # 1
    limpia = limpia.str.replace(r"[\r\n\t]+", " ", regex=True)        # 2
    limpia = limpia.str.replace(r" {2,}", " ", regex=True)
    limpia = limpia.mask(limpia == "", pd.NA)                         # 3
    return limpia


def _normalizar_fechas(serie: pd.Series) -> pd.Series:
    """Paso 7: dd/mm/aaaa o cadena vacia si la fecha no es interpretable."""

    def convertir(valor: object) -> str:
        if pd.isna(valor):
            return ""
        texto = str(valor).strip()

        coincidencia = re.match(PATRON_FECHA_INGLES, texto)
        if coincidencia:
            mes = MESES_EN.get(coincidencia.group(1).lower())
            dia, anio = int(coincidencia.group(2)), int(coincidencia.group(3))
            if mes and _fecha_valida(anio, mes, dia):
                return f"{dia:02d}/{mes:02d}/{anio:04d}"
            return ""

        coincidencia = re.match(PATRON_FECHA_ISO, texto)
        if coincidencia:
            anio, mes, dia = (int(g) for g in coincidencia.groups())
            if _fecha_valida(anio, mes, dia):
                return f"{dia:02d}/{mes:02d}/{anio:04d}"
            return ""

        coincidencia = re.match(PATRON_FECHA_DMY, texto)
        if coincidencia:
            dia, mes, anio = (int(g) for g in coincidencia.groups())
            if _fecha_valida(anio, mes, dia):
                return f"{dia:02d}/{mes:02d}/{anio:04d}"
            return ""

        return ""

    return serie.map(convertir).astype("string")


def _duracion_en_minutos(df: pd.DataFrame) -> pd.Series:
    """Paso 8: minutos numericos solo para peliculas; nulo en el resto."""
    minutos = pd.to_numeric(
        df["duration"].astype("string").str.extract(r"(\d+)", expand=False),
        errors="coerce",
    )
    es_pelicula = df["type"].astype("string").str.strip().eq("Movie")
    minutos = minutos.where(es_pelicula)
    return minutos.astype("Int64")


def limpiar(df_original: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Aplica la limpieza completa y devuelve (dataframe_limpio, metricas)."""
    filas_originales = len(df_original)
    columnas_originales = len(df_original.columns)

    df = df_original.copy()

    # Pasos 1-3: texto
    for columna in df.columns:
        df[columna] = _limpiar_texto(df[columna])

    # Paso 4: filas completamente duplicadas
    antes = len(df)
    df = df.drop_duplicates(keep="first")
    duplicados_filas = antes - len(df)

    # Paso 5: sin show_id
    antes = len(df)
    df = df[df["show_id"].notna()]
    sin_show_id = antes - len(df)

    # Paso 6: show_id repetido (se conserva la primera aparicion)
    antes = len(df)
    df = df.drop_duplicates(subset="show_id", keep="first")
    show_id_repetido = antes - len(df)

    # Paso 7: fecha dd/mm/aaaa
    df["date_added"] = _normalizar_fechas(df["date_added"])

    # Paso 8: duration_min
    df["duration_min"] = _duracion_en_minutos(df)

    # Paso 9: columnas originales + duration_min al final
    df = df[COLUMNAS_LIMPIAS].reset_index(drop=True)

    # Paso 10: los desconocidos permanecen nulos (no se imputa nada)
    es_pelicula = df["type"].eq("Movie")
    con_duracion = int((es_pelicula & df["duration_min"].notna() & (df["duration_min"] > 0)).sum())
    sin_duracion = int(es_pelicula.sum()) - con_duracion

    metricas: dict[str, Any] = {
        "generado_en": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "archivo_origen": str(RUTA_ORIGINAL.name),
        "archivo_salida": RUTA_LIMPIA.name,
        "registros_originales": filas_originales,
        "columnas_originales": columnas_originales,
        "duplicados_filas": duplicados_filas,
        "sin_show_id": sin_show_id,
        "show_id_repetido": show_id_repetido,
        "registros_limpios": len(df),
        "columnas_limpias": len(df.columns),
        "peliculas_con_duracion": con_duracion,
        "peliculas_sin_duracion": sin_duracion,
        "peliculas": int(es_pelicula.sum()),
        "series": int(df["type"].eq("TV Show").sum()),
        "fechas_validas": int(df["date_added"].ne("").sum()),
        "fechas_vacias": int(df["date_added"].eq("").sum()),
        "nulos_por_columna": {
            columna: int(df[columna].isna().sum()) for columna in df.columns
        },
    }
    return df, metricas


def guardar(df: pd.DataFrame, metricas: dict[str, Any], ruta: Path | str = RUTA_LIMPIA) -> Path:
    """Paso 11: escribe el CSV limpio (UTF-8, cabecera, sin indice)."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta, index=False, encoding="utf-8", lineterminator="\n")

    metricas["archivo_salida_bytes"] = ruta.stat().st_size
    metricas["archivo_salida"] = ruta.name
    RUTA_METRICAS.parent.mkdir(parents=True, exist_ok=True)
    RUTA_METRICAS.write_text(
        json.dumps(metricas, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return ruta


def ejecutar(
    entrada: Path | str = RUTA_ORIGINAL,
    salida: Path | str = RUTA_LIMPIA,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Pipeline completo del Reto 1: leer, limpiar y guardar."""
    asegurar_directorios()
    original = leer_original(entrada)
    limpio, metricas = limpiar(original)
    guardar(limpio, metricas, salida)
    return limpio, metricas


def cargar_limpio(ruta: Path | str = RUTA_LIMPIA) -> pd.DataFrame:
    """Carga netflix_clean.csv respetando los tipos del archivo limpio."""
    ruta = Path(ruta)
    if not ruta.exists():
        limpio, _ = ejecutar()
        return limpio

    df = pd.read_csv(ruta, dtype=str, keep_default_na=False, na_values=[""])
    df["duration_min"] = pd.to_numeric(df["duration_min"], errors="coerce").astype("Int64")
    if "release_year" in df.columns:
        df["release_year"] = pd.to_numeric(df["release_year"], errors="coerce").astype("Int64")
    return df
