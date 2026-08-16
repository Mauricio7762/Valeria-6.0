"""Generador de mejoras — recomendaciones accionables."""

from __future__ import annotations

from typing import Any


class GeneradorMejoras:
    def generar(
        self,
        resumen: dict[str, Any],
        patrones: dict[str, Any],
        problemas: list[dict[str, str]],
    ) -> list[str]:
        mejoras: list[str] = []

        if resumen.get("archivos", 0) == 0:
            return ["No se encontraron archivos Python para analizar."]

        if patrones.get("capas_vacias"):
            mejoras.append(
                "Completar capas aún vacías: " + ", ".join(patrones["capas_vacias"])
            )

        altas = [p for p in problemas if p["severidad"] == "alta"]
        medias = [p for p in problemas if p["severidad"] == "media"]
        if altas:
            mejoras.append(f"Corregir {len(altas)} error(es) de sintaxis antes de seguir.")
        if medias:
            mejoras.append(f"Revisar {len(medias)} aviso(s) de severidad media (archivos grandes / except).")

        grandes = resumen.get("top_grandes") or []
        if grandes and grandes[0]["lineas"] > 350:
            mejoras.append(
                f"Refactorizar `{grandes[0]['path']}` ({grandes[0]['lineas']} líneas) en módulos más chicos."
            )

        if "orquestador" in patrones.get("capas_cubiertas", []):
            mejoras.append("El orquestador está presente: buen punto central de integración.")

        if not mejoras:
            mejoras.append("El proyecto se ve coherente a nivel estructural. Seguí sumando tests.")

        return mejoras
