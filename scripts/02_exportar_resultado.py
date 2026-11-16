#!/usr/bin/env python
"""Reto 2 - Reune las partes del resultado de Hadoop en mapreduce_actores.csv.

Uso (despues de descargar las partes de HDFS con `hdfs dfs -get`):

    python scripts/02_exportar_resultado.py --partes ./partes
    python scripts/02_exportar_resultado.py --partes ./partes \
        --salida datos/resultados/mapreduce_actores.csv

Salida: CSV con cabecera actor,cantidad_titulos ordenado por cantidad
descendente y, en caso de empate, por nombre ascendente.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):  # pragma: no cover
    pass

from pipeline.config import RUTA_MAPREDUCE  # noqa: E402


def leer_partes(directorio: Path) -> pd.DataFrame:
    archivos = sorted(
        archivo
        for archivo in directorio.glob("part-*")
        if archivo.is_file() and not archivo.name.endswith(".crc")
    )
    if not archivos:
        raise FileNotFoundError(
            f"No se encontraron archivos part-* en {directorio}. "
            "Descargue las partes con: hdfs dfs -get /data/netflix/results/actores/part-* ./partes/"
        )

    registros: list[tuple[str, int]] = []
    for archivo in archivos:
        with archivo.open("r", encoding="utf-8", errors="replace") as manejador:
            for numero, linea in enumerate(manejador, start=1):
                linea = linea.rstrip("\n\r")
                if not linea:
                    continue
                actor, separador, cantidad = linea.rpartition("\t")
                if not separador:
                    print(f"  aviso: linea ignorada en {archivo.name}:{numero}")
                    continue
                actor = actor.strip()
                if not actor:
                    continue
                registros.append((actor, int(cantidad)))

    if not registros:
        raise ValueError(f"Las partes de {directorio} no contienen registros validos")

    print(f"Partes leidas: {len(archivos)} -> {', '.join(a.name for a in archivos)}")
    print(f"Lineas leidas: {len(registros)}")
    return pd.DataFrame(registros, columns=["actor", "cantidad_titulos"])


def consolidar(df: pd.DataFrame) -> pd.DataFrame:
    """Suma las cantidades si un actor apareciera en varias partes."""
    consolidado = (
        df.groupby("actor", as_index=False)
        .agg(cantidad_titulos=("cantidad_titulos", "sum"))
        .sort_values(["cantidad_titulos", "actor"], ascending=[False, True])
        .reset_index(drop=True)
    )
    consolidado["cantidad_titulos"] = consolidado["cantidad_titulos"].astype(int)
    return consolidado


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta el resultado de MapReduce")
    parser.add_argument("--partes", type=Path, required=True, help="Carpeta con los part-*")
    parser.add_argument("--salida", type=Path, default=RUTA_MAPREDUCE)
    argumentos = parser.parse_args()

    if not argumentos.partes.is_dir():
        print(f"ERROR: no existe la carpeta {argumentos.partes}")
        return 1

    crudo = leer_partes(argumentos.partes)
    resultado = consolidar(crudo)

    argumentos.salida.parent.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(argumentos.salida, index=False, encoding="utf-8", lineterminator="\n")

    print(f"Actores distintos: {len(resultado)}")
    print(f"Archivo generado : {argumentos.salida}")
    print()
    print("Top 10:")
    print(resultado.head(10).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
