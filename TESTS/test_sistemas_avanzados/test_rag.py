"""
Tests de SISTEMAS_AVANZADOS/RAG.

No dependen de pypdf: prueban chunking (con texto ya "extraído"),
persistencia del almacén y el retriever, que son la parte con lógica
propia. La extracción real de PDF (_extraer_pypdf) solo se ejercita
si pypdf está instalado, así que se deja fuera para no requerir red.
"""

from SISTEMAS_AVANZADOS.RAG.almacen_chunks import AlmacenChunks
from SISTEMAS_AVANZADOS.RAG.ingesta_pdf import IngestaPDF
from SISTEMAS_AVANZADOS.RAG.retriever import RetrieverRAG


# ---------- IngestaPDF (chunking) ----------

def test_chunkear_texto_vacio_da_lista_vacia():
    assert IngestaPDF().chunkear("") == []


def test_chunkear_respeta_tamano_maximo_y_agrega_ids_secuenciales():
    ing = IngestaPDF(max_chars_chunk=50, solape=10)
    texto = "palabra " * 30  # 240 caracteres
    chunks = ing.chunkear(texto, fuente="doc.pdf")
    assert len(chunks) > 1
    assert all(len(c["texto"]) <= 60 for c in chunks)  # margen por corte en espacio
    assert [c["id"] for c in chunks] == [f"doc.pdf:{i}" for i in range(len(chunks))]


def test_chunkear_corta_en_espacio_no_a_mitad_de_palabra():
    ing = IngestaPDF(max_chars_chunk=20, solape=5)
    texto = "una frase con varias palabras para cortar en espacios correctamente"
    chunks = ing.chunkear(texto)
    for c in chunks[:-1]:  # el último puede terminar donde termina el texto
        assert not c["texto"].endswith(" ")


def test_ingerir_sin_pypdf_no_rompe_devuelve_vacio_si_no_hay_texto():
    # Sin pypdf instalado, _extraer_pypdf devuelve "" y no debe lanzar excepción.
    resultado = IngestaPDF().ingerir(b"contenido binario falso", nombre="x.pdf")
    assert resultado == []


# ---------- AlmacenChunks ----------

def test_almacen_agregar_deduplica_por_id(tmp_path):
    almacen = AlmacenChunks(tmp_path / "chunks.json")
    n1 = almacen.agregar([{"id": "a:0", "texto": "hola"}])
    n2 = almacen.agregar([{"id": "a:0", "texto": "hola"}, {"id": "a:1", "texto": "chau"}])
    assert n1 == 1
    assert n2 == 1  # "a:0" ya estaba, solo cuenta "a:1"
    assert almacen.total() == 2


def test_almacen_persiste_y_recarga(tmp_path):
    ruta = tmp_path / "chunks.json"
    a1 = AlmacenChunks(ruta)
    a1.agregar([{"id": "a:0", "texto": "hola"}])

    a2 = AlmacenChunks(ruta)  # nueva instancia, misma ruta
    assert a2.total() == 1
    assert a2.chunks[0]["texto"] == "hola"


def test_almacen_ruta_inexistente_arranca_vacio(tmp_path):
    almacen = AlmacenChunks(tmp_path / "no_existe.json")
    assert almacen.total() == 0


# ---------- RetrieverRAG ----------

def test_retriever_sin_chunks_devuelve_vacio(tmp_path):
    almacen = AlmacenChunks(tmp_path / "chunks.json")
    r = RetrieverRAG(almacen)
    assert r.buscar("cualquier cosa") == []
    assert r.contexto_para_prompt("cualquier cosa") == ""


def test_retriever_encuentra_por_solapamiento_de_palabras(tmp_path):
    almacen = AlmacenChunks(tmp_path / "chunks.json")
    almacen.agregar(
        [
            {"id": "a:0", "texto": "el sistema glial regula la homeostasis cognitiva", "fuente": "doc.pdf"},
            {"id": "a:1", "texto": "los jugadores de futsal entrenan los martes", "fuente": "doc.pdf"},
        ]
    )
    r = RetrieverRAG(almacen)
    hits = r.buscar("¿qué regula el sistema glial?")
    assert hits
    assert "glial" in hits[0]["texto"]


def test_retriever_contexto_para_prompt_incluye_fuente(tmp_path):
    almacen = AlmacenChunks(tmp_path / "chunks.json")
    almacen.agregar([{"id": "a:0", "texto": "el sistema glial regula la homeostasis", "fuente": "manual.pdf"}])
    r = RetrieverRAG(almacen)
    contexto = r.contexto_para_prompt("qué regula el sistema glial")
    assert "manual.pdf" in contexto
    assert contexto.startswith("[Contexto de documentos]")


def test_retriever_top_k_limita_resultados(tmp_path):
    almacen = AlmacenChunks(tmp_path / "chunks.json")
    almacen.agregar(
        [{"id": f"a:{i}", "texto": "sistema glial homeostasis", "fuente": "doc.pdf"} for i in range(10)]
    )
    r = RetrieverRAG(almacen)
    hits = r.buscar("sistema glial", top_k=3)
    assert len(hits) == 3
