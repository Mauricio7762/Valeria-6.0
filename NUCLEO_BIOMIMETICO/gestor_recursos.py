"""
Gestor de Recursos (Homeostasis Primaria)
========================================
Capa 1: Administración real de CPU / RAM.
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
        self.soft_limit = self.config.get("soft_limit_warning", 70)
        logger.debug("Gestor de Recursos inicializado (Capa 1)")

    def obtener_estado(self) -> dict[str, float]:
        mem = psutil.virtual_memory()
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "ram_percent": mem.percent,
            "ram_available_mb": round(mem.available / (1024 * 1024), 1),
            "ram_total_mb": round(mem.total / (1024 * 1024), 1),
        }

    def esta_bajo_presion(self) -> bool:
        estado = self.obtener_estado()
        return (
            estado["cpu_percent"] > self.max_cpu
            or estado["ram_percent"] > self.max_ram
        )

    def esta_cerca_del_limite(self) -> bool:
        estado = self.obtener_estado()
        return (
            estado["cpu_percent"] > self.soft_limit
            or estado["ram_percent"] > self.soft_limit
        )
