"""
Agente Monitor (Cingulada Anterior)
Métricas internas y ajuste del sistema.
"""

from __future__ import annotations

from typing import Any
from loguru import logger
from .base_agente import BaseAgente


class AgenteMonitor(BaseAgente):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__("Monitor", config)
        self.metricas: dict[str, Any] = {
            "ciclos_totales": 0,
            "errores": 0,
            "alertas": [],
        }

    async def procesar(self, mensaje: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "error": "disabled"}

        tipo = mensaje.get("tipo", "ping")

        if tipo == "reporte":
            resultado = {"ok": True, "metricas": self.metricas.copy()}
        elif tipo == "alerta":
            alerta = mensaje.get("alerta", "desconocida")
            self.metricas["alertas"].append(alerta)
            if len(self.metricas["alertas"]) > 50:
                self.metricas["alertas"] = self.metricas["alertas"][-30:]
            resultado = {"ok": True, "alerta_registrada": alerta}
        else:
            resultado = {"ok": True, "msg": "Monitor activo", "ciclos": self.metricas["ciclos_totales"]}

        self._mensajes_procesados += 1
        self._ultimo_resultado = resultado
        return resultado

    async def tick(self) -> None:
        self.metricas["ciclos_totales"] += 1
        await super().tick()
