"""Texto libre → ideas → extractor → grafo."""
from __future__ import annotations

import json
import re
from typing import Any

from loguru import logger

_VERBOS = (
    r"regula|regulan|limpia|limpian|defiende|defienden|"
    r"ejecuta|realiza|sirve|forma|pertenece|encarga|regularizar"
)
_REL_OK = {
    "es_un", "es_parte_de", "tiene_funcion", "tiene_proposito",
    "causa", "tiene_propiedad", "tiene", "es",
}
_CONECTORES = re.compile(
    r"\s*,\s*mientras que\s+|\s*,\s*y además\s+|\s*;\s*|\s*,\s*además\s+|\s+Además,\s+",
    re.IGNORECASE,
)


def limpiar_sujeto(s: str) -> str:
    s = (s or "").strip().lower().replace(" ", "_")
    s = re.split(rf"_+(?:{_VERBOS})", s)[0]
    s = re.sub(r"^(el|la|los|las)_", "", s)
    return s.strip("_")


def segmentar_ideas(texto: str) -> list[str]:
    texto = re.sub(r"\s+", " ", (texto or "").strip())
    if not texto:
        return []
    partes = re.split(r"(?<=[\.\!\?])\s+", texto)
    ideas: list[str] = []
    for p in partes:
        p = p.strip()
        if not p:
            continue
        for s in _CONECTORES.split(p):
            s = s.strip(" ,;")
            if len(s) < 3:
                continue
            s = re.sub(r"^(además|también)\s*,?\s*", "", s, flags=re.I)
            if not s.endswith((".", "!", "?")):
                s += "."
            ideas.append(s[0].upper() + s[1:])
    return ideas


def _parse_json_array(raw: str) -> list[dict]:
    raw = (raw or "").strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    m = re.search(r"\[.*\]", raw, re.DOTALL)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    out = []
    for item in data:
        if not isinstance(item, dict):
            continue
        s = limpiar_sujeto(str(item.get("sujeto") or ""))
        r = str(item.get("relacion") or "").strip().lower()
        o = str(item.get("objeto") or "").strip().lower()
        if not s or not r or not o or r not in _REL_OK:
            continue
        if len(s) < 2 or len(s) > 60:
            continue
        out.append({"sujeto": s, "relacion": r, "objeto": o})
    return out


def aprender_texto(texto: str, grafo: Any, usar_llm: bool = True) -> list[dict]:
    """Extrae hechos del texto y los agrega al grafo. Devuelve lista guardada."""
    from .extractor_hechos import extraer_hecho
    from .extractor_llm import extraer_hechos_llm

    guardados: list[dict] = []
    seen: set[tuple] = set()

    for idea in segmentar_ideas(texto):
        hechos: list[dict] = []

        h = extraer_hecho(idea)
        if h is not None:
            hechos.append({
                "sujeto": limpiar_sujeto(h.sujeto),
                "relacion": h.relacion,
                "objeto": h.objeto.strip().lower(),
            })
        elif usar_llm:
            try:
                raw_list = extraer_hechos_llm(idea)
                if isinstance(raw_list, list):
                    hechos.extend(raw_list)
                elif isinstance(raw_list, str):
                    hechos.extend(_parse_json_array(raw_list))
            except Exception as e:
                logger.warning(f"extractor_llm: {e}")

        for item in hechos:
            if not isinstance(item, dict):
                continue
            s = limpiar_sujeto(str(item.get("sujeto", "")))
            r = str(item.get("relacion", "")).lower()
            o = str(item.get("objeto", "")).strip().lower()
            if not s or r not in _REL_OK or not o:
                continue
            key = (s, r, o)
            if key in seen:
                continue
            seen.add(key)
            try:
                grafo.agregar_hecho(s, r, o)
                guardados.append({"sujeto": s, "relacion": r, "objeto": o})
            except TypeError:
                try:
                    grafo.agregar_hecho(s, r, o, confianza=0.7, origen="usuario")
                    guardados.append({"sujeto": s, "relacion": r, "objeto": o})
                except Exception as e:
                    logger.warning(f"No se pudo agregar hecho {key}: {e}")
            except Exception as e:
                logger.warning(f"No se pudo agregar hecho {key}: {e}")

    return guardados
