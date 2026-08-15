"""
Agente Razonamiento (Prefrontal Dorsolateral)
Lógica, Chain-of-Thought, RAG básico.
"""

from __future__ import annotations

from typing import Any
from loguru import logger
from .base_agente import BaseAgente


class AgenteRazonamiento(BaseAgente):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__("Razonamiento", config)

    async def procesar(self, mensaje: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "error": "disabled"}

        pregunta = mensaje.get("pregunta") or mensaje.get("contenido") or ""
        # Placeholder de razonamiento estructurado
        pasos = [
            f"1. Entender la pregunta: {pregunta[:60]}...",
            "2. Buscar conocimiento relevante (RAG futuro)",
            "3. Aplicar lógica / CoT",
            "4. Formular respuesta",
        ]
        resultado = {
            "ok": True,
            "razonamiento": pasos,
            "conclusion": f"[Placeholder] Respuesta a: {pregunta[:80]}",
        }

        self._mensajes_procesados += 1
        self._ultimo_resultado = resultado
        logger.debug(f"Razonamiento procesó: {pregunta[:40]}...")
        return resultado

    async def tick(self) -> None:
        await super().tick()
