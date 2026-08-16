"""Orquestador holístico — pipeline completo de análisis del repo."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .detector_patrones import DetectorPatrones
from .detector_problemas import DetectorProblemas
from .extractor_ast import ExtractorAST
from .generador_mejoras import GeneradorMejoras
from .scanner_proyecto import ScannerProyecto
from .validador_sintaxis import ValidadorSintaxis


class OrquestadorHolistico:
    def __init__(self, raiz: Path | str) -> None:
        self.raiz = Path(raiz)
        self.scanner = ScannerProyecto(self.raiz)
        self.ast = ExtractorAST()
        self.patrones = DetectorPatrones()
        self.problemas = DetectorProblemas()
        self.mejoras = GeneradorMejoras()
        self.validador = ValidadorSintaxis()
        self.ultimo_informe: dict[str, Any] | None = None

    def analizar(self) -> dict[str, Any]:
        archivos = self.scanner.escanear()
        # No guardar textos enormes en el informe final
        extracciones = []
        sintaxis = []
        for a in archivos:
            ex = self.ast.extraer(a["texto"], a["path"])
            extracciones.append(ex)
            sintaxis.append(self.validador.validar(a["path"], a["texto"]))

        resumen = self.scanner.resumen(archivos)
        # quitar texto del resumen top
        resumen["top_grandes"] = [
            {"path": x["path"], "lineas": x["lineas"]} for x in resumen["top_grandes"]
        ]
        patrones = self.patrones.detectar(extracciones)
        problemas = self.problemas.detectar(archivos, extracciones)
        mejoras = self.mejoras.generar(resumen, patrones, problemas)

        clases = sum(len(e.get("clases", [])) for e in extracciones)
        funciones = sum(len(e.get("funciones", [])) for e in extracciones)
        errores_sint = sum(1 for s in sintaxis if not s["ok"])

        informe = {
            "resumen": resumen,
            "metricas": {
                "clases": clases,
                "funciones": funciones,
                "errores_sintaxis": errores_sint,
            },
            "patrones": patrones,
            "problemas": problemas[:30],
            "mejoras": mejoras,
        }
        self.ultimo_informe = informe
        return informe

    def informe_markdown(self, informe: dict[str, Any] | None = None) -> str:
        inf = informe or self.ultimo_informe
        if not inf:
            return "Todavía no hay análisis. Ejecutá el analizador primero."

        r = inf["resumen"]
        m = inf["metricas"]
        lineas = [
            "## Análisis holístico del código",
            "",
            f"- **Archivos:** {r['archivos']}",
            f"- **Líneas:** {r['lineas_totales']}",
            f"- **Clases / funciones:** {m['clases']} / {m['funciones']}",
            f"- **Errores de sintaxis:** {m['errores_sintaxis']}",
            "",
            "### Capas detectadas",
            ", ".join(inf["patrones"].get("capas_cubiertas") or ["—"]) or "—",
            "",
        ]
        vacias = inf["patrones"].get("capas_vacias") or []
        if vacias:
            lineas.append("### Capas débiles o vacías")
            lineas.append(", ".join(vacias))
            lineas.append("")

        if r.get("top_grandes"):
            lineas.append("### Archivos más grandes")
            for t in r["top_grandes"][:5]:
                lineas.append(f"- `{t['path']}` — {t['lineas']} líneas")
            lineas.append("")

        probs = inf.get("problemas") or []
        if probs:
            lineas.append(f"### Problemas ({len(probs)})")
            for p in probs[:12]:
                lineas.append(
                    f"- **[{p['severidad']}]** `{p['path']}` — {p['tipo']}: {p['detalle']}"
                )
            lineas.append("")

        lineas.append("### Mejoras sugeridas")
        for mej in inf.get("mejoras") or []:
            lineas.append(f"- {mej}")

        return "\n".join(lineas)
