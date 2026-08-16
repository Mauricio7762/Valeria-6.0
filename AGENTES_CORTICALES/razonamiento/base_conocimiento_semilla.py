"""
Base de Conocimiento Semilla
=============================
Hechos iniciales de VALERIA: arquitectura, glía, agentes, meta,
curiosidad, neurogénesis y causas de ejemplo.
"""

from __future__ import annotations

from .grafo_conocimiento import GrafoConocimiento

HECHOS_SEMILLA: list[tuple[str, str, str]] = [
    # --- Identidad ---
    ("valeria", "es_un", "cerebro_humano_digital"),
    ("valeria", "es_un", "sistema_biomimetico"),
    ("cerebro_humano_digital", "tiene_proposito", "replicar la complejidad y resiliencia del cerebro biologico"),
    ("biomimesis", "es_un", "enfoque_de_diseno"),
    ("biomimesis", "tiene_proposito", "imitar principios de la biologia en sistemas artificiales"),

    # --- Núcleo y glía ---
    ("nucleo_biomimetico", "es_parte_de", "valeria"),
    ("sistema_glial", "es_parte_de", "nucleo_biomimetico"),
    ("sistema_glial", "tiene_funcion", "mantener la homeostasis y eficiencia cognitiva del sistema"),
    ("astrocitos", "es_parte_de", "sistema_glial"),
    ("oligodendrocitos", "es_parte_de", "sistema_glial"),
    ("microglia", "es_parte_de", "sistema_glial"),
    ("glia_radial", "es_parte_de", "sistema_glial"),
    ("astrocitos", "tiene_funcion", "regular la carga cognitiva y la atencion"),
    ("oligodendrocitos", "tiene_funcion", "cachear y optimizar rutas de procesamiento frecuentes"),
    ("microglia", "tiene_funcion", "limpiar contextos obsoletos y detectar inconsistencias"),
    ("glia_radial", "tiene_funcion", "dar soporte estructural a la neurogenesis"),
    ("orquestador_principal", "es_parte_de", "nucleo_biomimetico"),
    ("orquestador_principal", "tiene_funcion", "coordinar el arranque los ciclos y el estado de consciencia"),
    ("gestor_recursos", "es_parte_de", "nucleo_biomimetico"),
    ("gestor_recursos", "tiene_funcion", "monitorear cpu y memoria del sistema"),

    # --- Agentes corticales ---
    ("agentes_corticales", "es_parte_de", "valeria"),
    ("agente_memoria", "es_parte_de", "agentes_corticales"),
    ("agente_razonamiento", "es_parte_de", "agentes_corticales"),
    ("agente_emocional", "es_parte_de", "agentes_corticales"),
    ("agente_acciones", "es_parte_de", "agentes_corticales"),
    ("agente_percepcion", "es_parte_de", "agentes_corticales"),
    ("agente_planificacion", "es_parte_de", "agentes_corticales"),
    ("agente_monitor", "es_parte_de", "agentes_corticales"),
    ("agente_memoria", "tiene_funcion", "guardar episodios y conocimiento semantico"),
    ("agente_razonamiento", "tiene_funcion", "inferir con grafo deductivo abductivo y cbr"),
    ("agente_emocional", "tiene_funcion", "modular el tono afectivo de las respuestas"),
    ("agente_percepcion", "tiene_funcion", "normalizar entradas del usuario"),
    ("agente_planificacion", "tiene_funcion", "descomponer objetivos en pasos"),
    ("agente_monitor", "tiene_funcion", "registrar metricas internas del sistema"),
    ("agente_acciones", "tiene_funcion", "ejecutar o simular acciones externas"),
    ("grafo_conocimiento", "es_parte_de", "agente_razonamiento"),
    ("grafo_conocimiento", "tiene_funcion", "almacenar hechos sujeto relacion objeto"),
    ("motor_inferencia", "es_parte_de", "agente_razonamiento"),
    ("motor_inferencia", "tiene_funcion", "deducir abducir y razonar por casos"),

    # --- Metacognición ---
    ("metacognicion", "es_parte_de", "valeria"),
    ("metacognicion", "tiene_funcion", "monitorear evaluar planificar ajustar y reflexionar sobre el razonamiento"),
    ("monitor_metacognitivo", "es_parte_de", "metacognicion"),
    ("evaluador_metacognitivo", "es_parte_de", "metacognicion"),
    ("planificador_metacognitivo", "es_parte_de", "metacognicion"),
    ("ajustador_metacognitivo", "es_parte_de", "metacognicion"),
    ("autorreflexion", "es_parte_de", "metacognicion"),
    ("monitor_metacognitivo", "tiene_funcion", "registrar confianza y estrategia de cada turno"),
    ("planificador_metacognitivo", "tiene_funcion", "elegir el orden de estrategias de inferencia"),
    ("ajustador_metacognitivo", "tiene_funcion", "aprender pesos de estrategias segun resultados"),
    ("autorreflexion", "tiene_funcion", "resumir fortalezas debilidades y lagunas de la sesion"),

    # --- Curiosidad ---
    ("curiosidad_computacional", "es_parte_de", "valeria"),
    ("curiosidad_computacional", "tiene_funcion", "generar preguntas sobre lagunas y novedades"),
    ("curiosidad_epistemica", "es_parte_de", "curiosidad_computacional"),
    ("curiosidad_perceptual", "es_parte_de", "curiosidad_computacional"),
    ("curiosidad_diversiva", "es_parte_de", "curiosidad_computacional"),
    ("explorador_autonomo", "es_parte_de", "curiosidad_computacional"),
    ("sistema_recompensa", "es_parte_de", "curiosidad_computacional"),
    ("curiosidad_epistemica", "tiene_funcion", "preguntar por lo que el sistema no sabe"),
    ("sistema_recompensa", "tiene_funcion", "señalar aprendizaje exploracion y maestria"),

    # --- Neurogénesis ---
    ("neurogenesis_artificial", "es_parte_de", "valeria"),
    ("neurogenesis_artificial", "tiene_funcion", "crecer reforzar y podar conexiones del grafo"),
    ("crecimiento_dinamico", "es_parte_de", "neurogenesis_artificial"),
    ("plasticidad_estructural", "es_parte_de", "neurogenesis_artificial"),
    ("podado_sinaptico", "es_parte_de", "neurogenesis_artificial"),
    ("homeostasis_red", "es_parte_de", "neurogenesis_artificial"),
    ("plasticidad_estructural", "tiene_funcion", "aumentar confianza de hechos muy usados"),
    ("podado_sinaptico", "tiene_funcion", "eliminar hechos inferidos debiles sin uso"),

    # --- Capas e interfaces ---
    ("capa_0", "es_parte_de", "valeria"),
    ("capa_1", "es_parte_de", "valeria"),
    ("capa_2", "es_parte_de", "valeria"),
    ("capa_3", "es_parte_de", "valeria"),
    ("capa_0", "tiene_funcion", "fundacion infraestructura y configuracion"),
    ("capa_1", "tiene_funcion", "nucleo biomimetico y sistema glial"),
    ("capa_2", "tiene_funcion", "agentes corticales y razonamiento"),
    ("capa_3", "tiene_funcion", "metacognicion curiosidad y neurogenesis"),
    ("interfaz_streamlit", "es_parte_de", "valeria"),
    ("interfaz_api", "es_parte_de", "valeria"),
    ("interfaz_streamlit", "tiene_funcion", "chat grafico con historial y atajos"),
    ("interfaz_api", "tiene_funcion", "exponer chat y estado por http"),
    ("analizador_holistico", "es_parte_de", "valeria"),
    ("analizador_holistico", "tiene_funcion", "escanear el codigo del proyecto y proponer mejoras"),

    # --- Memoria ---
    ("memoria_episodica", "es_parte_de", "agente_memoria"),
    ("memoria_semantica", "es_parte_de", "agente_memoria"),
    ("memoria_trabajo", "es_parte_de", "agente_memoria"),
    ("memoria_episodica", "tiene_funcion", "guardar eventos de la conversacion con tiempo"),
    ("memoria_semantica", "tiene_funcion", "guardar hechos estables y el grafo"),
    ("memoria_trabajo", "tiene_funcion", "mantener el contexto reciente del dialogo"),

    # --- Causas (abducción) ---
    ("saturacion de cpu", "causa", "lentitud de respuesta"),
    ("falta de mielinizacion", "causa", "lentitud de respuesta"),
    ("contexto obsoleto", "causa", "inconsistencia"),
    ("grafo incompleto", "causa", "baja confianza"),
    ("sin hechos relevantes", "causa", "respuesta incierta"),
    ("muchos stubs", "causa", "comportamiento incompleto"),
    ("archivo muy grande", "causa", "dificultad de mantenimiento"),
]


def cargar_semilla(grafo: GrafoConocimiento) -> int:
    """Carga los hechos semilla. Devuelve cuántos agregó."""
    agregados = 0
    for sujeto, relacion, objeto in HECHOS_SEMILLA:
        antes = grafo.total_hechos()
        grafo.agregar_hecho(sujeto, relacion, objeto, confianza=0.95, origen="base")
        if grafo.total_hechos() > antes:
            agregados += 1
    return agregados
