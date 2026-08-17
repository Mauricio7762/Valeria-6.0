"""
Agente Percepción (Cortezas Sensoriales)
========================================
Entrada multimodal: texto, imagen, audio (normalizados a texto_para_razonar).
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from .base_agente import BaseAgente
from PROCESAMIENTO_MULTIMODAL.normalizador_entrada import NormalizadorEntrada


class AgentePercepcion(BaseAgente):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__("Percepcion", config)
        self.ultima_entrada: dict[str, Any] | None = None
        self.normalizador = NormalizadorEntrada()

    async def procesar(self, mensaje: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "error": "disabled"}

        # Si ya viene normalizado completo
        if mensaje.get("percepcion_normalizada"):
            entrada = mensaje["percepcion_normalizada"]
        else:
            tipo = mensaje.get("tipo", "texto")
            contenido = mensaje.get("contenido", "")
            if tipo == "imagen":
                entrada = self.normalizador.normalizar_imagen(
                    nombre=str(mensaje.get("nombre") or "imagen"),
                    tamaño_bytes=int(mensaje.get("tamaño_bytes") or 0),
                    caption=mensaje.get("caption") or (contenido if contenido else None),
                    ruta=mensaje.get("ruta"),
                    mime=mensaje.get("mime"),
                )
            elif tipo == "audio":
                entrada = self.normalizador.normalizar_audio(
                    nombre=str(mensaje.get("nombre") or "audio"),
                    tamaño_bytes=int(mensaje.get("tamaño_bytes") or 0),
                    transcripcion=mensaje.get("transcripcion") or (contenido if contenido else None),
                    ruta=mensaje.get("ruta"),
                    mime=mensaje.get("mime"),
                )
            else:
                entrada = self.normalizador.normalizar_texto(str(contenido))

        self.ultima_entrada = entrada
        resultado = {
            "ok": True,
            "percepcion": entrada,
            "texto_para_razonar": entrada.get("texto_para_razonar", ""),
            "msg": f"Entrada '{entrada.get('tipo')}' percibida",
        }
        self._mensajes_procesados += 1
        self._ultimo_resultado = resultado
        return resultado

    async def tick(self) -> None:
        await super().tick()
