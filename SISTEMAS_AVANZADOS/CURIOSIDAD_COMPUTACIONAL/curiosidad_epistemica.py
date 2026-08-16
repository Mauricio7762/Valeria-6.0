"""
Curiosidad epistémica
=====================
Drive a reducir incertidumbre: ¿qué no sé que debería saber?
Genera preguntas a partir de lagunas del grafo y fallos recientes.
"""

from __future__ import annotations

from typing import Any


class CuriosidadEpistemica:
    def generar_preguntas(
        self,
        lagunas: list[str],
        sujetos_grafo: list[str],
        max_preguntas: int = 5,
    ) -> list[dict[str, str]]:
        preguntas: list[dict[str, str]] = []

        for lag in lagunas[-8:]:
            texto = lag.strip()
            if not texto:
                continue
            preguntas.append(
                {
                    "tipo": "epistemica",
                    "pregunta": f"¿Qué debería saber sobre: {texto[:80]}?",
                    "origen": "laguna",
                }
            )

        # Sujetos sin muchas relaciones: curiosidad de profundidad
        for s in sujetos_grafo[:15]:
            preguntas.append(
                {
                    "tipo": "epistemica",
                    "pregunta": f"¿Qué más es verdad sobre {s.replace('_', ' ')}?",
                    "origen": "profundizar_sujeto",
                }
            )
            if len(preguntas) >= max_preguntas * 2:
                break

        # Deduplicar por pregunta
        vistas: set[str] = set()
        unicas: list[dict[str, str]] = []
        for p in preguntas:
            if p["pregunta"] not in vistas:
                vistas.add(p["pregunta"])
                unicas.append(p)
            if len(unicas) >= max_preguntas:
                break
        return unicas
