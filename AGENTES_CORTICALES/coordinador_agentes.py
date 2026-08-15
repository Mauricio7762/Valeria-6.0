"""
Coordinador de Agentes Corticales
Recibe mensajes del Orquestador y los distribuye a los agentes especializados.
"""

from __future__ import annotations

from typing import Any
from loguru import logger

from .agente_memoria import AgenteMemoria
from .agente_razonamiento import AgenteRazonamiento
from .agente_emocional import AgenteEmocional
from .agente_acciones import AgenteAcciones
from .agente_percepcion import AgentePercepcion
from .agente_planificacion import AgentePlanificacion
from .agente_monitor import AgenteMonitor


class CoordinadorAgentes:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.agentes = {
            "memoria": AgenteMemoria(self.config.get("memoria")),
            "razonamiento": AgenteRazonamiento(self.config.get("razonamiento")),
            "emocional": AgenteEmocional(self.config.get("emocional")),
            "acciones": AgenteAcciones(self.config.get("acciones")),
            "percepcion": AgentePercepcion(self.config.get("percepcion")),
            "planificacion": AgentePlanificacion(self.config.get("planificacion")),
            "monitor": AgenteMonitor(self.config.get("monitor")),
        }
        logger.info(f"Coordinador de Agentes listo ({len(self.agentes)} agentes)")

    async def tick(self) -> None:
        """Ciclo de mantenimiento de todos los agentes."""
        for agente in self.agentes.values():
            await agente.tick()

    async def enviar(self, destino: str, mensaje: dict[str, Any]) -> dict[str, Any]:
        """Envía un mensaje a un agente específico."""
        agente = self.agentes.get(destino)
        if not agente:
            return {"ok": False, "error": f"Agente '{destino}' no existe"}
        return await agente.procesar(mensaje)

    async def broadcast(self, mensaje: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Envía el mismo mensaje a todos los agentes."""
        resultados = {}
        for nombre, agente in self.agentes.items():
            resultados[nombre] = await agente.procesar(mensaje)
        return resultados

    def estado(self) -> dict[str, Any]:
        return {
            nombre: agente.estado()
            for nombre, agente in self.agentes.items()
        }
