"""
Metacognición nivel 5 — Autorreflexión
======================================
Resume qué ha aprendido el sistema sobre su propio funcionamiento:
fortalezas, debilidades, lagunas de conocimiento, hábitos de estrategia.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from .nivel1_monitoreo import MonitorMetacognitivo, RegistroMeta
from .nivel4_ajuste import AjustadorMetacognitivo


class AutorreflexionMetacognitiva:
    def reflexionar(
        self,
        monitor: MonitorMetacognitivo,
        ajustador: AjustadorMetacognitivo,
        grafo_estado: dict[str, Any] | None = None,
        memoria_estado: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        hist = monitor.historial
        if not hist:
            return {
                "texto": (
                    "Todavía no tengo suficiente experiencia en esta sesión "
                    "para reflexionar. Hablame un rato y después pedime /reflexion."
                ),
                "metricas": {},
            }

        n = len(hist)
        confs = [r.confianza for r in hist]
        conf_media = sum(confs) / n
        por_est = Counter(r.estrategia for r in hist)
        aprendizajes = sum(1 for r in hist if r.fue_aprendizaje)
        fallos = sum(1 for r in hist if r.necesita_mas_datos or r.confianza < 0.35)
        intenciones = Counter(r.intencion for r in hist)

        # Fortaleza = estrategia con mejor confianza media (mín. 2 usos)
        conf_por_est: dict[str, list[float]] = {}
        for r in hist:
            conf_por_est.setdefault(r.estrategia, []).append(r.confianza)
        mejores = []
        for est, vals in conf_por_est.items():
            if len(vals) >= 1:
                mejores.append((est, sum(vals) / len(vals), len(vals)))
        mejores.sort(key=lambda x: x[1], reverse=True)

        pesos = ajustador.prefs.pesos
        estrategia_preferida = max(pesos, key=lambda k: pesos[k]) if pesos else "—"

        lineas = [
            "## Autorreflexión",
            "",
            f"En esta sesión procesé **{n}** interacciones "
            f"(**{aprendizajes}** aprendizajes, **{fallos}** con baja certeza).",
            f"Confianza media: **{conf_media:.0%}**.",
            "",
        ]

        if mejores:
            top = mejores[0]
            lineas.append(
                f"**Fortaleza:** la estrategia *{top[0]}* me funciona mejor "
                f"(conf. media {top[1]:.0%} en {top[2]} usos)."
            )
        if len(mejores) > 1 and mejores[-1][1] < 0.45:
            weak = mejores[-1]
            lineas.append(
                f"**Debilidad:** *{weak[0]}* rinde poco "
                f"(conf. media {weak[1]:.0%})."
            )

        lineas.append(
            f"**Preferencia ajustada:** el nivel 4 favorece *{estrategia_preferida}* "
            f"(peso {pesos.get(estrategia_preferida, 0):.2f})."
        )

        if intenciones:
            top_i = intenciones.most_common(1)[0]
            lineas.append(
                f"**Patrón de uso:** la intención más frecuente fue *{top_i[0]}* "
                f"({top_i[1]} veces)."
            )

        if grafo_estado:
            lineas.append(
                f"**Conocimiento:** {grafo_estado.get('total_hechos', 0)} hechos en el grafo, "
                f"{grafo_estado.get('sujetos_distintos', 0)} sujetos."
            )
        if memoria_estado:
            lineas.append(
                f"**Memoria episódica:** {memoria_estado.get('episodica', 0)} episodios."
            )

        # Lagunas: preguntas recientes con baja confianza
        lagunas = [
            r.texto_usuario[:60]
            for r in hist
            if (r.necesita_mas_datos or r.confianza < 0.35) and not r.fue_aprendizaje
        ][-5:]
        if lagunas:
            lineas.append("")
            lineas.append("**Lagunas recientes** (no supe responder bien):")
            for L in lagunas:
                lineas.append(f"- {L}")

        lineas.append("")
        lineas.append(
            "*Qué he aprendido sobre mí:* ajusto el orden de estrategias según "
            "lo que funciona, pido enseñanza cuando el grafo no alcanza, y "
            "guardo lo que me enseñás para la próxima vez."
        )

        return {
            "texto": "\n".join(lineas),
            "metricas": {
                "interacciones": n,
                "confianza_media": round(conf_media, 3),
                "aprendizajes": aprendizajes,
                "fallos": fallos,
                "estrategias": dict(por_est),
                "pesos": {k: round(v, 3) for k, v in pesos.items()},
            },
        }
