"""
Tests del razonamiento simbólico: GrafoConocimiento + MotorInferencia
(Capa 2 — AgenteRazonamiento)
"""

from AGENTES_CORTICALES.razonamiento import GrafoConocimiento, MotorInferencia


def _grafo_basico() -> GrafoConocimiento:
    g = GrafoConocimiento()
    g.agregar_hecho("gato", "es_un", "mamifero")
    g.agregar_hecho("mamifero", "es_un", "animal")
    g.agregar_hecho("animal", "tiene_propiedad", "necesita comer")
    g.agregar_hecho("saturacion de cpu", "causa", "lentitud")
    g.agregar_hecho("falta de cache", "causa", "lentitud")
    return g


def test_agregar_hecho_evita_duplicados():
    g = _grafo_basico()
    total_antes = g.total_hechos()
    g.agregar_hecho("gato", "es_un", "mamifero")
    assert g.total_hechos() == total_antes


def test_normaliza_tildes_y_mayusculas():
    g = GrafoConocimiento()
    g.agregar_hecho("Microglía", "es_parte_de", "Sistema Glial")
    assert g.existe("microglia")
    assert g.buscar(sujeto="MICROGLIA")


def test_deduccion_directa():
    g = _grafo_basico()
    motor = MotorInferencia(g)
    resultado = motor.deducir("gato", relacion_objetivo="es_un")
    assert resultado.conclusion == "mamifero"


def test_deduccion_por_herencia_de_propiedad():
    g = _grafo_basico()
    motor = MotorInferencia(g)
    resultado = motor.deducir("gato", relacion_objetivo="tiene_propiedad")
    assert resultado.conclusion == "necesita comer"
    assert resultado.confianza < 1.0


def test_deduccion_transitiva_sin_relacion_objetivo():
    g = _grafo_basico()
    motor = MotorInferencia(g)
    resultado = motor.deducir("gato")
    assert resultado.conclusion is not None
    assert "animal" in resultado.conclusion


def test_deduccion_sujeto_inexistente():
    g = _grafo_basico()
    motor = MotorInferencia(g)
    resultado = motor.deducir("unicornio")
    assert resultado.conclusion is None
    assert resultado.confianza == 0.0


def test_abduccion_con_una_causa():
    g = GrafoConocimiento()
    g.agregar_hecho("virus", "causa", "fiebre")
    motor = MotorInferencia(g)
    resultado = motor.abducir("fiebre")
    assert resultado.conclusion == "virus"
    assert resultado.confianza > 0.5


def test_abduccion_con_causas_ambiguas_reduce_confianza():
    g = _grafo_basico()
    motor = MotorInferencia(g)
    resultado = motor.abducir("lentitud")
    assert resultado.conclusion in ("saturacion de cpu", "falta de cache")
    assert resultado.confianza < 1.0


def test_abduccion_sin_causas_conocidas():
    g = _grafo_basico()
    motor = MotorInferencia(g)
    resultado = motor.abducir("efecto desconocido")
    assert resultado.conclusion is None


def test_razonamiento_por_casos_encuentra_similar():
    g = GrafoConocimiento()
    motor = MotorInferencia(g)
    motor.registrar_caso("como optimizo el cache", ["optimizo", "cache"], "usa oligodendrocitos")
    resultado = motor.razonar_por_casos(["optimizar", "cache"])
    assert resultado.conclusion is not None
    assert "oligodendrocitos" in resultado.conclusion


def test_razonamiento_por_casos_sin_similitud():
    g = GrafoConocimiento()
    motor = MotorInferencia(g)
    motor.registrar_caso("como optimizo el cache", ["optimizo", "cache"], "usa oligodendrocitos")
    resultado = motor.razonar_por_casos(["clima", "lluvia"])
    assert resultado.conclusion is None
