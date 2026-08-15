"""
Gestor de Recursos (Homeostasis Primaria)
========================================
Administración de CPU / GPU / RAM y límites del sistema.
"""

from __future__ import annotations

from typing import Any

import psutil
from loguru import logger


class GestorRecursos:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.max_cpu = self.config.get("max_cpu_percent", 80)
        self.max_ram = self.config.get("max_ram_percent", 75)
        logger.debug("Gestor de Recursos inicializado")

    def obtener_estado(self) -> dict[str, float]:
        """Devuelve el uso actual de recursos."""
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "ram_percent": psutil.virtual_memory().percent,
            "ram_available_mb": psutil.virtual_memory().available / (1024 * 1024),
        }

    def esta_bajo_presion(self) -> bool:
        estado = self.obtener_estado()
        return (
            estado["cpu_percent"] > self.max_cpu
            or estado["ram_percent"] > self.max_ram
        )
