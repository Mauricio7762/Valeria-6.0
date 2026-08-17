"""
Tests de SISTEMAS_AVANZADOS/CURIOSIDAD_COMPUTACIONAL.
"""

from SISTEMAS_AVANZADOS.CURIOSIDAD_COMPUTACIONAL import (
    CuriosidadDiversiva,
    CuriosidadEpistemica,
    CuriosidadPerceptual,
    ExploradorAutonomo,
    SistemaRecompensa,
)


# ---------- CuriosidadPerceptual ----------

def test_perceptual_alerta_solo_en_primera_aparicion():
    c = CuriosidadPerceptual()
    primera = c.observar("microglia", "definicion")
    segunda = c.observar("microglia", "definicion")
    assert len(primera) == 1
    assert primera[0]["tipo"] == "perceptual"
    assert segunda == []  # ya no es novedad
    assert c.entidades_vistas["microglia"] == 2


def test_perceptual_estado_resume_entidades_e_intenciones():
    c = CuriosidadPerceptual()
    c.observar("microglia", "definicion")
    c.observar("astrocitos", "definicion")
    estado = c.estado()
    assert estado["entidades_distintas"] == 2
    assert estado["intenciones"]["definicion"] == 2


# ---------- CuriosidadEpistemica ----------

def test_epistemica_genera_desde_lagunas_y_sujetos():
    c = CuriosidadEpistemica()
    preguntas = c.generar_preguntas(
        lagunas=["unicornio"], sujetos_grafo=["microglia", "astrocitos"], max_preguntas=5
    )
    assert any("unicornio" in p["pregunta"] for p in preguntas)
    assert len(preguntas) <= 5


def test_epistemica_deduplica_y_respeta_max():
    c = CuriosidadEpistemica()
    preguntas = c.generar_preguntas(
        lagunas=["x"] * 10, sujetos_grafo=["a"] * 10, max_preguntas=3
    )
    textos = [p["pregunta"] for p in preguntas]
    assert len(textos) == len(set(textos))  # sin duplicados
    assert len(preguntas) <= 3


# ---------- CuriosidadDiversiva ----------

def test_diversiva_respeta_n_y_usa_sujetos_del_grafo():
    c = CuriosidadDiversiva()
    sugerencias = c.sugerir(n=2, sujetos_grafo=["microglia"])
    assert len(sugerencias) == 2
    assert all(s["tipo"] == "diversiva" for s in sugerencias)


# ---------- SistemaRecompensa ----------

def test_recompensa_acumula_total_y_guarda_historial():
    r = SistemaRecompensa()
    r.por_aprendizaje()
    r.por_alta_confianza(0.9)
    assert r.total > 0
    assert len(r.historial) == 2


def test_recompensa_trunca_historial_a_max_hist():
    r = SistemaRecompensa(max_hist=5)
    for _ in range(10):
        r.por_exploracion()
    assert len(r.historial) == 5


# ---------- ExploradorAutonomo ----------

def test_explorador_observar_turno_no_rompe_sin_reg_meta():
    e = ExploradorAutonomo()
    e.observar_turno("microglia", "definicion", None)
    assert e.perceptual.entidades_vistas["microglia"] == 1


def test_explorador_genera_sugerencias_y_actualiza_recompensa():
    e = ExploradorAutonomo()
    total_antes = e.recompensa.total
    sugerencias = e.generar(lagunas=["algo"], sujetos_grafo=["microglia"], max_total=3)
    assert len(sugerencias) <= 3
    if sugerencias:
        assert e.ultima_sugerencia == sugerencias[0]
        assert e.recompensa.total > total_antes


def test_explorador_estado_incluye_las_tres_subareas():
    e = ExploradorAutonomo()
    estado = e.estado()
    assert "recompensa" in estado
    assert "perceptual" in estado
    assert "ultima_sugerencia" in estado
