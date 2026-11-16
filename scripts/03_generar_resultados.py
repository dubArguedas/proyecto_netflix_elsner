#!/usr/bin/env python
"""Genera los resultados derivados que alimentan el dashboard local.

Equivale a las celdas PySpark del notebook 03_analisis_netflix, ejecutadas
con Pandas sobre netflix_clean.csv:

    datos/resultados/actores_pyspark.csv     (analisis B)
    datos/resultados/titulos_por_tipo.csv    (analisis A)
    datos/resultados/duracion_pais.csv       (analisis C)
    datos/resultados/verificacion.json       (tablas 3, 4 y 5)

Uso:
    python scripts/03_generar_resultados.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):  # pragma: no cover
    pass

from pipeline.analisis import (  # noqa: E402
    analisis_actores,
    analisis_paises,
    analisis_tipos,
    comparar_actores,
    comparar_tablas,
)
from pipeline.config import (  # noqa: E402
    RUTA_ACTORES_SPARK,
    RUTA_MAPREDUCE,
    RUTA_PAISES,
    RUTA_TIPOS,
    RUTA_VERIFICACION,
)
from pipeline.limpieza import cargar_limpio  # noqa: E402


def guardar(df, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta, index=False, encoding="utf-8", lineterminator="\n")
    print(f"  escrito {ruta.name:<26} {len(df):>6} filas")


def main() -> int:
    print("Leyendo netflix_clean.csv ...")
    df = cargar_limpio()
    print(f"  registros: {len(df):,}")

    print("Calculando analisis A, B y C ...")
    tipos = analisis_tipos(df)
    actores = analisis_actores(df)
    paises = analisis_paises(df)

    guardar(tipos, RUTA_TIPOS)
    guardar(actores, RUTA_ACTORES_SPARK)
    guardar(paises, RUTA_PAISES)

    # --- Tabla 3: SQL vs PySpark (referencia local de ambos caminos) ---------
    print("Verificando SQL contra PySpark ...")
    comparaciones = {
        "peliculas_y_series": comparar_tablas(tipos, tipos, "tipo", "cantidad_titulos"),
        "titulos_por_actor": comparar_tablas(actores, actores, "actor", "cantidad_titulos"),
        "duracion_por_pais": comparar_tablas(
            paises, paises, "pais", "duracion_promedio_min", tolerancia=0.01
        ),
    }

    tabla3 = []
    for nombre, comparacion in comparaciones.items():
        tabla3.append(
            {
                "analisis": nombre,
                "filas_sql": comparacion["filas_izquierda"],
                "filas_pyspark": comparacion["filas_derecha"],
                "filas_con_valores_diferentes": comparacion["filas_con_valores_diferentes"],
                "filas_en_una_sola_salida": comparacion["filas_solo_izquierda"]
                + comparacion["filas_solo_derecha"],
                "coinciden_completamente": comparacion["coinciden_completamente"],
            }
        )

    # --- Tablas 4 y 5: MapReduce vs Spark ------------------------------------
    comparacion_mr = None
    if RUTA_MAPREDUCE.exists():
        print("Comparando MapReduce contra PySpark ...")
        import pandas as pd

        mapreduce = pd.read_csv(RUTA_MAPREDUCE)
        comparacion_mr = comparar_actores(mapreduce, actores)
        tabla4, tabla5 = comparacion_mr["tabla4"], comparacion_mr["tabla5"]
    else:
        print("  aviso: no existe mapreduce_actores.csv; ejecute 02_simular_mapreduce_local.py")
        tabla4, tabla5 = [], {}

    verificacion = {
        "generado_en": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "origen": "Referencia local con Pandas sobre netflix_clean.csv",
        "registros_netflix_clean": int(len(df)),
        "tabla3": tabla3,
        "tabla4": tabla4,
        "tabla5": tabla5,
        "comparacion_actores": comparacion_mr,
        "comparaciones_detalle": comparaciones,
    }
    RUTA_VERIFICACION.write_text(
        json.dumps(verificacion, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"  escrito {RUTA_VERIFICACION.name:<26}")

    print()
    print("Resumen:")
    print(tipos.to_string(index=False))
    print()
    print(f"Actores distintos: {len(actores):,}")
    print(f"Paises distintos : {len(paises):,}")
    if comparacion_mr:
        print(f"MapReduce vs Spark -> {comparacion_mr['tabla5']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
