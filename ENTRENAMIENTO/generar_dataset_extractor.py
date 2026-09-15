#!/usr/bin/env python3
"""
Dataset SFT: texto libre → hechos (sujeto, relación, objeto) para el grafo VALERIA.

Uso:
  python ENTRENAMIENTO/generar_dataset_extractor.py

Salida:
  ENTRENAMIENTO/dataset_extractor_hechos.jsonl
"""

from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

random.seed(42)
OUT = Path(__file__).resolve().parent / "dataset_extractor_hechos.jsonl"
REPO = Path(__file__).resolve().parent.parent

# --- Semilla (misma forma que base_conocimiento_semilla) ---
sys.path.insert(0, str(REPO))
try:
    from AGENTES_CORTICALES.razonamiento.base_conocimiento_semilla import HECHOS_SEMILLA
except Exception:
    # Fallback mínimo si no está el paquete
    HECHOS_SEMILLA = [
        ("valeria", "es_un", "cerebro_humano_digital"),
        ("sistema_glial", "es_parte_de", "nucleo_biomimetico"),
        ("microglia", "tiene_funcion", "limpiar contextos obsoletos"),
        ("astrocitos", "es_parte_de", "sistema_glial"),
        ("agente_razonamiento", "es_parte_de", "agentes_corticales"),
    ]

RELACIONES_VALIDAS = {
    "es_un",
    "es_parte_de",
    "tiene_funcion",
    "tiene_proposito",
    "tiene_propiedad",
    "tiene",
    "causa",
    "es",
}

SYSTEM = (
    "Extraé hechos estructurados del texto en español. "
    "Devolvé SOLO un JSON array. Cada elemento: "
    '{"sujeto":"...","relacion":"...","objeto":"..."}. '
    "Relaciones permitidas: es_un, es_parte_de, tiene_funcion, tiene_proposito, "
    "tiene_propiedad, tiene, causa, es. "
    "Normalizá sujeto/objeto en minúsculas, sin artículos (el/la/los/las), "
    "espacios como guiones bajos si son nombres de módulo. "
    "Si no hay hechos factuales, devolvé []."
)

INSTRUCTION_TEMPLATES = [
    "Extraé hechos (sujeto, relación, objeto) del siguiente texto.\nTexto: {texto}",
    "Convertí este texto en triples para el grafo de conocimiento.\n{texto}",
    "¿Qué hechos estructurados hay acá?\n{texto}",
    "Parseá hechos VALERIA:\n{texto}",
]


def humanizar(x: str) -> str:
    return x.replace("_", " ").strip()


def normalizar_id(x: str) -> str:
    x = x.strip().lower()
    x = re.sub(r"^(el|la|los|las|un|una)\s+", "", x)
    x = x.replace(" ", "_")
    x = re.sub(r"_+", "_", x)
    return x.strip("_")


def frase_para(s: str, r: str, o: str) -> str:
    s_h, o_h = humanizar(s), humanizar(o)
    if r == "es_un" or r == "es":
        return random.choice(
            [
                f"{s_h} es un {o_h}.",
                f"{s_h.capitalize()} es, en esencia, un {o_h}.",
                f"Se puede decir que {s_h} es un {o_h}.",
            ]
        )
    if r == "es_parte_de":
        return random.choice(
            [
                f"{s_h} forma parte de {o_h}.",
                f"{s_h} es parte de {o_h}.",
                f"Dentro de VALERIA, {s_h} pertenece a {o_h}.",
                f"{s_h.capitalize()} está integrado en {o_h}.",
            ]
        )
    if r == "tiene_funcion":
        return random.choice(
            [
                f"{s_h} sirve para {o_h}.",
                f"La función de {s_h} es {o_h}.",
                f"{s_h.capitalize()} se encarga de {o_h}.",
                f"{s_h} tiene la función de {o_h}.",
            ]
        )
    if r == "tiene_proposito":
        return random.choice(
            [
                f"El propósito de {s_h} es {o_h}.",
                f"{s_h.capitalize()} existe para {o_h}.",
            ]
        )
    if r == "causa":
        return random.choice(
            [
                f"{s_h} puede causar {o_h}.",
                f"Cuando hay {s_h}, puede aparecer {o_h}.",
            ]
        )
    if r == "tiene_propiedad":
        return f"{s_h} tiene la propiedad de {o_h}."
    return f"{s_h} {r.replace('_', ' ')} {o_h}."


def triple_dict(s: str, r: str, o: str) -> dict:
    return {
        "sujeto": normalizar_id(s),
        "relacion": r if r in RELACIONES_VALIDAS else "es",
        "objeto": normalizar_id(o) if r in ("es_un", "es_parte_de", "es") else o.replace("_", " ").strip().lower(),
    }


def output_json(triples: list[dict]) -> str:
    return json.dumps(triples, ensure_ascii=False)


def make_example(texto: str, triples: list[dict]) -> dict:
    inst = random.choice(INSTRUCTION_TEMPLATES).format(texto=texto)
    return {
        "instruction": inst,
        "output": output_json(triples),
    }


def main() -> None:
    ejemplos: list[dict] = []
    hechos = [(s, r, o) for s, r, o in HECHOS_SEMILLA if r in RELACIONES_VALIDAS or True]

    # 1) Un hecho → una frase
    for s, r, o in hechos:
        for _ in range(2):
            texto = frase_para(s, r, o)
            ejemplos.append(make_example(texto, [triple_dict(s, r, o)]))

    # 2) Dos hechos del mismo sujeto
    by_subj: dict[str, list] = {}
    for s, r, o in hechos:
        by_subj.setdefault(s, []).append((s, r, o))
    for s, lista in by_subj.items():
        if len(lista) < 2:
            continue
        pair = random.sample(lista, 2)
        texto = " ".join(frase_para(*t) for t in pair)
        ejemplos.append(
            make_example(texto, [triple_dict(*t) for t in pair])
        )

    # 3) Párrafo de 3 hechos aleatorios
    if len(hechos) >= 3:
        for _ in range(min(80, len(hechos))):
            sample = random.sample(hechos, 3)
            texto = " ".join(frase_para(*t) for t in sample)
            ejemplos.append(
                make_example(texto, [triple_dict(*t) for t in sample])
            )

    # 4) Prefijos de enseñanza
    for s, r, o in random.sample(hechos, k=min(40, len(hechos))):
        base = frase_para(s, r, o)
        texto = random.choice(
            [
                f"Recordá que {base[0].lower() + base[1:]}",
                f"Aprendé esto: {base}",
                f"Guardá que {base[0].lower() + base[1:]}",
            ]
        )
        ejemplos.append(make_example(texto, [triple_dict(s, r, o)]))

    # 5) Negativos / sin hechos
    negativos = [
        "Hola, ¿cómo andás?",
        "Gracias por la ayuda.",
        "Estoy cansado hoy.",
        "¿Qué hora es?",
        "Contame un chiste.",
        "No sé qué hacer con mi vida.",
        "El cielo se ve lindo esta tarde.",
        "Mmm, interesante.",
        "Ok.",
        "Perfecto, seguimos mañana.",
    ]
    for t in negativos:
        for _ in range(2):
            ejemplos.append(make_example(t, []))

    # 6) Preguntas → vacío (no son afirmaciones)
    preguntas = [
        "¿Qué es la microglía?",
        "¿De qué es parte el sistema glial?",
        "¿Para qué sirve VALERIA?",
    ]
    for t in preguntas:
        ejemplos.append(make_example(t, []))

    # Dedupe por instruction
    seen = set()
    clean = []
    for e in ejemplos:
        k = e["instruction"].strip().lower()
        if k in seen:
            continue
        seen.add(k)
        clean.append(e)

    random.shuffle(clean)
    with OUT.open("w", encoding="utf-8") as f:
        for e in clean:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    n_empty = sum(1 for e in clean if e["output"] == "[]")
    print(f"Generados {len(clean)} ejemplos → {OUT}")
    print(f"  con hechos: {len(clean) - n_empty} | vacíos: {n_empty}")
    print(f"  hechos semilla usados: {len(hechos)}")


if __name__ == "__main__":
    main()
