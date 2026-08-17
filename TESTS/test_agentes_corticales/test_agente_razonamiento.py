"""
Tests de integración del AgenteRazonamiento (Capa 2 + Route C).

Todos los tests pasan una ruta de persistencia en tmp_path, para no
leer/escribir el grafo.json real del proyecto durante la corrida.

Las aserciones de texto usan substrings estables (fragmentos de la
conclusión) en vez de comparar el mensaje completo, porque el NLG
varía la redacción según la confianza — así el test no se rompe cada
vez que se ajuste una frase, pero sí detecta si deja de responder lo
que corresponde.
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
    assert "cerebro humano digital" in resultado["conclusion"].lower()


@pytest.mark.asyncio
async def test_pregunta_causal_usa_abduccion(tmp_path):
    agente = _agente(tmp_path)
    resultado = await agente.procesar({"pregunta": "¿Por qué hay lentitud de respuesta?"})
    assert resultado["ok"] is True
    assert resultado["estrategia"] == "abductiva"


@pytest.mark.asyncio
async def test_pregunta_sin_hechos_cae_a_cbr_y_no_rompe(tmp_path):
    agente = _agente(tmp_path)
    resultado = await agente.procesar({"pregunta": "algo totalmente fuera de contexto sin sentido"})
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
    assert "deporte" in r_pregunta["conclusion"].lower()


@pytest.mark.asyncio
async def test_regresion_puntuacion_pegada_y_pregunta_con_quien(tmp_path):
    """Regresión del bug real reportado: 'BocaJrs.' (con punto, por la
    abreviatura) guardado como sujeto no coincidía con la entidad
    extraída de '¿Quién es BocaJrs?' (sin punto)."""
    agente = _agente(tmp_path)
    r1 = await agente.procesar({"contenido": "BocaJrs. es el mejor club de la Argentina"})
    assert r1["estrategia"] == "aprendizaje"

    r2 = await agente.procesar({"pregunta": "¿Quién es BocaJrs?"})
    assert r2["estrategia"] == "deductiva"
    assert "club" in r2["conclusion"].lower()


@pytest.mark.asyncio
async def test_plan_de_estrategias_metacognitivo_se_respeta(tmp_path):
    """Si el orquestador (metacognición) manda un orden explícito de
    estrategias, el agente debe intentarlas en ese orden antes de caer
    a su heurística por defecto."""
    agente = _agente(tmp_path)
    resultado = await agente.procesar(
        {"pregunta": "¿Por qué hay lentitud de respuesta?", "plan_estrategias": ["cbr", "abductiva"]}
    )
    # cbr no tiene casos previos todavía -> debe seguir al siguiente de la lista
    assert resultado["estrategia"] == "abductiva"
