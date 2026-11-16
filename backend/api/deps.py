"""Dependencias compartidas de la API."""

from __future__ import annotations

from backend.services.datastore import DataStore, datastore


def obtener_datastore() -> DataStore:
    """Entrega el almacen ya cargado (se inicializa en el arranque)."""
    datastore.cargar()
    return datastore
