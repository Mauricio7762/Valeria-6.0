"""
Agente Percepción (Cortezas Sensoriales)
Entrada multimodal: texto, (futuro: visión, audio, OCR).
"""

from __future__ import annotations

from typing import Any
from loguru import logger
from .base_agente import BaseAgente


class AgentePercepcion(BaseAgente):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__("Percepcion", config)
        self.ultima_entrada: dict[str, Any] | None = None

    async def procesar(self, mensaje: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "error": "disabled"}

        tipo = mensaje.get("tipo", "texto")
        contenido = mensaje.get("contenido", "")

        # Normalización básica
        entrada_normalizada = {
            "tipo": tipo,
            "contenido": str(contenido).strip(),
            "longitud": len(str(contenido)),
            "idioma_detectado": "es",  # placeholder
        }

        self.ultima_entrada = entrada_normalizada

        resultado = {
            "ok": True,
            "percepcion": entrada_normalizada,
            "msg": f"Entrada de tipo '{tipo}' percibida correctamente",
        }

        self._mensajes_procesados += 1
        self._ultimo_resultado = resultado
        return resultado

    async def tick(self) -> None:
        await super().tick()
