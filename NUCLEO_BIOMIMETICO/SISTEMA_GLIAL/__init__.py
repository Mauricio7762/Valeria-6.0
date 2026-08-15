"""
SISTEMA GLIAL COMPUTACIONAL - Infraestructura Cognitiva de VALERIA 6.0

Las glías no "piensan", pero hacen que el pensamiento sea posible,
estable y eficiente. Representan ~50% del cerebro biológico de soporte.
"""

from .sistema_glial import SistemaGlial
from .astrocitos import Astrocitos
from .oligodendrocitos import Oligodendrocitos
from .microglia import Microglia
from .glia_radial import GliaRadial

__all__ = [
    "SistemaGlial",
    "Astrocitos",
    "Oligodendrocitos",
    "Microglia",
    "GliaRadial",
]
