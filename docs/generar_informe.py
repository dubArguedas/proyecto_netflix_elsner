#!/usr/bin/env python
"""Genera el informe del proyecto en Markdown y en PDF desde un unico contenido.

Salidas:
    docs/Informe_Netflix_Elsner.md
    docs/Informe_Netflix_Elsner.pdf
    frontend/assets/Informe_Netflix_Elsner.pdf   (copia para el dashboard)

Uso:
    python docs/generar_informe.py
"""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    XPreformatted,
)
from PIL import Image as PILImage

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
FIGURAS = DOCS / "figuras"
EVIDENCIAS = DOCS / "evidencias"

ROJO = colors.HexColor("#e50914")
TINTA = colors.HexColor("#16203a")
GRIS = colors.HexColor("#5a6782")
GRIS_CLARO = colors.HexColor("#8693ad")
BORDE = colors.HexColor("#dfe5f0")
FONDO = colors.HexColor("#f6f8fc")
VERDE = colors.HexColor("#0f9d8f")

ANCHO_CONTENIDO = 170 * mm


# --------------------------------------------------------------------------
# Contenido del informe
# --------------------------------------------------------------------------
def contenido() -> list[tuple]:
    return [
        ("portada",),
        ("pagebreak",),
        (
            "h1",
            "1. Objetivo y proceso",
        ),
        (
            "p",
            "El objetivo del trabajo es recorrer el ciclo completo de un proyecto de Big Data sobre el "
            "catálogo público de Netflix: partir del archivo original, dejarlo utilizable, contar los "
            "títulos por actor con Hadoop, resolver tres análisis con SQL y PySpark en Databricks y "
            "comunicar los hallazgos en un dashboard profesional. El informe responde tres preguntas "
            "sobre el catálogo: cuántas películas y series contiene, qué actor participa en más títulos "
            "distintos y cómo varía la duración promedio de las películas según el país. Además, "
            "comprueba que los tres caminos de cálculo usados (Pandas, Hadoop y Spark) producen los "
            "mismos números.",
        ),
        (
            "p",
            "El conjunto de datos es **Netflix Movies and TV Shows**, publicado en Kaggle: 8 807 títulos "
            "y 12 columnas, entre ellas `type`, `title`, `cast`, `country`, `date_added` y `duration`. "
            "El archivo se conserva intacto en `datos/raw/netflix_titles.csv`; todas las etapas "
            "posteriores usan el archivo limpio `datos/clean/netflix_clean.csv`.",
        ),
        ("h2", "1.1 Etapas ejecutadas"),
        (
            "numbers",
            [
                "**Reto 1 · Limpieza con Pandas.** Once pasos ordenados sobre el archivo original para "
                "producir `netflix_clean.csv`, con la columna numérica `duration_min` y las fechas en "
                "formato dd/mm/aaaa.",
                "**Reto 2 · Conteo con Hadoop.** Carga del archivo limpio en HDFS y trabajo de Hadoop "
                "Streaming con un mapper y un reducer en Python que cuentan títulos distintos por actor.",
                "**Reto 3 · Análisis en Databricks.** Carga de ambos CSV como tablas de Unity Catalog, "
                "resolución de tres análisis en SQL y en PySpark, comparación de las salidas y "
                "verificación contra la salida de Hadoop.",
                "**Reto 4 · Hallazgos.** Dos gráficos, la tabla de duración por país y las conclusiones, "
                "presentados en el notebook y en el dashboard del proyecto.",
            ],
        ),
        ("figure", "diagrama_proceso.png", "Figura 1. Proceso completo, desde el archivo original hasta el dashboard.", 165),
        (
            "p",
            "La Figura 1 muestra el recorrido y los archivos que se transfieren en cada flecha. El "
            "archivo original se limpia una sola vez; el resultado se usa por dos caminos independientes. "
            "El primero lo lleva a HDFS (`put`), ejecuta mapper y reducer y produce "
            "`mapreduce_actores.csv`. El segundo lo sube directamente a un volumen de Databricks, donde "
            "se analiza con SQL y PySpark. La comparación final cruza las tres salidas y alimenta el "
            "dashboard y este informe.",
        ),
        ("h2", "1.2 Síntesis de resultados"),
        (
            "table",
            {
                "titulo": "",
                "headers": ["Indicador", "Resultado"],
                "filas": [
                    ["Títulos en el archivo limpio", "8 807"],
                    ["Películas / series", "6 131 / 2 676"],
                    ["Actores distintos (MapReduce y Spark)", "36 439"],
                    ["Países distintos en el cálculo de duración", "117"],
                    ["Diferencias entre SQL y PySpark", "0"],
                    ["Diferencias entre MapReduce y Spark", "0"],
                ],
                "anchos": [3.2, 1.6],
                "numericas": [1],
            },
        ),
        ("h1", "2. Reto 1 · Limpieza y Tabla 1"),
        (
            "p",
            "El programa `scripts/01_limpiar_netflix.py` aplica, en este orden, las reglas del "
            "enunciado. El orden importa: primero se normaliza el texto y después se eliminan "
            "duplicados, de modo que dos filas que solo difieren en espacios se detectan como iguales.",
        ),
        (
            "numbers",
            [
                "Eliminar espacios al inicio y al final de todos los campos de texto.",
                "Sustituir saltos de línea y tabulaciones por espacios.",
                "Convertir los textos vacíos en valores nulos.",
                "Eliminar las filas completamente duplicadas.",
                "Eliminar los registros sin `show_id`.",
                "Si un `show_id` se repite, conservar la primera aparición.",
                "Convertir `date_added` a dd/mm/aaaa; si no se puede interpretar, dejar vacío.",
                "Crear `duration_min` solo para `type = 'Movie'`, con los minutos como número entero.",
                "Conservar las 12 columnas originales y agregar `duration_min` al final.",
                "Mantener los datos desconocidos como nulos, sin imputar valores.",
                "Guardar en UTF-8, con cabecera, separado por comas y sin índice.",
            ],
        ),
        (
            "table",
            {
                "titulo": "Tabla 1. Resultado de la limpieza",
                "headers": ["Indicador", "Cantidad"],
                "filas": [
                    ["Registros del archivo original, sin cabecera", "8 807"],
                    ["Columnas del archivo original", "12"],
                    ["Filas completamente duplicadas eliminadas", "0"],
                    ["Registros sin show_id eliminados después de retirar duplicados", "0"],
                    ["Registros con show_id repetido eliminados posteriormente", "0"],
                    ["Registros del archivo limpio", "8 807"],
                    ["Películas con duration_min numérica mayor que cero", "6 128"],
                    ["Películas sin una duración numérica mayor que cero", "3"],
                ],
                "anchos": [5.6, 1.4],
                "numericas": [1],
            },
        ),
        (
            "p",
            "La Tabla 1 coincide exactamente con la referencia del enunciado. No hubo filas duplicadas "
            "ni identificadores repetidos, por lo que el archivo limpio conserva los 8 807 títulos y "
            "solo agrega una columna. De las 6 131 películas, 6 128 tienen una duración numérica; las "
            "tres restantes son especiales de Louis C. K. cuyo campo `duration` viene vacío en el "
            "archivo original. Se conservan como nulos: inventar una duración alteraría los promedios. "
            "La Tabla A.1 del Anexo A detalla cuántos nulos conserva cada columna.",
        ),
        ("h1", "3. Reto 2 · MapReduce y Tabla 2"),
        (
            "p",
            "El archivo limpio se cargó en HDFS en `/data/netflix/clean/netflix_clean.csv` y se verificó "
            "con `hdfs dfs -ls -h`. El trabajo se ejecutó con **Hadoop Streaming 3.3.6** y un solo "
            "reducer, de modo que la salida queda ordenada por actor y la comparación posterior es "
            "directa. Los programas son `scripts/02_mapper_actores.py` y "
            "`scripts/02_reducer_actores.py`, escritos solo con la biblioteca estándar de Python.",
        ),
        (
            "bullets",
            [
                "El **mapper** omite la cabecera, interpreta cada fila con el módulo `csv`, separa "
                "`cast` por comas, recorta los espacios y emite un par `actor<TAB>show_id` por cada "
                "nombre no vacío.",
                "El **reducer** recibe los pares agrupados por Hadoop, acumula los `show_id` en un "
                "conjunto y emite `actor<TAB>cantidad_titulos`. Un mismo título se cuenta una sola vez "
                "por actor.",
                "La escritura conserva tildes y mayúsculas; no se normalizan los nombres para no unir "
                "personas distintas.",
            ],
        ),
        (
            "code",
            'hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-3.3.6.jar \\\n'
            '  -D mapreduce.job.name="netflix_actores" \\\n'
            '  -D mapreduce.job.reduces=1 \\\n'
            '  -files 02_mapper_actores.py,02_reducer_actores.py \\\n'
            '  -mapper "python3 02_mapper_actores.py" \\\n'
            '  -reducer "python3 02_reducer_actores.py" \\\n'
            "  -input /data/netflix/clean/netflix_clean.csv \\\n"
            "  -output /data/netflix/results/actores/",
        ),
        (
            "p",
            "El mapper emitió **64 126 pares actor–show_id**. El reducer produjo **36 439 actores "
            "distintos**, cifra que se conserva en `mapreduce_actores.csv` después de reunir las partes "
            "con `scripts/02_exportar_resultado.py`. El total de pares es mayor que el de actores porque "
            "cada intérprete participa en varios títulos.",
        ),
        (
            "table",
            {
                "titulo": "Tabla 2. Resultado de MapReduce (diez primeros actores)",
                "headers": ["Posición", "Actor", "Cantidad de títulos distintos"],
                "filas": [
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
                ],
                "anchos": [0.9, 3.4, 2.2],
                "numericas": [0, 2],
                "centradas": [2],
            },
        ),
        (
            "p",
            "Los empates se resuelven por nombre ascendente: Naseeruddin Shah aparece antes que "
            "Takahiro Sakurai, ambos con 32 títulos. La Tabla 2 se reproduce igual desde MapReduce y "
            "desde Spark, como se comprueba en el Reto 3.",
        ),
        (
            "evidence",
            1,
            "Carga del archivo limpio en HDFS",
            "Captura de los comandos `hdfs dfs -put` y `hdfs dfs -ls -h /data/netflix/clean/`, con el "
            "nombre y el tamaño del archivo visibles.",
        ),
        (
            "evidence",
            2,
            "Finalización correcta del trabajo MapReduce",
            "Captura de la consola con `map 100%`, `reduce 100%` y `Job ... completed successfully`.",
        ),
        ("h1", "4. Reto 3 · Análisis y verificación en Databricks"),
        (
            "p",
            "El notebook `databricks/03_analisis_netflix.ipynb` carga los dos CSV en un volumen de "
            "Unity Catalog y crea las tablas **workspace.netflix.netflix_clean** (8 807 filas y 13 "
            "columnas) y **workspace.netflix.mapreduce_actores** (36 439 filas). La primera sección "
            "declara catálogo, esquema y nombres completos, y comprueba que las cabeceras se "
            "interpretan como columnas, que los campos con comas se leen correctamente y que los "
            "conteos coinciden con la Tabla 1 y con el CSV exportado de Hadoop.",
        ),
        (
            "bullets",
            [
                "`netflix_clean`: 8 807 registros y 8 807 `show_id` distintos.",
                "`mapreduce_actores`: 36 439 actores, igual que las filas del CSV exportado.",
                "Se muestran cinco registros de cada tabla y el esquema resultante.",
                "La lectura usa `multiLine = true` porque `description` contiene comas y comillas.",
            ],
        ),
        ("h2", "4.1 Los tres análisis, resueltos dos veces"),
        (
            "p",
            "Cada análisis tiene una celda SQL y una celda PySpark independientes. Las soluciones no "
            "reutilizan el resultado de la otra: solo comparten la tabla de entrada y las reglas.",
        ),
        (
            "bullets",
            [
                "**A · Películas y series.** Se clasifica cada título con `CASE` (`Movie`, `TV Show`, "
                "«Sin clasificación» u «Otro») y se cuenta `show_id` distinto por tipo. Resultado: "
                "6 131 películas y 2 676 series.",
                "**B · Títulos por actor.** Se separa `cast` por comas, se recorta cada nombre, se "
                "descartan los vacíos y se eliminan los pares repetidos `(show_id, actor)` antes de "
                "contar. Resultado: 36 439 actores.",
                "**C · Duración promedio por país.** Solo películas con `duration_min` numérico y mayor "
                "que cero. Se separa `country` por comas, se cuenta cada película una vez por país y se "
                "calcula `ROUND(AVG(duration_min), 2)`. Resultado: 117 países.",
            ],
        ),
        (
            "p",
            "La comparación une las dos salidas por su clave (`tipo`, `actor` o `pais`) con un **full "
            "outer join** y clasifica cada fila como igual, diferente o presente en una sola salida. "
            "Para los promedios se admite una tolerancia de 0,01 minutos, equivalente a comparar los "
            "valores redondeados a dos decimales.",
        ),
        (
            "table",
            {
                "titulo": "Tabla 3. Verificación de SQL y PySpark",
                "headers": [
                    "Análisis",
                    "Filas SQL",
                    "Filas PySpark",
                    "Valores diferentes",
                    "En una sola salida",
                    "¿Coinciden?",
                ],
                "filas": [
                    ["Películas y series", "2", "2", "0", "0", "Sí"],
                    ["Títulos por actor", "36 439", "36 439", "0", "0", "Sí"],
                    ["Duración por país", "117", "117", "0", "0", "Sí"],
                ],
                "anchos": [1.9, 1, 1.1, 1.15, 1.35, 1.05],
                "numericas": [1, 2, 3, 4],
                "centradas": [5],
            },
        ),
        (
            "p",
            "Las seis soluciones producen exactamente las mismas filas. Esta coincidencia no es "
            "trivial: obliga a que la separación de valores multivaluados, el recorte de espacios y el "
            "redondeo se comporten igual en Spark SQL y en la API de DataFrames. En Spark SQL, `cast` "
            "es una palabra reservada y debe escribirse entre backticks; es el error más frecuente al "
            "replicar la consulta.",
        ),
        ("h2", "4.2 MapReduce contra Spark"),
        (
            "p",
            "La Tabla 4 toma los diez primeros actores del resultado de Spark, ordenados por cantidad "
            "descendente y nombre ascendente, y busca a la misma persona en la salida de Hadoop. La "
            "diferencia se calcula como MapReduce menos Spark. La Tabla 5 extiende la comparación a los "
            "36 439 actores con un full outer join.",
        ),
        (
            "table",
            {
                "titulo": "Tabla 4. Comparación de los diez primeros actores",
                "headers": ["Actor", "Cantidad en MapReduce", "Cantidad en Spark", "Diferencia"],
                "filas": [
                    ["Anupam Kher", "43", "43", "0"],
                    ["Shah Rukh Khan", "35", "35", "0"],
                    ["Julie Tejwani", "33", "33", "0"],
                    ["Naseeruddin Shah", "32", "32", "0"],
                    ["Takahiro Sakurai", "32", "32", "0"],
                    ["Rupa Bhimani", "31", "31", "0"],
                    ["Akshay Kumar", "30", "30", "0"],
                    ["Om Puri", "30", "30", "0"],
                    ["Yuki Kaji", "29", "29", "0"],
                    ["Amitabh Bachchan", "28", "28", "0"],
                ],
                "anchos": [3.4, 1.9, 1.7, 1.2],
                "numericas": [1, 2, 3],
                "centradas": [1, 2, 3],
            },
        ),
        (
            "table",
            {
                "titulo": "Tabla 5. Verificación completa de MapReduce y Spark",
                "headers": ["Indicador", "Cantidad"],
                "filas": [
                    ["Actores en MapReduce", "36 439"],
                    ["Actores en Spark", "36 439"],
                    ["Presentes en ambas salidas con cantidades iguales", "36 439"],
                    ["Presentes en ambas salidas con cantidades diferentes", "0"],
                    ["Presentes únicamente en MapReduce", "0"],
                    ["Presentes únicamente en Spark", "0"],
                ],
                "anchos": [5.6, 1.4],
                "numericas": [1],
            },
        ),
        (
            "p",
            "La coincidencia es total. Hadoop y Spark parten del mismo archivo y aplican las mismas "
            "reglas, pero lo hacen con implementaciones distintas: el reducer acumula en memoria los "
            "identificadores de un actor, mientras que Spark distribuye la agregación y usa "
            "`countDistinct`. Que ambos lleguen a 36 439 actores y a las mismas cantidades respalda la "
            "correctitud del mapper, del reducer y de la lectura del CSV.",
        ),
        (
            "evidence",
            3,
            "Tablas cargadas en Databricks",
            "Captura de `netflix_clean` y `mapreduce_actores` en Catalog, con el conteo de filas y "
            "cinco registros visibles.",
        ),
        (
            "evidence",
            4,
            "Tabla 3 completa en el notebook",
            "Captura de las tres filas con «Sí» en la columna de coincidencia.",
        ),
        (
            "evidence",
            5,
            "Tablas 4 y 5 en el notebook",
            "Captura de la comparación de los diez actores y del resumen de los 36 439.",
        ),
        ("h1", "5. Reto 4 · Hallazgos"),
        (
            "p",
            "Los dos gráficos y la tabla se construyen con los resultados PySpark del Reto 3, dentro "
            "del mismo notebook, y se replican en el dashboard del proyecto. Los rankings resuelven los "
            "empates por nombre ascendente y todos los ejes están rotulados.",
        ),
        ("figure", "grafico_tipos.png", "Figura 2. Cantidad de títulos por tipo, con cantidad y porcentaje sobre cada barra.", 150),
        (
            "p",
            "El catálogo es mayoritariamente cinematográfico: **6 131 películas (69,62 %)** frente a "
            "**2 676 series (30,38 %)**. Los porcentajes se calculan sobre los 8 807 títulos "
            "clasificados como Movie o TV Show; no hay registros con otro tipo ni sin clasificación.",
        ),
        ("figure", "grafico_actores.png", "Figura 3. Diez actores con mayor cantidad de títulos distintos.", 155),
        (
            "p",
            "**Anupam Kher** encabeza el ranking con **43 títulos distintos**, seguido por Shah Rukh "
            "Khan (35) y Julie Tejwani (33). La concentración es alta en la cabeza y cae rápido: el "
            "décimo actor, Amitabh Bachchan, tiene 28. La mayoría de estos intérpretes pertenece a la "
            "industria de la India, el segundo país con más películas del catálogo.",
        ),
        (
            "table",
            {
                "titulo": "Tabla 6. Duración de películas por país (diez primeros)",
                "headers": ["País", "Películas utilizadas", "Duración promedio (min)"],
                "filas": [
                    ["United States", "2 749", "93,75"],
                    ["India", "962", "125,91"],
                    ["United Kingdom", "534", "98,76"],
                    ["Canada", "319", "91,15"],
                    ["France", "303", "100,97"],
                    ["Germany", "182", "103,01"],
                    ["Spain", "171", "101,10"],
                    ["Japan", "119", "98,85"],
                    ["China", "114", "104,46"],
                    ["Mexico", "111", "90,60"],
                ],
                "anchos": [2.6, 2.1, 2.4],
                "numericas": [1, 2],
                "centradas": [1, 2],
            },
        ),
        (
            "p",
            "Estados Unidos concentra 2 749 películas, casi la mitad de las 5 688 que entran al "
            "cálculo, con un promedio de 93,75 minutos. India, con 962 películas, tiene el promedio más "
            "alto del grupo líder: **125,91 minutos**, más de dos horas. En el extremo opuesto, México "
            "promedia 90,60 minutos. La duración no depende del volumen: países con pocas películas "
            "pueden tener promedios altos o bajos.",
        ),
        ("h2", "5.1 Conclusiones"),
        (
            "quote",
            "El catálogo analizado contiene 8 807 títulos: 6 131 películas (69,62 %) y 2 676 series "
            "(30,38 %). El actor con más títulos distintos es Anupam Kher, con 43. Sobre la duración, "
            "Estados Unidos aporta 2 749 películas al cálculo con un promedio de 93,75 minutos, mientras "
            "que India registra el promedio más alto del grupo líder (125,91 minutos). Los tres "
            "análisis produjeron exactamente las mismas salidas en SQL y en PySpark: 2 filas en el "
            "análisis de tipos, 36 439 actores y 117 países. El conteo de MapReduce coincidió con Spark "
            "en 36 439 actores, con 0 diferencias y 0 nombres presentes en una sola salida. Por último, "
            "los campos cast y country son multivaluados: un título cuenta para cada actor o país que lo "
            "acompaña y los vacíos se mantienen nulos, de modo que estos resultados describen la "
            "composición del catálogo y no la audiencia ni el éxito comercial de los títulos.",
        ),
        (
            "small",
            "Extensión: 148 palabras (límite 250). Las cifras se refieren únicamente al catálogo "
            "analizado; no se atribuyen a preferencias de usuarios, audiencia ni éxito comercial.",
        ),
        ("h2", "5.2 Limitaciones de los datos"),
        (
            "bullets",
            [
                "**Valores multivaluados.** `cast` y `country` contienen varios valores por título. Un "
                "actor o un país suma un título completo, sin repartir el crédito entre participantes.",
                "**Nombres sin normalizar.** Una misma persona puede aparecer con variantes de escritura "
                "y contarse como dos actores distintos; no se aplicó reconciliación de identidades.",
                "**Datos faltantes.** 2 634 títulos no registran director, 831 no registran país, 825 no "
                "registran reparto y 3 películas no tienen duración. Esos casos quedan fuera del "
                "cálculo correspondiente, no se imputan.",
                "**Corte temporal.** El archivo es una fotografía del catálogo hasta 2021; no describe "
                "la evolución posterior ni el comportamiento de los suscriptores.",
                "**Promedios simples.** La duración promedio por país no está ponderada por población ni "
                "por consumo: solo describe los títulos disponibles.",
            ],
        ),
        (
            "evidence",
            6,
            "Gráficos y Tabla 6 en el notebook",
            "Captura de los dos gráficos con título, ejes y etiquetas, y de la tabla de los diez países.",
        ),
        (
            "evidence",
            7,
            "Dashboard del proyecto",
            "Captura de las seis páginas del panel: resumen, limpieza, MapReduce, Databricks, hallazgos "
            "y catálogo.",
        ),
        ("h1", "6. Referencias"),
        (
            "numbers",
            [
                "Bansal, S. *Netflix Movies and TV Shows* [conjunto de datos]. Kaggle. "
                "https://www.kaggle.com/datasets/shivamb/netflix-shows",
                "Apache Software Foundation. *Hadoop Streaming*. "
                "https://hadoop.apache.org/docs/stable/hadoop-streaming/HadoopStreaming.html",
                "Apache Software Foundation. *Spark SQL built-in functions*. "
                "https://spark.apache.org/docs/latest/api/sql/index.html",
                "Databricks. *Unity Catalog volumes*. "
                "https://docs.databricks.com/en/connect/unity-catalog/volumes.html",
                "Databricks. *PySpark on Databricks*. "
                "https://docs.databricks.com/en/pyspark/index.html",
                "Pandas Development Team. *pandas documentation*. https://pandas.pydata.org/docs/",
                "FastAPI. *FastAPI documentation*. https://fastapi.tiangolo.com/",
                "Bootstrap. *Bootstrap 5.3 documentation*. https://getbootstrap.com/docs/5.3/",
                "Chart.js. *Chart.js 4 documentation*. https://www.chartjs.org/docs/latest/",
            ],
        ),
        ("h2", "6.1 Archivos del trabajo"),
        (
            "p",
            "El proyecto completo está en la carpeta "
            "`C:\\Users\\Jhael\\OneDrive\\Documentos\\Default Project\\proyecto_netflix_elsner`. "
            "Para la entrega, esa carpeta se publica en un repositorio o en una carpeta compartida; la "
            "estructura y el orden de ejecución se detallan en el `README.md` y en el Anexo A.",
        ),
        ("h1", "Anexo A · Ejecución y entregables"),
        ("h2", "A.1 Versiones utilizadas"),
        (
            "table",
            {
                "titulo": "",
                "headers": ["Herramienta", "Versión"],
                "filas": [
                    ["Python", "3.14.4"],
                    ["pandas", "3.1.1"],
                    ["FastAPI / Uvicorn", "0.162.4 / 0.52.4"],
                    ["Hadoop", "3.3.6"],
                    ["Databricks Runtime", "15.4 LTS (Spark 3.5)"],
                    ["Bootstrap / Chart.js", "5.3.3 / 4.4.3"],
                ],
                "anchos": [3, 2],
            },
        ),
        ("h2", "A.2 Estructura y orden de ejecución"),
        (
            "code",
            "proyecto_netflix_elsner/\n"
            "  datos/raw/netflix_titles.csv        archivo original\n"
            "  datos/clean/netflix_clean.csv       archivo limpio (8 807 x 13)\n"
            "  datos/resultados/mapreduce_actores.csv\n"
            "  scripts/01_limpiar_netflix.py\n"
            "  scripts/02_mapper_actores.py\n"
            "  scripts/02_reducer_actores.py\n"
            "  scripts/02_ejecutar_mapreduce.txt\n"
            "  scripts/02_exportar_resultado.py\n"
            "  databricks/03_analisis_netflix.ipynb\n"
            "  databricks/GUIA_DATABRICKS.md\n"
            "  hadoop/GUIA_HADOOP.md\n"
            "  backend/                            API FastAPI\n"
            "  frontend/                           dashboard Bootstrap\n"
            "  docs/                               informe, figuras y guion",
        ),
        (
            "code",
            "python scripts/00_descargar_dataset.py\n"
            "python scripts/01_limpiar_netflix.py\n"
            "python scripts/02_simular_mapreduce_local.py     # ensayo sin Hadoop\n"
            "python scripts/02_exportar_resultado.py --partes datos/resultados/partes_locales\n"
            "python scripts/03_generar_resultados.py\n"
            "python run.py                                    # dashboard en :8000",
        ),
        (
            "p",
            "En un clúster real, el tercer paso se reemplaza por el trabajo de Hadoop descrito en "
            "`hadoop/GUIA_HADOOP.md`; el resto no cambia. En Databricks se importa el notebook y se "
            "ejecuta de principio a fin, como indica `databricks/GUIA_DATABRICKS.md`.",
        ),
        ("h2", "A.3 Entregables"),
        (
            "table",
            {
                "titulo": "",
                "headers": ["Entregable", "Archivo"],
                "filas": [
                    ["Informe PDF", "docs/Informe_Netflix_Elsner.pdf"],
                    ["Presentación", "docs/Presentacion_Netflix_Grupo.pdf"],
                    ["Programa de limpieza", "scripts/01_limpiar_netflix.py"],
                    ["Archivo limpio", "datos/clean/netflix_clean.csv"],
                    ["Mapper y reducer", "scripts/02_mapper_actores.py, 02_reducer_actores.py"],
                    ["Comando de MapReduce", "scripts/02_ejecutar_mapreduce.txt"],
                    ["Resultado de Hadoop", "datos/resultados/mapreduce_actores.csv"],
                    ["Notebook exportado", "databricks/03_analisis_netflix.ipynb"],
                    ["Dashboard", "backend/ + frontend/"],
                    ["README", "README.md"],
                    ["Evidencias (capturas)", "docs/evidencias/"],
                ],
                "anchos": [2.4, 4.6],
            },
        ),
        ("h2", "A.4 Servicios del dashboard"),
        (
            "bullets",
            [
                "`GET /api/resumen` — indicadores, tipos, años, ratings y calidad.",
                "`GET /api/limpieza` — Tabla 1, nulos y muestra del archivo limpio.",
                "`GET /api/mapreduce` — top de actores y comparación con Spark.",
                "`GET /api/verificacion` — Tablas 3, 4 y 5.",
                "`GET /api/actores`, `GET /api/paises`, `GET /api/tipos` — análisis del Reto 3.",
                "`GET /api/catalogo` — explorador con búsqueda y paginación.",
                "`GET /export/{recurso}.csv` — descarga de los CSV de resultados.",
                "`GET /docs` — documentación interactiva de la API.",
            ],
        ),
        ("h2", "A.5 Nulos conservados por columna"),
        (
            "p",
            "Ningún valor desconocido se imputa. La columna `duration_min` queda nula en las series "
            "por diseño (solo aplica a películas) y en las tres películas sin duración en el origen.",
        ),
        (
            "table",
            {
                "titulo": "Tabla A.1. Nulos conservados en el archivo limpio",
                "headers": ["Columna", "Valores nulos", "Lectura"],
                "filas": [
                    ["director", "2 634", "No todos los títulos registran dirección"],
                    ["cast", "825", "Títulos sin reparto declarado"],
                    ["country", "831", "País no informado"],
                    ["date_added", "10", "Fecha no interpretable; se deja vacía"],
                    ["rating", "4", "Clasificación ausente"],
                    ["duration", "3", "Películas sin duración en el origen"],
                    ["duration_min", "2 679", "3 películas sin dato + 2 676 series (por diseño)"],
                ],
                "anchos": [1.6, 1.2, 4.2],
                "numericas": [1],
            },
        ),
        (
            "small",
            "Documento generado automáticamente con `python docs/generar_informe.py` a partir de los "
            "resultados reales del pipeline. Las evidencias 1 a 7 son capturas que el equipo adjunta en "
            "la versión final del PDF.",
        ),
    ]


# --------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------
def a_markdown(bloques: list[tuple]) -> str:
    salida: list[str] = []
    for bloque in bloques:
        tipo = bloque[0]
        if tipo == "portada":
            salida += [
                "# Análisis del catálogo de Netflix",
                "",
                "## Limpieza con Pandas, conteo con Hadoop MapReduce y verificación con Spark en Databricks",
                "",
                "**Informe · Evaluación Segundo Momento**",
                "",
                "| | |",
                "|---|---|",
                "| **Asignatura** | Tecnologías Emergentes I |",
                "| **Equipo** | Elsner |",
                "| **Integrantes** | Jhael Arguedas · Carlos Conde · Bryan Mamani |",
                "| **Fecha de exposición** | lunes 16 de noviembre de 2026 |",
                "| **Conjunto de datos** | Netflix Movies and TV Shows (Kaggle) · 8 807 títulos |",
                "| **Proyecto** | `proyecto_netflix_elsner` |",
                "",
                "> Documento generado a partir de los resultados reales del pipeline. Las cifras "
                "provienen de `datos/resultados/` y del notebook `03_analisis_netflix.ipynb`.",
                "",
            ]
        elif tipo == "h1":
            salida += [f"## {bloque[1]}", ""]
        elif tipo == "h2":
            salida += [f"### {bloque[1]}", ""]
        elif tipo == "p":
            salida += [bloque[1], ""]
        elif tipo == "small":
            salida += [f"*{bloque[1]}*", ""]
        elif tipo == "bullets":
            salida += [f"- {item}" for item in bloque[1]] + [""]
        elif tipo == "numbers":
            salida += [f"{indice}. {item}" for indice, item in enumerate(bloque[1], start=1)] + [""]
        elif tipo == "quote":
            salida += [f"> {bloque[1]}", ""]
        elif tipo == "code":
            salida += ["```text", bloque[1], "```", ""]
        elif tipo == "figure":
            nombre, leyenda = bloque[1], bloque[2]
            salida += [f"![{leyenda}](figuras/{nombre})", "", f"*{leyenda}*", ""]
        elif tipo == "table":
            datos = bloque[1]
            if datos.get("titulo"):
                salida += [f"**{datos['titulo']}**", ""]
            headers = datos["headers"]
            salida += ["| " + " | ".join(headers) + " |"]
            salida += ["|" + "|".join("---" for _ in headers) + "|"]
            for fila in datos["filas"]:
                salida += ["| " + " | ".join(fila) + " |"]
            salida += [""]
        elif tipo == "evidence":
            numero, titulo, texto = bloque[1], bloque[2], bloque[3]
            salida += [
                f"> **Evidencia {numero} · {titulo}.** {texto}",
                "",
            ]
        elif tipo == "pagebreak":
            salida += ["---", ""]
    return "\n".join(salida).replace("\n\n\n", "\n\n")


# --------------------------------------------------------------------------
# PDF
# --------------------------------------------------------------------------
def _inline(texto: str) -> str:
    texto = texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    texto = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)
    texto = re.sub(r"`(.+?)`", r'<font face="Courier" color="#8a2c33">\1</font>', texto)
    texto = texto.replace("«", '"').replace("»", '"')
    return texto


def _estilos() -> dict[str, ParagraphStyle]:
    return {
        "h1": ParagraphStyle(
            "h1",
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=TINTA,
            spaceBefore=4,
            spaceAfter=10,
            borderPadding=(0, 0, 6, 0),
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=ROJO,
            spaceBefore=12,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "p": ParagraphStyle(
            "p",
            fontName="Helvetica",
            fontSize=9.8,
            leading=15,
            textColor=TINTA,
            alignment=TA_JUSTIFY,
            spaceAfter=7,
        ),
        "pequeno": ParagraphStyle(
            "pequeno",
            fontName="Helvetica-Oblique",
            fontSize=8.2,
            leading=11.5,
            textColor=GRIS,
            spaceAfter=8,
        ),
        "lista": ParagraphStyle(
            "lista",
            fontName="Helvetica",
            fontSize=9.6,
            leading=14,
            textColor=TINTA,
            alignment=TA_JUSTIFY,
            leftIndent=12,
            bulletIndent=2,
            spaceAfter=4,
        ),
        "numero": ParagraphStyle(
            "numero",
            fontName="Helvetica",
            fontSize=9.6,
            leading=14,
            textColor=TINTA,
            alignment=TA_JUSTIFY,
            leftIndent=16,
            spaceAfter=5,
        ),
        "tabla_celda": ParagraphStyle(
            "tabla_celda",
            fontName="Helvetica",
            fontSize=8.4,
            leading=11,
            textColor=TINTA,
        ),
        "tabla_cabecera": ParagraphStyle(
            "tabla_cabecera",
            fontName="Helvetica-Bold",
            fontSize=8.3,
            leading=10.5,
            textColor=colors.white,
        ),
        "tabla_num": ParagraphStyle(
            "tabla_num",
            fontName="Helvetica",
            fontSize=8.4,
            leading=11,
            textColor=TINTA,
            alignment=TA_RIGHT,
        ),
        "tabla_num_cab": ParagraphStyle(
            "tabla_num_cab",
            fontName="Helvetica-Bold",
            fontSize=8.3,
            leading=10.5,
            textColor=colors.white,
            alignment=TA_RIGHT,
        ),
        "tabla_centro": ParagraphStyle(
            "tabla_centro",
            fontName="Helvetica",
            fontSize=8.4,
            leading=11,
            textColor=TINTA,
            alignment=TA_CENTER,
        ),
        "tabla_centro_cab": ParagraphStyle(
            "tabla_centro_cab",
            fontName="Helvetica-Bold",
            fontSize=8.3,
            leading=10.5,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        "leyenda": ParagraphStyle(
            "leyenda",
            fontName="Helvetica-Oblique",
            fontSize=8.2,
            leading=11,
            textColor=GRIS,
            alignment=TA_CENTER,
            spaceBefore=3,
            spaceAfter=10,
        ),
        "codigo": ParagraphStyle(
            "codigo",
            fontName="Courier",
            fontSize=7.6,
            leading=10,
            textColor=colors.HexColor("#1e293b"),
        ),
        "cita": ParagraphStyle(
            "cita",
            fontName="Helvetica",
            fontSize=9.4,
            leading=14,
            textColor=TINTA,
            alignment=TA_JUSTIFY,
            leftIndent=10,
            rightIndent=10,
            spaceBefore=2,
            spaceAfter=2,
        ),
        "evidencia_titulo": ParagraphStyle(
            "evidencia_titulo",
            fontName="Helvetica-Bold",
            fontSize=8.6,
            leading=11,
            textColor=ROJO,
        ),
        "evidencia_texto": ParagraphStyle(
            "evidencia_texto",
            fontName="Helvetica",
            fontSize=8.2,
            leading=11,
            textColor=GRIS,
        ),
        "portada_titulo": ParagraphStyle(
            "portada_titulo",
            fontName="Helvetica-Bold",
            fontSize=29,
            leading=33,
            textColor=TINTA,
            alignment=TA_LEFT,
        ),
        "portada_sub": ParagraphStyle(
            "portada_sub",
            fontName="Helvetica",
            fontSize=12.5,
            leading=18,
            textColor=GRIS,
            alignment=TA_LEFT,
        ),
        "portada_meta": ParagraphStyle(
            "portada_meta",
            fontName="Helvetica",
            fontSize=9.4,
            leading=13.5,
            textColor=TINTA,
        ),
        "portada_meta_b": ParagraphStyle(
            "portada_meta_b",
            fontName="Helvetica-Bold",
            fontSize=9.4,
            leading=13.5,
            textColor=TINTA,
        ),
    }


def _tabla(datos: dict, estilos: dict) -> Table:
    headers = datos["headers"]
    filas = datos["filas"]
    anchos = datos["anchos"]
    total = sum(anchos)
    columnas = [ANCHO_CONTENIDO * valor / total for valor in anchos]
    numericas = set(datos.get("numericas", []))
    centradas = set(datos.get("centradas", []))

    cabecera = []
    for indice, texto in enumerate(headers):
        if indice in numericas:
            estilo = estilos["tabla_num_cab"]
        elif indice in centradas:
            estilo = estilos["tabla_centro_cab"]
        else:
            estilo = estilos["tabla_cabecera"]
        cabecera.append(Paragraph(_inline(texto), estilo))

    cuerpo = [cabecera]
    for fila in filas:
        celdas = []
        for indice, valor in enumerate(fila):
            if indice in numericas:
                estilo = estilos["tabla_num"]
            elif indice in centradas:
                estilo = estilos["tabla_centro"]
            else:
                estilo = estilos["tabla_celda"]
            celdas.append(Paragraph(_inline(str(valor)), estilo))
        cuerpo.append(celdas)

    tabla = Table(cuerpo, colWidths=columnas, repeatRows=1, hAlign="LEFT")
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), TINTA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, BORDE),
    ]
    for fila in range(1, len(cuerpo)):
        if fila % 2 == 0:
            estilo.append(("BACKGROUND", (0, fila), (-1, fila), FONDO))
    tabla.setStyle(TableStyle(estilo))
    return tabla


def _evidencia(numero: int, titulo: str, texto: str, estilos: dict) -> Table:
    imagen = None
    for extension in ("png", "jpg", "jpeg"):
        ruta = EVIDENCIAS / f"evidencia_{numero}.{extension}"
        if ruta.exists():
            with PILImage.open(ruta) as archivo:
                ancho_px, alto_px = archivo.size
            ancho = ANCHO_CONTENIDO - 20
            alto = ancho * alto_px / ancho_px
            if alto > 78 * mm:
                alto = 78 * mm
                ancho = alto * ancho_px / alto_px
            imagen = Image(str(ruta), width=ancho, height=alto)
            imagen.hAlign = "CENTER"
            break

    contenido = [
        Paragraph(f"EVIDENCIA {numero} · {titulo.upper()}", estilos["evidencia_titulo"]),
        Spacer(1, 2),
        Paragraph(_inline(texto), estilos["evidencia_texto"]),
        Spacer(1, 4),
    ]
    if imagen is not None:
        contenido.extend([imagen, Spacer(1, 2)])
    else:
        contenido.append(
            Paragraph(
                '<font color="#8693ad" size="7.2">[ Insertar captura de pantalla ]</font>',
                estilos["evidencia_texto"],
            )
        )
    caja = Table([[contenido]], colWidths=[ANCHO_CONTENIDO], hAlign="LEFT")
    caja.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#f0c9cc")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fdf2f3")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return caja


def _portada(historia: list, estilos: dict) -> None:
    historia.append(Spacer(1, 28 * mm))
    historia.append(Paragraph("Análisis del catálogo de Netflix", estilos["portada_titulo"]))
    historia.append(Spacer(1, 4 * mm))
    historia.append(
        Paragraph(
            "Limpieza con Pandas, conteo con Hadoop MapReduce<br/>y verificación con Spark en Databricks",
            estilos["portada_sub"],
        )
    )
    historia.append(Spacer(1, 7 * mm))

    linea = Table([[""]], colWidths=[52 * mm], rowHeights=[1.6 * mm])
    linea.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ROJO)]))
    historia.append(linea)
    historia.append(Spacer(1, 9 * mm))

    filas = [
        ("Asignatura", "Tecnologías Emergentes I"),
        ("Evaluación", "Segundo Momento"),
        ("Equipo", "Elsner"),
        ("Integrantes", "Jhael Arguedas · Carlos Conde · Bryan Mamani"),
        ("Fecha de exposición", "lunes 16 de noviembre de 2026"),
        ("Conjunto de datos", "Netflix Movies and TV Shows · 8 807 títulos"),
        ("Documento", "Informe_Netflix_Elsner.pdf"),
    ]
    tabla = Table(
        [
            [Paragraph(etiqueta.upper(), estilos["portada_meta_b"]), Paragraph(valor, estilos["portada_meta"])]
            for etiqueta, valor in filas
        ],
        colWidths=[42 * mm, 108 * mm],
        hAlign="LEFT",
    )
    tabla.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LINEBELOW", (0, 0), (-1, -2), 0.4, BORDE),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
            ]
        )
    )
    historia.append(tabla)

    historia.append(Spacer(1, 22 * mm))
    nota = Table(
        [
            [
                Paragraph(
                    "Documento generado a partir de los resultados reales del pipeline. Las cifras "
                    "provienen de <font face='Courier'>datos/resultados/</font> y del notebook "
                    "<font face='Courier'>03_analisis_netflix.ipynb</font>.",
                    ParagraphStyle(
                        "nota",
                        fontName="Helvetica-Oblique",
                        fontSize=8.4,
                        leading=12,
                        textColor=GRIS,
                    ),
                )
            ]
        ],
        colWidths=[150 * mm],
    )
    nota.setStyle(
        TableStyle(
            [
                ("LINEBEFORE", (0, 0), (0, -1), 2.2, ROJO),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    historia.append(nota)


def _decorar_portada(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(ROJO)
    canvas.rect(0, 252 * mm, 210 * mm, 45 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 31)
    canvas.drawString(20 * mm, 274 * mm, "NF")
    canvas.setFont("Helvetica-Bold", 10.5)
    canvas.drawString(20 * mm, 264 * mm, "OBSERVATORIO NETFLIX")
    canvas.setFont("Helvetica", 8.6)
    canvas.drawString(20 * mm, 258 * mm, "Big Data · Tecnologías Emergentes I")

    canvas.setFillColor(TINTA)
    canvas.rect(0, 0, 210 * mm, 12 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(20 * mm, 4.6 * mm, "Evaluación Segundo Momento · 2026")
    canvas.drawRightString(190 * mm, 4.6 * mm, "Equipo Elsner")
    canvas.restoreState()


def _decorar_cuerpo(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(BORDE)
    canvas.setLineWidth(0.6)
    canvas.line(20 * mm, 16.5 * mm, 190 * mm, 16.5 * mm)
    canvas.setFont("Helvetica", 7.4)
    canvas.setFillColor(GRIS_CLARO)
    canvas.drawString(
        20 * mm, 11.8 * mm, "Observatorio Netflix · Equipo Elsner · Tecnologías Emergentes I"
    )
    canvas.drawRightString(190 * mm, 11.8 * mm, f"Página {doc.page - 1}")
    canvas.setFont("Helvetica", 7.2)
    canvas.drawString(20 * mm, 287 * mm, "INFORME · ANÁLISIS DEL CATÁLOGO DE NETFLIX")
    canvas.setStrokeColor(ROJO)
    canvas.setLineWidth(0.8)
    canvas.line(20 * mm, 284.5 * mm, 46 * mm, 284.5 * mm)
    canvas.restoreState()


def a_pdf(bloques: list[tuple], destino: Path) -> None:
    estilos = _estilos()
    document = BaseDocTemplate(
        str(destino),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=22 * mm,
        title="Análisis del catálogo de Netflix · Equipo Elsner",
        author="Jhael Arguedas · Carlos Conde · Bryan Mamani",
        subject="Evaluación Segundo Momento · Tecnologías Emergentes I",
    )
    marco = Frame(
        20 * mm,
        22 * mm,
        ANCHO_CONTENIDO,
        243 * mm,
        id="cuerpo",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    document.addPageTemplates(
        [
            PageTemplate(id="portada", frames=[marco], onPage=_decorar_portada),
            PageTemplate(id="cuerpo", frames=[marco], onPage=_decorar_cuerpo),
        ]
    )

    historia: list = []
    for bloque in bloques:
        tipo = bloque[0]
        if tipo == "portada":
            _portada(historia, estilos)
        elif tipo == "pagebreak":
            historia.append(PageBreak())
        elif tipo == "h1":
            if historia and not isinstance(historia[-1], PageBreak):
                historia.append(Spacer(1, 4 * mm))
            historia.append(Paragraph(_inline(bloque[1]), estilos["h1"]))
            historia.append(
                Table([[""]], colWidths=[ANCHO_CONTENIDO], rowHeights=[0.9 * mm],
                      style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), ROJO)]))
            )
            historia.append(Spacer(1, 5 * mm))
        elif tipo == "h2":
            historia.append(Paragraph(_inline(bloque[1]), estilos["h2"]))
        elif tipo == "p":
            historia.append(Paragraph(_inline(bloque[1]), estilos["p"]))
        elif tipo == "small":
            historia.append(Paragraph(_inline(bloque[1]), estilos["pequeno"]))
        elif tipo == "bullets":
            for item in bloque[1]:
                historia.append(
                    Paragraph(_inline(item), estilos["lista"], bulletText="•")
                )
            historia.append(Spacer(1, 3 * mm))
        elif tipo == "numbers":
            for indice, item in enumerate(bloque[1], start=1):
                historia.append(
                    Paragraph(_inline(item), estilos["numero"], bulletText=f"{indice}.")
                )
            historia.append(Spacer(1, 3 * mm))
        elif tipo == "quote":
            caja = Table([[Paragraph(_inline(bloque[1]), estilos["cita"])]], colWidths=[ANCHO_CONTENIDO])
            caja.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7f9fc")),
                        ("LINEBEFORE", (0, 0), (0, -1), 3, ROJO),
                        ("LEFTPADDING", (0, 0), (-1, -1), 12),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                        ("TOPPADDING", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ]
                )
            )
            historia.append(caja)
            historia.append(Spacer(1, 6 * mm))
        elif tipo == "code":
            caja = Table(
                [[XPreformatted(bloque[1], estilos["codigo"])]],
                colWidths=[ANCHO_CONTENIDO],
            )
            caja.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f6fa")),
                        ("BOX", (0, 0), (-1, -1), 0.5, BORDE),
                        ("LEFTPADDING", (0, 0), (-1, -1), 9),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                        ("TOPPADDING", (0, 0), (-1, -1), 7),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ]
                )
            )
            grupo_codigo: list = [caja]
            if (
                historia
                and isinstance(historia[-1], Paragraph)
                and getattr(historia[-1].style, "name", "") == "h2"
            ):
                grupo_codigo.insert(0, historia.pop())
            historia.append(KeepTogether(grupo_codigo))
            historia.append(Spacer(1, 5 * mm))
        elif tipo == "figure":
            nombre, leyenda, ancho_mm = bloque[1], bloque[2], bloque[3]
            ruta = FIGURAS / nombre
            with PILImage.open(ruta) as imagen:
                ancho_px, alto_px = imagen.size
            ancho = ancho_mm * mm
            alto = ancho * alto_px / ancho_px
            figura = Image(str(ruta), width=ancho, height=alto)
            figura.hAlign = "CENTER"
            historia.append(KeepTogether([figura, Paragraph(leyenda, estilos["leyenda"])]))
            historia.append(Spacer(1, 2 * mm))
        elif tipo == "table":
            datos = bloque[1]
            partes: list = []
            if datos.get("titulo"):
                partes.append(
                    Paragraph(
                        f"<b>{datos['titulo']}</b>",
                        ParagraphStyle(
                            "titulo_tabla",
                            fontName="Helvetica-Bold",
                            fontSize=8.8,
                            leading=11.5,
                            textColor=TINTA,
                            spaceAfter=3,
                        ),
                    )
                )
            partes.append(_tabla(datos, estilos))
            grupo: list = list(partes)
            if (
                historia
                and isinstance(historia[-1], Paragraph)
                and getattr(historia[-1].style, "name", "") == "h2"
            ):
                grupo.insert(0, historia.pop())
            historia.append(KeepTogether(grupo))
            historia.append(Spacer(1, 7 * mm))
        elif tipo == "evidence":
            historia.append(_evidencia(bloque[1], bloque[2], bloque[3], estilos))
            historia.append(Spacer(1, 5 * mm))

    document.build(historia)


def main() -> int:
    bloques = contenido()

    markdown = a_markdown(bloques)
    destino_md = DOCS / "Informe_Netflix_Elsner.md"
    destino_md.write_text(markdown, encoding="utf-8")

    destino_pdf = DOCS / "Informe_Netflix_Elsner.pdf"
    a_pdf(bloques, destino_pdf)

    copia = RAIZ / "frontend" / "assets" / "Informe_Netflix_Elsner.pdf"
    copia.parent.mkdir(parents=True, exist_ok=True)
    copia.write_bytes(destino_pdf.read_bytes())

    palabras = len(re.findall(r"\w+", markdown))
    print(f"Informe Markdown: {destino_md.relative_to(RAIZ)} ({palabras} palabras)")
    print(f"Informe PDF     : {destino_pdf.relative_to(RAIZ)} ({destino_pdf.stat().st_size / 1024:.1f} KB)")
    print(f"Copia frontend  : {copia.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
