#!/usr/bin/env python
"""Genera el diagrama del proceso y los dos graficos obligatorios del Reto 4.

Salidas (PNG, 200 ppp) en docs/figuras/:
    diagrama_proceso.png
    grafico_tipos.png
    grafico_actores.png

Uso:
    python docs/generar_figuras.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

RAIZ = Path(__file__).resolve().parent.parent
FIGURAS = RAIZ / "docs" / "figuras"

ROJO = "#e50914"
TINTA = "#16203a"
GRIS = "#5a6782"
BORDE = "#d7deec"
AZUL = "#2563eb"


def _caja(ax, x, y, ancho, alto, titulo, detalle, color, relleno=0.10):
    caja = FancyBboxPatch(
        (x, y),
        ancho,
        alto,
        boxstyle="round,pad=0.6,rounding_size=1.4",
        linewidth=1.3,
        edgecolor=color,
        facecolor=color,
        alpha=relleno,
        zorder=1,
    )
    ax.add_patch(caja)
    ax.text(
        x + ancho / 2,
        y + alto * 0.64,
        titulo,
        ha="center",
        va="center",
        fontsize=9.6,
        fontweight="bold",
        color=TINTA,
        zorder=3,
    )
    ax.text(
        x + ancho / 2,
        y + alto * 0.28,
        detalle,
        ha="center",
        va="center",
        fontsize=7.3,
        color=GRIS,
        zorder=3,
    )


def _flecha(ax, origen, destino, etiqueta="", color=GRIS, estilo="-|>", linea="-"):
    flecha = FancyArrowPatch(
        origen,
        destino,
        arrowstyle=estilo,
        mutation_scale=13,
        linewidth=1.5,
        color=color,
        linestyle=linea,
        shrinkA=4,
        shrinkB=4,
        connectionstyle="arc3,rad=0",
        zorder=2,
    )
    ax.add_patch(flecha)
    if etiqueta:
        ax.text(
            (origen[0] + destino[0]) / 2,
            (origen[1] + destino[1]) / 2 + 1.6,
            etiqueta,
            ha="center",
            va="bottom",
            fontsize=6.9,
            color=GRIS,
            style="italic",
            zorder=4,
        )


def diagrama() -> Path:
    fig, ax = plt.subplots(figsize=(12, 6.6))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    ax.text(
        50,
        97,
        "Del archivo original al dashboard: proceso completo del proyecto",
        ha="center",
        va="center",
        fontsize=13,
        fontweight="bold",
        color=TINTA,
    )

    # Fila 1 (izquierda a derecha)
    _caja(ax, 2, 74, 22, 15, "1 · Archivo original", "netflix_titles.csv · 8 807 × 12", TINTA)
    _caja(ax, 30, 74, 26, 15, "2 · Limpieza con Pandas", "11 pasos · duration_min", ROJO)
    _caja(ax, 62, 74, 26, 15, "3 · Archivo limpio", "netflix_clean.csv · 8 807 × 13", "#0f9d8f")

    # Fila 2 (derecha a izquierda)
    _caja(ax, 80, 45, 18, 15, "4 · HDFS", "/data/netflix/clean/", AZUL)
    _caja(ax, 46, 45, 28, 15, "5 · Hadoop Streaming", "mapper + reducer (Python)", AZUL)
    _caja(ax, 12, 45, 28, 15, "6 · Resultado por actor", "mapreduce_actores.csv", AZUL)

    # Fila 3 (izquierda a derecha)
    _caja(ax, 10, 12, 26, 15, "7 · Databricks", "carga directa del CSV limpio", "#7c3aed")
    _caja(ax, 42, 12, 26, 15, "8 · SQL y PySpark", "análisis A, B y C + tablas 3-5", "#7c3aed")
    _caja(ax, 74, 12, 24, 15, "9 · Hallazgos", "gráficos, tabla 6 y conclusiones", ROJO)

    _flecha(ax, (24, 81.5), (29.5, 81.5), "lectura")
    _flecha(ax, (56, 81.5), (61.5, 81.5), "escritura UTF-8")
    _flecha(ax, (84, 74), (89, 60.5), "netflix_clean.csv")
    _flecha(ax, (79.5, 52.5), (74.5, 52.5), "put")
    _flecha(ax, (45.5, 52.5), (40.5, 52.5), "part-*")
    _flecha(ax, (26, 45), (24, 27.5), "mapreduce_actores.csv")
    _flecha(ax, (36.5, 19.5), (41.5, 19.5))
    _flecha(ax, (68.5, 19.5), (73.5, 19.5))

    # Carga directa del mismo archivo limpio en Databricks (ruta punteada por el margen)
    ax.plot(
        [62, 1.4, 1.4, 9.4],
        [71.6, 71.6, 19.5, 19.5],
        color="#7c3aed",
        linewidth=1.4,
        linestyle=(0, (4, 3)),
        zorder=2,
    )
    ax.annotate(
        "",
        xy=(9.6, 19.5),
        xytext=(8.8, 19.5),
        arrowprops=dict(arrowstyle="-|>", color="#7c3aed", lw=1.4, mutation_scale=13),
        zorder=3,
    )
    ax.text(
        2.6,
        45,
        "carga directa del mismo archivo limpio",
        rotation=90,
        ha="center",
        va="center",
        fontsize=6.7,
        color="#7c3aed",
        style="italic",
    )

    fig.savefig(FIGURAS / "diagrama_proceso.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return FIGURAS / "diagrama_proceso.png"


def _formato(valor: float) -> str:
    return f"{valor:,.0f}".replace(",", " ")


def graficoTipos() -> Path:
    datos = pd.read_csv(RAIZ / "datos" / "resultados" / "titulos_por_tipo.csv")
    datos = datos[datos["tipo"].isin(["Movie", "TV Show"])].sort_values("cantidad_titulos", ascending=False)
    total = datos["cantidad_titulos"].sum()

    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    colores = [ROJO if tipo == "Movie" else TINTA for tipo in datos["tipo"]]
    barras = ax.bar(datos["tipo"], datos["cantidad_titulos"], color=colores, width=0.52)

    for barra, cantidad in zip(barras, datos["cantidad_titulos"]):
        porcentaje = cantidad / total * 100
        ax.text(
            barra.get_x() + barra.get_width() / 2,
            cantidad + 110,
            f"{_formato(cantidad)}\n{porcentaje:.2f} %",
            ha="center",
            va="bottom",
            fontsize=9.5,
            fontweight="bold",
            color=TINTA,
        )

    ax.set_title("Cantidad de títulos por tipo", fontsize=12.5, fontweight="bold", color=TINTA, pad=12)
    ax.set_xlabel("Tipo de contenido", fontsize=9.5, color=GRIS)
    ax.set_ylabel("Cantidad de títulos", fontsize=9.5, color=GRIS)
    ax.set_ylim(0, max(datos["cantidad_titulos"]) * 1.22)
    ax.tick_params(colors=GRIS, labelsize=9.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(BORDE)
    ax.grid(axis="y", color=BORDE, linewidth=0.7)
    ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(FIGURAS / "grafico_tipos.png", dpi=200, facecolor="white")
    plt.close(fig)
    return FIGURAS / "grafico_tipos.png"


def graficoActores() -> Path:
    datos = pd.read_csv(RAIZ / "datos" / "resultados" / "actores_pyspark.csv")
    top = (
        datos.sort_values(["cantidad_titulos", "actor"], ascending=[False, True])
        .head(10)
        .iloc[::-1]
    )

    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    colores = [ROJO if actor == top["actor"].iloc[-1] else "#f08089" for actor in top["actor"]]
    barras = ax.barh(top["actor"], top["cantidad_titulos"], color=colores, height=0.62)

    for barra, cantidad in zip(barras, top["cantidad_titulos"]):
        ax.text(
            cantidad + 0.55,
            barra.get_y() + barra.get_height() / 2,
            f"{cantidad}",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=TINTA,
        )

    ax.set_title(
        "Diez actores con más títulos distintos", fontsize=12.5, fontweight="bold", color=TINTA, pad=12
    )
    ax.set_xlabel("Cantidad de títulos distintos", fontsize=9.5, color=GRIS)
    ax.set_ylabel("Actor", fontsize=9.5, color=GRIS)
    ax.set_xlim(0, max(top["cantidad_titulos"]) * 1.12)
    ax.tick_params(colors=GRIS, labelsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(BORDE)
    ax.grid(axis="x", color=BORDE, linewidth=0.7)
    ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(FIGURAS / "grafico_actores.png", dpi=200, facecolor="white")
    plt.close(fig)
    return FIGURAS / "grafico_actores.png"


def main() -> int:
    FIGURAS.mkdir(parents=True, exist_ok=True)
    for ruta in (diagrama(), graficoTipos(), graficoActores()):
        print(f"  generado {ruta.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
