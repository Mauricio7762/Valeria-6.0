"""
Agente Planificación (Prefrontal)
Objetivos a largo plazo y descomposición de tareas.
"""

from __future__ import annotations

from typing import Any
from loguru import logger
from .base_agente import BaseAgente


class AgentePlanificacion(BaseAgente):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__("Planificacion", config)
        self.objetivos: list[dict[str, Any]] = []
        self.plan_actual: list[str] = []

    async def procesar(self, mensaje: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "error": "disabled"}

        accion = mensaje.get("accion", "estado")
        objetivo = mensaje.get("objetivo")

        if accion == "nuevo_objetivo" and objetivo:
            self.objetivos.append({"objetivo": objetivo, "estado": "pendiente"})
            # Descomposición simple
            self.plan_actual = [
                f"Analizar: {objetivo}",
                "Recuperar conocimiento relevante",
                "Generar pasos de acción",
                "Ejecutar y monitorear",
            ]
            resultado = {"ok": True, "objetivo_agregado": objetivo, "plan": self.plan_actual}

        elif accion == "estado":
            resultado = {
                "ok": True,
                "objetivos_activos": len([o for o in self.objetivos if o["estado"] == "pendiente"]),
                "plan_actual": self.plan_actual,
            }
        else:
            resultado = {"ok": True, "msg": "Planificación en espera"}

        self._mensajes_procesados += 1
        self._ultimo_resultado = resultado
        return resultado

    async def tick(self) -> None:
        await super().tick()
