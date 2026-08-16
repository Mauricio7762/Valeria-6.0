"""Detector de patrones — arquitectura biomimética / capas VALERIA."""

from __future__ import annotations

from typing import Any


_PATRONES_ESPERADOS = {
    "orquestador": ["orquestador_principal", "OrquestadorPrincipal"],
    "sistema_glial": ["SistemaGlial", "Astrocitos", "Microglia"],
    "agentes": ["AgenteRazonamiento", "CoordinadorAgentes", "BaseAgente"],
    "metacognicion": ["MonitorMetacognitivo", "PlanificadorMetacognitivo"],
    "curiosidad": ["ExploradorAutonomo", "CuriosidadEpistemica"],
    "neurogenesis": ["CoordinadorNeurogenesis", "PodadoSinaptico"],
    "razonamiento": ["GrafoConocimiento", "MotorInferencia"],
}


class DetectorPatrones:
    def detectar(self, extracciones: list[dict[str, Any]]) -> dict[str, Any]:
        nombres: set[str] = set()
        paths: set[str] = set()
        for ex in extracciones:
            paths.add(ex.get("path", ""))
            nombres.update(ex.get("clases", []))
            nombres.update(ex.get("funciones", []))

        presentes = {}
        faltantes = {}
        for capa, keys in _PATRONES_ESPERADOS.items():
            ok = [k for k in keys if any(k in n or k in p for n in nombres for p in [""]) or any(k in p for p in paths) or k in nombres]
            # simpler: string membership in all text of names+paths
            blob = " ".join(list(nombres) + list(paths))
            hallados = [k for k in keys if k in blob]
            presentes[capa] = hallados
            faltantes[capa] = [k for k in keys if k not in hallados]

        return {
            "capas_cubiertas": [c for c, h in presentes.items() if h],
            "capas_vacias": [c for c, h in presentes.items() if not h],
            "detalle": presentes,
            "faltantes": {c: f for c, f in faltantes.items() if f},
        }
