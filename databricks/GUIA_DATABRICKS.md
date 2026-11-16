# Guía paso a paso · Reto 3 en Databricks

Esta guía reproduce el notebook `databricks/03_analisis_netflix.py` directamente en la plataforma.
Cada paso indica **dónde hacer clic**, **qué código pegar** y **qué resultado debe verse**.
El notebook ya contiene todo el código; esta guía sirve para ejecutarlo, explicarlo y capturar las
evidencias que pide el enunciado.

| Dato | Valor |
|---|---|
| Cuenta gratuita | <https://www.databricks.com/try-databricks> (14 días) o Community Edition |
| Runtime probado | Databricks Runtime **15.4 LTS** (Scala 2.12, Spark 3.5) |
| Catálogo sugerido | `workspace` |
| Esquema | `netflix` |
| Volumen | `datos` |
| Archivos de entrada | `netflix_clean.csv` y `mapreduce_actores.csv` |
| Tiempo estimado | 25–35 minutos la primera vez |

> Si su workspace usa otro catálogo (por ejemplo `hive_metastore`), cambie el widget `catalogo`
> en el paso 5. No modifique el código.

---

## Paso 1 · Crear el workspace folder e importar el notebook

1. Abra su workspace de Databricks.
2. En la barra lateral, entre a **Workspace**.
3. Clic en **Create → Folder** y cree la carpeta `netflix_elsner`.
4. Abra la carpeta y use **Import** (o el menú **⋮ → Import**).
5. Elija **File**, arrastre `databricks/03_analisis_netflix.py` y confirme.
   Databricks lo reconoce como notebook porque la primera línea es `# Databricks notebook source`.
6. Abra el notebook. Arriba debe verse el nombre `03_analisis_netflix`.

**Evidencia para el informe:** captura de la carpeta con el notebook importado.

> También puede importar `03_analisis_netflix.ipynb` con la opción *File → Jupyter notebook*.
> Los dos archivos son equivalentes; el `.py` es el que se edita y el `.ipynb` se genera con
> `python databricks/generar_notebook.py`.

---

## Paso 2 · Crear el clúster

1. Barra lateral → **Compute** → **Create compute**.
2. Nombre: `cluster-elsner`.
3. **Cluster mode:** *Single node* (más barato y suficiente: el dataset pesa 3,2 MB).
4. **Databricks Runtime version:** `15.4 LTS` (o el LTS más reciente disponible).
5. **Node type:** el más pequeño que permita su cuenta.
6. **Terminate after:** `20 minutes` de inactividad.
7. Clic en **Create compute** y espere el estado **Running** (verde).

**Evidencia:** captura del clúster en estado *Running* con la versión del runtime visible.

> En Community Edition el clúster se crea automáticamente al abrir el notebook. Si aparece
> "Serverless", también funciona: el código es compatible.

---

## Paso 3 · Crear el esquema y el volumen

1. Barra lateral → **Catalog**.
2. Arriba, seleccione el catálogo (`workspace` por defecto).
3. Clic en **Create schema**:
   - Nombre: `netflix`
   - Ubicación: deje la predeterminada
   - Clic en **Create**.
4. Dentro del esquema, pestaña **Volumes** → **Create volume**:
   - Nombre: `datos`
   - Tipo: **Managed volume**
   - Clic en **Create**.
5. Abra el volumen `datos` → **Upload to this volume** y suba:
   - `datos/clean/netflix_clean.csv` (8 807 filas, 13 columnas, ~3,2 MB)
   - `datos/resultados/mapreduce_actores.csv` (36 439 filas)

**Evidencia:** captura del volumen `datos` con los dos archivos listados.

> **Alternativa sin Unity Catalog (Community Edition antigua):** suba los archivos a
> **Data → Add data → Upload files** y use las rutas
> `/FileStore/tables/netflix_clean.csv` y `/FileStore/tables/mapreduce_actores.csv`.
> En ese caso reemplace `RUTA_ENTRADA_LIMPIA` y `RUTA_ENTRADA_ACTORES` en la celda del paso 4.

---

## Paso 4 · Conectar el notebook y fijar los parámetros

1. Abra el notebook importado.
2. Arriba a la derecha, en **Connect**, seleccione `cluster-elsner`.
3. Ejecute la celda **Paso 0 · Parámetros del entorno** (Shift + Enter).

Código exacto de la celda:

```python
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
```

**Resultado esperado:** cuatro líneas con el catálogo, el esquema, la ruta del volumen y la versión
de Spark (3.5.x).

---

## Paso 5 · Crear las tablas desde el volumen

Ejecute la celda **Paso 1 · Cargar los CSV del volumen y crear las tablas**:

```python
from pyspark.sql import functions as F
from pyspark.sql import Window

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

netflix_clean = spark.table("netflix_clean")
mapreduce_actores = spark.table("mapreduce_actores")

print("Tablas creadas:")
print(f"  netflix_clean      -> {netflix_clean.count():>6} filas, {len(netflix_clean.columns)} columnas")
print(f"  mapreduce_actores  -> {mapreduce_actores.count():>6} filas")
```

**Resultado esperado:**

```
Tablas creadas:
  netflix_clean      ->   8807 filas, 13 columnas
  mapreduce_actores  ->  36439 filas
```

Por qué `multiLine = true`: la columna `description` contiene comas y comillas entrecomilladas; sin
esa opción Spark corta filas por la mitad. Las cadenas vacías se leen como `NULL`, igual que en el
archivo limpio.

Ejecute también la celda **Comprobación de la carga**. Debe mostrar:

| registros | show_id_distintos | peliculas | series | con_duracion_min |
|---:|---:|---:|---:|---:|
| 8 807 | 8 807 | 6 131 | 2 676 | 6 128 |

Y las tres aserciones finales imprimen `Validaciones de carga: OK`.

**Evidencia:** captura de la tabla `netflix_clean` en **Catalog → workspace → netflix → Tables**.

---

## Paso 6 · Análisis A · Películas y series (SQL y PySpark)

### 6.1 Celda SQL

```sql
CREATE OR REPLACE TEMP VIEW sql_peliculas_y_series AS
SELECT tipo,
       COUNT(DISTINCT show_id) AS cantidad_titulos
FROM (
  SELECT show_id,
         CASE
           WHEN `type` IS NULL THEN 'Sin clasificación'
           WHEN `type` IN ('Movie', 'TV Show') THEN `type`
           ELSE 'Otro'
         END AS tipo
  FROM netflix_clean
)
GROUP BY tipo
ORDER BY tipo;
```

Ejecute después `SELECT * FROM sql_peliculas_y_series;` → 2 filas:

| tipo | cantidad_titulos |
|---|---:|
| Movie | 6 131 |
| TV Show | 2 676 |

### 6.2 Celda PySpark

```python
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
```

**Qué explicar en la exposición:** el `CASE` y el `when/otherwise` implementan la misma regla; el
`GROUP BY` se hace sobre la etiqueta calculada y se cuenta `show_id` distinto para no duplicar.

---

## Paso 7 · Análisis B · Títulos por actor (SQL y PySpark)

`cast` es palabra reservada en Spark SQL: **siempre entre backticks**.

### 7.1 Celda SQL

```sql
CREATE OR REPLACE TEMP VIEW sql_titulos_por_actor AS
WITH actores AS (
  SELECT DISTINCT show_id, trim(actor) AS actor
  FROM netflix_clean
  LATERAL VIEW explode(split(`cast`, ',')) t AS actor
  WHERE `cast` IS NOT NULL
)
SELECT actor,
       COUNT(DISTINCT show_id) AS cantidad_titulos
FROM actores
WHERE actor <> ''
GROUP BY actor
ORDER BY cantidad_titulos DESC, actor ASC;
```

Compruebe con `SELECT * FROM sql_titulos_por_actor LIMIT 10;`:

| actor | cantidad_titulos |
|---|---:|
| Anupam Kher | 43 |
| Shah Rukh Khan | 35 |
| Julie Tejwani | 33 |
| Naseeruddin Shah | 32 |
| Takahiro Sakurai | 32 |
| Rupa Bhimani | 31 |
| Akshay Kumar | 30 |
| Om Puri | 30 |
| Yuki Kaji | 29 |
| Amitabh Bachchan | 28 |

### 7.2 Celda PySpark

```python
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
```

**Resultado esperado:** 36 439 actores distintos y el mismo top 10 de la tabla anterior.

**Qué explicar:** `explode(split(...))` convierte una fila con varios actores en varias filas; el
`DISTINCT (show_id, actor)` evita contar dos veces a la misma persona en el mismo título.

---

## Paso 8 · Análisis C · Duración promedio por país (SQL y PySpark)

Solo películas con `duration_min` numérico y mayor que cero. Un título cuenta una vez por país.

### 8.1 Celda SQL

```sql
CREATE OR REPLACE TEMP VIEW sql_duracion_por_pais AS
WITH peliculas AS (
  SELECT DISTINCT show_id, duration_min, trim(pais) AS pais
  FROM netflix_clean
  LATERAL VIEW explode(split(country, ',')) p AS pais
  WHERE `type` = 'Movie'
    AND duration_min IS NOT NULL
    AND duration_min > 0
    AND country IS NOT NULL
)
SELECT pais,
       COUNT(DISTINCT show_id) AS cantidad_peliculas,
       ROUND(AVG(duration_min), 2) AS duracion_promedio_min
FROM peliculas
WHERE pais <> ''
GROUP BY pais
ORDER BY cantidad_peliculas DESC, pais ASC;
```

Compruebe con `SELECT * FROM sql_duracion_por_pais LIMIT 10;`:

| pais | cantidad_peliculas | duracion_promedio_min |
|---|---:|---:|
| United States | 2 749 | 93,75 |
| India | 962 | 125,91 |
| United Kingdom | 534 | 98,76 |
| Canada | 319 | 91,15 |
| France | 303 | 100,97 |
| Germany | 182 | 103,01 |
| Spain | 171 | 101,10 |
| Japan | 119 | 98,85 |
| China | 114 | 104,46 |
| Mexico | 111 | 90,60 |

### 8.2 Celda PySpark

```python
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
```

**Resultado esperado:** 117 países distintos.

---

## Paso 9 · Tabla 3 · Verificación de SQL contra PySpark

La celda de la **Tabla 3** contiene la función `comparar_salidas`. Únela por clave con un
`full outer join` y clasifique cada fila en `igual`, `diferente`, `solo_izquierda` o `solo_derecha`:

```python
def comparar_salidas(izquierda, derecha, clave, valor, tolerancia=0.0):
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
    ...
```

Ejecute la celda completa y revise la tabla:

| Análisis | Filas SQL | Filas PySpark | Valores diferentes | En una sola salida | ¿Coinciden? |
|---|---:|---:|---:|---:|:--:|
| peliculas_y_series | 2 | 2 | 0 | 0 | Sí |
| titulos_por_actor | 36 439 | 36 439 | 0 | 0 | Sí |
| duracion_por_pais | 117 | 117 | 0 | 0 | Sí |

La aserción final imprime `Tabla 3: las tres salidas coinciden completamente`. Si falla, no siga:
revise los backticks de `cast` y la tolerancia de 0,01.

**Evidencia:** captura de la tabla con las tres filas en «Sí».

---

## Paso 10 · Tabla 4 · Diez primeros actores, MapReduce contra Spark

```python
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
```

**Resultado esperado:** diez filas con `diferencia = 0` en todas. La columna `mapreduce` viene del
CSV que produjo Hadoop y la columna `spark` del análisis B.

**Evidencia:** captura de la Tabla 4.

---

## Paso 11 · Tabla 5 · Verificación completa

```python
resumen_mapreduce = comparar_salidas(
    mapreduce_actores, pyspark_titulos_por_actor, "actor", "cantidad_titulos"
)
```

| Indicador | Valor |
|---|---:|
| actores_mapreduce | 36 439 |
| actores_spark | 36 439 |
| ambas_iguales | 36 439 |
| ambas_diferentes | 0 |
| solo_mapreduce | 0 |
| solo_spark | 0 |

**Evidencia:** captura de la Tabla 5 y de la aserción
`MapReduce vs Spark -> {... 'coinciden_completamente': True}`.

---

## Paso 12 · Gráficos obligatorios

El notebook genera tres figuras con `matplotlib` y las muestra con `display(fig)`:

1. **Barras verticales:** cantidad de títulos por tipo (Movie 6 131 / TV Show 2 676).
2. **Barras horizontales:** diez actores con más títulos distintos (Anupam Kher 43).
3. **Barras horizontales:** duración promedio de películas por país, top 10 (EE. UU. 93,75 min).

Si prefiere el gráfico nativo de Databricks: ejecute `display(top10_spark)` y use
**+ → Visualization → Bar**, eje X `actor`, eje Y `cantidad_titulos`.

**Evidencia:** captura de los tres gráficos.

---

## Paso 13 · Exportar resultados y notebook

1. La celda final escribe en `/Volumes/workspace/netflix/datos/salidas/`:
   - `titulos_por_tipo.csv`
   - `actores_pyspark.csv`
   - `duracion_pais.csv`
   - `verificacion_tabla3.csv`
   - `comparacion_top10.csv`
   - `verificacion_tabla5.csv`
2. Descárguelos desde **Catalog → workspace → netflix → datos → salidas**, o con
   **File → Download** desde el explorador del volumen.
3. Exporte el notebook: **File → Export → IPython Notebook**. Se descarga como
   `03_analisis_netflix.ipynb`; guárdelo en `databricks/`.
4. Si exporta también el `.py` (**File → Export → Source file**), reemplaza
   `databricks/03_analisis_netflix.py` y regenera el `.ipynb` con
   `python databricks/generar_notebook.py`.

---

## Paso 14 · Capturas para el informe (lista de verificación)

| # | Evidencia | Dónde se toma |
|---|---|---|
| 1 | Notebook importado | Workspace → carpeta `netflix_elsner` |
| 2 | Clúster en ejecución | Compute → `cluster-elsner` |
| 3 | Volumen con los dos CSV | Catalog → `netflix.datos` |
| 4 | `netflix_clean` con 8 807 filas | Catalog → tabla → **Sample data** |
| 5 | Análisis A en SQL y en PySpark | Celdas del paso 6 |
| 6 | Análisis B en SQL y en PySpark | Celdas del paso 7 |
| 7 | Análisis C en SQL y en PySpark | Celdas del paso 8 |
| 8 | Tabla 3 completa | Celda del paso 9 |
| 9 | Tabla 4 completa | Celda del paso 10 |
| 10 | Tabla 5 completa | Celda del paso 11 |
| 11 | Tres gráficos | Celdas del paso 12 |
| 12 | Notebook ejecutado de inicio a fin | **Run all** y vista general |

---

## Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `ParseException: extraneous input 'cast'` | `cast` es palabra reservada | Escriba `` `cast` `` con backticks |
| `[TABLE_OR_VIEW_NOT_FOUND] netflix_clean` | No ejecutó el paso 5 o cambió de esquema | Ejecute el paso 0 y el 5 en la misma sesión |
| `[CATALOG_NOT_FOUND] workspace` | Su cuenta usa otro catálogo | Cambie el widget `catalogo` (pruebe `hive_metastore`) o cree el esquema en el catálogo existente |
| `Path does not exist: /Volumes/...` | Archivo mal subido o volumen distinto | Revise **Catalog → Volumes** y el nombre exacto |
| Filas cortadas o columnas corridas | Se omitió `multiLine = true` | Vuelva a leer el CSV con la opción |
| `duration_min` llega como texto | `inferSchema` no se aplicó | Use `.option("inferSchema", True)` o `F.col("duration_min").cast("int")` |
| `AVG` con más decimales que el informe | Falta el redondeo | Use `ROUND(AVG(duration_min), 2)` o `F.round(F.avg(...), 2)` |
| El notebook se detiene en una aserción | Los datos no coinciden con lo esperado | No borre la aserción: significa que hay un error real en la carga o en la consulta |

---

## Anexo · Equivalencia con el dashboard local

El dashboard (`http://127.0.0.1:8000`) consume `datos/resultados/verificacion.json`, calculado con
Pandas sobre el mismo `netflix_clean.csv` y la misma lógica. Ese espejo permite mostrar el panel sin
estar conectado a Databricks; **la evidencia oficial del Reto 3 es este notebook ejecutado en la
plataforma**, con sus capturas y el `.ipynb` exportado.
