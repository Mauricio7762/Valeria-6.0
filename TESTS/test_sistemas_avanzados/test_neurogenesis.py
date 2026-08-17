"""
Tests de SISTEMAS_AVANZADOS/NEUROGENESIS_ARTIFICIAL.

Usa GrafoConocimiento real (no un mock) porque plasticidad y poda tocan
sus atributos internos (_hechos, _por_sujeto, _por_relacion) — es la
forma más fiel de probar que la reconstrucción de índices no rompe nada.
"""

from AGENTES_CORTICALES.razonamiento.grafo_conocimiento import GrafoConocimiento, Hecho
from SISTEMAS_AVANZADOS.NEUROGENESIS_ARTIFICIAL import (
    CoordinadorNeurogenesis,
    CrecimientoDinamico,
    HomeostasisRed,
    OptimizacionTopologica,
    PlasticidadEstructural,
    PodadoSinaptico,
)


def _grafo_con(*triples, origen="usuario", confianza=1.0):
    g = GrafoConocimiento()
    for s, r, o in triples:
        g.agregar_hecho(s, r, o, confianza=confianza, origen=origen)
    return g


# ---------- CrecimientoDinamico ----------

def test_crecimiento_no_materializa_confianza_baja():
    g = GrafoConocimiento()
    c = CrecimientoDinamico()
    creado = c.crecer_desde_inferencia(g, "gato", "es_un", "animal", confianza=0.3)
    assert creado is False
    assert g.total_hechos() == 0


def test_crecimiento_materializa_inferencia_nueva():
    g = GrafoConocimiento()
    c = CrecimientoDinamico()
    creado = c.crecer_desde_inferencia(g, "gato", "es_un", "animal", confianza=0.8)
    assert creado is True
    assert g.total_hechos() == 1
    hecho = g.buscar(sujeto="gato")[0]
    assert hecho.origen == "inferido"
    assert hecho.confianza == 0.8


def test_crecimiento_no_duplica_hecho_existente():
    g = _grafo_con(("gato", "es_un", "animal"))
    c = CrecimientoDinamico()
    creado = c.crecer_desde_inferencia(g, "gato", "es_un", "animal", confianza=0.9)
    assert creado is False
    assert g.total_hechos() == 1


def test_crecimiento_historial_trunca_a_40():
    g = GrafoConocimiento()
    c = CrecimientoDinamico()
    for i in range(50):
        c.crecer_desde_inferencia(g, f"sujeto{i}", "es_un", "cosa", confianza=0.9)
    assert len(c.historial) == 40
    assert c.nuevas_conexiones == 50


# ---------- HomeostasisRed ----------

def test_homeostasis_estado_ok_en_rango_normal():
    h = HomeostasisRed(max_hechos=500, min_hechos=5)
    r = h.evaluar(100)
    assert r["estado"] == "ok"
    assert r["necesita_poda"] is False


def test_homeostasis_detecta_sobrecrecimiento():
    h = HomeostasisRed(max_hechos=10, min_hechos=1)
    r = h.evaluar(15)
    assert r["estado"] == "sobrecrecimiento"
    assert r["necesita_poda"] is True
    assert h.alertas == 1


def test_homeostasis_detecta_subdesarrollo():
    h = HomeostasisRed(max_hechos=500, min_hechos=10)
    r = h.evaluar(3)
    assert r["estado"] == "subdesarrollo"
    assert r["necesita_poda"] is False


# ---------- OptimizacionTopologica ----------

def test_topologia_grafo_vacio():
    g = GrafoConocimiento()
    t = OptimizacionTopologica().analizar(g)
    assert t == {"hechos": 0, "densidad_relativa": 0.0}


def test_topologia_calcula_nodos_y_densidad():
    g = _grafo_con(("gato", "es_un", "mamifero"), ("mamifero", "es_un", "animal"))
    t = OptimizacionTopologica().analizar(g)
    assert t["hechos"] == 2
    assert t["nodos"] == 3  # gato, mamifero, animal
    assert t["densidad_relativa"] > 0


# ---------- PlasticidadEstructural ----------

def test_plasticidad_refuerza_hechos_muy_usados():
    g = _grafo_con(("gato", "es_un", "animal"), confianza=0.5)
    p = PlasticidadEstructural()
    p.registrar_uso("gato", "es_un", "animal")
    p.registrar_uso("gato", "es_un", "animal")  # 2 usos -> supera el umbral (>=2)
    reforzados = p.reforzar_hechos_usados(g)
    assert reforzados == 1
    assert g.buscar(sujeto="gato")[0].confianza > 0.5


def test_plasticidad_no_refuerza_con_un_solo_uso():
    g = _grafo_con(("gato", "es_un", "animal"), confianza=0.5)
    p = PlasticidadEstructural()
    p.registrar_uso("gato", "es_un", "animal")
    reforzados = p.reforzar_hechos_usados(g)
    assert reforzados == 0
    assert g.buscar(sujeto="gato")[0].confianza == 0.5


def test_plasticidad_reconstruye_indices_sin_perder_hechos():
    g = _grafo_con(("gato", "es_un", "animal"), ("perro", "es_un", "animal"), confianza=0.5)
    p = PlasticidadEstructural()
    p.registrar_uso("gato", "es_un", "animal")
    p.registrar_uso("gato", "es_un", "animal")
    p.reforzar_hechos_usados(g)
    # el hecho no tocado sigue accesible por índice
    assert g.existe("perro")
    assert g.total_hechos() == 2


# ---------- PodadoSinaptico ----------

def test_poda_no_actua_bajo_el_minimo():
    g = _grafo_con(*[(f"s{i}", "es_un", "cosa") for i in range(5)], origen="inferido", confianza=0.1)
    poda = PodadoSinaptico(min_hechos_para_podar=25)
    eliminados = poda.podar(g)
    assert eliminados == 0
    assert g.total_hechos() == 5


def test_poda_elimina_inferidos_de_baja_confianza_sin_uso():
    g = GrafoConocimiento()
    for i in range(30):
        g.agregar_hecho(f"s{i}", "es_un", "cosa", confianza=0.1, origen="inferido")
    poda = PodadoSinaptico(umbral_confianza=0.35, min_hechos_para_podar=25)
    eliminados = poda.podar(g)
    assert eliminados == 30
    assert g.total_hechos() == 0


def test_poda_preserva_base_y_usuario_con_confianza_alta():
    g = GrafoConocimiento()
    g.agregar_hecho("valeria", "es_un", "sistema", confianza=0.95, origen="base")
    g.agregar_hecho("futsal", "es_un", "deporte", confianza=0.9, origen="usuario")
    for i in range(25):
        g.agregar_hecho(f"s{i}", "es_un", "cosa", confianza=0.1, origen="inferido")
    poda = PodadoSinaptico(umbral_confianza=0.35, min_hechos_para_podar=25)
    poda.podar(g)
    assert g.existe("valeria")
    assert g.existe("futsal")


# ---------- CoordinadorNeurogenesis ----------

def test_coordinador_ciclo_mantenimiento_devuelve_resumen_completo():
    g = _grafo_con(("gato", "es_un", "animal"))
    coord = CoordinadorNeurogenesis()
    coord.registrar_hecho_usado("gato", "es_un", "animal")
    resultado = coord.ciclo_mantenimiento(g)
    assert "reforzados" in resultado
    assert "podados" in resultado
    assert "homeostasis" in resultado
    assert "topologia" in resultado
    assert coord.ciclos == 1
