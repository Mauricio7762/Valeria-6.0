"""
Agente Memoria (Hipocampo / Prefrontal)
Episódica + Semántica. Por ahora memoria en RAM (luego ChromaDB/Redis).
"""

from __future__ import annotations

from typing import Any
from loguru import logger
from .base_agente import BaseAgente


class AgenteMemoria(BaseAgente):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__("Memoria", config)
        self.episodica: list[dict[str, Any]] = []
        self.semantica: dict[str, Any] = {}

    async def procesar(self, mensaje: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "error": "disabled"}

        accion = mensaje.get("accion", "recordar")
        contenido = mensaje.get("contenido")

        if accion == "guardar_episodica":
            self.episodica.append({"contenido": contenido, "meta": mensaje.get("meta", {})})
            if len(self.episodica) > 200:
                self.episodica = self.episodica[-150:]
            resultado = {"ok": True, "tipo": "episodica", "total": len(self.episodica)}

        elif accion == "guardar_semantica":
            clave = mensaje.get("clave", "default")
            self.semantica[clave] = contenido
            resultado = {"ok": True, "tipo": "semantica", "clave": clave}

        elif accion == "recuperar":
            clave = mensaje.get("clave")
            if clave and clave in self.semantica:
                resultado = {"ok": True, "dato": self.semantica[clave]}
            else:
                # Búsqueda simple en episódica
                encontrados = [e for e in self.episodica if clave and clave in str(e.get("contenido", ""))]
                resultado = {"ok": True, "encontrados": len(encontrados), "datos": encontrados[-5:]}

        else:
            resultado = {"ok": True, "msg": "Memoria en espera", "episodica": len(self.episodica), "semantica": len(self.semantica)}

        self._mensajes_procesados += 1
        self._ultimo_resultado = resultado
        return resultado

    async def tick(self) -> None:
        await super().tick()
