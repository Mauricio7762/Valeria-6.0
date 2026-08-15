"""
Oligodendrocitos - Mielinización / Optimización de Rutas
=======================================================
Capa 1: Versión funcional con caché de rutas.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from loguru import logger


class Oligodendrocitos:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)

        cache_cfg = self.config.get("cache", {})
        self.max_entries = cache_cfg.get("max_entries", 512)

        myelin_cfg = self.config.get("myelinization", {})
        self.min_hits = myelin_cfg.get("min_hits_to_myelinize", 5)

        self.route_hits: dict[str, int] = defaultdict(int)
        self.route_cache: dict[str, Any] = {}
        self.myelinated_routes: set[str] = set()
        self._mielinizaciones = 0

        logger.debug("Oligodendrocitos listos (Capa 1)")

    def registrar_ruta(self, ruta: str) -> None:
        if not self.enabled:
            return
        self.route_hits[ruta] += 1
        if self.route_hits[ruta] >= self.min_hits and ruta not in self.myelinated_routes:
            self.myelinated_routes.add(ruta)
            self._mielinizaciones += 1
            logger.info(f"Oligodendrocitos: ruta mielinizada → {ruta}")

    async def mielinizar(self) -> None:
        if not self.enabled:
            return
        if len(self.route_cache) > self.max_entries:
            sorted_routes = sorted(self.route_hits.items(), key=lambda x: x[1], reverse=True)
            keep = {r for r, _ in sorted_routes[: self.max_entries // 2]}
            self.route_cache = {k: v for k, v in self.route_cache.items() if k in keep}

    def estado(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "cached_routes": len(self.route_cache),
            "myelinated_routes": len(self.myelinated_routes),
            "total_hits": sum(self.route_hits.values()),
            "mielinizaciones": self._mielinizaciones,
        }
