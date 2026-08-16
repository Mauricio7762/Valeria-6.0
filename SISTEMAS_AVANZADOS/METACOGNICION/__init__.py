"""Metacognición — 5 niveles: monitoreo → evaluación → plan → ajuste → autorreflexión."""

from .nivel1_monitoreo import MonitorMetacognitivo
from .nivel2_evaluacion import EvaluadorMetacognitivo
from .nivel3_planificacion import PlanificadorMetacognitivo, PlanRazonamiento
from .nivel4_ajuste import AjustadorMetacognitivo
from .nivel5_autorreflexion import AutorreflexionMetacognitiva

__all__ = [
    "MonitorMetacognitivo",
    "EvaluadorMetacognitivo",
    "PlanificadorMetacognitivo",
    "PlanRazonamiento",
    "AjustadorMetacognitivo",
    "AutorreflexionMetacognitiva",
]
