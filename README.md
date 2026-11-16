# Análisis del catálogo de Netflix · Equipo Elsner

Proyecto de **Tecnologías Emergentes I · Evaluación Segundo Momento**. Recorre el ciclo completo de un
proyecto de Big Data sobre el catálogo público de Netflix: limpieza con **Pandas**, conteo de actores con
**Hadoop MapReduce** sobre HDFS, tres análisis resueltos en **SQL y PySpark** dentro de **Databricks** y un
**dashboard** profesional para comunicar los hallazgos.

**Carpeta del proyecto:**
`C:\Users\Jhael\OneDrive\Documentos\Default Project\proyecto_netflix_elsner`

---

## Resultados en una vista

| Indicador | Resultado |
|-----------|-----------|
| Títulos en el archivo limpio | **8 807** |
| Películas / series | **6 131** (69,62 %) / **2 676** (30,38 %) |
| Actores distintos (MapReduce y Spark) | **36 439** |
| Pares actor–título procesados | **64 126** |
| Películas con duración numérica | **6 128** de 6 131 |
| Países en el cálculo de duración | **117** (5 688 películas) |
| Diferencias SQL vs PySpark | **0** |
| Diferencias MapReduce vs Spark | **0** |
| Actor con más títulos distintos | **Anupam Kher** (43) |
| Promedio de duración más alto del grupo líder | **India** (125,91 min · 962 películas) |

Tabla 1 del enunciado reproducida exactamente: 8 807 registros de entrada, 0 duplicados, 0 `show_id`
repetidos, 8 807 registros de salida, 6 128 películas con `duration_min` y 3 sin duración.

---

## Requisitos y versiones

| Herramienta | Versión usada |
|-------------|----------------|
| Python | 3.14.4 |
| pandas | 3.1.1 |
| FastAPI / Uvicorn | 0.162.4 / 0.52.4 |
| Hadoop | 3.3.6 (Streaming) |
| Databricks Runtime | 15.4 LTS (Spark 3.5) |
| Bootstrap / Chart.js | 5.3.3 / 4.4.3 |
| ReportLab / Matplotlib | informe y figuras |

Dependencias:

```powershell
python -m pip install -r requirements.txt        # pipeline + dashboard
python -m pip install -r requirements-docs.txt   # informe, presentación y figuras
```

---

## Puesta en marcha

```powershell
cd "C:\Users\Jhael\OneDrive\Documentos\Default Project\proyecto_netflix_elsner"

# 1. Dataset original (si no existe datos/raw/netflix_titles.csv)
python scripts/00_descargar_dataset.py

# 2. Limpieza con Pandas -> datos/clean/netflix_clean.csv
python scripts/01_limpiar_netflix.py

# 3. MapReduce: ensayo local sin Hadoop (genera partes locales)
python scripts/02_simular_mapreduce_local.py
python scripts/02_exportar_resultado.py --partes datos/resultados/partes_locales

# 4. Resultados de los Retos 3 y 4 -> datos/resultados/
python scripts/03_generar_resultados.py

# 5. Dashboard + API en http://127.0.0.1:8000
python run.py
```

En un clúster real, el paso 3 se reemplaza por el trabajo de Hadoop Streaming descrito en
[`hadoop/GUIA_HADOOP.md`](hadoop/GUIA_HADOOP.md); los pasos 4 y 5 no cambian.

---

## Estructura

```text
proyecto_netflix_elsner/
  run.py                         arranque del dashboard y de la API
  requirements.txt               dependencias del pipeline y del backend
  requirements-docs.txt          dependencias del informe, la presentación y las figuras
  datos/
    raw/netflix_titles.csv       archivo original sin modificar
    clean/netflix_clean.csv      8 807 x 13 (12 originales + duration_min)
    resultados/                  CSV y JSON con las salidas reales del pipeline
  pipeline/
    limpieza.py                  reglas de limpieza compartidas
    actores.py                   conteo de actores (mismas reglas que Hadoop)
    analisis.py                  análisis de tipos, actores y duración
    config.py                    rutas y constantes del proyecto
  scripts/
    00_descargar_dataset.py      descarga y verificación del CSV original
    01_limpiar_netflix.py        Reto 1
    02_mapper_actores.py         mapper de Hadoop Streaming
    02_reducer_actores.py        reducer de Hadoop Streaming
    02_simular_mapreduce_local.py  ensayo local sin clúster
    02_exportar_resultado.py     reúne las partes en mapreduce_actores.csv
    02_ejecutar_mapreduce.txt    comando exacto de Hadoop Streaming
    03_generar_resultados.py     Retos 3 y 4 (resultados para el dashboard)
  hadoop/GUIA_HADOOP.md          HDFS, trabajo Streaming, verificación y evidencias
  databricks/
    03_analisis_netflix.py       fuente del notebook (celdas + SQL + PySpark)
    03_analisis_netflix.ipynb    notebook exportado, listo para importar
    GUIA_DATABRICKS.md           paso a paso con el código exacto
    generar_notebook.py          convierte el .py en .ipynb
  backend/
    main.py                      FastAPI, CORS y montaje del frontend
    api/routers/                 resumen, limpieza, análisis, verificación, catálogo, descargas
    services/datastore.py        carga única de CSV y cálculos en memoria
  frontend/
    index.html                   resumen
    limpieza.html                Reto 1
    mapreduce.html               Reto 2
    databricks.html              Reto 3
    hallazgos.html               Reto 4
    catalogo.html                explorador con búsqueda y paginación
    assets/                      CSS, JS, Bootstrap 5.3.3, Chart.js 4.4.3, PDF del informe
  docs/
    Informe_Netflix_Elsner.pdf   informe final (13 páginas)
    Informe_Netflix_Elsner.md    misma contenido en Markdown
    Presentacion_Netflix_Grupo.pdf  presentación 16:9 (12 diapositivas)
    guion_exposicion.md          guion de 15 minutos con reparto y preguntas
    figuras/                     diagrama de proceso y gráficos del Reto 4
    evidencias/                  capturas numeradas (1 a 7) e instrucciones
    generar_figuras.py           regenera las figuras
    generar_informe.py           regenera el informe desde los resultados reales
    generar_presentacion.py      regenera la presentación
```

---

## Los cuatro retos

### Reto 1 · Limpieza con Pandas

Once reglas en orden: recorte de espacios, saltos de línea y tabulaciones, vacíos a nulos, eliminación de
duplicados exactos, `show_id` vacío o repetido, fechas a `dd/mm/aaaa`, `duration_min` numérico solo para
películas, 12 columnas + 1, nulos sin imputar y guardado en UTF-8. Resultado: **8 807 filas, 13 columnas,
0 duplicados**. Detalle completo en `scripts/01_limpiar_netflix.py` y en el informe (Tabla 1 y Tabla A.1).

### Reto 2 · MapReduce sobre HDFS

El archivo limpio se sube a `/data/netflix/clean/netflix_clean.csv` y se procesa con Hadoop Streaming:

```bash
hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-3.3.6.jar \
  -D mapreduce.job.name="netflix_actores" \
  -D mapreduce.job.reduces=1 \
  -files 02_mapper_actores.py,02_reducer_actores.py \
  -mapper "python3 02_mapper_actores.py" \
  -reducer "python3 02_reducer_actores.py" \
  -input /data/netflix/clean/netflix_clean.csv \
  -output /data/netflix/results/actores/
```

Salida: **64 126 pares** → **36 439 actores**, con un título contado una sola vez por actor. La guía
[`hadoop/GUIA_HADOOP.md`](hadoop/GUIA_HADOOP.md) incluye HDFS, verificación, exportación del resultado y las
capturas de evidencia 1 y 2.

### Reto 3 · SQL y PySpark en Databricks

El notebook [`databricks/03_analisis_netflix.ipynb`](databricks/03_analisis_netflix.ipynb) crea
`workspace.netflix.netflix_clean` (8 807 × 13) y `workspace.netflix.mapreduce_actores` (36 439), resuelve
los tres análisis dos veces (SQL y PySpark) y compara las salidas con un `full outer join`. Resultados:
**2 filas** de tipos, **36 439** actores, **117** países, **0 diferencias**. El paso a paso con el código
exacto está en [`databricks/GUIA_DATABRICKS.md`](databricks/GUIA_DATABRICKS.md).

### Reto 4 · Hallazgos

Dos gráficos (títulos por tipo y top 10 de actores), la Tabla 6 de duración por país y las conclusiones
(148 palabras). Estados Unidos 2 749 películas / 93,75 min; India 962 / 125,91 min; Reino Unido 534 / 98,76
min. Los gráficos están en `docs/figuras/` y se replican en el dashboard.

---

## Dashboard y API

`python run.py` sirve el frontend y la API en `http://127.0.0.1:8000`.

| Página | Ruta | Contenido |
|--------|------|-----------|
| Resumen | `/` | indicadores, tipos, años, ratings y calidad |
| Limpieza | `/limpieza.html` | Tabla 1, nulos y muestra del archivo limpio |
| MapReduce | `/mapreduce.html` | top de actores y comparación con Spark |
| Databricks | `/databricks.html` | Tablas 3, 4 y 5, y código del notebook |
| Hallazgos | `/hallazgos.html` | los dos gráficos y la Tabla 6 |
| Catálogo | `/catalogo.html` | búsqueda y paginación sobre 8 807 títulos |

Endpoints principales:

```text
GET /api/resumen            GET /api/limpieza          GET /api/mapreduce
GET /api/verificacion       GET /api/actores           GET /api/paises
GET /api/tipos              GET /api/catalogo          GET /docs (Swagger)
GET /api/export/{recurso}.csv
GET /api/descargas/informe | presentacion | notebook
```

El backend no depende del frontend: se puede consumir solo con la API. Las descargas sirven el informe, la
presentación y el notebook desde sus archivos reales, sin copias desincronizadas.

---

## Informe y presentación

```powershell
python docs/generar_figuras.py        # diagrama + gráficos del Reto 4
python docs/generar_informe.py        # docs/Informe_Netflix_Elsner.pdf + copia en frontend/assets
python docs/generar_presentacion.py   # docs/Presentacion_Netflix_Grupo.pdf
```

El informe sigue el orden oficial: portada, objetivo y diagrama, Reto 1 + Tabla 1, Reto 2 + Tabla 2,
Reto 3 + Tablas 3–5, Reto 4 (dos gráficos, Tabla 6 y conclusiones), referencias y anexo con ejecución y
entregables. Las **evidencias 1 a 7** son cajas numeradas: al guardar la captura como
`docs/evidencias/evidencia_N.png` y regenerar el PDF, la imagen reemplaza el marcador (ver
[`docs/evidencias/README.md`](docs/evidencias/README.md)).

---

## Entregables

| Entregable | Archivo |
|------------|---------|
| Informe PDF | `docs/Informe_Netflix_Elsner.pdf` |
| Presentación | `docs/Presentacion_Netflix_Grupo.pdf` |
| Notebook de Databricks | `databricks/03_analisis_netflix.ipynb` |
| Resultado de Hadoop | `datos/resultados/mapreduce_actores.csv` |
| Archivo limpio | `datos/clean/netflix_clean.csv` |
| Limpieza | `scripts/01_limpiar_netflix.py` |
| Mapper y reducer | `scripts/02_mapper_actores.py`, `scripts/02_reducer_actores.py` |
| Comando de MapReduce | `scripts/02_ejecutar_mapreduce.txt` |
| Dashboard | `backend/` + `frontend/` |
| Guion de exposición | `docs/guion_exposicion.md` |

---

## Notas metodológicas

- `cast` y `country` son multivaluados: un título cuenta para cada actor o país listado.
- Los nombres no se normalizan; una misma persona con variantes de escritura puede contarse dos veces.
- Los datos faltantes se conservan como nulos y se excluyen del cálculo correspondiente; no se imputan.
- La Tabla 4 del informe calcula la diferencia como **MapReduce − Spark**, tal como pide el enunciado.
- El dashboard consume los CSV de resultados del pipeline; el notebook de Databricks es la evidencia de
  SQL y PySpark, y el dashboard la presenta.

---

**Equipo Elsner:** Jhael Arguedas · Carlos Conde · Bryan Mamani
Tecnologías Emergentes I · Evaluación Segundo Momento · 2026
