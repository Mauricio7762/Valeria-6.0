"""
Sistema Glial Computacional - Coordinador Global
================================================
Orquesta Astrocitos, Oligodendrocitos, Microglía y Glía Radial.
Mantiene la homeostasis, eficiencia y estabilidad del entorno cognitivo.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from .astrocitos import Astrocitos
from .oligodendrocitos import Oligodendrocitos
from .microglia import Microglia
from .glia_radial import GliaRadial


class SistemaGlial:
    """
    Coordinador global de la infraestructura glial.
    No genera pensamiento; garantiza que el pensamiento sea posible,
    estable y eficiente.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)

        self.astrocitos = Astrocitos(self.config.get("astrocitos", {}))
        self.oligodendrocitos = Oligodendrocitos(self.config.get("oligodendrocitos", {}))
        self.microglia = Microglia(self.config.get("microglia", {}))
        self.glia_radial = GliaRadial(self.config.get("glia_radial", {}))

        logger.info("Sistema Glial inicializado")

    async def tick(self) -> None:
        """
        Ciclo de mantenimiento glial.
        Se ejecuta periódicamente desde el Orquestador.
        """
        if not self.enabled:
            return

        # Orden de ejecución recomendado (inspirado en biología)
        await self.astrocitos.regular()
        await self.oligodendrocitos.mielinizar()
        await self.microglia.limpiar_y_defender()
        await self.glia_radial.soportar_estructura()

    def estado(self) -> dict[str, Any]:
        """Devuelve el estado actual de toda la infraestructura glial."""
        return {
            "enabled": self.enabled,
            "astrocitos": self.astrocitos.estado(),
            "oligodendrocitos": self.oligodendrocitos.estado(),
            "microglia": self.microglia.estado(),
            "glia_radial": self.glia_radial.estado(),
        }
