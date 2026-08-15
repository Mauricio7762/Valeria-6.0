"""
7 Agentes Corticales de VALERIA 6.0
Procesamiento especializado en paralelo.
"""

from .base_agente import BaseAgente
from .agente_memoria import AgenteMemoria
from .agente_razonamiento import AgenteRazonamiento
from .agente_emocional import AgenteEmocional
from .agente_acciones import AgenteAcciones
from .agente_percepcion import AgentePercepcion
from .agente_planificacion import AgentePlanificacion
from .agente_monitor import AgenteMonitor
from .coordinador_agentes import CoordinadorAgentes

__all__ = [
    "BaseAgente",
    "AgenteMemoria",
    "AgenteRazonamiento",
    "AgenteEmocional",
    "AgenteAcciones",
    "AgentePercepcion",
    "AgentePlanificacion",
    "AgenteMonitor",
    "CoordinadorAgentes",
]
