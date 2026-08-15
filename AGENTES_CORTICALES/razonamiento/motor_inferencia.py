"""
Motor de Inferencia
====================
Tres estrategias de razonamiento simbólico sobre el GrafoConocimiento:

- Deductiva: aplica reglas de transitividad ("es_un") y herencia de
  propiedades para derivar hechos que no están escritos literalmente.
- Abductiva: dado un efecto observado, busca la(s) causa(s) más
  plausible(s) registradas como "causa" en el grafo.
- Basada en casos (CBR): si no hay hechos ni causas, busca la pregunta
  previa más parecida (por solapamiento de palabras clave) y adapta
  su conclusión.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .grafo_conocimiento import GrafoConocimiento, Hecho, normalizar

RELACIONES_JERARQUICAS = ("es_un", "es_parte_de")


@dataclass
class Caso:
    pregunta: str
    palabras_clave: frozenset[str]
    conclusion: str


@dataclass
class PasoRazonamiento:
    descripcion: str


@dataclass
class ResultadoInferencia:
    estrategia: str
    pasos: list[str]
    conclusion: str | None
    confianza: float
    hechos_usados: list[Hecho] = field(default_factory=list)


class MotorInferencia:
    def __init__(self, grafo: GrafoConocimiento, max_saltos: int = 4) -> None:
        self.grafo = grafo
        self.max_saltos = max_saltos
        self._casos: list[Caso] = []

    # ---------- Deductiva ----------
    def deducir(self, sujeto: str, relacion_objetivo: str | None = None) -> ResultadoInferencia:
        sujeto = normalizar(sujeto)
        pasos: list[str] = [f"Buscar hechos directos sobre '{sujeto}'"]
        hechos_directos = self.grafo.relacionados(sujeto)

        if relacion_objetivo:
            directos = [h for h in hechos_directos if h.relacion == relacion_objetivo]
            if directos:
                pasos.append(f"Encontrado directamente: {sujeto} {relacion_objetivo} {directos[0].objeto}")
                return ResultadoInferencia("deductiva", pasos, directos[0].objeto, directos[0].confianza, directos)

        if not hechos_directos:
            pasos.append(f"'{sujeto}' no existe en el grafo de conocimiento")
            return ResultadoInferencia("deductiva", pasos, None, 0.0)

        # Transitividad sobre relaciones jerárquicas: A es_un B, B es_un C => A es_un C
        cadena = [sujeto]
        actual = sujeto
        usados: list[Hecho] = []
        for _ in range(self.max_saltos):
            padres = [h for h in self.grafo.relacionados(actual) if h.relacion in RELACIONES_JERARQUICAS]
            if not padres:
                break
            padre = padres[0]
            usados.append(padre)
            cadena.append(padre.objeto)
            pasos.append(f"{actual} {padre.relacion} {padre.objeto}")

            if relacion_objetivo:
                propiedad = self.grafo.buscar(sujeto=padre.objeto, relacion=relacion_objetivo)
                if propiedad:
                    pasos.append(
                        f"Herencia: '{sujeto}' hereda '{relacion_objetivo}' de '{padre.objeto}' "
                        f"=> {propiedad[0].objeto}"
                    )
                    confianza = max(0.4, 0.9 - 0.15 * len(cadena))
                    return ResultadoInferencia(
                        "deductiva", pasos, propiedad[0].objeto, confianza, usados + propiedad
                    )
            actual = padre.objeto

        if len(cadena) > 1:
            relacion_usada = usados[0].relacion  # relación del primer salto, la más específica
            verbo = "es un" if relacion_usada == "es_un" else relacion_usada.replace("_", " ")
            conclusion = f"{sujeto} {verbo} {cadena[-1]} (vía: {' -> '.join(cadena)})"
            confianza = max(0.4, 0.9 - 0.15 * len(cadena))
            pasos.append(f"Conclusión por transitividad: {conclusion}")
            return ResultadoInferencia("deductiva", pasos, conclusion, confianza, usados)

        # No hubo transitividad útil: devolver lo directo que sí hay
        resumen = "; ".join(f"{h.relacion} {h.objeto}" for h in hechos_directos[:4])
        pasos.append(f"Sin herencia aplicable. Hechos directos: {resumen}")
        return ResultadoInferencia("deductiva", pasos, resumen, 0.6, hechos_directos)

    # ---------- Abductiva ----------
    def abducir(self, efecto: str) -> ResultadoInferencia:
        efecto = efecto.strip().lower()
        pasos = [f"Buscar causas conocidas de '{efecto}'"]
        candidatas = self.grafo.buscar(relacion="causa", objeto=efecto)

        if not candidatas:
            pasos.append("No hay causas registradas para ese efecto")
            return ResultadoInferencia("abductiva", pasos, None, 0.0)

        candidatas_ordenadas = sorted(candidatas, key=lambda h: h.confianza, reverse=True)
        mejor = candidatas_ordenadas[0]
        pasos.append(f"Candidatas: {[h.sujeto for h in candidatas_ordenadas]}")
        pasos.append(f"Mejor explicación (mayor confianza registrada): '{mejor.sujeto}'")

        confianza = mejor.confianza
        if len(candidatas_ordenadas) > 1:
            confianza *= 0.8  # ambigüedad reduce la confianza
            pasos.append("Hay más de una causa posible: se reduce la confianza")

        return ResultadoInferencia("abductiva", pasos, mejor.sujeto, round(confianza, 2), candidatas_ordenadas)

    # ---------- Basada en casos (CBR) ----------
    def registrar_caso(self, pregunta: str, palabras_clave: list[str], conclusion: str) -> None:
        self._casos.append(Caso(pregunta, frozenset(palabras_clave), conclusion))
        if len(self._casos) > 200:
            self._casos = self._casos[-150:]

    def razonar_por_casos(self, palabras_clave: list[str]) -> ResultadoInferencia:
        pasos = ["Sin hechos ni causas directas: buscar caso previo similar"]
        objetivo = frozenset(palabras_clave)

        if not self._casos or not objetivo:
            pasos.append("No hay casos previos comparables")
            return ResultadoInferencia("cbr", pasos, None, 0.0)

        mejor_caso: Caso | None = None
        mejor_score = 0.0
        for caso in self._casos:
            interseccion = len(objetivo & caso.palabras_clave)
            union = len(objetivo | caso.palabras_clave) or 1
            score = interseccion / union  # similitud de Jaccard
            if score > mejor_score:
                mejor_score = score
                mejor_caso = caso

        if not mejor_caso or mejor_score < 0.2:
            pasos.append("Ningún caso previo es suficientemente parecido")
            return ResultadoInferencia("cbr", pasos, None, 0.0)

        pasos.append(f"Caso más parecido: \"{mejor_caso.pregunta}\" (similitud {mejor_score:.2f})")
        pasos.append("Adaptando conclusión de ese caso a la nueva pregunta")
        conclusion = f"Por analogía con un caso similar: {mejor_caso.conclusion}"
        return ResultadoInferencia("cbr", pasos, conclusion, round(mejor_score, 2))
