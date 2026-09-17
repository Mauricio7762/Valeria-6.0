"""
Detector de Feedback Negativo
==============================
Reconoce cuando el usuario indica que la última respuesta fue
incorrecta ("está mal", "no es así", "te equivocaste"), para que el
agente de razonamiento pueda bajarle la confianza a los hechos que usó
para generarla.

No compite con la enseñanza ni con una corrección con datos nuevos:
si el texto trae además una afirmación tipo "X es Y" (por ejemplo
"no, en realidad hola es un saludo"), este detector se abstiene y deja
que lo maneje el extractor de hechos (que ya reconoce el prefijo de
corrección "no, ...").
"""

from __future__ import annotations

import re

_PATRON_ENSEÑANZA = re.compile(r"\bes\s+(un|una|parte\s+de)\b", re.IGNORECASE)

_FRASES_FEEDBACK_NEGATIVO = (
    "mal",
    "esta mal",
    "está mal",
    "eso esta mal",
    "eso está mal",
    "esa respuesta esta mal",
    "esa respuesta está mal",
    "no es asi",
    "no es así",
    "no es correcto",
    "eso no es correcto",
    "incorrecto",
    "eso es incorrecto",
    "eso esta mal dicho",
    "te equivocaste",
    "estas equivocada",
    "estás equivocada",
    "estas equivocado",
    "estás equivocado",
)


def _normalizar(texto: str) -> str:
    t = (texto or "").strip().lower()
    t = re.sub(r"[¡!¿?.,;:]+", "", t)
    return re.sub(r"\s+", " ", t).strip()


def detectar_feedback_negativo(texto: str) -> bool:
    """True si `texto` es, en sí mismo, feedback negativo puro (sin
    corrección adjunta). Si el texto trae una corrección con datos
    nuevos ("no, X es Y"), devuelve False para que lo maneje el
    extractor de hechos en su lugar."""
    crudo = texto or ""
    if _PATRON_ENSEÑANZA.search(crudo):
        return False

    t = _normalizar(crudo)
    return t in _FRASES_FEEDBACK_NEGATIVO
