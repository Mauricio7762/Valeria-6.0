"""
API HTTP de VALERIA 6.0
======================
Endpoints:
  GET  /salud
  GET  /estado
  GET  /hechos
  GET  /ayuda
  POST /chat   {"mensaje": "..."}

Arranque:
  pip install fastapi uvicorn loguru rich pyyaml psutil
  uvicorn INTERFACES.API.main:app --host 0.0.0.0 --port 8000
  Docs: http://localhost:8000/docs
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from NUCLEO_BIOMIMETICO.orquestador_principal import OrquestadorPrincipal
from NUCLEO_BIOMIMETICO.chat_comandos import (
    manejar_comando,
    cmd_estado,
    cmd_hechos,
    AYUDA,
)
from NUCLEO_BIOMIMETICO.pipeline_mensaje import procesar_mensaje
from NUCLEO_BIOMIMETICO.gestor_recursos import GestorRecursos
from NUCLEO_BIOMIMETICO.SISTEMA_GLIAL.sistema_glial import SistemaGlial
from AGENTES_CORTICALES.coordinador_agentes import CoordinadorAgentes

_orch: OrquestadorPrincipal | None = None


def _get_orch() -> OrquestadorPrincipal:
    if _orch is None:
        raise HTTPException(status_code=503, detail="VALERIA aún no está inicializada")
    return _orch


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _orch
    orch = OrquestadorPrincipal()
    orch.config = orch._cargar_config()
    orch.gestor_recursos = GestorRecursos(orch.config.get("resources", {}))
    orch.sistema_glial = SistemaGlial(orch.config.get("sistema_glial", {}))
    orch.coordinador = CoordinadorAgentes(orch.config.get("agentes", {}))
    raz = orch.coordinador.agentes.get("razonamiento")
    if raz is not None:
        raz.neurogenesis = orch.neurogenesis
    orch.estado_consciencia = "despierto"
    orch.running = True
    _orch = orch
    yield
    orch.running = False
    try:
        from NUCLEO_BIOMIMETICO.persistencia_meta import guardar_estado_meta

        guardar_estado_meta(orch.meta_ajuste, orch.curiosidad)
    except Exception:
        pass
    _orch = None


app = FastAPI(
    title="VALERIA 6.0",
    description="Cerebro Humano Digital — API de chat y estado",
    version="6.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatIn(BaseModel):
    mensaje: str = Field(..., min_length=1, max_length=4000, examples=["¿qué es valeria?"])


class ChatOut(BaseModel):
    respuesta: str
    tipo: str  # "comando" | "mensaje"


@app.get("/salud")
def salud() -> dict[str, str]:
    return {"status": "ok", "sistema": "VALERIA 6.0", "version": "6.0.0"}


@app.get("/ayuda")
def ayuda() -> dict[str, str]:
    return {"markdown": AYUDA.strip()}


@app.get("/estado")
async def estado() -> dict[str, Any]:
    orch = _get_orch()
    texto = await cmd_estado(orch)
    return {
        "markdown": texto,
        "consciencia": orch.estado_consciencia,
        "ciclos": orch._ciclo_count,
    }


@app.get("/hechos")
async def hechos() -> dict[str, Any]:
    orch = _get_orch()
    texto = await cmd_hechos(orch)
    return {"markdown": texto}


@app.post("/chat", response_model=ChatOut)
async def chat(body: ChatIn) -> ChatOut:
    orch = _get_orch()
    try:
        cmd = await manejar_comando(orch, body.mensaje)
        if cmd is not None:
            return ChatOut(respuesta=cmd or "(sin salida)", tipo="comando")
        resp = await procesar_mensaje(orch, body.mensaje)
        return ChatOut(respuesta=resp, tipo="mensaje")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
