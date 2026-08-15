"""
Agente Razonamiento (Prefrontal Dorsolateral)
==============================================
Razonamiento simbólico real (Route C): NLP por patrones + grafo de
conocimiento + motor de inferencia (deductiva / abductiva / CBR) +
NLG estructurado. Sin dependencia de ningún LLM.
"""

from __future__ import annotations

from typing import Any
from loguru import logger

from .base_agente import BaseAgente
from .razonamiento import (
    AnalizadorPatrones,
    GeneradorNLG,
    GrafoConocimiento,
    MotorInferencia,
    cargar_semilla,
)
from .razonamiento.grafo_conocimiento import normalizar

# Intenciones para las que abducción (buscar causa) es la estrategia natural
_INTENCIONES_CAUSALES = {"causal"}


class AgenteRazonamiento(BaseAgente):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__("Razonamiento", config)
        self.grafo = GrafoConocimiento()
        self.motor = MotorInferencia(self.grafo)
        self.nlp = AnalizadorPatrones()
        self.nlg = GeneradorNLG()
        n = cargar_semilla(self.grafo)
        logger.debug(f"Razonamiento: {n} hechos semilla cargados en el grafo")

    async def procesar(self, mensaje: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "error": "disabled"}

        pregunta = mensaje.get("pregunta") or mensaje.get("contenido") or ""
        analisis = self.nlp.analizar(pregunta)
        pasos: list[str] = [
            f"1. Analizar pregunta -> intención: {analisis.intencion}, "
            f"entidad: {analisis.entidad_principal or '—'}"
        ]

        inferencia = self._razonar(analisis)
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

    def _razonar(self, analisis):
        entidad = normalizar(analisis.entidad_principal) if analisis.entidad_principal else None

        if analisis.intencion in _INTENCIONES_CAUSALES and entidad:
            resultado = self.motor.abducir(entidad)
            if resultado.conclusion:
                return resultado

        if entidad and self.grafo.existe(entidad):
            resultado = self.motor.deducir(entidad)
            if resultado.conclusion:
                return resultado

        # Nada literal ni derivable en el grafo: razonar por analogía con casos previos
        return self.motor.razonar_por_casos(analisis.palabras_clave)

    async def tick(self) -> None:
        await super().tick()

    def estado(self) -> dict[str, Any]:
        base = super().estado()
        base["grafo"] = self.grafo.estado()
        return base
