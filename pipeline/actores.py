"""Reglas de conteo de titulos por actor (Retos 2 y 3B).

Reglas del enunciado que se aplican en los tres entornos:
    * Separar los actores de ``cast`` por comas y quitar espacios sobrantes.
    * Excluir nombres vacios.
    * Conservar la escritura original de los nombres, incluidas tildes.
    * Contar un mismo show_id una sola vez por actor.
"""

from __future__ import annotations

import pandas as pd

COLUMNAS_SALIDA = ["actor", "cantidad_titulos"]


def separar_actores(valor: object) -> list[str]:
    """Devuelve la lista de actores de un campo ``cast`` ya limpio."""
    if pd.isna(valor):
        return []
    return [nombre.strip() for nombre in str(valor).split(",") if nombre.strip()]


def separar_paises(valor: object) -> list[str]:
    """Devuelve la lista de paises de un campo ``country`` ya limpio."""
    if pd.isna(valor):
        return []
    return [nombre.strip() for nombre in str(valor).split(",") if nombre.strip()]


def contar_actores(df: pd.DataFrame) -> pd.DataFrame:
    """Cuenta titulos distintos por actor y ordena por cantidad y nombre."""
    base = df[["show_id", "cast"]].copy()
    base["actor"] = base["cast"].map(separar_actores)
    base = base.explode("actor")
    base = base[base["actor"].notna() & base["actor"].ne("")]
    base = base.drop_duplicates(subset=["actor", "show_id"])

    resultado = (
        base.groupby("actor", as_index=False)
        .agg(cantidad_titulos=("show_id", "nunique"))
        .sort_values(["cantidad_titulos", "actor"], ascending=[False, True])
        .reset_index(drop=True)
    )
    resultado["cantidad_titulos"] = resultado["cantidad_titulos"].astype(int)
    return resultado[COLUMNAS_SALIDA]


def actores_desde_mapreduce(ruta) -> pd.DataFrame:
    """Lee mapreduce_actores.csv generado por Hadoop."""
    df = pd.read_csv(ruta, dtype={"actor": str, "cantidad_titulos": int})
    return df.sort_values(
        ["cantidad_titulos", "actor"], ascending=[False, True]
    ).reset_index(drop=True)
