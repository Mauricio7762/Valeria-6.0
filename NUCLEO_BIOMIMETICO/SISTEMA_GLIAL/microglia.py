"""
Microglía - Limpieza, Defensa y Poda (Sistema Inmune)
====================================================
Capa 1: Versión funcional con garbage collection básico.
"""

from __future__ import annotations

import time
from typing import Any

from loguru import logger


class Microglia:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)

        gc_cfg = self.config.get("garbage_collection", {})
        self.gc_interval = gc_cfg.get("interval_seconds", 30)
        self.obsolete_ttl = gc_cfg.get("obsolete_context_ttl_seconds", 600)

        self.contextos: dict[str, float] = {}
        self.cleaned_contexts = 0
        self.pruned_routes = 0
        self.quarantined_modules: list[str] = []
        self._ultimo_gc = time.time()
        self._limpiezas = 0

        logger.debug("Microglía lista (Capa 1)")

    def registrar_contexto(self, context_id: str) -> None:
        self.contextos[context_id] = time.time()

    async def limpiar_y_defender(self) -> None:
        if not self.enabled:
            return

        ahora = time.time()
        if ahora - self._ultimo_gc < self.gc_interval:
            return

        obsoletos = [
            cid for cid, ts in self.contextos.items()
            if ahora - ts > self.obsolete_ttl
        ]
        for cid in obsoletos:
            del self.contextos[cid]
            self.cleaned_contexts += 1

        if obsoletos:
            logger.debug(f"Microglía: limpiados {len(obsoletos)} contextos obsoletos")

        self._ultimo_gc = ahora
        self._limpiezas += 1

    def poner_en_cuarentena(self, modulo: str) -> None:
        if modulo not in self.quarantined_modules:
            self.quarantined_modules.append(modulo)
            logger.warning(f"Microglía: módulo en cuarentena → {modulo}")

    def estado(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "active_contexts": len(self.contextos),
            "cleaned_contexts": self.cleaned_contexts,
            "pruned_routes": self.pruned_routes,
            "quarantined_modules": self.quarantined_modules,
            "limpiezas": self._limpiezas,
        }
