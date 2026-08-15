"""
Sistema Glial Computacional - Coordinador Global
================================================
Capa 1: Versión funcional.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from .astrocitos import Astrocitos
from .oligodendrocitos import Oligodendrocitos
from .microglia import Microglia
from .glia_radial import GliaRadial


class SistemaGlial:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)

        self.astrocitos = Astrocitos(self.config.get("astrocitos", {}))
        self.oligodendrocitos = Oligodendrocitos(self.config.get("oligodendrocitos", {}))
        self.microglia = Microglia(self.config.get("microglia", {}))
        self.glia_radial = GliaRadial(self.config.get("glia_radial", {}))

        self._ticks = 0
        logger.info("Sistema Glial inicializado (Capa 1 funcional)")

    async def tick(self) -> None:
        if not self.enabled:
            return

        self._ticks += 1

        await self.astrocitos.regular()
        await self.oligodendrocitos.mielinizar()
        await self.microglia.limpiar_y_defender()
        await self.glia_radial.soportar_estructura()

        if self._ticks % 20 == 0:
            logger.debug(f"Sistema Glial → tick #{self._ticks} completado")

    def estado(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "ticks": self._ticks,
            "astrocitos": self.astrocitos.estado(),
            "oligodendrocitos": self.oligodendrocitos.estado(),
            "microglia": self.microglia.estado(),
            "glia_radial": self.glia_radial.estado(),
        }
