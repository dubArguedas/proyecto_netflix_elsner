# Guion de exposición · Equipo Elsner

**Duración objetivo:** 15 minutos (13 de exposición + 2 de preguntas)
**Formato:** 12 diapositivas en `docs/Presentacion_Netflix_Grupo.pdf`
**Regla de oro:** cada cifra que se dice en voz alta existe en el informe o en el dashboard; no se improvisan números.

---

## Antes de empezar (5 minutos previos)

1. Abrir el dashboard: `python run.py` → `http://127.0.0.1:8000`.
2. Verificar que las seis páginas cargan datos (no debe quedar ningún «Cargando»).
3. Abrir el notebook `databricks/03_analisis_netflix.ipynb` en Databricks (o el PDF del informe como respaldo).
4. Tener a mano `datos/resultados/mapreduce_actores.csv` y las capturas de `docs/evidencias/`.
5. Cerrar notificaciones y pestañas personales.

---

## Diapositiva 1 · Portada (0:00 – 0:30)

> «Buenos días. Somos el equipo Elsner: Jhael Arguedas, Carlos Conde y Bryan Mamani. Vamos a presentar el análisis del catálogo de Netflix: 8 807 títulos que pasan por limpieza con Pandas, conteo con Hadoop y verificación con Spark en Databricks.»

No leer la portada completa. Nombrar el equipo, el tema y el orden de la exposición.

---

## Diapositiva 2 · Un catálogo, tres preguntas (0:30 – 2:00)

> «El trabajo responde tres preguntas concretas: cuántas películas y series hay, qué actor participa en más títulos distintos y cómo cambia la duración promedio de las películas según el país.»

> «La particularidad es que cada pregunta se resuelve por caminos independientes: Pandas para limpiar, Hadoop para contar y Spark para analizar. Al final comparamos los tres resultados. Si coinciden, la evidencia es fuerte; si no, hay un error que corregir.»

Señalar el conjunto de datos: Kaggle, 12 columnas, archivo original intacto en `datos/raw/`.

---

## Diapositiva 3 · Del archivo original al dashboard (2:00 – 3:30)

> «Este es el recorrido completo. El archivo original se limpia una sola vez y produce `netflix_clean.csv`, con 8 807 filas y 13 columnas: las 12 originales más `duration_min`.»

> «Ese archivo limpio entra por dos caminos. El primero lo sube a HDFS, ejecuta mapper y reducer y genera `mapreduce_actores.csv`. El segundo lo carga en un volumen de Unity Catalog y lo analiza con SQL y PySpark. La comparación de las tres salidas alimenta el dashboard y el informe.»

Explicar las flechas: cada una es un archivo que se transfiere. No hay cálculos duplicados sobre datos distintos: todos parten del mismo CSV limpio.

---

## Diapositiva 4 · Reto 1: limpieza con Pandas (3:30 – 5:00)

> «La limpieza aplica once reglas en orden. El orden importa: primero normalizamos el texto y después eliminamos duplicados, para que dos filas que solo difieren en espacios se detecten como iguales.»

Recorrer rápido las reglas: recorte de espacios, saltos de línea, vacíos a nulos, duplicados, `show_id` vacío o repetido, fechas a `dd/mm/aaaa`, `duration_min` solo para películas, 12 columnas más una, nulos sin imputar, guardado en UTF-8.

> «El resultado coincide exactamente con la referencia del enunciado: 8 807 registros de entrada, 8 807 de salida, cero duplicados y cero `show_id` repetidos. De las 6 131 películas, 6 128 tienen duración numérica; las tres restantes son especiales de Louis C. K. que vienen sin duración. No las inventamos: quedan nulas.»

Si preguntan por los nulos: 2 634 sin director, 831 sin país, 825 sin reparto, 4 sin rating. La Tabla A.1 del informe los detalla.

---

## Diapositiva 5 · Reto 2: conteo con Hadoop (5:00 – 7:00)

> «Cargamos el archivo limpio en HDFS, en `/data/netflix/clean/netflix_clean.csv`, y ejecutamos Hadoop Streaming con un mapper y un reducer escritos solo con la biblioteca estándar de Python.»

Describir el flujo:

- **Mapper:** omite la cabecera, lee cada fila con el módulo `csv`, separa `cast` por comas, recorta espacios y emite un par `actor ⇥ show_id` por cada nombre no vacío.
- **Shuffle:** Hadoop agrupa todos los pares de un mismo actor.
- **Reducer:** acumula los `show_id` en un conjunto y emite `actor ⇥ cantidad`. Un título cuenta una sola vez por actor, aunque aparezca repetido.

> «El mapper emitió 64 126 pares y el reducer produjo 36 439 actores distintos. Usamos un solo reducer para que la salida quede ordenada por actor y la comparación con Spark sea directa.»

Mostrar, si hay tiempo, la captura de la evidencia 2: `map 100%`, `reduce 100%`, `Job completed successfully`.

---

## Diapositiva 6 · Tabla 2: los diez actores con más títulos (7:00 – 8:00)

> «Anupam Kher lidera con 43 títulos distintos; le siguen Shah Rukh Khan con 35 y Julie Tejwani con 33. El décimo, Amitabh Bachchan, baja a 28: la concentración es alta en la cabeza y cae rápido.»

> «Ocho de los diez primeros pertenecen a la industria india, que además es el segundo país con más películas del catálogo. Los empates se resuelven por nombre ascendente: Naseeruddin Shah aparece antes que Takahiro Sakurai, ambos con 32.»

Aclarar que «títulos distintos» no es «protagonismos»: el campo `cast` lista todo el reparto, así que un actor secundario también suma.

---

## Diapositiva 7 · Reto 3: SQL y PySpark, dos caminos (8:00 – 10:00)

> «En Databricks cargamos los dos CSV en un volumen de Unity Catalog y creamos dos tablas: `netflix_clean`, con 8 807 filas y 13 columnas, y `mapreduce_actores`, con 36 439 filas.»

> «Cada uno de los tres análisis se resolvió dos veces: una celda SQL y una celda PySpark, sin reutilizar la salida de la otra. Los tres resultados son: 2 filas en tipos, 36 439 actores y 117 países.»

> «La comparación usa un full outer join por clave y clasifica cada fila como igual, diferente o presente en una sola salida. Resultado: cero diferencias en los tres análisis y, además, cero diferencias entre Hadoop y Spark en los 36 439 actores.»

Mencionar el detalle técnico que suele fallar: `cast` es palabra reservada en Spark SQL y va entre backticks; `GROUP BY 1` se evitó usando una subconsulta.

Si preguntan por la tolerancia: los promedios se comparan redondeados a dos decimales (tolerancia 0,01 minutos).

---

## Diapositiva 8 · Reto 4: títulos por tipo (10:00 – 11:00)

> «El catálogo es mayoritariamente cinematográfico: 6 131 películas, el 69,62 %, frente a 2 676 series, el 30,38 %. No hay registros con otro tipo ni sin clasificación, así que los porcentajes se calculan sobre los 8 807 títulos.»

Señalar que el gráfico tiene cantidad y porcentaje sobre cada barra, y ejes rotulados.

---

## Diapositiva 9 · Reto 4: actores con más títulos (11:00 – 12:00)

> «El mismo ranking de Hadoop se reproduce en Spark. Anupam Kher tiene 43 títulos distintos, seguido de Shah Rukh Khan con 35 y Julie Tejwani con 33. Son 36 439 actores a partir de 64 126 pares actor–título.»

> «La coincidencia entre las dos implementaciones respalda la correctitud del mapper, del reducer y de la lectura del CSV: el reducer acumula en memoria y Spark usa `countDistinct`, pero ambos llegan a las mismas cantidades.»

---

## Diapositiva 10 · Reto 4: duración por país (12:00 – 13:00)

> «Para la duración usamos solo películas con `duration_min` numérico mayor que cero: 5 688 películas y 117 países. Estados Unidos aporta 2 749 películas con un promedio de 93,75 minutos; India, con 962, tiene el promedio más alto del grupo líder: 125,91 minutos, más de dos horas. México cierra el grupo con 90,60.»

> «La duración no depende del volumen: un país con pocas películas puede tener un promedio alto o bajo.»

---

## Diapositiva 11 · Conclusiones (13:00 – 14:00)

> «Tres respuestas: 8 807 títulos, 6 131 películas y 2 676 series; Anupam Kher lidera con 43 títulos distintos; India promedia 125,91 minutos frente a 93,75 de Estados Unidos.»

> «Y una cifra que resume el trabajo: cero diferencias entre los tres caminos. MapReduce y Spark llegaron a los mismos 36 439 actores con las mismas cantidades.»

> «Limitaciones: `cast` y `country` son multivaluados, los nombres no están normalizados y los datos faltantes se conservan como nulos. Los resultados describen la composición del catálogo, no la audiencia ni el éxito comercial.»

---

## Diapositiva 12 · Dashboard y entrega (14:00 – 15:00)

> «Todo esto se puede recorrer en el dashboard: seis páginas conectadas a la API, con los mismos resultados del pipeline. El informe, la presentación, el notebook y los CSV están en la carpeta del proyecto.»

Demostración rápida (30 segundos por página, solo si el tiempo lo permite):

1. **Resumen:** indicadores y distribución por tipo, año y rating.
2. **Limpieza:** Tabla 1 y nulos.
3. **MapReduce:** top de actores y comparación con Spark.
4. **Databricks:** Tablas 3, 4 y 5.
5. **Hallazgos:** los dos gráficos y la Tabla 6.
6. **Catálogo:** buscador con paginación.

Cierre: «Gracias. Quedamos atentos a las preguntas.»

---

## Preguntas previsibles y respuestas cortas

| Pregunta | Respuesta |
|----------|-----------|
| ¿Por qué un solo reducer? | Para que la salida quede ordenada por actor y la comparación con Spark sea directa; el volumen (64 126 pares) no exige paralelismo. |
| ¿Por qué no imputar nulos? | Inventar país, reparto o duración alteraría los promedios y los conteos. Se conservan y se excluyen del cálculo correspondiente. |
| ¿Qué diferencia hay entre SQL y PySpark? | La sintaxis y el motor de ejecución; las reglas son las mismas. El notebook lo demuestra con celdas independientes y una comparación por clave. |
| ¿Por qué la Tabla 4 resta MapReduce − Spark? | Así lo pide el enunciado; un cero significa coincidencia exacta. |
| ¿Los actores están normalizados? | No. Se conservan tildes y mayúsculas; una misma persona con variantes de escritura podría contarse dos veces. Es una limitación declarada. |
| ¿Qué pasa con las 3 películas sin duración? | Quedan con `duration_min` nulo y fuera del promedio; son especiales de Louis C. K. sin duración en el origen. |
| ¿El dashboard usa Databricks en vivo? | No. Consume los CSV de resultados del pipeline. El notebook es la evidencia de SQL y PySpark; el dashboard los presenta. |

---

## Reparto sugerido

| Bloque | Minutos | Responsable |
|--------|---------|-------------|
| Portada, objetivo y proceso | 0:00 – 3:30 | Jhael |
| Reto 1 y Reto 2 | 3:30 – 8:00 | Carlos |
| Reto 3 y Reto 4 | 8:00 – 13:00 | Bryan |
| Conclusiones y dashboard | 13:00 – 15:00 | Jhael |

Ensayo recomendado: dos pasadas completas con cronómetro. Si se excede el tiempo, recortar la demo del dashboard (diapositiva 12), nunca las cifras de las conclusiones.
