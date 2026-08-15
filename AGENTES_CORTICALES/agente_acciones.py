"""
Agente Acciones (Corteza Motora)
Ejecución de APIs, plugins y herramientas.
"""

from __future__ import annotations

from typing import Any
from loguru import logger
from .base_agente import BaseAgente


class AgenteAcciones(BaseAgente):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__("Acciones", config)
        self.historial_acciones: list[dict[str, Any]] = []

    async def procesar(self, mensaje: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "error": "disabled"}

        accion = mensaje.get("accion", "noop")
        params = mensaje.get("params", {})

        # Por ahora solo registramos (luego se conectarán herramientas reales)
        registro = {"accion": accion, "params": params, "estado": "simulada"}
        self.historial_acciones.append(registro)
        if len(self.historial_acciones) > 100:
            self.historial_acciones = self.historial_acciones[-50:]

        resultado = {
            "ok": True,
            "accion_ejecutada": accion,
            "mensaje": f"Acción '{accion}' registrada (modo simulación)",
            "total_historial": len(self.historial_acciones),
        }

        self._mensajes_procesados += 1
        self._ultimo_resultado = resultado
        logger.debug(f"Acciones: {accion}")
        return resultado

    async def tick(self) -> None:
        await super().tick()
