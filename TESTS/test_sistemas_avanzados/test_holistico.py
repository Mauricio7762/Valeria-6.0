from pathlib import Path
from SISTEMAS_AVANZADOS.ANALIZADOR_HOLISTICO_CODIGO import OrquestadorHolistico


def test_holistico_analiza_repo():
    raiz = Path(__file__).resolve().parents[2]
    h = OrquestadorHolistico(raiz)
    inf = h.analizar()
    assert inf["resumen"]["archivos"] > 0
    assert "mejoras" in inf
    md = h.informe_markdown(inf)
    assert "Análisis holístico" in md
