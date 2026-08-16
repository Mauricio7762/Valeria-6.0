"""Tests metacognición nivel 4 + persistencia."""

from pathlib import Path

from SISTEMAS_AVANZADOS.METACOGNICION import (
    AjustadorMetacognitivo,
    MonitorMetacognitivo,
    PlanificadorMetacognitivo,
)
from SISTEMAS_AVANZADOS.METACOGNICION.nivel1_monitoreo import RegistroMeta
from SISTEMAS_AVANZADOS.CURIOSIDAD_COMPUTACIONAL import ExploradorAutonomo
from NUCLEO_BIOMIMETICO.persistencia_meta import cargar_estado_meta, guardar_estado_meta


def test_plan_causal_prioriza_abduccion():
    p = PlanificadorMetacognitivo().planificar(
        "causal", "lentitud", grafo_tiene_entidad=False, grafo_tiene_causas=True
    )
    assert p.estrategias[0] == "abductiva"


def test_ajuste_refuerza_alta_confianza():
    aj = AjustadorMetacognitivo()
    antes = aj.prefs.pesos["deductiva"]
    reg = RegistroMeta("q", "deductiva", 0.9, "definicion", False, False)
    aj.ajustar_desde_registro(reg)
    assert aj.prefs.pesos["deductiva"] > antes


def test_persistencia_roundtrip(tmp_path):
    ruta = tmp_path / "meta.json"
    aj = AjustadorMetacognitivo()
    cur = ExploradorAutonomo()
    aj.prefs.pesos["cbr"] = 1.5
    cur.recompensa.total = 3.2
    guardar_estado_meta(aj, cur, ruta=ruta)
    aj2 = AjustadorMetacognitivo()
    cur2 = ExploradorAutonomo()
    assert cargar_estado_meta(aj2, cur2, ruta=ruta) is True
    assert aj2.prefs.pesos["cbr"] == 1.5
    assert cur2.recompensa.total == 3.2


def test_monitor_registra():
    m = MonitorMetacognitivo()
    m.registrar("hola", {"estrategia": "cbr", "confianza": 0.1, "intencion": "general", "conclusion": "no tengo hechos"})
    assert m.estado()["registros"] == 1
