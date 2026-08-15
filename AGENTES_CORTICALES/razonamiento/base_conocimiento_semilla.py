"""
Base de Conocimiento Semilla
=============================
Hechos iniciales que se cargan al arrancar el grafo: autoconocimiento
de la arquitectura de VALERIA (permite responder "qué es X" sobre sí
misma) y un puñado de hechos causales de ejemplo para el razonamiento
abductivo. Se puede ampliar libremente sin tocar el motor.
"""

from __future__ import annotations

from .grafo_conocimiento import GrafoConocimiento

HECHOS_SEMILLA: list[tuple[str, str, str]] = [
    # Autoconocimiento arquitectónico (jerarquía es_un / es_parte_de)
    ("valeria", "es_un", "cerebro_humano_digital"),
    ("cerebro_humano_digital", "tiene_proposito", "replicar la complejidad y resiliencia del cerebro biológico"),
    ("astrocitos", "es_parte_de", "sistema_glial"),
    ("oligodendrocitos", "es_parte_de", "sistema_glial"),
    ("microglia", "es_parte_de", "sistema_glial"),
    ("glia_radial", "es_parte_de", "sistema_glial"),
    ("sistema_glial", "es_parte_de", "nucleo_biomimetico"),
    ("sistema_glial", "tiene_funcion", "mantener la homeostasis y eficiencia cognitiva del sistema"),
    ("astrocitos", "tiene_funcion", "regular la carga cognitiva y la atención"),
    ("oligodendrocitos", "tiene_funcion", "cachear y optimizar rutas de procesamiento frecuentes"),
    ("microglia", "tiene_funcion", "limpiar contextos obsoletos y detectar inconsistencias"),
    ("glia_radial", "tiene_funcion", "dar soporte estructural a la neurogénesis"),
    ("agente_razonamiento", "es_parte_de", "agentes_corticales"),
    ("agente_memoria", "es_parte_de", "agentes_corticales"),
    ("agentes_corticales", "es_parte_de", "cerebro_humano_digital"),
    # Hechos causales de ejemplo (para razonamiento abductivo)
    ("saturación de cpu", "causa", "lentitud de respuesta"),
    ("contexto obsoleto", "causa", "inconsistencia"),
    ("falta de mielinización", "causa", "lentitud de respuesta"),
]


def cargar_semilla(grafo: GrafoConocimiento) -> int:
    """Carga los hechos semilla en el grafo si aún no están. Devuelve cuántos agregó."""
    agregados = 0
    for sujeto, relacion, objeto in HECHOS_SEMILLA:
        antes = grafo.total_hechos()
        grafo.agregar_hecho(sujeto, relacion, objeto, confianza=0.95, origen="base")
        if grafo.total_hechos() > antes:
            agregados += 1
    return agregados
