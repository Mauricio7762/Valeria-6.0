"""
Agente Emocional (Sistema Límbico / Amígdala)
Modulación afectiva del sistema.
"""

from __future__ import annotations

from typing import Any
from loguru import logger
from .base_agente import BaseAgente


class AgenteEmocional(BaseAgente):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__("Emocional", config)
        self.estado_afectivo = "neutral"
        self.intensidad = 0.3

    async def procesar(self, mensaje: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "error": "disabled"}

        texto = str(mensaje.get("contenido", "")).lower()

        # Detección muy simple de polaridad
        positivos = ["bien", "gracias", "excelente", "feliz", "amor", "genial"]
        negativos = ["mal", "odio", "triste", "enojo", "problema", "error"]

        if any(p in texto for p in positivos):
            self.estado_afectivo = "positivo"
            self.intensidad = min(1.0, self.intensidad + 0.15)
        elif any(n in texto for n in negativos):
            self.estado_afectivo = "negativo"
            self.intensidad = min(1.0, self.intensidad + 0.15)
        else:
            self.intensidad = max(0.1, self.intensidad - 0.05)
            if self.intensidad < 0.25:
                self.estado_afectivo = "neutral"

        resultado = {
            "ok": True,
            "estado_afectivo": self.estado_afectivo,
            "intensidad": round(self.intensidad, 2),
            "modulacion": self._modular_respuesta(),
        }

        self._mensajes_procesados += 1
        self._ultimo_resultado = resultado
        return resultado

    def _modular_respuesta(self) -> str:
        if self.estado_afectivo == "positivo":
            return "tono cálido y entusiasta"
        if self.estado_afectivo == "negativo":
            return "tono empático y calmado"
        return "tono neutro y profesional"

    async def tick(self) -> None:
        # Decaimiento natural de la intensidad
        self.intensidad = max(0.1, self.intensidad - 0.01)
        await super().tick()
