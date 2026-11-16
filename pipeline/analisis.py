"""Analisis del Reto 3 y comparaciones SQL / PySpark / MapReduce."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from pipeline.actores import COLUMNAS_SALIDA, contar_actores, separar_paises
from pipeline.config import TIPOS_OFICIALES


def clasificar_tipo(df: pd.DataFrame) -> pd.Series:
    """Normaliza ``type`` en Movie, TV Show, Otro o Sin clasificacion."""
    tipo = df["type"].astype("string").str.strip()
    return pd.Series(
        np.where(
            tipo.isna() | tipo.eq(""),
            "Sin clasificación",
            np.where(tipo.isin(TIPOS_OFICIALES), tipo, "Otro"),
        ),
        index=df.index,
        dtype="object",
    )


def analisis_tipos(df: pd.DataFrame) -> pd.DataFrame:
    """Analisis A: cantidad de titulos distintos por tipo."""
    tipos = clasificar_tipo(df)
    conteo = (
        pd.DataFrame({"tipo": tipos, "show_id": df["show_id"].values})
        .groupby("tipo", as_index=False)
        .agg(cantidad_titulos=("show_id", "nunique"))
    )

    orden = {nombre: posicion for posicion, nombre in enumerate(TIPOS_OFICIALES)}
    conteo["_orden"] = conteo["tipo"].map(orden).fillna(len(orden))
    conteo = conteo.sort_values(["_orden", "tipo"]).drop(columns="_orden")

    total_clasificado = int(
        conteo.loc[conteo["tipo"].isin(TIPOS_OFICIALES), "cantidad_titulos"].sum()
    )
    conteo["porcentaje"] = np.where(
        conteo["tipo"].isin(TIPOS_OFICIALES) & (total_clasificado > 0),
        (conteo["cantidad_titulos"] / total_clasificado * 100).round(2),
        np.nan,
    )
    conteo["cantidad_titulos"] = conteo["cantidad_titulos"].astype(int)
    return conteo.reset_index(drop=True)


def analisis_actores(df: pd.DataFrame) -> pd.DataFrame:
    """Analisis B: cantidad de titulos distintos por actor."""
    return contar_actores(df)


def analisis_paises(df: pd.DataFrame) -> pd.DataFrame:
    """Analisis C: peliculas y duracion promedio por pais."""
    base = df[
        df["type"].eq("Movie")
        & df["duration_min"].notna()
        & (df["duration_min"] > 0)
        & df["country"].notna()
    ][["show_id", "country", "duration_min"]].copy()

    base["pais"] = base["country"].map(separar_paises)
    base = base.explode("pais")
    base = base[base["pais"].notna() & base["pais"].ne("")]
    base = base.drop_duplicates(subset=["pais", "show_id"])
    base["duration_min"] = base["duration_min"].astype(float)

    resultado = (
        base.groupby("pais", as_index=False)
        .agg(
            cantidad_peliculas=("show_id", "nunique"),
            duracion_promedio_min=("duration_min", "mean"),
        )
        .sort_values(["cantidad_peliculas", "pais"], ascending=[False, True])
        .reset_index(drop=True)
    )
    resultado["duracion_promedio_min"] = resultado["duracion_promedio_min"].round(2)
    resultado["cantidad_peliculas"] = resultado["cantidad_peliculas"].astype(int)
    return resultado


def comparar_tablas(
    izquierda: pd.DataFrame,
    derecha: pd.DataFrame,
    clave: str,
    columna_valor: str,
    tolerancia: float = 0.0,
) -> dict[str, Any]:
    """Compara dos salidas por su clave, incluyendo filas de una sola salida."""
    izq = izquierda[[clave, columna_valor]].rename(columns={columna_valor: "valor_izq"})
    der = derecha[[clave, columna_valor]].rename(columns={columna_valor: "valor_der"})

    union = izq.merge(der, on=clave, how="outer", indicator=True)
    union["valor_izq"] = pd.to_numeric(union["valor_izq"], errors="coerce")
    union["valor_der"] = pd.to_numeric(union["valor_der"], errors="coerce")
    union["diferencia"] = union["valor_izq"] - union["valor_der"]

    solo_izq = union["_merge"].eq("left_only")
    solo_der = union["_merge"].eq("right_only")
    ambos = union["_merge"].eq("both")

    diferentes = ambos & (
        union["diferencia"].abs().fillna(np.inf) > tolerancia
    )
    iguales = ambos & ~diferentes

    detalle = union.loc[
        solo_izq | solo_der | diferentes, [clave, "valor_izq", "valor_der", "diferencia", "_merge"]
    ].copy()
    detalle["_merge"] = detalle["_merge"].map(
        {"left_only": "solo_izquierda", "right_only": "solo_derecha", "both": "valores_diferentes"}
    )

    return {
        "clave": clave,
        "filas_izquierda": int(len(izquierda)),
        "filas_derecha": int(len(derecha)),
        "filas_comparadas": int(ambos.sum()),
        "filas_con_valores_diferentes": int(diferentes.sum()),
        "filas_solo_izquierda": int(solo_izq.sum()),
        "filas_solo_derecha": int(solo_der.sum()),
        "filas_en_ambas_iguales": int(iguales.sum()),
        "coinciden_completamente": bool(
            len(detalle) == 0 and len(izquierda) == len(derecha)
        ),
        "detalle_diferencias": detalle.head(50).to_dict(orient="records"),
    }


def comparar_actores(
    mapreduce: pd.DataFrame, spark: pd.DataFrame
) -> dict[str, Any]:
    """Tablas 4 y 5: verifica MapReduce contra el resultado de Spark."""
    mr = mapreduce[COLUMNAS_SALIDA].rename(columns={"cantidad_titulos": "mapreduce"})
    sp = spark[COLUMNAS_SALIDA].rename(columns={"cantidad_titulos": "spark"})

    union = mr.merge(sp, on="actor", how="outer", indicator=True)
    union["diferencia"] = union["mapreduce"] - union["spark"]

    solo_mr = union["_merge"].eq("left_only")
    solo_spark = union["_merge"].eq("right_only")
    ambos = union["_merge"].eq("both")
    iguales = ambos & (union["diferencia"] == 0)
    diferentes = ambos & (union["diferencia"] != 0)

    top10 = (
        sp.sort_values(["spark", "actor"], ascending=[False, True])
        .head(10)
        .merge(mr, on="actor", how="left")
    )
    top10["diferencia"] = top10["mapreduce"] - top10["spark"]

    tabla4 = [
        {
            "posicion": posicion,
            "actor": fila["actor"],
            "mapreduce": _entero(fila["mapreduce"]),
            "spark": _entero(fila["spark"]),
            "diferencia": _entero(fila["diferencia"]),
        }
        for posicion, (_, fila) in enumerate(top10.iterrows(), start=1)
    ]

    tabla5 = {
        "actores_mapreduce": int(len(mr)),
        "actores_spark": int(len(sp)),
        "ambas_iguales": int(iguales.sum()),
        "ambas_diferentes": int(diferentes.sum()),
        "solo_mapreduce": int(solo_mr.sum()),
        "solo_spark": int(solo_spark.sum()),
    }

    return {
        "tabla4": tabla4,
        "tabla5": tabla5,
        "coinciden_completamente": bool(len(union) == len(mr) == len(sp)) and int(diferentes.sum()) == 0,
        "detalle_diferencias": union.loc[
            solo_mr | solo_spark | diferentes, ["actor", "mapreduce", "spark", "diferencia"]
        ]
        .head(50)
        .fillna(0)
        .to_dict(orient="records"),
    }


def _entero(valor: Any) -> int:
    if pd.isna(valor):
        return 0
    return int(valor)
