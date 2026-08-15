"""Subpaquete de razonamiento simbólico (Route C): NLP por patrones,
grafo de conocimiento, motor de inferencia (deductiva/abductiva/CBR)
y generación de lenguaje natural estructurado."""

from .base_conocimiento_semilla import cargar_semilla
from .generador_nlg import GeneradorNLG
from .grafo_conocimiento import GrafoConocimiento, Hecho
from .motor_inferencia import MotorInferencia, ResultadoInferencia
from .nlp_patrones import AnalisisNLP, AnalizadorPatrones

__all__ = [
    "cargar_semilla",
    "GeneradorNLG",
    "GrafoConocimiento",
    "Hecho",
    "MotorInferencia",
    "ResultadoInferencia",
    "AnalisisNLP",
    "AnalizadorPatrones",
]
