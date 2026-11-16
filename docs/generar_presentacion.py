#!/usr/bin/env python
"""Genera la presentacion del proyecto en PDF (16:9), a partir de los resultados reales.

Salida:
    docs/Presentacion_Netflix_Grupo.pdf

Uso:
    python docs/generar_presentacion.py
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
FIGURAS = DOCS / "figuras"
SALIDA = DOCS / "Presentacion_Netflix_Grupo.pdf"

ANCHO = 338.667 * mm
ALTO = 190.5 * mm

TINTA = colors.HexColor("#16203a")
TINTA_CLARA = colors.HexColor("#243154")
ROJO = colors.HexColor("#e50914")
GRIS = colors.HexColor("#5a6782")
GRIS_CLARO = colors.HexColor("#8f9bb3")
BORDE = colors.HexColor("#dfe5f0")
FONDO = colors.HexColor("#f6f8fc")
BLANCO = colors.white
VERDE = colors.HexColor("#0f9d8f")

MARGEN = 20 * mm
ANCHO_UTIL = ANCHO - 2 * MARGEN

NORMAL = "Helvetica"
NEGRITA = "Helvetica-Bold"
ITALICA = "Helvetica-Oblique"


# --------------------------------------------------------------------------
# Utilidades de dibujo
# --------------------------------------------------------------------------
def _palabras_ricas(texto: str) -> list[tuple[str, bool]]:
    """Divide el texto en palabras marcando las que van entre **...** como negrita."""
    piezas = texto.split("**")
    salida: list[tuple[str, bool]] = []
    for indice, pieza in enumerate(piezas):
        negrita = indice % 2 == 1
        for palabra in pieza.split():
            salida.append((palabra, negrita))
    return salida


def _cortar_lineas(
    palabras: list[tuple[str, bool]], tam: float, ancho: float, fuente: str, fuente_negrita: str
) -> list[list[tuple[str, bool, float]]]:
    lineas: list[list[tuple[str, bool, float]]] = []
    actual: list[tuple[str, bool, float]] = []
    usado = 0.0
    espacio = stringWidth(" ", fuente, tam)
    for palabra, negrita in palabras:
        fuente_palabra = fuente_negrita if negrita else fuente
        w = stringWidth(palabra, fuente_palabra, tam)
        extra = w if not actual else w + espacio
        if usado + extra > ancho and actual:
            lineas.append(actual)
            actual = [(palabra, negrita, w)]
            usado = w
        else:
            actual.append((palabra, negrita, w))
            usado += extra
    if actual:
        lineas.append(actual)
    return lineas


def parrafo(
    c: canvas.Canvas,
    x: float,
    y: float,
    ancho: float,
    texto: str,
    tam: float = 13,
    color=TINTA,
    alto_linea: float | None = None,
    fuente: str = NORMAL,
    fuente_negrita: str = NEGRITA,
) -> float:
    alto_linea = alto_linea or tam * 1.42
    lineas = _cortar_lineas(_palabras_ricas(texto), tam, ancho, fuente, fuente_negrita)
    c.setFillColor(color)
    for linea in lineas:
        cursor = x
        for palabra, negrita, w in linea:
            c.setFont(fuente_negrita if negrita else fuente, tam)
            c.drawString(cursor, y, palabra)
            cursor += w + stringWidth(" ", fuente, tam)
        y -= alto_linea
    return y


def vineta(c: canvas.Canvas, x: float, y: float, ancho: float, texto: str, tam: float = 13, color=TINTA) -> float:
    c.setFillColor(ROJO)
    c.rect(x, y + tam * 0.28, 2.1 * mm, 2.1 * mm, stroke=0, fill=1)
    return parrafo(c, x + 6 * mm, y, ancho - 6 * mm, texto, tam, color)


def etiqueta(c: canvas.Canvas, x: float, y: float, texto: str, color=GRIS_CLARO, tam: float = 8.5) -> None:
    c.setFillColor(color)
    c.setFont(NEGRITA, tam)
    c.drawString(x, y, texto.upper())


def tarjeta(
    c: canvas.Canvas,
    x: float,
    y: float,
    ancho: float,
    alto: float,
    valor: str,
    titulo: str,
    detalle: str = "",
    color_valor=ROJO,
) -> None:
    c.setFillColor(BLANCO)
    c.setStrokeColor(BORDE)
    c.setLineWidth(0.8)
    c.roundRect(x, y, ancho, alto, 2.5 * mm, stroke=1, fill=1)
    c.setFillColor(color_valor)
    c.setFont(NEGRITA, 27)
    c.drawString(x + 7 * mm, y + alto - 13 * mm, valor)
    c.setFillColor(TINTA)
    c.setFont(NEGRITA, 10)
    c.drawString(x + 7 * mm, y + alto - 19.5 * mm, titulo)
    if detalle:
        c.setFillColor(GRIS)
        c.setFont(NORMAL, 8.6)
        c.drawString(x + 7 * mm, y + 6 * mm, detalle)


def tabla(
    c: canvas.Canvas,
    x: float,
    y: float,
    anchos: list[float],
    cabecera: list[str],
    filas: list[list[str]],
    alto_fila: float = 8.2 * mm,
    tam: float = 9.6,
    alinear_derecha: tuple[int, ...] = (),
) -> float:
    anchos_mm = [a * mm for a in anchos]
    ancho_total = sum(anchos_mm)
    # cabecera
    c.setFillColor(TINTA)
    c.rect(x, y - alto_fila, ancho_total, alto_fila, stroke=0, fill=1)
    c.setFillColor(BLANCO)
    c.setFont(NEGRITA, tam - 0.4)
    cursor = x
    for indice, texto in enumerate(cabecera):
        if indice in alinear_derecha:
            c.drawRightString(cursor + anchos_mm[indice] - 3 * mm, y - alto_fila + 2.7 * mm, texto)
        else:
            c.drawString(cursor + 3 * mm, y - alto_fila + 2.7 * mm, texto)
        cursor += anchos_mm[indice]
    y -= alto_fila
    for numero, fila in enumerate(filas):
        c.setFillColor(FONDO if numero % 2 else BLANCO)
        c.rect(x, y - alto_fila, ancho_total, alto_fila, stroke=0, fill=1)
        c.setStrokeColor(BORDE)
        c.setLineWidth(0.4)
        c.line(x, y - alto_fila, x + ancho_total, y - alto_fila)
        cursor = x
        for indice, valor in enumerate(fila):
            c.setFillColor(TINTA)
            c.setFont(NEGRITA if indice == 0 else NORMAL, tam)
            if indice in alinear_derecha:
                c.drawRightString(cursor + anchos_mm[indice] - 3 * mm, y - alto_fila + 2.6 * mm, valor)
            else:
                c.drawString(cursor + 3 * mm, y - alto_fila + 2.6 * mm, valor)
            cursor += anchos_mm[indice]
        y -= alto_fila
    return y


def imagen_ajustada(
    c: canvas.Canvas,
    ruta: Path,
    x: float,
    y: float,
    ancho_max: float,
    alto_max: float,
    centrar_en: float | None = None,
) -> None:
    from PIL import Image as PILImage

    with PILImage.open(ruta) as im:
        ancho_px, alto_px = im.size
    escala = min(ancho_max / ancho_px, alto_max / alto_px)
    ancho = ancho_px * escala
    alto = alto_px * escala
    if centrar_en is not None:
        x = centrar_en - ancho / 2
    c.drawImage(str(ruta), x, y, width=ancho, height=alto, mask="auto")


# --------------------------------------------------------------------------
# Estructura de las diapositivas
# --------------------------------------------------------------------------
def fondo_claro(c: canvas.Canvas) -> None:
    c.setFillColor(colors.HexColor("#ffffff"))
    c.rect(0, 0, ANCHO, ALTO, stroke=0, fill=1)


def cabecera(c: canvas.Canvas, seccion: str, titulo: str, subtitulo: str = "") -> float:
    etiqueta(c, MARGEN, ALTO - 16 * mm, seccion, ROJO, 8.5)
    c.setFillColor(TINTA)
    c.setFont(NEGRITA, 24)
    c.drawString(MARGEN, ALTO - 28 * mm, titulo)
    c.setFillColor(ROJO)
    c.rect(MARGEN, ALTO - 33 * mm, 34 * mm, 1.5 * mm, stroke=0, fill=1)
    if subtitulo:
        c.setFillColor(GRIS)
        c.setFont(NORMAL, 11.5)
        c.drawString(MARGEN, ALTO - 41 * mm, subtitulo)
        return ALTO - 50 * mm
    return ALTO - 44 * mm


def pie(c: canvas.Canvas, numero: int) -> None:
    c.setStrokeColor(BORDE)
    c.setLineWidth(0.6)
    c.line(MARGEN, 14 * mm, ANCHO - MARGEN, 14 * mm)
    c.setFillColor(GRIS_CLARO)
    c.setFont(NORMAL, 8)
    c.drawString(MARGEN, 9 * mm, "Análisis del catálogo de Netflix · Equipo Elsner · Tecnologías Emergentes I")
    c.setFont(NEGRITA, 8)
    c.drawRightString(ANCHO - MARGEN, 9 * mm, f"{numero:02d}")


def portada(c: canvas.Canvas) -> None:
    c.setFillColor(TINTA)
    c.rect(0, 0, ANCHO, ALTO, stroke=0, fill=1)
    c.setFillColor(TINTA_CLARA)
    c.circle(ANCHO - 20 * mm, ALTO - 10 * mm, 55 * mm, stroke=0, fill=1)
    c.setFillColor(ROJO)
    c.rect(0, ALTO - 7 * mm, ANCHO, 7 * mm, stroke=0, fill=1)

    etiqueta(c, MARGEN, ALTO - 26 * mm, "Netflix · Observatorio de datos", colors.HexColor("#ff6b73"), 9)

    c.setFillColor(BLANCO)
    c.setFont(NEGRITA, 44)
    c.drawString(MARGEN, ALTO - 62 * mm, "Análisis del catálogo")
    c.drawString(MARGEN, ALTO - 77 * mm, "de Netflix")
    c.setFillColor(ROJO)
    c.rect(MARGEN, ALTO - 86 * mm, 60 * mm, 1.8 * mm, stroke=0, fill=1)

    c.setFillColor(colors.HexColor("#c8d2e4"))
    c.setFont(NORMAL, 16)
    c.drawString(MARGEN, ALTO - 98 * mm, "Limpieza con Pandas · conteo con Hadoop MapReduce")
    c.drawString(MARGEN, ALTO - 107 * mm, "y verificación con Spark en Databricks")

    c.setFillColor(colors.HexColor("#93a3c0"))
    c.setFont(NORMAL, 11.5)
    c.drawString(MARGEN, 44 * mm, "Tecnologías Emergentes I · Evaluación Segundo Momento · 2026")
    c.setFillColor(BLANCO)
    c.setFont(NEGRITA, 13)
    c.drawString(MARGEN, 34 * mm, "Equipo Elsner")
    c.setFillColor(colors.HexColor("#93a3c0"))
    c.setFont(NORMAL, 11)
    c.drawString(MARGEN, 26 * mm, "Jhael Arguedas · Carlos Conde · Bryan Mamani")
    c.drawRightString(ANCHO - MARGEN, 26 * mm, "16 de noviembre de 2026")
    c.setFillColor(ROJO)
    c.rect(0, 0, ANCHO, 4 * mm, stroke=0, fill=1)


def diapositiva_objetivo(c: canvas.Canvas, n: int) -> None:
    fondo_claro(c)
    y = cabecera(c, "01 · Punto de partida", "Un catálogo, tres preguntas", "Netflix Movies and TV Shows · Kaggle · 8 807 títulos · 12 columnas")
    preguntas = [
        "¿Cuántas **películas** y **series** contiene el catálogo y qué peso tiene cada tipo?",
        "¿Qué **actor** participa en más títulos distintos?",
        "¿Cómo varía la **duración promedio** de las películas según el país?",
    ]
    y_inicio = y - 2 * mm
    for i, pregunta in enumerate(preguntas):
        c.setFillColor(FONDO)
        c.setStrokeColor(BORDE)
        c.setLineWidth(0.7)
        c.roundRect(MARGEN, y_inicio - 24 * mm, ANCHO_UTIL, 21 * mm, 2.5 * mm, stroke=1, fill=1)
        c.setFillColor(ROJO)
        c.setFont(NEGRITA, 22)
        c.drawString(MARGEN + 7 * mm, y_inicio - 15 * mm, f"{i + 1:02d}")
        parrafo(c, MARGEN + 24 * mm, y_inicio - 10 * mm, ANCHO_UTIL - 32 * mm, pregunta, 13.5, TINTA)
        y_inicio -= 27 * mm

    y_inicio -= 3 * mm
    c.setFillColor(TINTA)
    c.setFont(NEGRITA, 11)
    c.drawString(MARGEN, y_inicio - 4 * mm, "Además, el trabajo comprueba que Pandas, Hadoop y Spark producen los mismos números.")
    c.setFillColor(GRIS)
    c.setFont(NORMAL, 10)
    c.drawString(MARGEN, y_inicio - 10 * mm, "Tres caminos de cálculo independientes sobre el mismo archivo limpio: la coincidencia es la evidencia.")
    pie(c, n)


def diapositiva_proceso(c: canvas.Canvas, n: int) -> None:
    fondo_claro(c)
    y = cabecera(c, "02 · Arquitectura", "Del archivo original al dashboard", "Cada flecha es un archivo que se transfiere entre etapas")
    alto_disponible = y - 18 * mm
    imagen_ajustada(c, FIGURAS / "diagrama_proceso.png", MARGEN, 16 * mm, ANCHO_UTIL, alto_disponible, centrar_en=ANCHO / 2)
    c.setFillColor(GRIS)
    c.setFont(ITALICA, 9)
    c.drawCentredString(ANCHO / 2, 10 * mm + 2 * mm, "Figura 1 · Proceso completo: Pandas → HDFS/MapReduce → Databricks → dashboard")
    pie(c, n)


def diapositiva_limpieza(c: canvas.Canvas, n: int) -> None:
    fondo_claro(c)
    y = cabecera(c, "03 · Reto 1", "Limpieza con Pandas", "Once reglas ordenadas sobre las 12 columnas originales")

    izquierda = MARGEN
    ancho_texto = 175 * mm
    yy = y
    yy = parrafo(
        c,
        izquierda,
        yy,
        ancho_texto,
        "El orden importa: primero se normaliza el texto y después se eliminan duplicados, "
        "de modo que dos filas que solo difieren en espacios se detectan como iguales.",
        12.5,
    )
    yy -= 3 * mm
    for texto in [
        "Recorte de espacios, saltos de línea y tabulaciones; textos vacíos a nulos.",
        "Duplicados exactos, `show_id` vacío y `show_id` repetido: se conserva la primera aparición.",
        "`date_added` a dd/mm/aaaa y nueva columna `duration_min` solo para películas.",
        "Doce columnas originales + una; datos desconocidos se mantienen nulos, sin imputar.",
    ]:
        yy = vineta(c, izquierda, yy, ancho_texto, texto, 11.5)
        yy -= 2.5 * mm

    x_tarjetas = MARGEN + 188 * mm
    ancho_tarjeta = (ANCHO - MARGEN - x_tarjetas - 6 * mm) / 2
    tarjeta(c, x_tarjetas, y - 23 * mm, ancho_tarjeta, 27 * mm, "8 807", "filas conservadas", "100 % del original", ROJO)
    tarjeta(c, x_tarjetas + ancho_tarjeta + 6 * mm, y - 23 * mm, ancho_tarjeta, 27 * mm, "0", "duplicados", "ni show_id repetidos", VERDE)
    tarjeta(c, x_tarjetas, y - 54 * mm, ancho_tarjeta, 27 * mm, "6 128", "películas con duración", "de 6 131 (3 nulos)", ROJO)
    tarjeta(c, x_tarjetas + ancho_tarjeta + 6 * mm, y - 54 * mm, ancho_tarjeta, 27 * mm, "+1", "columna nueva", "duration_min", TINTA)

    yy -= 2 * mm
    yy = parrafo(
        c,
        x_tarjetas,
        yy - 8 * mm,
        ANCHO - MARGEN - x_tarjetas,
        "Tabla 1 del informe: 8 807 registros de entrada, 8 807 de salida, 12 columnas originales.",
        9.5,
        GRIS,
        alto_linea=4.6 * mm,
    )
    pie(c, n)


def diapositiva_mapreduce(c: canvas.Canvas, n: int) -> None:
    fondo_claro(c)
    y = cabecera(c, "04 · Reto 2", "Conteo de actores con Hadoop", "Hadoop Streaming 3.3.6 · un mapper y un reducer en Python estándar")

    # flujo
    cajas = [
        ("netflix_clean.csv", "8 807 títulos", TINTA),
        ("MAPPER", "actor ⇥ show_id", ROJO),
        ("SHUFFLE", "agrupa por actor", TINTA_CLARA),
        ("REDUCER", "conjunto de show_id", ROJO),
        ("mapreduce_actores.csv", "36 439 actores", TINTA),
    ]
    ancho_caja = 48 * mm
    separacion = (ANCHO_UTIL - len(cajas) * ancho_caja) / (len(cajas) - 1)
    x = MARGEN
    y_caja = y - 22 * mm
    for indice, (titulo, detalle, color) in enumerate(cajas):
        c.setFillColor(BLANCO)
        c.setStrokeColor(color)
        c.setLineWidth(1.2)
        c.roundRect(x, y_caja, ancho_caja, 17 * mm, 2 * mm, stroke=1, fill=1)
        c.setFillColor(color)
        c.setFont(NEGRITA, 8.6)
        c.drawCentredString(x + ancho_caja / 2, y_caja + 11.4 * mm, titulo)
        c.setFillColor(GRIS)
        c.setFont(NORMAL, 7.8)
        c.drawCentredString(x + ancho_caja / 2, y_caja + 6.2 * mm, detalle)
        if indice < len(cajas) - 1:
            c.setStrokeColor(GRIS_CLARO)
            c.setLineWidth(0.9)
            x_flecha = x + ancho_caja
            c.line(x_flecha + 1.5 * mm, y_caja + 8.5 * mm, x_flecha + separacion - 1.5 * mm, y_caja + 8.5 * mm)
            c.setFillColor(GRIS_CLARO)
            c.circle(x_flecha + separacion - 1 * mm, y_caja + 8.5 * mm, 0.8 * mm, stroke=0, fill=1)
        x += ancho_caja + separacion

    yy = y_caja - 12 * mm
    yy = parrafo(
        c,
        MARGEN,
        yy,
        ANCHO_UTIL,
        "El mapper emitió **64 126 pares** actor–show_id. El reducer acumuló los identificadores en un "
        "conjunto, de modo que un título se cuenta una sola vez por actor, y emitió **36 439 actores**.",
        12.5,
    )
    yy -= 6 * mm
    yy = parrafo(
        c,
        MARGEN,
        yy,
        ANCHO_UTIL,
        "La salida queda ordenada por actor (un solo reducer), lo que permite compararla directamente con Spark. "
        "Los nombres conservan tildes y mayúsculas: no se normalizan para no unir personas distintas.",
        10.5,
        GRIS,
        alto_linea=5 * mm,
    )
    pie(c, n)


def diapositiva_tabla2(c: canvas.Canvas, n: int) -> None:
    fondo_claro(c)
    y = cabecera(c, "05 · Reto 2", "Los diez actores con más títulos", "Tabla 2 del informe · orden: cantidad descendente y nombre ascendente")
    filas = [
        ["1", "Anupam Kher", "43"],
        ["2", "Shah Rukh Khan", "35"],
        ["3", "Julie Tejwani", "33"],
        ["4", "Naseeruddin Shah", "32"],
        ["5", "Takahiro Sakurai", "32"],
        ["6", "Rupa Bhimani", "31"],
        ["7", "Akshay Kumar", "30"],
        ["8", "Om Puri", "30"],
        ["9", "Yuki Kaji", "29"],
        ["10", "Amitabh Bachchan", "28"],
    ]
    y_tabla = y + 2 * mm
    tabla(
        c,
        MARGEN,
        y_tabla,
        [12, 100, 45],
        ["#", "Actor", "Títulos distintos"],
        filas,
        alto_fila=9.6 * mm,
        tam=11,
        alinear_derecha=(0, 2),
    )

    x_nota = MARGEN + 172 * mm
    c.setFillColor(ROJO)
    c.setFont(NEGRITA, 30)
    c.drawString(x_nota, y_tabla - 20 * mm, "43")
    c.setFillColor(TINTA)
    c.setFont(NEGRITA, 11)
    c.drawString(x_nota + 22 * mm, y_tabla - 18 * mm, "títulos distintos")
    parrafo(
        c,
        x_nota,
        y_tabla - 30 * mm,
        118 * mm,
        "Anupam Kher lidera el ranking. La cabeza es india: ocho de los diez actores pertenecen a esa industria, "
        "el segundo país con más películas del catálogo.",
        11.5,
        GRIS,
        alto_linea=5.6 * mm,
    )
    parrafo(
        c,
        x_nota,
        y_tabla - 52 * mm,
        118 * mm,
        "Los empates se resuelven por nombre ascendente: Naseeruddin Shah aparece antes que Takahiro Sakurai, ambos con 32.",
        9.8,
        GRIS_CLARO,
        alto_linea=4.8 * mm,
    )
    pie(c, n)


def diapositiva_databricks(c: canvas.Canvas, n: int) -> None:
    fondo_claro(c)
    y = cabecera(c, "06 · Reto 3", "SQL y PySpark: dos caminos, un resultado", "Unity Catalog · notebook 03_analisis_netflix.ipynb · DBR 15.4 LTS")

    ancho_tarjeta = 62 * mm
    x = MARGEN
    for valor, titulo, detalle, color in [
        ("0", "diferencias SQL / PySpark", "36 439 filas comparadas", VERDE),
        ("0", "diferencias MapReduce / Spark", "full outer join", VERDE),
        ("117", "países analizados", "5 688 películas con duración", ROJO),
    ]:
        tarjeta(c, x, y - 24 * mm, ancho_tarjeta, 26 * mm, valor, titulo, detalle, color)
        x += ancho_tarjeta + 7 * mm

    y_tabla = y - 32 * mm
    tabla(
        c,
        MARGEN,
        y_tabla,
        [110, 44, 46, 40, 46],
        ["Análisis", "Filas SQL", "Filas Spark", "Diferentes", "¿Coinciden?"],
        [
            ["Películas y series", "2", "2", "0", "Sí"],
            ["Títulos por actor", "36 439", "36 439", "0", "Sí"],
            ["Duración por país", "117", "117", "0", "Sí"],
        ],
        alto_fila=8.6 * mm,
        tam=10.2,
        alinear_derecha=(1, 2, 3),
    )

    yy = y_tabla - 39 * mm
    yy = parrafo(
        c,
        MARGEN,
        yy,
        ANCHO_UTIL,
        "Cada análisis se resolvió dos veces, sin reutilizar la salida de la otra vía: una celda SQL y una celda "
        "PySpark comparten solo la tabla de entrada. La comparación usa un **full outer join** por clave y "
        "clasifica cada fila como igual, diferente o presente en una sola salida.",
        11,
    )
    yy -= 3 * mm
    for texto in [
        "**A · Tipos:** 6 131 películas y 2 676 series, sin registros «Otro» ni «Sin clasificación».",
        "**B · Actores:** 36 439, separando `cast` por comas y eliminando pares (show_id, actor) repetidos.",
        "**C · Duración:** 117 países, solo películas con `duration_min` numérico y mayor que cero.",
    ]:
        yy = vineta(c, MARGEN, yy, ANCHO_UTIL, texto, 10.8)
        yy -= 1.5 * mm
    pie(c, n)


def diapositiva_tipos(c: canvas.Canvas, n: int) -> None:
    fondo_claro(c)
    y = cabecera(c, "07 · Reto 4", "El catálogo es mayoritariamente cinematográfico", "Figura 2 · títulos por tipo, con cantidad y porcentaje")
    imagen_ajustada(c, FIGURAS / "grafico_tipos.png", MARGEN, 18 * mm, 165 * mm, y - 20 * mm)

    x = MARGEN + 178 * mm
    ancho = ANCHO - MARGEN - x
    c.setFillColor(ROJO)
    c.setFont(NEGRITA, 34)
    c.drawString(x, y - 14 * mm, "69,62 %")
    c.setFillColor(TINTA)
    c.setFont(NEGRITA, 11)
    c.drawString(x, y - 21 * mm, "películas")
    parrafo(c, x, y - 30 * mm, ancho, "6 131 de los 8 807 títulos son películas; las 2 676 series representan el 30,38 %.", 11, GRIS, 5.2 * mm)
    c.setFillColor(TINTA)
    c.setFont(NEGRITA, 34)
    c.drawString(x, y - 48 * mm, "8 807")
    c.setFillColor(TINTA)
    c.setFont(NEGRITA, 11)
    c.drawString(x, y - 55 * mm, "títulos clasificados")
    parrafo(c, x, y - 64 * mm, ancho, "No hay registros con otro tipo ni sin clasificación: los porcentajes se calculan sobre el total.", 11, GRIS, 5.2 * mm)
    c.setFillColor(FONDO)
    c.setStrokeColor(BORDE)
    c.roundRect(x, 20 * mm, ancho, 24 * mm, 2 * mm, stroke=1, fill=1)
    parrafo(c, x + 6 * mm, 36 * mm, ancho - 12 * mm, "Dos barras, una lectura: el cine domina el catálogo disponible.", 9.5, GRIS, 4.6 * mm)
    pie(c, n)


def diapositiva_actores(c: canvas.Canvas, n: int) -> None:
    fondo_claro(c)
    y = cabecera(c, "08 · Reto 4", "Pocos actores concentran muchos títulos", "Figura 3 · diez actores con mayor cantidad de títulos distintos")
    imagen_ajustada(c, FIGURAS / "grafico_actores.png", MARGEN, 18 * mm, 172 * mm, y - 20 * mm)

    x = MARGEN + 186 * mm
    ancho = ANCHO - MARGEN - x
    c.setFillColor(ROJO)
    c.setFont(NEGRITA, 34)
    c.drawString(x, y - 14 * mm, "43")
    c.setFillColor(TINTA)
    c.setFont(NEGRITA, 11)
    c.drawString(x, y - 21 * mm, "títulos · Anupam Kher")
    parrafo(c, x, y - 30 * mm, ancho, "Le siguen Shah Rukh Khan (35) y Julie Tejwani (33). El décimo, Amitabh Bachchan, baja a 28.", 11, GRIS, 5.2 * mm)
    c.setFillColor(TINTA)
    c.setFont(NEGRITA, 34)
    c.drawString(x, y - 50 * mm, "36 439")
    c.setFillColor(TINTA)
    c.setFont(NEGRITA, 11)
    c.drawString(x, y - 57 * mm, "actores distintos")
    parrafo(c, x, y - 66 * mm, ancho, "64 126 pares actor–título: cada intérprete participa en varios títulos, y el mismo título cuenta una vez por actor.", 11, GRIS, 5.2 * mm)
    c.setFillColor(FONDO)
    c.setStrokeColor(BORDE)
    c.roundRect(x, 20 * mm, ancho, 24 * mm, 2 * mm, stroke=1, fill=1)
    parrafo(c, x + 6 * mm, 36 * mm, ancho - 12 * mm, "Ocho de los diez primeros actores pertenecen a la industria india.", 9.5, GRIS, 4.6 * mm)
    pie(c, n)


def diapositiva_duracion(c: canvas.Canvas, n: int) -> None:
    fondo_claro(c)
    y = cabecera(c, "09 · Reto 4", "La duración no depende del volumen", "Tabla 6 · películas con duración numérica, promedio por país")

    filas = [
        ["United States", "2 749", "93,75"],
        ["India", "962", "125,91"],
        ["United Kingdom", "534", "98,76"],
        ["Canada", "319", "91,15"],
        ["France", "303", "100,97"],
        ["Germany", "182", "103,01"],
        ["Spain", "171", "101,10"],
        ["Japan", "119", "98,85"],
    ]
    y_tabla = y + 2 * mm
    tabla(
        c,
        MARGEN,
        y_tabla,
        [70, 38, 42],
        ["País", "Películas", "Promedio (min)"],
        filas,
        alto_fila=9.0 * mm,
        tam=10.4,
        alinear_derecha=(1, 2),
    )

    x = MARGEN + 165 * mm
    ancho = ANCHO - MARGEN - x
    c.setFillColor(ROJO)
    c.setFont(NEGRITA, 34)
    c.drawString(x, y_tabla - 16 * mm, "125,91")
    c.setFillColor(TINTA)
    c.setFont(NEGRITA, 11)
    c.drawString(x + 38 * mm, y_tabla - 15 * mm, "min · India")
    parrafo(
        c,
        x,
        y_tabla - 25 * mm,
        ancho,
        "India es el promedio más alto del grupo líder, con más de dos horas por película. Estados Unidos aporta "
        "2 749 películas con 93,75 minutos: el volumen no eleva el promedio.",
        11.2,
        GRIS,
        5.4 * mm,
    )
    c.setFillColor(TINTA)
    c.setFont(NEGRITA, 11)
    c.drawString(x, y_tabla - 53 * mm, "5 688 películas entran al cálculo")
    parrafo(
        c,
        x,
        y_tabla - 61 * mm,
        ancho,
        "Solo películas con duración numérica mayor que cero. Se excluyen las 3 sin dato y las 2 676 series. "
        "Cada película cuenta una vez por cada país listado.",
        10,
        GRIS,
        5 * mm,
    )
    c.setFillColor(FONDO)
    c.setStrokeColor(BORDE)
    c.roundRect(MARGEN, 18 * mm, ANCHO_UTIL, 17 * mm, 2 * mm, stroke=1, fill=1)
    parrafo(
        c,
        MARGEN + 7 * mm,
        27 * mm,
        ANCHO_UTIL - 14 * mm,
        "**Lectura:** países con pocas películas pueden tener promedios altos o bajos; el promedio describe el catálogo, no el consumo.",
        10.5,
        GRIS,
        5.2 * mm,
    )
    pie(c, n)


def diapositiva_conclusiones(c: canvas.Canvas, n: int) -> None:
    fondo_claro(c)
    y = cabecera(c, "10 · Cierre", "Tres respuestas y una misma cifra", "Conclusiones del informe · menos de 250 palabras")

    ancho_col = (ANCHO_UTIL - 8 * mm) / 2
    yy = y
    yy = parrafo(c, MARGEN, yy, ancho_col, "**Tipos.** 8 807 títulos: 6 131 películas (69,62 %) y 2 676 series (30,38 %).", 12.5)
    yy -= 2 * mm
    yy = parrafo(c, MARGEN, yy, ancho_col, "**Actor.** Anupam Kher encabeza con 43 títulos distintos; le siguen Shah Rukh Khan (35) y Julie Tejwani (33).", 12.5)
    yy -= 2 * mm
    yy = parrafo(c, MARGEN, yy, ancho_col, "**Duración.** Estados Unidos aporta 2 749 películas con 93,75 minutos; India registra el promedio más alto del grupo líder: 125,91 minutos.", 12.5)

    x2 = MARGEN + ancho_col + 8 * mm
    c.setFillColor(FONDO)
    c.setStrokeColor(BORDE)
    c.roundRect(x2, 26 * mm, ancho_col, 72 * mm, 3 * mm, stroke=1, fill=1)
    c.setFillColor(ROJO)
    c.setFont(NEGRITA, 45)
    c.drawString(x2 + 8 * mm, 70 * mm, "0")
    c.setFillColor(TINTA)
    c.setFont(NEGRITA, 12)
    c.drawString(x2 + 8 * mm, 62 * mm, "diferencias entre los tres caminos")
    parrafo(c, x2 + 8 * mm, 53 * mm, ancho_col - 16 * mm, "MapReduce y Spark llegaron a 36 439 actores con las mismas cantidades.", 10.5, GRIS, 5 * mm)
    c.setFillColor(TINTA)
    c.setFont(NEGRITA, 10)
    c.drawString(x2 + 8 * mm, 33 * mm, "Limitaciones: campos multivaluados, nombres sin normalizar")
    c.drawString(x2 + 8 * mm, 27.5 * mm, "y ausencias que se conservan como nulos, sin imputar.")
    pie(c, n)


def diapositiva_entregables(c: canvas.Canvas, n: int) -> None:
    fondo_claro(c)
    y = cabecera(c, "11 · Entrega", "Dashboard y archivos del proyecto", "FastAPI + Bootstrap 5.3 + Chart.js 4.4 · seis páginas conectadas a la API")

    paginas = ["Resumen", "Limpieza", "MapReduce", "Databricks", "Hallazgos", "Catálogo"]
    ancho_pag = 46 * mm
    x = MARGEN
    for pagina in paginas:
        c.setFillColor(TINTA)
        c.roundRect(x, y - 16 * mm, ancho_pag, 11 * mm, 1.6 * mm, stroke=0, fill=1)
        c.setFillColor(BLANCO)
        c.setFont(NEGRITA, 8.6)
        c.drawCentredString(x + ancho_pag / 2, y - 12.3 * mm, pagina.upper())
        x += ancho_pag + 4.4 * mm

    yy = y - 26 * mm
    yy = parrafo(
        c,
        MARGEN,
        yy,
        ANCHO_UTIL,
        "El panel consume los resultados reales del pipeline desde la API (`/api/resumen`, `/api/limpieza`, "
        "`/api/mapreduce`, `/api/verificacion`, `/api/actores`, `/api/paises`, `/api/tipos`, `/api/catalogo`).",
        11,
        GRIS,
        5.2 * mm,
    )
    yy -= 5 * mm
    yy = parrafo(
        c,
        MARGEN,
        yy,
        ANCHO_UTIL,
        "Entregables: `Informe_Netflix_Elsner.pdf`, `Presentacion_Netflix_Grupo.pdf`, `03_analisis_netflix.ipynb`, "
        "`mapreduce_actores.csv`, los programas de limpieza y MapReduce, el dashboard y este guion de exposición.",
        11,
        GRIS,
        5.2 * mm,
    )

    c.setFillColor(TINTA)
    c.setFont(NEGRITA, 30)
    c.drawString(MARGEN, 34 * mm, "Gracias")
    c.setFillColor(ROJO)
    c.rect(MARGEN, 28 * mm, 30 * mm, 1.4 * mm, stroke=0, fill=1)
    c.setFillColor(GRIS)
    c.setFont(NORMAL, 10)
    c.drawString(MARGEN, 21 * mm, "Equipo Elsner · Jhael Arguedas · Carlos Conde · Bryan Mamani")
    c.drawRightString(ANCHO - MARGEN, 21 * mm, "Tecnologías Emergentes I · 2026")
    pie(c, n)


# --------------------------------------------------------------------------
# Composición
# --------------------------------------------------------------------------
def main() -> int:
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(SALIDA), pagesize=(ANCHO, ALTO))
    c.setTitle("Análisis del catálogo de Netflix · Equipo Elsner")
    c.setAuthor("Jhael Arguedas · Carlos Conde · Bryan Mamani")
    c.setSubject("Evaluación Segundo Momento · Tecnologías Emergentes I")

    portada(c)
    c.showPage()
    for indice, dibujar in enumerate(
        [
            diapositiva_objetivo,
            diapositiva_proceso,
            diapositiva_limpieza,
            diapositiva_mapreduce,
            diapositiva_tabla2,
            diapositiva_databricks,
            diapositiva_tipos,
            diapositiva_actores,
            diapositiva_duracion,
            diapositiva_conclusiones,
            diapositiva_entregables,
        ],
        start=2,
    ):
        dibujar(c, indice)
        c.showPage()

    c.save()
    print(f"Presentacion PDF: {SALIDA.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
