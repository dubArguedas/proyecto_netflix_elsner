#!/usr/bin/env python
"""Convierte 03_analisis_netflix.py (databricks notebook source) a .ipynb.

El archivo .py sigue el formato de exportacion de Databricks:
    # Databricks notebook source
    # COMMAND ----------
    # MAGIC %md
    # MAGIC texto

Asi el mismo contenido se puede importar en Databricks y, ademas, entregar como
notebook de Jupyter sin mantener dos copias a mano.

Uso:
    python databricks/generar_notebook.py
"""

from __future__ import annotations

import json
from pathlib import Path

DIR = Path(__file__).resolve().parent
ORIGEN = DIR / "03_analisis_netflix.py"
DESTINO = DIR / "03_analisis_netflix.ipynb"

SEPARADOR = "# COMMAND ----------"
PREFIJO_MAGIC = "# MAGIC"
CABECERA = "# Databricks notebook source"


def _quitar_magic(lineas: list[str]) -> list[str]:
    """Elimina el prefijo '# MAGIC ' conservando las lineas vacias."""
    salida: list[str] = []
    for linea in lineas:
        if linea == PREFIJO_MAGIC:
            salida.append("")
        elif linea.startswith(PREFIJO_MAGIC + " "):
            salida.append(linea[len(PREFIJO_MAGIC) + 1 :])
        else:
            salida.append(linea)
    return salida


def _lineas_fuente(texto: str) -> list[str]:
    """Devuelve las lineas en el formato de nbformat (con \\n salvo la ultima)."""
    if not texto:
        return []
    partes = texto.split("\n")
    return [parte + "\n" for parte in partes[:-1]] + ([partes[-1]] if partes[-1] else [])


def convertir(contenido: str) -> dict:
    lineas = contenido.splitlines()
    if lineas and lineas[0].strip() == CABECERA:
        lineas = lineas[1:]

    celdas: list[dict] = []
    actual: list[str] = []

    def cerrar() -> None:
        while actual and not actual[0].strip():
            actual.pop(0)
        while actual and not actual[-1].strip():
            actual.pop()
        if not actual:
            return

        primera = actual[0].strip()
        if primera in {"# MAGIC %md", "# MAGIC %md "}:
            texto = "\n".join(_quitar_magic(actual[1:]))
            celdas.append(
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": _lineas_fuente(texto),
                }
            )
        elif primera.startswith("# MAGIC %"):
            texto = "\n".join(_quitar_magic(actual))
            celdas.append(
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": _lineas_fuente(texto),
                }
            )
        else:
            texto = "\n".join(actual)
            celdas.append(
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": _lineas_fuente(texto),
                }
            )

    for linea in lineas:
        if linea.strip() == SEPARADOR:
            cerrar()
            actual = []
        else:
            actual.append(linea)
    cerrar()

    return {
        "cells": celdas,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.11",
                "mimetype": "text/x-python",
                "file_extension": ".py",
                "pygments_lexer": "ipython3",
                "codemirror_mode": {"name": "ipython", "version": 3},
                "nbconvert_exporter": "python",
            },
            "application": {
                "name": "Observatorio Netflix - Equipo Elsner",
                "version": "1.0",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> int:
    contenido = ORIGEN.read_text(encoding="utf-8")
    notebook = convertir(contenido)
    DESTINO.write_text(
        json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    markdown = sum(1 for c in notebook["cells"] if c["cell_type"] == "markdown")
    codigo = len(notebook["cells"]) - markdown
    print(f"Notebook generado: {DESTINO.name}")
    print(f"  celdas: {len(notebook['cells'])} ({markdown} markdown, {codigo} codigo)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
