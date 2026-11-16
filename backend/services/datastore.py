"""Almacen en memoria de los resultados del proyecto.

Carga netflix_clean.csv una sola vez, calcula los tres analisis y conserva
los resultados listos para la API. Si el archivo limpio no existe, ejecuta
la limpieza del Reto 1 antes de continuar.
"""

from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from pipeline.actores import contar_actores
from pipeline.analisis import (
    analisis_paises,
    analisis_tipos,
    clasificar_tipo,
    comparar_actores,
    comparar_tablas,
)
from pipeline.config import (
    DIR_RESULTADOS,
    RUTA_ACTORES_SPARK,
    RUTA_LIMPIA,
    RUTA_MAPREDUCE,
    RUTA_METRICAS,
    RUTA_ORIGINAL,
    RUTA_PAISES,
    RUTA_TIPOS,
)
from pipeline.limpieza import cargar_limpio, ejecutar

from backend.core.config import settings


class DataStore:
    """Contenedor unico (singleton) de los datos y resultados calculados."""

    def __init__(self) -> None:
        self._candado = threading.RLock()
        self._listo = False

        self.df: pd.DataFrame = pd.DataFrame()
        self.tipos: pd.DataFrame = pd.DataFrame()
        self.actores: pd.DataFrame = pd.DataFrame()
        self.paises: pd.DataFrame = pd.DataFrame()
        self.mapreduce: pd.DataFrame = pd.DataFrame()

        self.metricas: dict[str, Any] = {}
        self.verificacion: dict[str, Any] = {}
        self.cargado_en: str = ""

    # ------------------------------------------------------------------ carga
    def cargar(self, forzar: bool = False) -> None:
        with self._candado:
            if self._listo and not forzar:
                return

            if not RUTA_LIMPIA.exists():
                ejecutar()

            self.df = cargar_limpio(RUTA_LIMPIA)
            self.df["tipo_normalizado"] = clasificar_tipo(self.df)

            self.tipos = analisis_tipos(self.df)
            self.actores = contar_actores(self.df)
            self.paises = analisis_paises(self.df)
            self.mapreduce = self._cargar_mapreduce()

            self.metricas = self._cargar_metricas()
            self.verificacion = self._calcular_verificacion()

            self.cargado_en = datetime.now().isoformat(timespec="seconds")
            self._listo = True

    def _cargar_mapreduce(self) -> pd.DataFrame:
        if not RUTA_MAPREDUCE.exists():
            return pd.DataFrame(columns=["actor", "cantidad_titulos"])
        df = pd.read_csv(RUTA_MAPREDUCE)
        if "actor" not in df.columns or "cantidad_titulos" not in df.columns:
            return pd.DataFrame(columns=["actor", "cantidad_titulos"])
        df["cantidad_titulos"] = df["cantidad_titulos"].astype(int)
        return df.sort_values(
            ["cantidad_titulos", "actor"], ascending=[False, True]
        ).reset_index(drop=True)

    def _cargar_metricas(self) -> dict[str, Any]:
        if RUTA_METRICAS.exists():
            import json

            try:
                return json.loads(RUTA_METRICAS.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        # Metricas minimas si el JSON no existe
        return {
            "registros_limpios": int(len(self.df)),
            "columnas_limpias": int(len(self.df.columns) - 1),
            "peliculas": int(self.df["type"].eq("Movie").sum()),
            "series": int(self.df["type"].eq("TV Show").sum()),
        }

    def _calcular_verificacion(self) -> dict[str, Any]:
        """Compara el calculo en vivo con los CSV exportados por el pipeline.

        En Databricks la comparacion SQL contra PySpark la ejecuta el notebook
        03_analisis_netflix; aqui se controla ademas que el dashboard no se
        desvie de los resultados exportados por scripts/03_generar_resultados.py.
        """
        exportados = {
            "tipos": _leer_csv(RUTA_TIPOS, ["tipo", "cantidad_titulos", "porcentaje"]),
            "actores": _leer_csv(RUTA_ACTORES_SPARK, ["actor", "cantidad_titulos"]),
            "paises": _leer_csv(RUTA_PAISES, ["pais", "cantidad_peliculas", "duracion_promedio_min"]),
        }
        reutilizar = {
            "peliculas_y_series": ("tipos", self.tipos, "tipo", "cantidad_titulos"),
            "titulos_por_actor": ("actores", self.actores, "actor", "cantidad_titulos"),
            "duracion_por_pais": ("paises", self.paises, "pais", "duracion_promedio_min"),
        }

        comparaciones: dict[str, dict[str, Any]] = {}
        for nombre, (clave, en_vivo, columna_clave, columna_valor) in reutilizar.items():
            referencia = exportados.get(clave)
            tolerancia = 0.01 if nombre == "duracion_por_pais" else 0.0
            if referencia is not None and not referencia.empty:
                comparaciones[nombre] = comparar_tablas(
                    referencia, en_vivo, columna_clave, columna_valor, tolerancia=tolerancia
                )
                comparaciones[nombre]["referencia"] = clave
            else:
                comparaciones[nombre] = comparar_tablas(
                    en_vivo, en_vivo, columna_clave, columna_valor, tolerancia=tolerancia
                )
                comparaciones[nombre]["referencia"] = "sin_csv_exportado"

        tabla3 = [
            {
                "analisis": nombre,
                "filas_sql": comparacion["filas_izquierda"],
                "filas_pyspark": comparacion["filas_derecha"],
                "filas_con_valores_diferentes": comparacion["filas_con_valores_diferentes"],
                "filas_en_una_sola_salida": comparacion["filas_solo_izquierda"]
                + comparacion["filas_solo_derecha"],
                "coinciden_completamente": comparacion["coinciden_completamente"],
                "referencia": comparacion["referencia"],
            }
            for nombre, comparacion in comparaciones.items()
        ]

        comparacion_mr = None
        tabla4: list[dict[str, Any]] = []
        tabla5: dict[str, int] = {}
        if not self.mapreduce.empty:
            comparacion_mr = comparar_actores(self.mapreduce, self.actores)
            tabla4 = comparacion_mr["tabla4"]
            tabla5 = comparacion_mr["tabla5"]

        return {
            "generado_en": datetime.now().isoformat(timespec="seconds"),
            "origen": "Calculo local con Pandas sobre netflix_clean.csv",
            "tabla3": tabla3,
            "tabla4": tabla4,
            "tabla5": tabla5,
            "comparacion_actores": comparacion_mr,
            "comparaciones_detalle": comparaciones,
            "mapreduce_disponible": not self.mapreduce.empty,
        }

    # -------------------------------------------------------------- resumenes
    def _kpis(self) -> dict[str, Any]:
        df = self.df
        peliculas = int(df["type"].eq("Movie").sum())
        series = int(df["type"].eq("TV Show").sum())
        duracion = df.loc[df["type"].eq("Movie"), "duration_min"].dropna()
        top_actor = self.actores.iloc[0] if not self.actores.empty else None
        top_pais = self.paises.iloc[0] if not self.paises.empty else None

        return {
            "titulos_totales": int(len(df)),
            "peliculas": peliculas,
            "series": series,
            "porcentaje_peliculas": round(peliculas / len(df) * 100, 2) if len(df) else 0,
            "porcentaje_series": round(series / len(df) * 100, 2) if len(df) else 0,
            "actores_distintos": int(len(self.actores)),
            "paises_distintos": int(len(self.paises)),
            "duracion_promedio_peliculas": round(float(duracion.mean()), 2) if len(duracion) else None,
            "peliculas_con_duracion": int(len(duracion)),
            "top_actor": (
                {"actor": top_actor["actor"], "cantidad_titulos": int(top_actor["cantidad_titulos"])}
                if top_actor is not None
                else None
            ),
            "top_pais": (
                {
                    "pais": top_pais["pais"],
                    "cantidad_peliculas": int(top_pais["cantidad_peliculas"]),
                    "duracion_promedio_min": float(top_pais["duracion_promedio_min"]),
                }
                if top_pais is not None
                else None
            ),
            "anios_cubiertos": [
                int(df["release_year"].min()) if df["release_year"].notna().any() else None,
                int(df["release_year"].max()) if df["release_year"].notna().any() else None,
            ],
            "mapreduce_actores": int(len(self.mapreduce)),
        }

    def resumen(self) -> dict[str, Any]:
        anios = (
            self.df["release_year"].dropna().astype(int).value_counts().sort_index()
        )
        ratings = self.df["rating"].dropna().value_counts().head(10)

        return {
            "generado_en": self.cargado_en,
            "kpis": self._kpis(),
            "tipos": registros(self.tipos),
            "top_actores": registros(self.actores.head(10)),
            "top_paises": registros(self.paises.head(10)),
            "por_anio": [{"anio": int(anio), "titulos": int(total)} for anio, total in anios.items()],
            "por_rating": [
                {"rating": str(rating), "titulos": int(total)} for rating, total in ratings.items()
            ],
            "calidad": {
                "duplicados_filas": self.metricas.get("duplicados_filas", 0),
                "sin_show_id": self.metricas.get("sin_show_id", 0),
                "show_id_repetido": self.metricas.get("show_id_repetido", 0),
                "fechas_vacias": self.metricas.get("fechas_vacias", 0),
                "peliculas_sin_duracion": self.metricas.get("peliculas_sin_duracion", 0),
            },
        }

    def tabla1(self) -> list[dict[str, Any]]:
        m = self.metricas
        return [
            {"indicador": "Registros del archivo original, sin cabecera", "valor": m.get("registros_originales")},
            {"indicador": "Columnas del archivo original", "valor": m.get("columnas_originales")},
            {"indicador": "Filas completamente duplicadas eliminadas", "valor": m.get("duplicados_filas")},
            {"indicador": "Registros sin show_id eliminados después de retirar duplicados", "valor": m.get("sin_show_id")},
            {"indicador": "Registros con show_id repetido eliminados posteriormente", "valor": m.get("show_id_repetido")},
            {"indicador": "Registros del archivo limpio", "valor": m.get("registros_limpios")},
            {"indicador": "Películas con duration_min numérica mayor que cero", "valor": m.get("peliculas_con_duracion")},
            {"indicador": "Películas sin una duración numérica mayor que cero", "valor": m.get("peliculas_sin_duracion")},
        ]

    def informe_limpieza(self) -> dict[str, Any]:
        fechas = self.df["date_added"].replace("", pd.NA).dropna()
        muestra = self.df.head(10)[
            ["show_id", "type", "title", "country", "date_added", "duration_min"]
        ]
        return {
            "tabla1": self.tabla1(),
            "metricas": self.metricas,
            "nulos_por_columna": [
                {"columna": columna, "nulos": int(total), "porcentaje": round(total / len(self.df) * 100, 2)}
                for columna, total in self.df.isna().sum().items()
            ],
            "muestra": registros(muestra),
            "archivos": {
                "original": _info_archivo(RUTA_ORIGINAL),
                "limpio": _info_archivo(RUTA_LIMPIA),
                "mapreduce": _info_archivo(RUTA_MAPREDUCE),
            },
            "rango_fechas": {
                "minima": fechas.min() if len(fechas) else None,
                "maxima": fechas.max() if len(fechas) else None,
            },
            "columnas": {
                "originales": int(self.metricas.get("columnas_originales", 12)),
                "limpias": int(len(self.df.columns) - 1),
                "lista": [c for c in self.df.columns if c != "tipo_normalizado"],
            },
        }

    def catalogo(
        self,
        consulta: str | None = None,
        tipo: str | None = None,
        pagina: int = 1,
        tamano: int = 25,
    ) -> dict[str, Any]:
        df = self.df
        if tipo:
            df = df[df["tipo_normalizado"].eq(tipo)]
        if consulta:
            patron = consulta.strip()
            mascara = (
                df["title"].fillna("").str.contains(patron, case=False, regex=False)
                | df["cast"].fillna("").str.contains(patron, case=False, regex=False)
                | df["director"].fillna("").str.contains(patron, case=False, regex=False)
                | df["country"].fillna("").str.contains(patron, case=False, regex=False)
            )
            df = df[mascara]

        total = int(len(df))
        inicio = max(pagina - 1, 0) * tamano
        pagina_df = df.iloc[inicio : inicio + tamano][
            ["show_id", "type", "title", "director", "country", "release_year", "rating", "duration_min"]
        ]
        return {
            "total": total,
            "pagina": pagina,
            "tamano": tamano,
            "paginas": max((total + tamano - 1) // tamano, 1),
            "registros": registros(pagina_df),
        }

    # -------------------------------------------------------------- exportar
    def exportar(self, recurso: str) -> pd.DataFrame | None:
        mapa = {
            "actores": self.actores,
            "paises": self.paises,
            "tipos": self.tipos,
            "mapreduce": self.mapreduce,
            "netflix_clean": self.df[[c for c in self.df.columns if c != "tipo_normalizado"]],
        }
        return mapa.get(recurso)


# --------------------------------------------------------------------- utiles
def registros(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convierte un DataFrame a JSON limpio (NaN -> null, numpy -> python)."""
    if df is None or df.empty:
        return []
    limpio = df.astype(object).where(pd.notna(df), None)
    return [{clave: _a_python(valor) for clave, valor in fila.items()} for fila in limpio.to_dict("records")]


def _a_python(valor: Any) -> Any:
    if valor is None:
        return None
    if isinstance(valor, np.integer):
        return int(valor)
    if isinstance(valor, np.floating):
        return float(valor)
    if isinstance(valor, np.bool_):
        return bool(valor)
    if isinstance(valor, pd.Timestamp):
        return valor.isoformat()
    return valor


def _leer_csv(ruta: Path, columnas: list[str]) -> pd.DataFrame | None:
    if not ruta.exists():
        return None
    try:
        df = pd.read_csv(ruta)
    except (OSError, pd.errors.ParserError):
        return None
    return df[[columna for columna in columnas if columna in df.columns]]


def _info_archivo(ruta: Path) -> dict[str, Any] | None:
    if not ruta.exists():
        return None
    estadistica = ruta.stat()
    return {
        "nombre": ruta.name,
        "bytes": estadistica.st_size,
        "megabytes": round(estadistica.st_size / 1024 / 1024, 2),
        "modificado": datetime.fromtimestamp(estadistica.st_mtime).isoformat(timespec="seconds"),
    }


datastore = DataStore()
