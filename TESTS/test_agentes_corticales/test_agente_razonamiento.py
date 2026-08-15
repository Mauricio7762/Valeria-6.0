"""
Tests de integración del AgenteRazonamiento (Capa 2).

Todos los tests pasan una ruta de persistencia en tmp_path, para no
leer/escribir el grafo.json real del proyecto durante la corrida.
"""

import pytest

from AGENTES_CORTICALES.agente_razonamiento import AgenteRazonamiento


def _agente(tmp_path, **config_extra):
    config = {"ruta_grafo": str(tmp_path / "grafo.json"), **config_extra}
    return AgenteRazonamiento(config=config)


@pytest.mark.asyncio
async def test_pregunta_definicion_sobre_si_misma_usa_deduccion(tmp_path):
    agente = _agente(tmp_path)
    resultado = await agente.procesar({"pregunta": "¿Qué es valeria?"})
    assert resultado["ok"] is True
    assert resultado["estrategia"] == "deductiva"
    assert "cerebro_humano_digital" in resultado["conclusion"]


@pytest.mark.asyncio
async def test_pregunta_causal_usa_abduccion(tmp_path):
    agente = _agente(tmp_path)
    resultado = await agente.procesar({"pregunta": "¿Por qué hay lentitud de respuesta?"})
    assert resultado["ok"] is True
    assert resultado["estrategia"] == "abductiva"


@pytest.mark.asyncio
async def test_pregunta_sin_hechos_cae_a_cbr_y_no_rompe(tmp_path):
    agente = _agente(tmp_path)
    resultado = await agente.procesar({"pregunta": "algo totalmente fuera de contexto"})
    assert resultado["ok"] is True
    assert resultado["estrategia"] == "cbr"
    assert resultado["conclusion"]  # siempre da alguna respuesta, aunque sea "no sé"


@pytest.mark.asyncio
async def test_agente_deshabilitado_no_procesa(tmp_path):
    agente = _agente(tmp_path, enabled=False)
    resultado = await agente.procesar({"pregunta": "¿Qué es valeria?"})
    assert resultado == {"ok": False, "error": "disabled"}


@pytest.mark.asyncio
async def test_casos_se_registran_para_analogia_futura(tmp_path):
    agente = _agente(tmp_path)
    await agente.procesar({"pregunta": "¿Qué es valeria?"})
    assert len(agente.motor._casos) >= 1


def test_estado_incluye_resumen_del_grafo(tmp_path):
    agente = _agente(tmp_path)
    estado = agente.estado()
    assert "grafo" in estado
    assert estado["grafo"]["total_hechos"] > 0


@pytest.mark.asyncio
async def test_aprender_no_se_confunde_con_preguntar(tmp_path):
    agente = _agente(tmp_path)
    resultado = await agente.procesar({"pregunta": "¿Qué es valeria?"})
    assert resultado["estrategia"] != "aprendizaje"


@pytest.mark.asyncio
async def test_aprende_y_persiste_para_la_proxima_instancia(tmp_path):
    ruta = tmp_path / "grafo.json"

    agente1 = AgenteRazonamiento(config={"ruta_grafo": str(ruta)})
    r_aprender = await agente1.procesar({"contenido": "el futsal es un deporte"})
    assert r_aprender["estrategia"] == "aprendizaje"
    assert ruta.exists()

    # Nueva instancia (simula reiniciar el proceso/la app): debe recordar lo aprendido
    agente2 = AgenteRazonamiento(config={"ruta_grafo": str(ruta)})
    r_pregunta = await agente2.procesar({"pregunta": "¿Qué es el futsal?"})
    assert r_pregunta["estrategia"] == "deductiva"
    assert "deporte" in r_pregunta["conclusion"]
