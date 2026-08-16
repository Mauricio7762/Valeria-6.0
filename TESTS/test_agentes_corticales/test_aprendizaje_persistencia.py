"""
Tests de aprendizaje (extractor_hechos) y persistencia (GrafoConocimiento).
"""

from AGENTES_CORTICALES.razonamiento.extractor_hechos import extraer_hecho
from AGENTES_CORTICALES.razonamiento.grafo_conocimiento import GrafoConocimiento


# ---------- Extractor de hechos ----------

def test_extrae_es_un():
    h = extraer_hecho("el futsal es un deporte")
    assert h is not None
    assert h.sujeto == "futsal"  # sin artículo
    assert h.relacion == "es_un"
    assert h.objeto == "deporte"


def test_extrae_causa():
    h = extraer_hecho("el estres causa mal rendimiento")
    assert h is not None
    assert h.relacion == "causa"
    assert h.sujeto == "estres"
    assert h.objeto == "mal rendimiento"


def test_extrae_es_parte_de():
    h = extraer_hecho("el arquero es parte de la defensa")
    assert h is not None
    assert h.relacion == "es_parte_de"


def test_prefijo_explicito_recorda_que():
    h = extraer_hecho("recorda que Mauricio es programador")
    assert h is not None
    assert h.explicito is True


def test_no_extrae_de_preguntas_con_signo():
    assert extraer_hecho("¿Qué es el futsal?") is None
    assert extraer_hecho("¿el futsal es un deporte?") is None


def test_no_extrae_de_preguntas_sin_signo():
    assert extraer_hecho("que es el futsal") is None
    assert extraer_hecho("como funciona el sistema glial") is None


def test_no_extrae_de_texto_irrelevante():
    assert extraer_hecho("quiero optimizar el rendimiento") is None


# ---------- Persistencia ----------

def test_guardar_y_cargar_roundtrip(tmp_path):
    ruta = tmp_path / "grafo.json"
    g1 = GrafoConocimiento()
    g1.agregar_hecho("futsal", "es_un", "deporte", confianza=0.9, origen="usuario")
    g1.guardar(ruta)

    g2 = GrafoConocimiento()
    agregados = g2.cargar(ruta)
    assert agregados == 1
    assert g2.existe("futsal")
    assert g2.buscar(sujeto="futsal", relacion="es_un")[0].objeto == "deporte"


def test_cargar_archivo_inexistente_no_rompe(tmp_path):
    g = GrafoConocimiento()
    assert g.cargar(tmp_path / "no_existe.json") == 0


def test_guardar_es_atomico_no_dejar_tmp(tmp_path):
    ruta = tmp_path / "grafo.json"
    g = GrafoConocimiento()
    g.agregar_hecho("a", "es_un", "b")
    g.guardar(ruta)
    assert ruta.exists()
    assert not ruta.with_suffix(ruta.suffix + ".tmp").exists()

def test_extrae_es_parte_del_contraccion():
    """'del' = de + el; debe mapear a es_parte_de."""
    from AGENTES_CORTICALES.razonamiento.extractor_hechos import extraer_hecho
    h = extraer_hecho('la microglía es parte del sistema glial')
    assert h is not None
    assert h.relacion == 'es_parte_de'
    assert 'microgl' in h.sujeto  # microglia / microglía
    assert 'sistema glial' in h.objeto

