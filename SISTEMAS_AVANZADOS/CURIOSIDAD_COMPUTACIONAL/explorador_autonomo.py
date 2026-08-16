"""
Explorador autónomo
===================
Orquesta curiosidad epistémica + perceptual + diversiva y elige
qué pregunta “haría” VALERIA si pudiera indagar sola.
"""

from __future__ import annotations

from typing import Any

from .curiosidad_diversiva import CuriosidadDiversiva
from .curiosidad_epistemica import CuriosidadEpistemica
from .curiosidad_perceptual import CuriosidadPerceptual
from .sistema_recompensa import SistemaRecompensa


class ExploradorAutonomo:
    def __init__(self) -> None:
        self.epistemica = CuriosidadEpistemica()
        self.perceptual = CuriosidadPerceptual()
        self.diversiva = CuriosidadDiversiva()
        self.recompensa = SistemaRecompensa()
        self.ultima_sugerencia: dict[str, str] | None = None

    def observar_turno(
        self,
        entidad: str | None,
        intencion: str | None,
        reg_meta: Any | None,
    ) -> None:
        self.perceptual.observar(entidad, intencion)
        if reg_meta is not None:
            if getattr(reg_meta, "fue_aprendizaje", False):
                self.recompensa.por_aprendizaje()
            elif getattr(reg_meta, "confianza", 0) >= 0.7:
                self.recompensa.por_alta_confianza(reg_meta.confianza)
            elif getattr(reg_meta, "necesita_mas_datos", False):
                self.recompensa.por_laguna_detectada()

    def generar(
        self,
        lagunas: list[str],
        sujetos_grafo: list[str],
        max_total: int = 6,
    ) -> list[dict[str, str]]:
        candidatas: list[dict[str, str]] = []
        candidatas.extend(
            self.epistemica.generar_preguntas(lagunas, sujetos_grafo, max_preguntas=3)
        )
        candidatas.extend(self.diversiva.sugerir(n=2, sujetos_grafo=sujetos_grafo))

        # Prioridad: epistemica (laguna) > perceptual ya se emitió al observar > diversiva
        orden = {"epistemica": 0, "perceptual": 1, "diversiva": 2}
        candidatas.sort(key=lambda p: orden.get(p.get("tipo", ""), 9))

        vistas: set[str] = set()
        out: list[dict[str, str]] = []
        for p in candidatas:
            if p["pregunta"] in vistas:
                continue
            vistas.add(p["pregunta"])
            out.append(p)
            if len(out) >= max_total:
                break

        if out:
            self.ultima_sugerencia = out[0]
            self.recompensa.por_exploracion()
        return out

    def estado(self) -> dict[str, Any]:
        return {
            "recompensa": self.recompensa.estado(),
            "perceptual": self.perceptual.estado(),
            "ultima_sugerencia": self.ultima_sugerencia,
        }
