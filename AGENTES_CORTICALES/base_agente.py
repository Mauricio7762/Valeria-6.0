"""
Clase base para todos los Agentes Corticales.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from loguru import logger


class BaseAgente(ABC):
    """Interfaz común de todos los agentes corticales."""

    def __init__(self, nombre: str, config: dict[str, Any] | None = None) -> None:
        self.nombre = nombre
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self._mensajes_procesados = 0
        self._ultimo_resultado: Any = None
        logger.debug(f"Agente [{self.nombre}] inicializado")

    @abstractmethod
    async def procesar(self, mensaje: dict[str, Any]) -> dict[str, Any]:
        """Procesa un mensaje y devuelve un resultado."""
        ...

    async def tick(self) -> None:
        """Ciclo de mantenimiento del agente (llamado por el coordinador)."""
        if not self.enabled:
            return

    def estado(self) -> dict[str, Any]:
        return {
            "nombre": self.nombre,
            "enabled": self.enabled,
            "mensajes_procesados": self._mensajes_procesados,
            "ultimo_resultado": str(self._ultimo_resultado)[:80] if self._ultimo_resultado else None,
        }
