#!/usr/bin/env python
"""Reto 2 - Mapper de Hadoop Streaming: titulos por actor.

Entrada : registros de netflix_clean.csv por la entrada estandar.
Salida  : pares "actor<TAB>show_id".

Reglas:
    * Reconoce y omite la cabecera.
    * Interpreta las filas con el modulo csv (campos con comas entrecomilladas).
    * Separa los actores de cast por comas y elimina espacios sobrantes.
    * Excluye nombres vacios y conserva la escritura original, con tildes.
"""

from __future__ import annotations

import csv
import sys

COLUMNA_ID = "show_id"
COLUMNA_CAST = "cast"


def emitir(actor: str, show_id: str) -> None:
    sys.stdout.write(f"{actor}\t{show_id}\n")


def main() -> int:
    lector = csv.reader(sys.stdin)
    indices: dict[str, int] | None = None

    for fila in lector:
        if not fila:
            continue

        if indices is None:
            cabecera = [columna.strip().lower() for columna in fila]
            if COLUMNA_ID not in cabecera or COLUMNA_CAST not in cabecera:
                sys.stderr.write("ERROR: la cabecera no contiene show_id y cast\n")
                return 1
            indices = {
                COLUMNA_ID: cabecera.index(COLUMNA_ID),
                COLUMNA_CAST: cabecera.index(COLUMNA_CAST),
            }
            continue  # omite la cabecera

        if len(fila) <= max(indices.values()):
            continue

        show_id = fila[indices[COLUMNA_ID]].strip()
        if not show_id:
            continue

        for actor in fila[indices[COLUMNA_CAST]].split(","):
            actor = actor.strip()
            if actor:
                emitir(actor, show_id)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
