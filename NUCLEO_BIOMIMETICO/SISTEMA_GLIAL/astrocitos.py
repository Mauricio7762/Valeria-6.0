"""
Astrocitos - Regulación y Homeostasis Cognitiva
===============================================
Capa 1: Versión funcional con balanceo de carga real.
"""

from __future__ import annotations

from typing import Any

import psutil
from loguru import logger


class Astrocitos:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)

        lb = self.config.get("load_balancing", {})
        self.reduce_threshold = lb.get("reduce_vision_threshold", 0.85)

        att = self.config.get("attention", {})
        self.max_hot_contexts = att.get("max_hot_contexts", 12)

        self.hot_contexts: list[str] = []
        self.current_load: float = 0.0
        self.throttling: bool = False
        self._regulaciones = 0

        logger.debug("Astrocitos listos (Capa 1)")

    async def regular(self) -> None:
        if not self.enabled:
            return

        cpu = psutil.cpu_percent(interval=0.05)
        ram = psutil.virtual_memory().percent
        self.current_load = max(cpu, ram) / 100.0

        if self.current_load >= self.reduce_threshold:
            if not self.throttling:
                logger.warning(
                    f"Astrocitos: carga alta ({self.current_load:.0%}) → activando throttling"
                )
                self.throttling = True
        else:
            if self.throttling and self.current_load < self.reduce_threshold * 0.8:
                logger.info("Astrocitos: carga normalizada → desactivando throttling")
                self.throttling = False

        if len(self.hot_contexts) > self.max_hot_contexts:
            self.hot_contexts = self.hot_contexts[-self.max_hot_contexts:]

        self._regulaciones += 1

    def estado(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "current_load": round(self.current_load, 3),
            "throttling": self.throttling,
            "hot_contexts": len(self.hot_contexts),
            "regulaciones": self._regulaciones,
        }
