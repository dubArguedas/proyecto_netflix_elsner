#!/usr/bin/env python
"""Arranca el backend y sirve el dashboard en un solo comando.

    python run.py

Variables opcionales:
    NETFLIX_API_HOST, NETFLIX_API_PORT, NETFLIX_API_RELOAD
"""

from __future__ import annotations

import uvicorn

from backend.core.config import settings


def main() -> None:
    print(f"Dashboard : http://{settings.host}:{settings.puerto}/")
    print(f"API docs  : http://{settings.host}:{settings.puerto}/docs")
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.puerto,
        reload=settings.recargar,
        log_level="info",
    )


if __name__ == "__main__":
    main()
