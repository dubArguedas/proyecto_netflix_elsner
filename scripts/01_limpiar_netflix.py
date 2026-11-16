#!/usr/bin/env python
"""Reto 1 - Genera netflix_clean.csv a partir de netflix_titles.csv.

Uso:
    python scripts/01_limpiar_netflix.py
    python scripts/01_limpiar_netflix.py --entrada datos/raw/netflix_titles.csv \
                                         --salida  datos/clean/netflix_clean.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

try:  # consola de Windows con acentos
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):  # pragma: no cover
    pass

from pipeline.config import RUTA_LIMPIA, RUTA_ORIGINAL  # noqa: E402
from pipeline.limpieza import ejecutar  # noqa: E402

LINEA = "=" * 62


def imprimir_tabla(metricas: dict) -> None:
    filas = [
        ("Registros del archivo original, sin cabecera", metricas["registros_originales"]),
        ("Columnas del archivo original", metricas["columnas_originales"]),
        ("Filas completamente duplicadas eliminadas", metricas["duplicados_filas"]),
        ("Registros sin show_id eliminados después de retirar duplicados", metricas["sin_show_id"]),
        ("Registros con show_id repetido eliminados posteriormente", metricas["show_id_repetido"]),
        ("Registros del archivo limpio", metricas["registros_limpios"]),
        ("Películas con duration_min numérica mayor que cero", metricas["peliculas_con_duracion"]),
        ("Películas sin una duración numérica mayor que cero", metricas["peliculas_sin_duracion"]),
    ]
    print(LINEA)
    print("TABLA 1. RESULTADO DE LA LIMPIEZA")
    print(LINEA)
    for etiqueta, valor in filas:
        print(f"{etiqueta:<62} {valor:>6}")
    print(LINEA)


def main() -> int:
    parser = argparse.ArgumentParser(description="Limpieza del catalogo de Netflix")
    parser.add_argument("--entrada", type=Path, default=RUTA_ORIGINAL)
    parser.add_argument("--salida", type=Path, default=RUTA_LIMPIA)
    argumentos = parser.parse_args()

    print(f"Archivo de entrada : {argumentos.entrada}")
    print(f"Archivo de salida  : {argumentos.salida}")

    limpio, metricas = ejecutar(argumentos.entrada, argumentos.salida)

    print()
    imprimir_tabla(metricas)
    print()
    print(f"Filas escritas      : {len(limpio)}")
    print(f"Columnas escritas   : {len(limpio.columns)} -> {', '.join(limpio.columns)}")
    print(f"Fechas validas      : {metricas['fechas_validas']} (vacias: {metricas['fechas_vacias']})")
    print(f"Tamano del CSV      : {metricas['archivo_salida_bytes'] / 1024:.1f} KB")
    print()
    print("Limpieza finalizada correctamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
