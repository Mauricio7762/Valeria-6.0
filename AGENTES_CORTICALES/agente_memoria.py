"""
Agente Memoria (Hipocampo / Prefrontal)
========================================
Jerarquía simplificada:
  - trabajo: buffer corto de la conversación actual
  - episódica: eventos con timestamp (persistente JSON)
  - semántica: claves/valores + vínculo con el grafo de razonamiento
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from loguru import logger

from .base_agente import BaseAgente

_ROOT = Path(__file__).resolve().parent.parent
_RUTA_EPISODICA = _ROOT / "DATA" / "MEMORY" / "episodica" / "episodios.json"


class AgenteMemoria(BaseAgente):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__("Memoria", config)
        cfg = config or {}
        self._ruta_episodica = Path(cfg.get("ruta_episodica", _RUTA_EPISODICA))
        self.max_episodica = int(cfg.get("max_episodica", 300))
        self.max_trabajo = int(cfg.get("max_trabajo", 20))

        self.trabajo: list[dict[str, Any]] = []
        self.episodica: list[dict[str, Any]] = []
        self.semantica: dict[str, Any] = {}

        cargados = self._cargar_episodica()
        if cargados:
            logger.debug(f"Memoria: {cargados} episodios cargados desde disco")

    def _cargar_episodica(self) -> int:
        if not self._ruta_episodica.exists():
            return 0
        try:
            datos = json.loads(self._ruta_episodica.read_text(encoding="utf-8"))
            self.episodica = list(datos.get("episodios", []))[-self.max_episodica :]
            return len(self.episodica)
        except (json.JSONDecodeError, OSError):
            return 0

    def _guardar_episodica(self) -> None:
        self._ruta_episodica.parent.mkdir(parents=True, exist_ok=True)
        payload = {"episodios": self.episodica[-self.max_episodica :]}
        tmp = self._ruta_episodica.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self._ruta_episodica)

    def _push_trabajo(self, rol: str, contenido: str, meta: dict | None = None) -> None:
        self.trabajo.append(
            {
                "rol": rol,
                "contenido": contenido,
                "meta": meta or {},
                "ts": time.time(),
            }
        )
        if len(self.trabajo) > self.max_trabajo:
            self.trabajo = self.trabajo[-self.max_trabajo :]

    async def procesar(self, mensaje: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "error": "disabled"}

        accion = mensaje.get("accion", "recordar")
        contenido = mensaje.get("contenido")
        meta = mensaje.get("meta") or {}

        if accion == "guardar_episodica":
            episodio = {
                "contenido": contenido,
                "meta": meta,
                "ts": time.time(),
            }
            self.episodica.append(episodio)
            if len(self.episodica) > self.max_episodica:
                self.episodica = self.episodica[-self.max_episodica :]
            self._push_trabajo("usuario", str(contenido), meta)
            self._guardar_episodica()
            resultado = {
                "ok": True,
                "tipo": "episodica",
                "total": len(self.episodica),
                "persistido": True,
            }

        elif accion == "guardar_respuesta":
            self._push_trabajo("valeria", str(contenido), meta)
            resultado = {"ok": True, "tipo": "trabajo", "total": len(self.trabajo)}

        elif accion == "guardar_semantica":
            clave = str(mensaje.get("clave", "default"))
            self.semantica[clave] = contenido
            resultado = {"ok": True, "tipo": "semantica", "clave": clave}

        elif accion == "recuperar":
            consulta = str(mensaje.get("clave") or contenido or "").lower().strip()
            resultado = self._recuperar(consulta)

        elif accion == "contexto_reciente":
            n = int(mensaje.get("n", 5))
            resultado = {
                "ok": True,
                "trabajo": self.trabajo[-n:],
                "episodios_recientes": self.episodica[-n:],
            }

        else:
            resultado = {
                "ok": True,
                "msg": "Memoria en espera",
                "trabajo": len(self.trabajo),
                "episodica": len(self.episodica),
                "semantica": len(self.semantica),
            }

        self._mensajes_procesados += 1
        self._ultimo_resultado = resultado
        return resultado

    def _recuperar(self, consulta: str) -> dict[str, Any]:
        if not consulta:
            return {
                "ok": True,
                "encontrados": 0,
                "datos": [],
                "semantica": None,
            }

        # Semántica exacta
        if consulta in self.semantica:
            return {
                "ok": True,
                "encontrados": 1,
                "dato_semantico": self.semantica[consulta],
                "datos": [],
            }

        # Búsqueda por palabras en episódica (más recientes primero)
        tokens = [t for t in consulta.replace("?", " ").split() if len(t) > 2]
        puntuados: list[tuple[int, dict]] = []
        for ep in reversed(self.episodica):
            texto = str(ep.get("contenido", "")).lower()
            score = sum(1 for t in tokens if t in texto)
            if score:
                puntuados.append((score, ep))
        puntuados.sort(key=lambda x: x[0], reverse=True)
        datos = [ep for _, ep in puntuados[:8]]

        return {
            "ok": True,
            "encontrados": len(datos),
            "datos": datos,
            "tokens": tokens,
        }

    async def tick(self) -> None:
        await super().tick()

    def estado(self) -> dict[str, Any]:
        base = super().estado()
        base.update(
            {
                "trabajo": len(self.trabajo),
                "episodica": len(self.episodica),
                "semantica_claves": len(self.semantica),
            }
        )
        return base
