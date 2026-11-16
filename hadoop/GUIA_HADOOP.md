# Guía paso a paso · Reto 2 en Hadoop (HDFS + Hadoop Streaming)

Esta guía ejecuta el conteo de títulos por actor con Hadoop real. Los programas son
`scripts/02_mapper_actores.py` y `scripts/02_reducer_actores.py` (solo biblioteca estándar de
Python), el comando completo está en `scripts/02_ejecutar_mapreduce.txt` y el resultado final se
reconstruye con `scripts/02_exportar_resultado.py`.

| Elemento | Valor |
|---|---|
| Hadoop de referencia | 3.3.6 (funciona en cualquier 3.3.x) |
| Python del clúster | 3.8 o superior (`python3`) |
| Entrada HDFS | `/data/netflix/clean/netflix_clean.csv` |
| Salida HDFS | `/data/netflix/results/actores/` |
| Archivo final | `datos/resultados/mapreduce_actores.csv` |
| Filas esperadas | 36 439 actores, 64 126 pares actor–show_id |
| Verificación | `Anupam Kher = 43` títulos distintos |

> **Entorno:** Ubuntu 22.04 con Hadoop 3.3.6 en modo pseudo-distribuido. En WSL2 funciona igual;
> en Windows nativo no hay HDFS, use WSL2, Docker o una máquina virtual Linux.

---

## Paso 0 · Verificar la instalación

```bash
hadoop version
hdfs version
python3 --version
echo $HADOOP_HOME
```

Debe verse `Hadoop 3.3.x` y `Python 3.x`. Si `HADOOP_HOME` está vacío, expórtelo antes de continuar:

```bash
export HADOOP_HOME=/usr/local/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
```

Compruebe que los demonios estén arriba:

```bash
jps
```

Deben aparecer `NameNode`, `DataNode`, `ResourceManager` y `NodeManager`. Si faltan:

```bash
start-dfs.sh
start-yarn.sh
```

---

## Paso 1 · Preparar los programas

Copie el proyecto al clúster o a WSL2 y ubíquese en la carpeta de los programas:

```bash
cd ~/netflix/mapreduce
cp ~/proyecto_netflix_elsner/scripts/02_mapper_actores.py .
cp ~/proyecto_netflix_elsner/scripts/02_reducer_actores.py .
chmod +x 02_mapper_actores.py 02_reducer_actores.py
```

Prueba rápida sin Hadoop (debe emitir pares `actor<TAB>show_id`):

```bash
head -n 5 ../datos/clean/netflix_clean.csv | python3 02_mapper_actores.py
```

---

## Paso 2 · Cargar el archivo limpio en HDFS

```bash
hdfs dfs -mkdir -p /data/netflix/clean/
hdfs dfs -put -f netflix_clean.csv /data/netflix/clean/
hdfs dfs -ls -h /data/netflix/clean/
```

**Resultado esperado:** una línea con `netflix_clean.csv` y un tamaño cercano a `3.2 M`.

Verificación del contenido:

```bash
hdfs dfs -cat /data/netflix/clean/netflix_clean.csv | head -n 3
hdfs dfs -cat /data/netflix/clean/netflix_clean.csv | wc -l
```

La última orden debe devolver `8808` (8 807 registros + cabecera).

**Evidencia 1:** captura del `-put` y del `-ls -h` con nombre y tamaño visibles.

---

## Paso 3 · Ejecutar el trabajo MapReduce

Hadoop no sobrescribe una carpeta de salida existente. Elimínela si ya existe:

```bash
hdfs dfs -rm -r -f /data/netflix/results/actores/
```

Localice el jar de Streaming (la versión cambia según la instalación):

```bash
ls $HADOOP_HOME/share/hadoop/tools/lib/ | grep streaming
```

Ejecute el trabajo con la ruta que haya aparecido:

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

**Resultado esperado en la consola:**

```
Job job_... completed successfully
map 100% reduce 100%
```

Un solo reducer es intencional: así la salida queda ordenada por actor y la comparación con Spark
es directa. Con más reducers también funciona; `02_exportar_resultado.py` suma las partes.

**Evidencia 2:** captura de la ejecución con `map 100%`, `reduce 100%` y
`completed successfully`.

---

## Paso 4 · Revisar y descargar el resultado

```bash
hdfs dfs -ls -h /data/netflix/results/actores/
hdfs dfs -cat /data/netflix/results/actores/part-* | wc -l
hdfs dfs -cat /data/netflix/results/actores/part-* | sort -t$'\t' -k2,2nr | head -n 20
```

**Resultado esperado:** `36439` líneas (una por actor) y el top 3 así:

```
Anupam Kher     43
Shah Rukh Khan  35
Julie Tejwani   33
```

Descargue **todas** las partes:

```bash
mkdir -p ./partes
hdfs dfs -get /data/netflix/results/actores/part-* ./partes/
ls -l ./partes/
```

**Evidencia 3:** captura del listado de HDFS con `part-00000` y del top de actores.

---

## Paso 5 · Reunir las partes en `mapreduce_actores.csv`

```bash
python3 02_exportar_resultado.py --partes ./partes \
  --salida ../datos/resultados/mapreduce_actores.csv

head -n 11 ../datos/resultados/mapreduce_actores.csv
wc -l ../datos/resultados/mapreduce_actores.csv
```

**Resultado esperado:** 36 439 actores y un archivo con 36 440 líneas (cabecera incluida):

```
actor,cantidad_titulos
Anupam Kher,43
Shah Rukh Khan,35
Julie Tejwani,33
...
```

Estructura obligatoria: una fila por actor, ordenada por cantidad descendente y, en caso de
empate, por nombre ascendente. El programa de exportación aplica ese orden.

---

## Paso 6 · Ensayo local sin Hadoop (opcional)

Si no hay clúster disponible, el simulador reproduce el comportamiento de Streaming (mapper,
ordenamiento por clave y reducer) sobre el mismo archivo:

```bash
python scripts/02_simular_mapreduce_local.py
```

Escribe `datos/resultados/partes_locales/part-00000` y deja el resultado listo para
`02_exportar_resultado.py`. **No sustituye las capturas de HDFS y del job**, que son obligatorias.

---

## Entregables del Reto 2

| Entregable | Archivo |
|---|---|
| Mapper | `scripts/02_mapper_actores.py` |
| Reducer | `scripts/02_reducer_actores.py` |
| Comando completo | `scripts/02_ejecutar_mapreduce.txt` |
| Programa de exportación | `scripts/02_exportar_resultado.py` |
| Resultado final | `datos/resultados/mapreduce_actores.csv` |
| Evidencia de carga en HDFS | captura propia (evidencia 1) |
| Evidencia de fin del job | captura propia (evidencia 2) |
| Tabla 2 | en `docs/Informe_Netflix_Elsner.md` |

---

## Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `python3: command not found` | El nodo no hereda el PATH | Agregue `-D mapreduce.map.env="PATH=/usr/bin:/bin"` y lo mismo para `reduce` |
| `Output directory already exists` | La carpeta de salida quedó de una ejecución previa | `hdfs dfs -rm -r -f /data/netflix/results/actores/` |
| `ClassNotFoundException` con Streaming | Ruta del jar equivocada | `ls $HADOOP_HOME/share/hadoop/tools/lib/ | grep stream` y ajuste la versión |
| `Permission denied` | Usuario sin permisos en `/data` | `hdfs dfs -mkdir -p /data/netflix && hdfs dfs -chmod -R 777 /data/netflix` |
| El mapper devuelve 0 líneas | Se leyó el archivo sin cabecera o con otro separador | Verifique que sea `netflix_clean.csv` con cabecera y comas |
| Un actor aparece dos veces | Se usaron más reducers y no se consolidó | Use `02_exportar_resultado.py`, que suma por actor |
| Nombres con tildes salen raros | Codificación de la consola, no del archivo | El CSV se escribe en UTF-8; abra con esa codificación |
