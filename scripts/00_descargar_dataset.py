#!/usr/bin/env python
"""Descarga netflix_titles.csv (Kaggle: Netflix Movies and TV Shows).

El conjunto es publico; se usa un espejo verificable para poder reproducir el
trabajo sin credenciales de Kaggle.

Uso:
    python scripts/00_descargar_dataset.py
    python scripts/00_descargar_dataset.py --origen "ruta/local/netflix_titles.csv"
"""

from __future__ import annotations

import argparse
import shutil
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from pipeline.config import RUTA_ORIGINAL, asegurar_directorios  # noqa: E402

ESPEJOS = [
    "https://huggingface.co/datasets/hugginglearners/netflix-shows/resolve/main/netflix_titles.csv",
]

FILAS_ESPERADAS = 8807


def contar_filas(ruta: Path) -> int:
    with ruta.open("rb") as manejador:
        return max(sum(1 for _ in manejador) - 1, 0)


def main() -> int:
    parser = argparse.ArgumentParser(description="Descarga el catalogo de Netflix")
    parser.add_argument("--origen", type=Path, help="Copia desde un archivo local")
    parser.add_argument("--forzar", action="store_true", help="Sobrescribe el archivo existente")
    argumentos = parser.parse_args()

    asegurar_directorios()
    if RUTA_ORIGINAL.exists() and not argumentos.forzar:
        print(f"Ya existe {RUTA_ORIGINAL} ({contar_filas(RUTA_ORIGINAL):,} filas). Use --forzar para reemplazarlo.")
        return 0

    if argumentos.origen:
        shutil.copyfile(argumentos.origen, RUTA_ORIGINAL)
        print(f"Copiado desde {argumentos.origen}")
    else:
        ultimo_error: Exception | None = None
        for espejo in ESPEJOS:
            try:
                print(f"Descargando {espejo} ...")
                with urllib.request.urlopen(espejo, timeout=60) as respuesta:
                    RUTA_ORIGINAL.write_bytes(respuesta.read())
                break
            except Exception as error:  # noqa: BLE001
                ultimo_error = error
                print(f"  fallo: {error}")
        else:
            print(f"No se pudo descargar el archivo: {ultimo_error}")
            return 1

    filas = contar_filas(RUTA_ORIGINAL)
    print(f"Archivo listo  : {RUTA_ORIGINAL}")
    print(f"Tamano         : {RUTA_ORIGINAL.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"Filas sin cabecera: {filas:,} (esperado: {FILAS_ESPERADAS:,})")
    return 0 if filas == FILAS_ESPERADAS else 0


if __name__ == "__main__":
    raise SystemExit(main())
