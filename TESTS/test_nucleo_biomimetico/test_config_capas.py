"""
Tests de NUCLEO_BIOMIMETICO/config_capas.py.

Cubre la regresión real que motivó este módulo: .env y
valeria_config.yaml tenían nombres y valores de flags que se
contradecían y que además nadie leía. Estos tests fijan la
precedencia acordada: env > yaml > True por defecto.
"""

import os

import pytest

from NUCLEO_BIOMIMETICO.config_capas import resolver_capas, resumen_capas


@pytest.fixture(autouse=True)
def _limpiar_env_layers():
    """Evita que variables LAYER_N_ENABLED de una corrida anterior
    (u otro test) contaminen estos tests."""
    claves = [f"LAYER_{n}_ENABLED" for n in range(5)]
    guardadas = {k: os.environ.pop(k, None) for k in claves}
    yield
    for k, v in guardadas.items():
        if v is not None:
            os.environ[k] = v
        else:
            os.environ.pop(k, None)


def _yaml(**overrides):
    base = {
        "layer_0_fundacion": True,
        "layer_1_nucleo_glial": True,
        "layer_2_agentes_corticales": True,
        "layer_3_sistemas_avanzados": True,
        "layer_4_multimodal_interfaces": True,
    }
    base.update(overrides)
    return {"layers": base}


def test_sin_env_usa_el_yaml():
    r = resolver_capas(_yaml(layer_1_nucleo_glial=False))
    assert r[1] is False
    assert r[0] is True


def test_sin_yaml_ni_env_default_true():
    r = resolver_capas({})
    assert r == {0: True, 1: True, 2: True, 3: True, 4: True}


def test_env_tiene_prioridad_sobre_yaml():
    os.environ["LAYER_3_ENABLED"] = "false"
    r = resolver_capas(_yaml(layer_3_sistemas_avanzados=True))
    assert r[3] is False


def test_env_puede_prender_lo_que_el_yaml_apaga():
    os.environ["LAYER_1_ENABLED"] = "true"
    r = resolver_capas(_yaml(layer_1_nucleo_glial=False))
    assert r[1] is True


@pytest.mark.parametrize(
    "valor,esperado",
    [
        ("true", True), ("True", True), ("1", True), ("si", True), ("SÍ", True), ("on", True),
        ("false", False), ("0", False), ("no", False), ("off", False),
    ],
)
def test_valores_de_env_se_interpretan_case_insensitive(valor, esperado):
    os.environ["LAYER_2_ENABLED"] = valor
    r = resolver_capas(_yaml())
    assert r[2] is esperado


def test_valor_de_env_invalido_cae_al_yaml():
    os.environ["LAYER_4_ENABLED"] = "tal-vez"
    r = resolver_capas(_yaml(layer_4_multimodal_interfaces=False))
    assert r[4] is False  # el valor basura se ignora, manda el yaml


def test_resumen_capas_incluye_las_5():
    r = resolver_capas(_yaml())
    texto = resumen_capas(r)
    for n in range(5):
        assert f"Capa {n}" in texto
