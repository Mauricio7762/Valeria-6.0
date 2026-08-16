"""
NLP por patrones — intención y entidad en español.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del",
    "que", "es", "son", "y", "o", "a", "en", "por", "para", "se", "su",
    "sus", "al", "lo", "como", "con", "no", "me", "mi", "tu", "hay",
}

_PATRONES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^\s*por qu[eé]\b"), "causal"),
    (re.compile(r"\bcausa(?:do)?\s+por\b|\bse debe a\b"), "causal"),
    (re.compile(r"^\s*para qu[eé]\b|\bqu[eé] funci[oó]n\b|\bpara qu[eé] sirve\b"), "propiedad"),
    (re.compile(r"^\s*qu[eé] es\b|^\s*qu[eé]\s+son\b"), "definicion"),
    (re.compile(r"^\s*qui[eé]n(?:es)?\s+es\b|^\s*qui[eé]n(?:es)?\s+son\b"), "definicion"),
    (re.compile(r"^\s*c[oó]mo\b"), "procedimental"),
    (re.compile(r"^\s*(?:es|son)\b.+\?"), "verificacion"),
    (re.compile(r"\bdiferencia\b|\bcompar"), "comparacion"),
    (re.compile(r"\bqu[eé] (?:tiene|tienen|hace|hacen)\b"), "propiedad"),
]

# Alias comunes → nombre canónico del grafo
_ALIAS = {
    "valeria 6.0": "valeria",
    "valeria 6": "valeria",
    "sistema glial": "sistema_glial",
    "nucleo biomimetico": "nucleo_biomimetico",
    "núcleo biomimético": "nucleo_biomimetico",
    "agentes corticales": "agentes_corticales",
    "agente de memoria": "agente_memoria",
    "agente de razonamiento": "agente_razonamiento",
    "grafo": "grafo_conocimiento",
    "neurogenesis": "neurogenesis_artificial",
    "neurogénesis": "neurogenesis_artificial",
    "metacognicion": "metacognicion",
    "curiosidad": "curiosidad_computacional",
    "streamlit": "interfaz_streamlit",
    "api": "interfaz_api",
    "orquestador": "orquestador_principal",
}


@dataclass
class AnalisisNLP:
    texto_original: str
    intencion: str
    entidad_principal: str | None
    palabras_clave: list[str]


class AnalizadorPatrones:
    def analizar(self, texto: str) -> AnalisisNLP:
        texto_norm = (texto or "").strip().lower()
        texto_norm = texto_norm.lstrip("¿¡")

        intencion = "general"
        for patron, tipo in _PATRONES:
            if patron.search(texto_norm):
                intencion = tipo
                break

        palabras = re.findall(r"[a-záéíóúñü0-9]+", texto_norm)
        palabras_clave = [p for p in palabras if p not in _STOPWORDS and len(p) > 2]

        entidad = self._extraer_entidad(texto_norm, intencion, palabras_clave)
        if entidad:
            entidad = _ALIAS.get(entidad, entidad)
            # también intentar frase completa en alias
            for alias, canon in _ALIAS.items():
                if alias in texto_norm:
                    entidad = canon
                    break

        return AnalisisNLP(
            texto_original=texto,
            intencion=intencion,
            entidad_principal=entidad,
            palabras_clave=palabras_clave,
        )

    def _extraer_entidad(self, texto_norm: str, intencion: str, palabras_clave: list[str]) -> str | None:
        m = re.search(
            r"qu(?:[eé]|i[eé]n(?:es)?) (?:es|son)(?:\s+(?:un|una|el|la))?\s+([a-záéíóúñü0-9\s\.]+?)[\?\.]?$",
            texto_norm,
        )
        if m:
            return m.group(1).strip()

        m = re.search(
            r"(?:para qu[eé] sirve|qu[eé] funci[oó]n tiene)\s+(?:el|la|los|las)?\s*(.+?)[\?\.]?$",
            texto_norm,
        )
        if m:
            return m.group(1).strip()

        m = re.search(r"por qu[eé]\s+(?:hay|existe|se produce|se da)?\s*(.+?)[\?\.]?$", texto_norm)
        if m:
            return m.group(1).strip()

        return palabras_clave[-1] if palabras_clave else None
