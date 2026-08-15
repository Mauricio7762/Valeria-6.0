"""
Tests básicos del Sistema Glial (Capa 0)
"""

import pytest

from NUCLEO_BIOMIMETICO.SISTEMA_GLIAL import (
    SistemaGlial,
    Astrocitos,
    Oligodendrocitos,
    Microglia,
    GliaRadial,
)


def test_sistema_glial_inicializa():
    sistema = SistemaGlial()
    assert sistema.enabled is True
    assert isinstance(sistema.astrocitos, Astrocitos)
    assert isinstance(sistema.oligodendrocitos, Oligodendrocitos)
    assert isinstance(sistema.microglia, Microglia)
    assert isinstance(sistema.glia_radial, GliaRadial)


def test_estado_sistema_glial():
    sistema = SistemaGlial()
    estado = sistema.estado()
    assert "enabled" in estado
    assert "astrocitos" in estado
    assert "oligodendrocitos" in estado
    assert "microglia" in estado
    assert "glia_radial" in estado


@pytest.mark.asyncio
async def test_tick_sistema_glial():
    sistema = SistemaGlial()
    await sistema.tick()  # No debe lanzar excepción
