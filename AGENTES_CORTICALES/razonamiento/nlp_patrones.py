"""
Analizador de Patrones (NLP simbólico)
=======================================
Clasifica la intención de una pregunta y extrae la entidad principal
mediante reglas y expresiones regulares. No usa modelos de lenguaje:
es determinístico y barato en CPU, pensado para correr en un celular.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del",
    "que", "es", "son", "y", "o", "a", "en", "por", "para", "se", "su",
    "sus", "al", "lo", "como", "con", "no", "me", "mi", "tu",
}

# (patrón regex, tipo de intención) — orden importa, primero el más específico
_PATRONES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^\s*por qu[eé]\b"), "causal"),
    (re.compile(r"\bcausa(?:do)?\s+por\b|\bse debe a\b"), "causal"),
    (re.compile(r"^\s*qu[eé] es\b|^\s*qu[eé]\s+son\b"), "definicion"),
    (re.compile(r"^\s*qui[eé]n(?:es)?\s+es\b|^\s*qui[eé]n(?:es)?\s+son\b"), "definicion"),
    (re.compile(r"^\s*c[oó]mo\b"), "procedimental"),
    (re.compile(r"^\s*(?:es|son)\b.+\?"), "verificacion"),
    (re.compile(r"\bdiferencia\b|\bcompar"), "comparacion"),
    (re.compile(r"\bqu[eé] (?:tiene|tienen|hace|hacen)\b"), "propiedad"),
]


@dataclass
class AnalisisNLP:
    texto_original: str
    intencion: str
    entidad_principal: str | None
    palabras_clave: list[str]


class AnalizadorPatrones:
    """Extrae intención + entidad de una oración en español."""

    def analizar(self, texto: str) -> AnalisisNLP:
        texto_norm = (texto or "").strip().lower()
        texto_norm = texto_norm.lstrip("¿¡")

        intencion = "general"
        for patron, tipo in _PATRONES:
            if patron.search(texto_norm):
                intencion = tipo
                break

        palabras = re.findall(r"[a-záéíóúñü]+", texto_norm)
        palabras_clave = [p for p in palabras if p not in _STOPWORDS and len(p) > 2]

        entidad_principal = self._extraer_entidad(texto_norm, intencion, palabras_clave)

        return AnalisisNLP(
            texto_original=texto,
            intencion=intencion,
            entidad_principal=entidad_principal,
            palabras_clave=palabras_clave,
        )

    def _extraer_entidad(self, texto_norm: str, intencion: str, palabras_clave: list[str]) -> str | None:
        # Para "qué es X" / "quién es X" la entidad es lo que sigue al patrón
        m = re.search(
            r"qu(?:[eé]|i[eé]n(?:es)?) (?:es|son)(?:\s+(?:un|una|el|la))?\s+([a-záéíóúñü\s]+?)[\?\.]?$",
            texto_norm,
        )
        if m:
            return m.group(1).strip()

        m = re.search(r"por qu[eé]\s+(?:hay|existe|se produce|se da)?\s*(.+?)[\?\.]?$", texto_norm)
        if m:
            return m.group(1).strip()

        # Fallback: la última palabra clave suele ser el foco de la pregunta
        return palabras_clave[-1] if palabras_clave else None
