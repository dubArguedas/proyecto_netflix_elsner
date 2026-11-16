#!/usr/bin/env python
"""Reto 2 - Reducer de Hadoop Streaming: cuenta titulos distintos por actor.

Entrada : pares "actor<TAB>show_id" agrupados por actor (Hadoop ordena por clave).
Salida  : "actor<TAB>cantidad_titulos".

Un mismo show_id se cuenta una sola vez por actor.
"""

from __future__ import annotations

import sys


def emitir(actor: str, cantidad: int) -> None:
    sys.stdout.write(f"{actor}\t{cantidad}\n")


def main() -> int:
    actor_actual: str | None = None
    titulos: set[str] = set()

    for linea in sys.stdin:
        linea = linea.rstrip("\n\r")
        if not linea:
            continue

        actor, separador, show_id = linea.rpartition("\t")
        if not separador:  # linea sin tabulador: se ignora
            continue
        show_id = show_id.strip()
        if not show_id:
            continue

        if actor != actor_actual:
            if actor_actual is not None:
                emitir(actor_actual, len(titulos))
            actor_actual = actor
            titulos = set()

        titulos.add(show_id)

    if actor_actual is not None:
        emitir(actor_actual, len(titulos))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
