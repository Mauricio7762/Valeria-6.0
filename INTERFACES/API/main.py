"""
API mínima FastAPI para VALERIA 6.0
===================================
POST /chat  {"mensaje": "..."}
GET  /estado
GET  /salud

Uso:
  pip install fastapi uvicorn
  uvicorn INTERFACES.API.main:app --reload
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from NUCLEO_BIOMIMETICO.orquestador_principal import OrquestadorPrincipal
from NUCLEO_BIOMIMETICO.chat_comandos import manejar_comando
from NUCLEO_BIOMIMETICO.pipeline_mensaje import procesar_mensaje

_orch: OrquestadorPrincipal | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _orch
    _orch = OrquestadorPrincipal()
    _orch.config = _orch._cargar_config()
    from NUCLEO_BIOMIMETICO.gestor_recursos import GestorRecursos
    from NUCLEO_BIOMIMETICO.SISTEMA_GLIAL.sistema_glial import SistemaGlial
    from AGENTES_CORTICALES.coordinador_agentes import CoordinadorAgentes

    _orch.gestor_recursos = GestorRecursos(_orch.config.get("resources", {}))
    _orch.sistema_glial = SistemaGlial(_orch.config.get("sistema_glial", {}))
    _orch.coordinador = CoordinadorAgentes(_orch.config.get("agentes", {}))
    raz = _orch.coordinador.agentes.get("razonamiento")
    if raz is not None:
        raz.neurogenesis = _orch.neurogenesis
    _orch.estado_consciencia = "despierto"
    _orch.running = True
    yield
    _orch.running = False


app = FastAPI(title="VALERIA 6.0", version="6.0.0", lifespan=lifespan)


class ChatIn(BaseModel):
    mensaje: str = Field(..., min_length=1, max_length=4000)


class ChatOut(BaseModel):
    respuesta: str
    tipo: str  # comando | mensaje


@app.get("/salud")
def salud() -> dict[str, str]:
    return {"status": "ok", "sistema": "VALERIA 6.0"}


@app.get("/estado")
async def estado() -> dict[str, Any]:
    assert _orch is not None
    from NUCLEO_BIOMIMETICO.chat_comandos import cmd_estado

    texto = await cmd_estado(_orch)
    return {"markdown": texto, "consciencia": _orch.estado_consciencia}


@app.post("/chat", response_model=ChatOut)
async def chat(body: ChatIn) -> ChatOut:
    assert _orch is not None
    cmd = await manejar_comando(_orch, body.mensaje)
    if cmd is not None:
        return ChatOut(respuesta=cmd or "(apagado)", tipo="comando")
    resp = await procesar_mensaje(_orch, body.mensaje)
    return ChatOut(respuesta=resp, tipo="mensaje")
