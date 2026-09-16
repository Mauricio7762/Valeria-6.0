"""
Detector de actos de habla conversacionales (saludos, despedidas, cortesías)
=============================================================================
Capa liviana que corre ANTES del pipeline de extracción de hechos /
razonamiento simbólico. Evita que un saludo como "Hola Valeria" se
interprete como una consulta sobre la entidad "valeria" (o que "gracias"
dispare el CBR pidiendo enseñanza).

No compite con el aprendizaje ni con las preguntas reales: si el texto
contiene un patrón de afirmación tipo "X es un/una Y" o "X es parte de Y"
(lo que el extractor de hechos usa para aprender o el usuario usa para
preguntar), esta capa se abstiene y devuelve None para que el mensaje
siga el camino normal.

Uso:
    from AGENTES_CORTICALES.razonamiento.detector_intencion import detectar_saludo
    resp = detectar_saludo(texto)
    if resp is not None:
        return resp  # no seguir al pipeline de razonamiento
"""

from __future__ import annotations

import random
import re

# Si el texto tiene un patrón de definición ("X es un/una/parte de Y"),
# no es small talk: es enseñanza o consulta real, y debe ir al extractor.
_PATRON_ENSENANZA = re.compile(r"\bes\s+(un|una|parte\s+de)\b", re.IGNORECASE)

_SALUDOS = (
    "buenos dias", "buenos días", "buenas tardes", "buenas noches",
    "buen dia", "buen día", "que tal", "qué tal",
    "hola", "holaa", "holaaa", "holis", "buenas", "hey", "ey",
)
_DESPEDIDAS = (
    "hasta luego", "hasta pronto", "nos vemos", "me voy",
    "chau", "chao", "adios", "adiós", "bye",
)
_AGRADECIMIENTOS = ("muchas gracias", "mil gracias", "te agradezco", "gracias")
_COMO_ESTAS = (
    "como estas", "cómo estás", "como andas", "cómo andás",
    "como te va", "cómo te va", "que tal estas", "qué tal estás",
)

_RESP_SALUDO = (
    "¡Hola! ¿En qué te ayudo?",
    "Hola, te escucho.",
    "¡Hola! Contame qué necesitás.",
)
_RESP_DESPEDIDA = (
    "¡Nos vemos! Acá voy a estar.",
    "Chau, cuando quieras retomamos.",
)
_RESP_GRACIAS = (
    "De nada, para eso estoy.",
    "¡Un gusto ayudarte!",
)
_RESP_COMO_ESTAS = (
    "Funcionando bien, gracias por preguntar. ¿Y vos?",
    "Todo en orden por acá. ¿En qué te ayudo?",
)


def _normalizar(texto: str) -> str:
    t = (texto or "").strip().lower()
    t = re.sub(r"[¡!¿?.,;:]+", "", t)
    return re.sub(r"\s+", " ", t).strip()


def _match_prefijo(t: str, frases: tuple[str, ...]) -> str | None:
    for frase in frases:
        if t == frase or t.startswith(frase + " "):
            return frase
    return None


def detectar_saludo(texto: str) -> str | None:
    """Devuelve una respuesta fija si `texto` es un saludo, despedida,
    agradecimiento o pregunta de cortesía ("cómo estás"). Devuelve None
    si no aplica, o si el texto parece una afirmación/pregunta real
    (contiene "es un/una/parte de") que debe seguir al razonamiento.
    """
    crudo = texto or ""
    if _PATRON_ENSENANZA.search(crudo):
        return None

    t = _normalizar(crudo)
    if not t:
        return None

    if _match_prefijo(t, _COMO_ESTAS):
        return random.choice(_RESP_COMO_ESTAS)

    if _match_prefijo(t, _AGRADECIMIENTOS):
        return random.choice(_RESP_GRACIAS)

    if _match_prefijo(t, _DESPEDIDAS):
        return random.choice(_RESP_DESPEDIDA)

    frase = _match_prefijo(t, _SALUDOS)
    if frase is not None:
        # "hola" solo, o "hola" + vocativo/nombre corto ("hola valeria").
        # Si sigue mucho texto después del saludo, dejamos que continúe
        # al pipeline normal (puede ser una pregunta real).
        resto = t[len(frase):].split()
        if len(resto) <= 3:
            return random.choice(_RESP_SALUDO)

    return None
