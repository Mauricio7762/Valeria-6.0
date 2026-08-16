"""
Agente Razonamiento (Prefrontal Dorsolateral)
==============================================
Razonamiento simbólico real (Route C): NLP por patrones + grafo de
conocimiento + motor de inferencia (deductiva / abductiva / CBR) +
NLG estructurado. Sin dependencia de ningún LLM.

Además de responder preguntas, este agente APRENDE: si el usuario
afirma algo ("la microglía es parte del sistema glial"), lo guarda
como hecho nuevo en el grafo y lo persiste en disco (JSON), así el
conocimiento sobrevive a que se cierre el proceso.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from loguru import logger

from .base_agente import BaseAgente
from .razonamiento import (
    AnalizadorPatrones,
    GeneradorNLG,
    GrafoConocimiento,
    MotorInferencia,
    cargar_semilla,
    extraer_hecho,
)
from .razonamiento.grafo_conocimiento import normalizar

# Intenciones para las que abducción (buscar causa) es la estrategia natural
_INTENCIONES_CAUSALES = {"causal"}

# Repo root: AGENTES_CORTICALES/agente_razonamiento.py -> parent.parent
_ROOT = Path(__file__).resolve().parent.parent
_RUTA_GRAFO_DEFAULT = _ROOT / "DATA" / "MEMORY" / "semantica" / "grafo_conocimiento.json"


class AgenteRazonamiento(BaseAgente):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__("Razonamiento", config)
        self.grafo = GrafoConocimiento()
        self.motor = MotorInferencia(self.grafo)
        self.nlp = AnalizadorPatrones()
        self.nlg = GeneradorNLG()

        self._ruta_persistencia = Path(
            (self.config or {}).get("ruta_grafo", _RUTA_GRAFO_DEFAULT)
        )

        n_semilla = cargar_semilla(self.grafo)
        n_aprendido = self.grafo.cargar(self._ruta_persistencia)
        logger.debug(
            f"Razonamiento: {n_semilla} hechos semilla + "
            f"{n_aprendido} hechos aprendidos cargados desde {self._ruta_persistencia}"
        )

    async def procesar(self, mensaje: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "error": "disabled"}

        texto = mensaje.get("pregunta") or mensaje.get("contenido") or ""

        hecho = extraer_hecho(texto)
        if hecho:
            return self._aprender(texto, hecho)

        plan = mensaje.get("plan_estrategias")
        return self._responder_pregunta(texto, estrategias=plan)

    def _aprender(self, texto: str, hecho) -> dict[str, Any]:
        agregado = self.grafo.agregar_hecho(
            hecho.sujeto, hecho.relacion, hecho.objeto, confianza=0.9, origen="usuario"
        )
        self.grafo.guardar(self._ruta_persistencia)

        conclusion_texto = self.nlg.generar_aprendizaje(
            agregado.sujeto, agregado.relacion, agregado.objeto
        )
        resultado = {
            "ok": True,
            "intencion": "enseñanza",
            "estrategia": "aprendizaje",
            "confianza": agregado.confianza,
            "razonamiento": [
                f"1. Detectada afirmación (no pregunta): \"{texto}\"",
                f"2. Hecho extraído: {agregado.as_tupla()}",
                f"3. Guardado en el grafo y persistido en {self._ruta_persistencia.name}",
            ],
            "conclusion": conclusion_texto,
        }
        self._mensajes_procesados += 1
        self._ultimo_resultado = resultado
        logger.debug(f"Razonamiento aprendió: {agregado.as_tupla()}")
        return resultado

    def _responder_pregunta(self, pregunta: str, estrategias: list[str] | None = None) -> dict[str, Any]:
        analisis = self.nlp.analizar(pregunta)
        pasos: list[str] = [
            f"1. Analizar pregunta -> intención: {analisis.intencion}, "
            f"entidad: {analisis.entidad_principal or '—'}"
        ]
        if estrategias:
            pasos.append(f"1b. Plan metacognitivo: {' → '.join(estrategias)}")

        inferencia = self._razonar(analisis, estrategias=estrategias)
        pasos.append("2. Estrategia elegida: " + inferencia.estrategia)
        pasos.extend(f"   - {p}" for p in inferencia.pasos)

        conclusion_texto = self.nlg.generar(inferencia, pregunta)
        pasos.append(f"3. Generar respuesta ({inferencia.estrategia}, confianza {inferencia.confianza})")

        if inferencia.conclusion:
            self.motor.registrar_caso(pregunta, analisis.palabras_clave, inferencia.conclusion)

        resultado = {
            "ok": True,
            "intencion": analisis.intencion,
            "estrategia": inferencia.estrategia,
            "confianza": inferencia.confianza,
            "razonamiento": pasos,
            "conclusion": conclusion_texto,
        }

        self._mensajes_procesados += 1
        self._ultimo_resultado = resultado
        logger.debug(f"Razonamiento ({inferencia.estrategia}) procesó: {pregunta[:40]}...")
        return resultado

    def _razonar(self, analisis, estrategias: list[str] | None = None):
        entidad = normalizar(analisis.entidad_principal) if analisis.entidad_principal else None
        orden = estrategias or []

        # Plan por defecto si no viene de metacognición
        if not orden:
            if analisis.intencion in _INTENCIONES_CAUSALES and entidad:
                orden = ["abductiva", "deductiva", "cbr"]
            elif entidad and self.grafo.existe(entidad):
                orden = ["deductiva", "cbr"]
            else:
                orden = ["cbr", "deductiva"]

        for estrategia in orden:
            if estrategia == "abductiva" and entidad:
                # Efecto puede ser la entidad o palabras clave tipo "lentitud"
                resultado = self.motor.abducir(entidad)
                if not resultado.conclusion and analisis.palabras_clave:
                    for kw in analisis.palabras_clave:
                        resultado = self.motor.abducir(kw)
                        if resultado.conclusion:
                            break
                if resultado.conclusion:
                    return resultado
            elif estrategia == "deductiva" and entidad and self.grafo.existe(entidad):
                resultado = self.motor.deducir(entidad)
                if resultado.conclusion:
                    return resultado
            elif estrategia == "cbr":
                resultado = self.motor.razonar_por_casos(analisis.palabras_clave)
                if resultado.conclusion:
                    return resultado

        return self.motor.razonar_por_casos(analisis.palabras_clave)

    async def tick(self) -> None:
        await super().tick()

    def estado(self) -> dict[str, Any]:
        base = super().estado()
        base["grafo"] = self.grafo.estado()
        return base
