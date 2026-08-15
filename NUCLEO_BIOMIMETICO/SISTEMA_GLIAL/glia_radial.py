"""
Glía Radial - Soporte Estructural y Reconfiguración
==================================================
Capa 1: Versión funcional con andamiaje básico.
"""

from __future__ import annotations

from typing import Any

from loguru import logger


class GliaRadial:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)

        self.structural_support = self.config.get("structural_support", True)
        self.guide_new_routes = self.config.get("guide_new_routes", True)

        self.active_scaffolds = 0
        self.rutas_guiadas = 0
        self._soportes = 0

        logger.debug("Glía Radial lista (Capa 1)")

    async def soportar_estructura(self) -> None:
        if not self.enabled:
            return
        self._soportes += 1
        if self.structural_support and self.active_scaffolds == 0:
            self.active_scaffolds = 1

    def guiar_nueva_ruta(self, origen: str, destino: str) -> bool:
        if not self.enabled or not self.guide_new_routes:
            return False
        self.rutas_guiadas += 1
        logger.info(f"Glía Radial: guiando ruta {origen} → {destino}")
        return True

    def estado(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "active_scaffolds": self.active_scaffolds,
            "rutas_guiadas": self.rutas_guiadas,
            "soportes": self._soportes,
        }
