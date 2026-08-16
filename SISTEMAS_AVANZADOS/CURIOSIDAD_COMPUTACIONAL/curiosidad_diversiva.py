"""
Curiosidad diversiva
====================
Exploración lúdica / cambio de tema cuando hay estancamiento
(muchas fallas seguidas o poca novedad).
"""

from __future__ import annotations

import random
from typing import Any

_TEMAS_SEMILLA = [
    "¿Cómo se relacionan el sistema glial y los agentes corticales?",
    "¿Qué pasaría si la microglía no limpiara contextos?",
    "¿Cuál es la función de los oligodendrocitos en VALERIA?",
    "¿Qué diferencia hay entre memoria episódica y el grafo semántico?",
    "¿Para qué sirve la metacognición nivel 5?",
]


class CuriosidadDiversiva:
    def __init__(self, temas_extra: list[str] | None = None) -> None:
        self.temas = list(_TEMAS_SEMILLA)
        if temas_extra:
            self.temas.extend(temas_extra)

    def sugerir(self, n: int = 2, sujetos_grafo: list[str] | None = None) -> list[dict[str, str]]:
        pool = list(self.temas)
        if sujetos_grafo:
            for s in sujetos_grafo[:8]:
                pool.append(f"¿Qué función tiene {s.replace('_', ' ')}?")
        random.shuffle(pool)
        return [
            {"tipo": "diversiva", "pregunta": p, "origen": "exploracion_libre"}
            for p in pool[:n]
        ]
