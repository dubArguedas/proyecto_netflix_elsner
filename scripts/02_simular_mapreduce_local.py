#!/usr/bin/env python
"""Ensayo local del Reto 2 sin Hadoop (mapper -> sort -> reducer).

Hadoop Streaming ejecuta exactamente: mapper | sort por clave | reducer.
Este script reproduce ese flujo para poder demostrar el algoritmo en una
maquina sin cluster. La evidencia oficial sigue siendo la ejecucion en HDFS.

Uso:
    python scripts/02_simular_mapreduce_local.py
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_PARTES = RAIZ / "datos" / "resultados" / "partes_locales"

sys.path.insert(0, str(RAIZ))

from pipeline.config import RUTA_LIMPIA, RUTA_MAPREDUCE  # noqa: E402


def cargar_exportador():
    """Carga 02_exportar_resultado.py (su nombre no es un identificador valido)."""
    ruta = RAIZ / "scripts" / "02_exportar_resultado.py"
    especificacion = importlib.util.spec_from_file_location("exportador_actores", ruta)
    if especificacion is None or especificacion.loader is None:
        raise ImportError(f"No se pudo cargar {ruta}")
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


def main() -> int:
    if not RUTA_LIMPIA.exists():
        print("ERROR: falta datos/clean/netflix_clean.csv. Ejecute 01_limpiar_netflix.py")
        return 1

    mapper = RAIZ / "scripts" / "02_mapper_actores.py"
    reducer = RAIZ / "scripts" / "02_reducer_actores.py"

    print(f"1/4 Ejecutando mapper sobre {RUTA_LIMPIA.name} ...")
    with RUTA_LIMPIA.open("rb") as entrada:
        salida_mapper = subprocess.run(
            [sys.executable, str(mapper)],
            stdin=entrada,
            capture_output=True,
            check=True,
        ).stdout

    lineas = salida_mapper.decode("utf-8").splitlines()
    print(f"2/4 Ordenando {len(lineas):,} pares por clave ...")
    lineas_ordenadas = sorted(lineas)

    print("3/4 Ejecutando reducer ...")
    entrada_reducer = ("\n".join(lineas_ordenadas) + "\n").encode("utf-8")
    salida_reducer = subprocess.run(
        [sys.executable, str(reducer)],
        input=entrada_reducer,
        capture_output=True,
        check=True,
    )

    DIR_PARTES.mkdir(parents=True, exist_ok=True)
    for viejo in DIR_PARTES.glob("part-*"):
        viejo.unlink()
    parte = DIR_PARTES / "part-00000"
    parte.write_bytes(salida_reducer.stdout)

    print("4/4 Reuniendo las partes en mapreduce_actores.csv ...")
    exportador = cargar_exportador()
    resultado = exportador.consolidar(exportador.leer_partes(DIR_PARTES))
    resultado.to_csv(RUTA_MAPREDUCE, index=False, encoding="utf-8", lineterminator="\n")

    print()
    print(f"Pares generados por el mapper : {len(lineas):,}")
    print(f"Actores distintos (reducer)   : {len(resultado):,}")
    print(f"Archivo final                 : {RUTA_MAPREDUCE}")
    print()
    print(resultado.head(10).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
