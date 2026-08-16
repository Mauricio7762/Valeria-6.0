"""
Generador de Lenguaje Natural (NLG estructurado)
=================================================
Convierte ResultadoInferencia / aprendizaje en español más natural.
Sin LLM: plantillas + humanización de identificadores.
"""

from __future__ import annotations

import re

from .motor_inferencia import ResultadoInferencia

_REL_FRASE = {
    "es_un": "es un",
    "es_parte_de": "forma parte de",
    "causa": "puede causar",
    "tiene_funcion": "tiene la función de",
    "tiene_propiedad": "tiene la propiedad de",
    "tiene": "tiene",
    "es": "es",
}


def humanizar(texto: str) -> str:
    """microglia / cerebro_humano_digital → formas más legibles."""
    if not texto:
        return ""
    t = str(texto).replace("_", " ").strip()
    # Espacios múltiples
    t = re.sub(r"\s+", " ", t)
    return t


def humanizar_conclusion_cadena(conclusion: str) -> str:
    """Limpia conclusiones del motor con vías transitivas."""
    if not conclusion:
        return ""
    c = humanizar(conclusion)
    # "valeria es un cerebro humano digital (vía: valeria -> cerebro humano digital)"
    c = re.sub(r"\s*\(v[ií]a:\s*[^)]+\)", "", c, flags=re.IGNORECASE).strip()
    return c


class GeneradorNLG:
    def generar(self, resultado: ResultadoInferencia, pregunta_original: str) -> str:
        if not resultado.conclusion:
            return (
                "No tengo hechos suficientes para responder con certeza. "
                "Puedes enseñarme con una afirmación del tipo: "
                "«X es parte de Y» o «X es un Y»."
            )

        conclusion = humanizar_conclusion_cadena(resultado.conclusion)
        estrategia = resultado.estrategia
        conf = resultado.confianza

        if estrategia == "deductiva":
            if conf >= 0.7:
                texto = f"{conclusion.capitalize()}."
            elif conf >= 0.45:
                texto = f"Según lo que sé, {conclusion}."
            else:
                texto = f"Con poca certeza: {conclusion}."

        elif estrategia == "abductiva":
            causa = humanizar(resultado.conclusion)
            if conf >= 0.7:
                texto = f"La explicación más plausible es: {causa}."
            else:
                texto = (
                    f"Una posible causa es {causa}, "
                    f"aunque puede haber otras."
                )

        elif estrategia == "cbr":
            # El motor a veces ya trae "Por analogía..."
            if conclusion.lower().startswith("por analogía"):
                texto = conclusion if conclusion.endswith(".") else conclusion + "."
            else:
                texto = f"Por analogía con un caso parecido: {conclusion}."
            if conf < 0.35:
                texto += " (similitud baja; tómalo como hipótesis)"

        else:
            texto = conclusion if conclusion.endswith(".") else conclusion + "."

        return texto

    def generar_aprendizaje(self, sujeto: str, relacion: str, objeto: str) -> str:
        rel = _REL_FRASE.get(relacion, relacion.replace("_", " "))
        return (
            f"Entendido. Aprendí que {humanizar(sujeto)} {rel} {humanizar(objeto)}."
        )
