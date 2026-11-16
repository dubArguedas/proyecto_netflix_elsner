# Databricks notebook source
# MAGIC %md
# MAGIC # Reto 3 · Análisis del catálogo de Netflix con SQL y PySpark
# MAGIC
# MAGIC **Proyecto:** Observatorio Netflix · Evaluación Segundo Momento · Equipo Elsner  
# MAGIC **Materia:** Tecnologías Emergentes I  
# MAGIC **Integrantes:** Jhael Arguedas · Carlos Conde · Bryan Mamani
# MAGIC
# MAGIC Este notebook resuelve los tres análisis del Reto 3 **dos veces**: una celda SQL y una celda
# MAGIC PySpark por análisis. Después compara las salidas completas (Tabla 3), contrasta los diez
# MAGIC primeros actores contra la salida de Hadoop (Tabla 4) y verifica los 36 439 actores del
# MAGIC catálogo (Tabla 5).
# MAGIC
# MAGIC | Elemento | Valor esperado |
# MAGIC |---|---|
# MAGIC | Registros de `netflix_clean` | 8 807 |
# MAGIC | Películas / series | 6 131 / 2 676 |
# MAGIC | Actores distintos | 36 439 |
# MAGIC | Países distintos (películas con duración) | 117 |
# MAGIC | Pares actor–show_id del mapper | 64 126 |
# MAGIC
# MAGIC **Requisitos:** un clúster con Databricks Runtime 15.4 LTS o superior, un esquema de Unity
# MAGIC Catalog y los dos CSV cargados en un volumen. La guía paso a paso está en
# MAGIC `databricks/GUIA_DATABRICKS.md`.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Paso 0 · Parámetros del entorno
# MAGIC
# MAGIC Los nombres se controlan con widgets para que el notebook funcione en cualquier workspace.
# MAGIC Si su catálogo no es `workspace`, cámbielo en la barra superior del notebook antes de ejecutar.
# MAGIC En una cuenta gratuita o Community Edition el catálogo suele ser `workspace` o `hive_metastore`.

# COMMAND ----------

dbutils.widgets.removeAll()

dbutils.widgets.text("catalogo", "workspace", "Catálogo")
dbutils.widgets.text("esquema", "netflix", "Esquema")
dbutils.widgets.text("volumen", "datos", "Volumen")

CATALOGO = dbutils.widgets.get("catalogo").strip()
ESQUEMA = dbutils.widgets.get("esquema").strip()
VOLUMEN = dbutils.widgets.get("volumen").strip()

RUTA_VOLUMEN = f"/Volumes/{CATALOGO}/{ESQUEMA}/{VOLUMEN}"
RUTA_ENTRADA_LIMPIA = f"{RUTA_VOLUMEN}/netflix_clean.csv"
RUTA_ENTRADA_ACTORES = f"{RUTA_VOLUMEN}/mapreduce_actores.csv"
RUTA_SALIDAS = f"{RUTA_VOLUMEN}/salidas"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{CATALOGO}`.`{ESQUEMA}`")
spark.sql(f"USE CATALOG `{CATALOGO}`")
spark.sql(f"USE SCHEMA `{ESQUEMA}`")

print(f"Catálogo : {CATALOGO}")
print(f"Esquema  : {ESQUEMA}")
print(f"Volumen  : {RUTA_VOLUMEN}")
print(f"Spark    : {spark.version}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Paso 1 · Cargar los CSV del volumen y crear las tablas
# MAGIC
# MAGIC En **Catalog → Create schema** cree el esquema `netflix`; dentro, en **Create volume**, cree el
# MAGIC volumen `datos` de tipo *Managed volume*. Suba allí estos dos archivos:
# MAGIC
# MAGIC 1. `datos/clean/netflix_clean.csv` (salida del Reto 1, 8 807 filas y 13 columnas).
# MAGIC 2. `datos/resultados/mapreduce_actores.csv` (salida del Reto 2, 36 439 filas).
# MAGIC
# MAGIC La lectura usa `multiLine = true` porque la columna `description` conserva comas y comillas
# MAGIC entrecomilladas. Las cadenas vacías se interpretan como nulos, igual que en el archivo limpio.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql import Window

# --- Tabla base del Reto 1 ---------------------------------------------------
df_clean = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .option("multiLine", True)
    .option("encoding", "UTF-8")
    .csv(RUTA_ENTRADA_LIMPIA)
)

(df_clean.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable("netflix_clean"))

# --- Salida del Reto 2 -------------------------------------------------------
mapreduce_actores = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv(RUTA_ENTRADA_ACTORES)
)

(mapreduce_actores.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable("mapreduce_actores"))

# Se recargan desde el metastore para trabajar con las tablas Delta reales.
netflix_clean = spark.table("netflix_clean")
mapreduce_actores = spark.table("mapreduce_actores")

print("Tablas creadas:")
print(f"  netflix_clean      -> {netflix_clean.count():>6} filas, {len(netflix_clean.columns)} columnas")
print(f"  mapreduce_actores  -> {mapreduce_actores.count():>6} filas")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Comprobación de la carga
# MAGIC
# MAGIC Debe coincidir con la Tabla 1 del informe: 8 807 registros, 8 807 `show_id` distintos y
# MAGIC 36 439 actores en la salida de Hadoop.

# COMMAND ----------

display(
    netflix_clean.agg(
        F.count("*").alias("registros"),
        F.countDistinct("show_id").alias("show_id_distintos"),
        F.sum(F.when(F.col("type") == "Movie", 1).otherwise(0)).alias("peliculas"),
        F.sum(F.when(F.col("type") == "TV Show", 1).otherwise(0)).alias("series"),
        F.sum(F.when(F.col("duration_min").isNotNull(), 1).otherwise(0)).alias("con_duracion_min"),
    )
)

display(netflix_clean.limit(5))
display(mapreduce_actores.orderBy(F.desc("cantidad_titulos")).limit(5))

assert netflix_clean.count() == 8807, "netflix_clean no tiene 8 807 registros"
assert netflix_clean.select("show_id").distinct().count() == 8807, "Hay show_id repetidos"
assert mapreduce_actores.count() == 36439, "mapreduce_actores no tiene 36 439 actores"
print("Validaciones de carga: OK")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Análisis A · Cantidad de películas y series
# MAGIC
# MAGIC Se clasifica cada título con `CASE` (los valores desconocidos se conservan como
# MAGIC «Sin clasificación» y lo que no es Movie/TV Show como «Otro») y se cuentan `show_id` distintos.
# MAGIC
# MAGIC **SQL** — la consulta se guarda como vista temporal para poder compararla después.

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TEMP VIEW sql_peliculas_y_series AS
# MAGIC SELECT tipo,
# MAGIC        COUNT(DISTINCT show_id) AS cantidad_titulos
# MAGIC FROM (
# MAGIC   SELECT show_id,
# MAGIC          CASE
# MAGIC            WHEN `type` IS NULL THEN 'Sin clasificación'
# MAGIC            WHEN `type` IN ('Movie', 'TV Show') THEN `type`
# MAGIC            ELSE 'Otro'
# MAGIC          END AS tipo
# MAGIC   FROM netflix_clean
# MAGIC )
# MAGIC GROUP BY tipo
# MAGIC ORDER BY tipo;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM sql_peliculas_y_series;

# COMMAND ----------

# MAGIC %md
# MAGIC **PySpark** — la misma regla con `when/otherwise`, sin mirar el resultado de SQL.

# COMMAND ----------

pyspark_peliculas_y_series = (
    netflix_clean
    .withColumn(
        "tipo",
        F.when(F.col("type").isNull(), "Sin clasificación")
         .when(F.col("type").isin("Movie", "TV Show"), F.col("type"))
         .otherwise("Otro"),
    )
    .groupBy("tipo")
    .agg(F.countDistinct("show_id").alias("cantidad_titulos"))
    .orderBy("tipo")
)

display(pyspark_peliculas_y_series)

(pyspark_peliculas_y_series.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable("resultado_a_tipos"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Análisis B · Cantidad de títulos distintos por actor
# MAGIC
# MAGIC `cast` es multivaluado y además es una palabra reservada de Spark SQL: siempre va entre
# MAGIC backticks. Se separa por comas, se recorta cada nombre, se descartan los vacíos y se eliminan
# MAGIC los pares repetidos `(show_id, actor)` antes de contar.
# MAGIC
# MAGIC **SQL**

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TEMP VIEW sql_titulos_por_actor AS
# MAGIC WITH actores AS (
# MAGIC   SELECT DISTINCT show_id, trim(actor) AS actor
# MAGIC   FROM netflix_clean
# MAGIC   LATERAL VIEW explode(split(`cast`, ',')) t AS actor
# MAGIC   WHERE `cast` IS NOT NULL
# MAGIC )
# MAGIC SELECT actor,
# MAGIC        COUNT(DISTINCT show_id) AS cantidad_titulos
# MAGIC FROM actores
# MAGIC WHERE actor <> ''
# MAGIC GROUP BY actor
# MAGIC ORDER BY cantidad_titulos DESC, actor ASC;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM sql_titulos_por_actor LIMIT 10;

# COMMAND ----------

# MAGIC %md
# MAGIC **PySpark**

# COMMAND ----------

pyspark_titulos_por_actor = (
    netflix_clean
    .where(F.col("cast").isNotNull())
    .select(
        "show_id",
        F.explode(F.split(F.col("cast"), r",\s*")).alias("actor"),
    )
    .withColumn("actor", F.trim("actor"))
    .where(F.col("actor") != "")
    .dropDuplicates(["show_id", "actor"])
    .groupBy("actor")
    .agg(F.countDistinct("show_id").alias("cantidad_titulos"))
    .orderBy(F.desc("cantidad_titulos"), F.asc("actor"))
)

display(pyspark_titulos_por_actor.limit(10))
print(f"Actores distintos: {pyspark_titulos_por_actor.count()}")

(pyspark_titulos_por_actor.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable("resultado_b_actores"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Análisis C · Duración promedio de películas por país
# MAGIC
# MAGIC Solo se consideran películas (`type = 'Movie'`) con `duration_min` numérico y mayor que cero.
# MAGIC El país también es multivaluado: una película cuenta para cada país que la acompaña, pero una
# MAGIC sola vez por país. El promedio se redondea a dos decimales.
# MAGIC
# MAGIC **SQL**

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TEMP VIEW sql_duracion_por_pais AS
# MAGIC WITH peliculas AS (
# MAGIC   SELECT DISTINCT show_id, duration_min, trim(pais) AS pais
# MAGIC   FROM netflix_clean
# MAGIC   LATERAL VIEW explode(split(country, ',')) p AS pais
# MAGIC   WHERE `type` = 'Movie'
# MAGIC     AND duration_min IS NOT NULL
# MAGIC     AND duration_min > 0
# MAGIC     AND country IS NOT NULL
# MAGIC )
# MAGIC SELECT pais,
# MAGIC        COUNT(DISTINCT show_id) AS cantidad_peliculas,
# MAGIC        ROUND(AVG(duration_min), 2) AS duracion_promedio_min
# MAGIC FROM peliculas
# MAGIC WHERE pais <> ''
# MAGIC GROUP BY pais
# MAGIC ORDER BY cantidad_peliculas DESC, pais ASC;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM sql_duracion_por_pais LIMIT 10;

# COMMAND ----------

# MAGIC %md
# MAGIC **PySpark**

# COMMAND ----------

pyspark_duracion_por_pais = (
    netflix_clean
    .where(
        (F.col("type") == "Movie")
        & (F.col("duration_min").isNotNull())
        & (F.col("duration_min") > 0)
        & F.col("country").isNotNull()
    )
    .select(
        "show_id",
        "duration_min",
        F.explode(F.split(F.col("country"), r",\s*")).alias("pais"),
    )
    .withColumn("pais", F.trim("pais"))
    .where(F.col("pais") != "")
    .dropDuplicates(["show_id", "pais"])
    .groupBy("pais")
    .agg(
        F.countDistinct("show_id").alias("cantidad_peliculas"),
        F.round(F.avg("duration_min"), 2).alias("duracion_promedio_min"),
    )
    .orderBy(F.desc("cantidad_peliculas"), F.asc("pais"))
)

display(pyspark_duracion_por_pais.limit(10))
print(f"Países distintos: {pyspark_duracion_por_pais.count()}")

(pyspark_duracion_por_pais.write
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable("resultado_c_paises"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Tabla 3 · Verificación de SQL contra PySpark
# MAGIC
# MAGIC Cada salida se une con la otra por su clave (`tipo`, `actor` o `pais`) mediante un
# MAGIC **full outer join**. Luego se clasifica cada fila en cuatro estados:
# MAGIC
# MAGIC | Estado | Significado |
# MAGIC |---|---|
# MAGIC | `igual` | La clave existe en ambas salidas y el valor coincide |
# MAGIC | `diferente` | La clave existe en ambas, pero el valor no coincide |
# MAGIC | `solo_izquierda` | La clave solo aparece en la salida SQL |
# MAGIC | `solo_derecha` | La clave solo aparece en la salida PySpark |
# MAGIC
# MAGIC En los promedios se admite una tolerancia de 0,01 minutos para absorber el redondeo.

# COMMAND ----------

def comparar_salidas(izquierda, derecha, clave, valor, tolerancia=0.0):
    """Compara dos salidas por su clave y devuelve el resumen de la Tabla 3."""
    a = izquierda.select(
        F.col(clave).cast("string").alias("clave"),
        F.col(valor).cast("double").alias("valor_sql"),
    )
    b = derecha.select(
        F.col(clave).cast("string").alias("clave"),
        F.col(valor).cast("double").alias("valor_pyspark"),
    )

    unido = a.join(b, "clave", "full_outer")
    en_ambas = F.col("valor_sql").isNotNull() & F.col("valor_pyspark").isNotNull()

    if tolerancia > 0:
        coinciden = en_ambas & (F.abs(F.col("valor_sql") - F.col("valor_pyspark")) <= tolerancia)
    else:
        coinciden = en_ambas & (F.col("valor_sql") == F.col("valor_pyspark"))

    con_estado = unido.withColumn(
        "estado",
        F.when(F.col("valor_sql").isNull(), "solo_derecha")
         .when(F.col("valor_pyspark").isNull(), "solo_izquierda")
         .when(coinciden, "igual")
         .otherwise("diferente"),
    )

    conteo = {fila["estado"]: fila["cantidad"] for fila in con_estado.groupBy("estado").count().collect()}
    iguales = conteo.get("igual", 0)
    diferentes = conteo.get("diferente", 0)
    solo_sql = conteo.get("solo_izquierda", 0)
    solo_pyspark = conteo.get("solo_derecha", 0)

    return {
        "filas_sql": izquierda.count(),
        "filas_pyspark": derecha.count(),
        "filas_comparadas": unido.count(),
        "filas_con_valores_diferentes": diferentes,
        "filas_en_una_sola_salida": solo_sql + solo_pyspark,
        "filas_en_ambas_iguales": iguales,
        "coinciden_completamente": diferentes == 0 and solo_sql == 0 and solo_pyspark == 0,
    }


sql_tipos = spark.table("sql_peliculas_y_series")
sql_actores = spark.table("sql_titulos_por_actor")
sql_paises = spark.table("sql_duracion_por_pais")

comparaciones = {
    "peliculas_y_series": comparar_salidas(
        sql_tipos, pyspark_peliculas_y_series, "tipo", "cantidad_titulos"
    ),
    "titulos_por_actor": comparar_salidas(
        sql_actores, pyspark_titulos_por_actor, "actor", "cantidad_titulos"
    ),
    "duracion_por_pais": comparar_salidas(
        sql_paises, pyspark_duracion_por_pais, "pais", "duracion_promedio_min", tolerancia=0.01
    ),
}

filas_tabla3 = [(nombre, datos) for nombre, datos in comparaciones.items()]
tabla3 = spark.createDataFrame(
    [
        (
            nombre,
            datos["filas_sql"],
            datos["filas_pyspark"],
            datos["filas_con_valores_diferentes"],
            datos["filas_en_una_sola_salida"],
            datos["coinciden_completamente"],
        )
        for nombre, datos in filas_tabla3
    ],
    "analisis string, filas_sql int, filas_pyspark int, "
    "filas_con_valores_diferentes int, filas_en_una_sola_salida int, coinciden_completamente boolean",
)

display(tabla3)

assert all(datos["coinciden_completamente"] for datos in comparaciones.values()), (
    "SQL y PySpark no coinciden: revise las diferencias antes de continuar"
)
print("Tabla 3: las tres salidas coinciden completamente")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Tabla 4 · Diez primeros actores: MapReduce contra Spark
# MAGIC
# MAGIC Se toma el top 10 de Spark (orden: cantidad descendente y nombre ascendente) y se busca la
# MAGIC misma persona en la salida de Hadoop. `diferencia = mapreduce - spark`, como pide el enunciado.

# COMMAND ----------

top10_spark = (
    pyspark_titulos_por_actor
    .orderBy(F.desc("cantidad_titulos"), F.asc("actor"))
    .limit(10)
)

totales_mapreduce = {
    fila["actor"]: fila["cantidad_titulos"] for fila in mapreduce_actores.collect()
}

filas_tabla4 = []
for posicion, fila in enumerate(top10_spark.collect(), start=1):
    cantidad_mr = int(totales_mapreduce.get(fila["actor"], 0))
    cantidad_spark = int(fila["cantidad_titulos"])
    filas_tabla4.append(
        (posicion, fila["actor"], cantidad_mr, cantidad_spark, cantidad_mr - cantidad_spark)
    )

tabla4 = spark.createDataFrame(
    filas_tabla4,
    "posicion int, actor string, mapreduce int, spark int, diferencia int",
)

display(tabla4)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Tabla 5 · Verificación completa de MapReduce contra Spark
# MAGIC
# MAGIC Se comparan los 36 439 actores de ambas salidas. Cualquier diferencia obligaría a revisar el
# MAGIC mapper, el reducer o la lectura del CSV.

# COMMAND ----------

resumen_mapreduce = comparar_salidas(
    mapreduce_actores, pyspark_titulos_por_actor, "actor", "cantidad_titulos"
)

tabla5 = spark.createDataFrame(
    [
        ("actores_mapreduce", resumen_mapreduce["filas_sql"]),
        ("actores_spark", resumen_mapreduce["filas_pyspark"]),
        ("ambas_iguales", resumen_mapreduce["filas_en_ambas_iguales"]),
        ("ambas_diferentes", resumen_mapreduce["filas_con_valores_diferentes"]),
        ("solo_mapreduce", resumen_mapreduce["filas_sql"] - resumen_mapreduce["filas_en_ambas_iguales"] - resumen_mapreduce["filas_con_valores_diferentes"]),
        ("solo_spark", resumen_mapreduce["filas_pyspark"] - resumen_mapreduce["filas_en_ambas_iguales"] - resumen_mapreduce["filas_con_valores_diferentes"]),
    ],
    "indicador string, valor int",
)

display(tabla5)
print(f"MapReduce vs Spark -> {resumen_mapreduce}")

assert resumen_mapreduce["coinciden_completamente"], (
    "La salida de Hadoop no coincide con Spark: revise los pasos del Reto 2"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gráficos obligatorios del Reto 4
# MAGIC
# MAGIC Los tres gráficos se generan dentro del notebook para que queden como evidencia en la
# MAGIC exportación. Son los mismos que muestra el dashboard en «Hallazgos».

# COMMAND ----------

import matplotlib.pyplot as plt

# --- Gráfico 1: películas y series ------------------------------------------
datos_tipos = sql_tipos.orderBy(F.desc("cantidad_titulos")).toPandas()
fig, ax = plt.subplots(figsize=(6.4, 3.8))
colores = ["#e50914" if tipo == "Movie" else "#16203a" for tipo in datos_tipos["tipo"]]
barras = ax.bar(datos_tipos["tipo"], datos_tipos["cantidad_titulos"], color=colores, width=0.55)
ax.set_title("Cantidad de títulos por tipo", fontsize=12, fontweight="bold")
ax.set_ylabel("Títulos")
ax.spines[["top", "right"]].set_visible(False)
for barra, valor in zip(barras, datos_tipos["cantidad_titulos"]):
    ax.text(barra.get_x() + barra.get_width() / 2, valor, f"{valor:,}".replace(",", " "),
            ha="center", va="bottom", fontsize=9)
display(fig)

# COMMAND ----------

# --- Gráfico 2: diez actores con más títulos --------------------------------
datos_actores = top10_spark.toPandas().sort_values("cantidad_titulos")
fig, ax = plt.subplots(figsize=(7.2, 4.2))
ax.barh(datos_actores["actor"], datos_actores["cantidad_titulos"], color="#e50914", height=0.62)
ax.set_title("Diez actores con más títulos distintos", fontsize=12, fontweight="bold")
ax.set_xlabel("Títulos distintos")
ax.spines[["top", "right"]].set_visible(False)
for y, valor in enumerate(datos_actores["cantidad_titulos"]):
    ax.text(valor, y, f" {valor}", va="center", fontsize=9)
display(fig)

# COMMAND ----------

# --- Gráfico 3: duración promedio por país (top 10) -------------------------
datos_paises = sql_paises.orderBy(F.desc("cantidad_peliculas")).limit(10).toPandas()
fig, ax = plt.subplots(figsize=(7.2, 4.2))
ax.barh(datos_paises["pais"], datos_paises["duracion_promedio_min"], color="#2563eb", height=0.62)
ax.invert_yaxis()
ax.set_title("Duración promedio de películas por país (top 10)", fontsize=12, fontweight="bold")
ax.set_xlabel("Minutos")
ax.spines[["top", "right"]].set_visible(False)
for y, valor in enumerate(datos_paises["duracion_promedio_min"]):
    ax.text(valor, y, f" {valor:.2f}", va="center", fontsize=9)
display(fig)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Exportar resultados al volumen
# MAGIC
# MAGIC Cada resultado se escribe como un único CSV dentro de
# MAGIC `/Volumes/<catálogo>/<esquema>/<volumen>/salidas/`. Desde ahí se descarga con
# MAGIC **Catalog → volumen → archivo → Download**, y ese archivo es el que se adjunta al informe.

# COMMAND ----------

dbutils.fs.mkdirs(RUTA_SALIDAS)


def guardar_csv(tabla, nombre):
    """Escribe una tabla como un solo CSV en el volumen de salidas."""
    destino = f"{RUTA_SALIDAS}/{nombre}.csv"
    temporal = f"{RUTA_SALIDAS}/{nombre}_tmp"
    dbutils.fs.rm(temporal, True)
    (tabla.coalesce(1)
        .write
        .mode("overwrite")
        .option("header", True)
        .csv(temporal))
    partes = [archivo.path for archivo in dbutils.fs.ls(temporal) if archivo.path.endswith(".csv")]
    dbutils.fs.cp(partes[0], destino, True)
    dbutils.fs.rm(temporal, True)
    print(f"  {nombre}.csv -> {destino}")
    return destino


guardar_csv(sql_tipos, "titulos_por_tipo")
guardar_csv(pyspark_titulos_por_actor, "actores_pyspark")
guardar_csv(sql_paises, "duracion_pais")
guardar_csv(tabla3, "verificacion_tabla3")
guardar_csv(tabla4, "comparacion_top10")
guardar_csv(tabla5, "verificacion_tabla5")

display(dbutils.fs.ls(RUTA_SALIDAS))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cierre
# MAGIC
# MAGIC Con el notebook ejecutado de principio a fin se obtiene evidencia de:
# MAGIC
# MAGIC - Las tablas `netflix_clean` (8 807 filas) y `mapreduce_actores` (36 439 filas).
# MAGIC - Los análisis A, B y C resueltos en SQL y en PySpark.
# MAGIC - La Tabla 3 con las tres salidas coincidiendo al 100 %.
# MAGIC - Las Tablas 4 y 5, que confirman que Hadoop y Spark cuentan igual.
# MAGIC - Los tres gráficos obligatorios y los CSV exportados.
# MAGIC
# MAGIC **Para la entrega:** exporte este notebook con **File → Export → IPython Notebook**
# MAGIC (queda como `03_analisis_netflix.ipynb`), descargue los CSV de `salidas/` y tome capturas de
# MAGIC la ejecución completa, de las tablas y de los gráficos.
