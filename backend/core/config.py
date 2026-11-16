"""Configuracion del backend (sin dependencias externas)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.config import RAIZ_PROYECTO


@dataclass(frozen=True)
class Settings:
    app_name: str = "API Analisis Netflix - Equipo Elsner"
    version: str = "1.0.0"
    descripcion: str = (
        "Resultados del proyecto de Tecnologias Emergentes I: limpieza con Pandas, "
        "MapReduce sobre HDFS y analisis SQL / PySpark en Databricks."
    )
    host: str = os.getenv("NETFLIX_API_HOST", "127.0.0.1")
    puerto: int = int(os.getenv("NETFLIX_API_PORT", "8000"))
    recargar: bool = os.getenv("NETFLIX_API_RELOAD", "1") == "1"
    dir_frontend: Path = RAIZ_PROYECTO / "frontend"
    cors_origins: list[str] = field(
        default_factory=lambda: [
            origen.strip()
            for origen in os.getenv("NETFLIX_CORS_ORIGINS", "*").split(",")
            if origen.strip()
        ]
    )
    limite_maximo: int = 5000
    recursos_exportables: tuple[str, ...] = (
        "actores",
        "paises",
        "tipos",
        "mapreduce",
        "netflix_clean",
    )


settings = Settings()
