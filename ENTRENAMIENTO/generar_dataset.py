"""
Genera dataset.jsonl para fine-tuning (Llama 3.2 1B) a partir de los
hechos reales de VALERIA (base_conocimiento_semilla.py).

Para cada hecho relevante:
  - "template": lo que responde HOY el NLG estructurado (rígido).
  - "output":   una versión natural (lo que queremos que el modelo
                aprenda a producir), con variación de frases para que
                no aprenda una sola plantilla fija.

Uso:
    python generar_dataset.py
Genera: dataset_valeria_nlg.jsonl
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

# Ajustá esta ruta si tu carpeta se llama distinto
REPO_ROOT = Path(__file__).resolve().parent / "Valeria-6.0-main"
STUBS = Path(__file__).resolve().parent / "stubs"
sys.path.insert(0, str(STUBS))  # stub de loguru (no disponible sin red)
sys.path.insert(0, str(REPO_ROOT))

from AGENTES_CORTICALES.razonamiento.grafo_conocimiento import GrafoConocimiento, normalizar
from AGENTES_CORTICALES.razonamiento.motor_inferencia import MotorInferencia
from AGENTES_CORTICALES.razonamiento.generador_nlg import GeneradorNLG, humanizar
from AGENTES_CORTICALES.razonamiento.base_conocimiento_semilla import HECHOS_SEMILLA, cargar_semilla

random.seed(7)

grafo = GrafoConocimiento()
cargar_semilla(grafo)
motor = MotorInferencia(grafo)
nlg = GeneradorNLG()

# --- Bancos de frases para variar el estilo natural (evita 1 sola plantilla) ---
ABRE_ES_UN = [
    "{sujeto} es {objeto}.",
    "{sujeto} es, básicamente, {objeto}.",
    "En VALERIA, {sujeto} es {objeto}.",
    "Podría decirse que {sujeto} es {objeto}.",
]
ABRE_ES_PARTE_DE = [
    "{sujeto} forma parte de {objeto}.",
    "{sujeto} es uno de los componentes de {objeto}.",
    "Dentro de VALERIA, {sujeto} vive dentro de {objeto}.",
    "{sujeto} está integrado en {objeto}.",
]
ABRE_FUNCION = [
    "La función de {sujeto} es {objeto}.",
    "{sujeto} se encarga de {objeto}.",
    "Lo que hace {sujeto} es {objeto}.",
    "El rol de {sujeto} dentro del sistema es {objeto}.",
]
ABRE_PROPOSITO = [
    "El propósito de {sujeto} es {objeto}.",
    "{sujeto} existe para {objeto}.",
    "La idea detrás de {sujeto} es {objeto}.",
]
ABRE_CAUSA = [
    "Cuando hay {efecto}, una causa probable es {causa}.",
    "{causa} suele explicar por qué aparece {efecto}.",
    "Si notás {efecto}, revisá si hay {causa}.",
]

PREGUNTAS_QUE_ES = ["¿Qué es {x}?", "¿Qué es {x} en VALERIA?", "Explicame qué es {x}"]
PREGUNTAS_FUNCION = ["¿Cuál es la función de {x}?", "¿Para qué sirve {x}?", "¿Qué hace {x}?"]
PREGUNTAS_PROPOSITO = ["¿Cuál es el propósito de {x}?", "¿Para qué existe {x}?"]
PREGUNTAS_PARTE = ["¿De qué es parte {x}?", "¿Dónde encaja {x} dentro de VALERIA?"]
PREGUNTAS_CAUSA = ["¿Por qué pasa que hay {x}?", "¿Cuál puede ser la causa de {x}?"]


def elegir(banco: list[str]) -> str:
    return random.choice(banco)


ejemplos = []

sujetos = sorted({s for s, _, _ in HECHOS_SEMILLA if "causa" not in _})

for sujeto in sujetos:
    hechos = [h for h in grafo.relacionados(normalizar(sujeto))]
    sujeto_h = humanizar(sujeto)

    for relacion in ("es_un", "es_parte_de", "tiene_funcion", "tiene_proposito"):
        directos = [h for h in hechos if h.relacion == relacion]
        if not directos:
            continue
        objeto_h = humanizar(directos[0].objeto)

        resultado = motor.deducir(sujeto, relacion)
        template = nlg.generar(resultado, f"¿Qué es {sujeto}?")

        if relacion == "es_un":
            pregunta = elegir(PREGUNTAS_QUE_ES).format(x=sujeto_h)
            natural = elegir(ABRE_ES_UN).format(sujeto=sujeto_h.capitalize(), objeto=objeto_h)
        elif relacion == "es_parte_de":
            pregunta = elegir(PREGUNTAS_PARTE).format(x=sujeto_h)
            natural = elegir(ABRE_ES_PARTE_DE).format(sujeto=sujeto_h.capitalize(), objeto=objeto_h)
        elif relacion == "tiene_funcion":
            pregunta = elegir(PREGUNTAS_FUNCION).format(x=sujeto_h)
            natural = elegir(ABRE_FUNCION).format(sujeto=sujeto_h.capitalize(), objeto=objeto_h)
        else:  # tiene_proposito
            pregunta = elegir(PREGUNTAS_PROPOSITO).format(x=sujeto_h)
            natural = elegir(ABRE_PROPOSITO).format(sujeto=sujeto_h.capitalize(), objeto=objeto_h)

        ejemplos.append({
            "instruction": pregunta,
            "template_actual": template,
            "output": natural,
        })

# --- Causales (abducción) ---
for causa, _, efecto in [(s, r, o) for s, r, o in HECHOS_SEMILLA if r == "causa"]:
    causa_h = humanizar(causa)
    efecto_h = humanizar(efecto)
    resultado = motor.abducir(efecto)
    template = nlg.generar(resultado, f"¿por qué {efecto}?")
    pregunta = elegir(PREGUNTAS_CAUSA).format(x=efecto_h)
    natural = elegir(ABRE_CAUSA).format(efecto=efecto_h, causa=causa_h)
    ejemplos.append({
        "instruction": pregunta,
        "template_actual": template,
        "output": natural,
    })

random.shuffle(ejemplos)

out_path = Path(__file__).resolve().parent / "dataset_valeria_nlg.jsonl"
with out_path.open("w", encoding="utf-8") as f:
    for ej in ejemplos:
        # Para el fine-tuning solo hacen falta instruction/output;
        # dejamos template_actual como referencia/auditoría, no se sube al modelo.
        f.write(json.dumps(ej, ensure_ascii=False) + "\n")

print(f"Generados {len(ejemplos)} ejemplos -> {out_path}")
