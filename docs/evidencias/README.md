# Evidencias del proyecto

Esta carpeta reúne las capturas de pantalla que respaldan cada etapa. El informe
(`docs/Informe_Netflix_Elsner.pdf`) reserva una caja numerada para cada evidencia.

## Cómo insertarlas

1. Guarda la captura con el nombre exacto de la tabla de abajo (`evidencia_1.png`,
   `evidencia_2.png`, …). Se aceptan `.png`, `.jpg` y `.jpeg`.
2. Ejecuta de nuevo el generador del informe:

   ```powershell
   python docs/generar_informe.py
   ```

3. El PDF reemplaza la caja de texto por la imagen, la escala al ancho de la página y
   la limita a 78 mm de alto. La copia de `frontend/assets/` se actualiza sola.

## Capturas requeridas

| # | Etapa | Qué debe verse | Nombre sugerido |
|---|-------|----------------|-----------------|
| 1 | HDFS | `hdfs dfs -put` y `hdfs dfs -ls -h /data/netflix/clean/` con nombre y tamaño del archivo | `evidencia_1.png` |
| 2 | Hadoop | Consola con `map 100%`, `reduce 100%` y `Job ... completed successfully` | `evidencia_2.png` |
| 3 | Databricks | Tablas `netflix_clean` y `mapreduce_actores` en Catalog con conteo de filas y muestra | `evidencia_3.png` |
| 4 | Databricks | Tabla 3 completa (tres filas con «Sí» en la columna de coincidencia) | `evidencia_4.png` |
| 5 | Databricks | Tablas 4 y 5 (diez actores y resumen de los 36 439) | `evidencia_5.png` |
| 6 | Reto 4 | Los dos gráficos y la Tabla 6 dentro del notebook | `evidencia_6.png` |
| 7 | Dashboard | Las seis páginas del panel: resumen, limpieza, MapReduce, Databricks, hallazgos y catálogo | `evidencia_7.png` |

## Orden recomendado de captura

1. Ejecuta `hadoop/GUIA_HADOOP.md` y captura los pasos 1 y 2.
2. Importa `databricks/03_analisis_netflix.ipynb` siguiendo `databricks/GUIA_DATABRICKS.md`
   y captura las celdas indicadas (evidencias 3 a 6).
3. Arranca el dashboard con `python run.py`, abre `http://127.0.0.1:8000` y captura las
   seis páginas (evidencia 7).

> Las capturas deben ser legibles: usa el ancho completo de la ventana, sin recortar
> encabezados ni mensajes de error. Si una captura supera los 78 mm de alto, el
> generador la reduce manteniendo la proporción.
