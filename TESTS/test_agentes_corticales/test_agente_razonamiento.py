"""
Tests de integración del AgenteRazonamiento (Capa 2).
"""

import pytest

from AGENTES_CORTICALES.agente_razonamiento import AgenteRazonamiento


@pytest.mark.asyncio
async def test_pregunta_definicion_sobre_si_misma_usa_deduccion():
    agente = AgenteRazonamiento()
    resultado = await agente.procesar({"pregunta": "¿Qué es valeria?"})
    assert resultado["ok"] is True
    assert resultado["estrategia"] == "deductiva"
    assert "cerebro_humano_digital" in resultado["conclusion"]


@pytest.mark.asyncio
async def test_pregunta_causal_usa_abduccion():
    agente = AgenteRazonamiento()
    resultado = await agente.procesar({"pregunta": "¿Por qué hay lentitud de respuesta?"})
    assert resultado["ok"] is True
    assert resultado["estrategia"] == "abductiva"


@pytest.mark.asyncio
async def test_pregunta_sin_hechos_cae_a_cbr_y_no_rompe():
    agente = AgenteRazonamiento()
    resultado = await agente.procesar({"pregunta": "algo totalmente fuera de contexto"})
    assert resultado["ok"] is True
    assert resultado["estrategia"] == "cbr"
    assert resultado["conclusion"]  # siempre da alguna respuesta, aunque sea "no sé"


@pytest.mark.asyncio
async def test_agente_deshabilitado_no_procesa():
    agente = AgenteRazonamiento(config={"enabled": False})
    resultado = await agente.procesar({"pregunta": "¿Qué es valeria?"})
    assert resultado == {"ok": False, "error": "disabled"}


@pytest.mark.asyncio
async def test_casos_se_registran_para_analogia_futura():
    agente = AgenteRazonamiento()
    await agente.procesar({"pregunta": "¿Qué es valeria?"})
    assert len(agente.motor._casos) >= 1


def test_estado_incluye_resumen_del_grafo():
    agente = AgenteRazonamiento()
    estado = agente.estado()
    assert "grafo" in estado
    assert estado["grafo"]["total_hechos"] > 0
