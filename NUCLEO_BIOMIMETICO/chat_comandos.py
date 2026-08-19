"""
Comandos del chat interactivo de VALERIA.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from NUCLEO_BIOMIMETICO.orquestador_principal import OrquestadorPrincipal

AYUDA = """
**Comandos**
- `/ayuda` — esta ayuda
- `/estado` — sistema, emoción, grafo, metacognición
- `/hechos` — hechos del grafo de conocimiento
- `/grafo` — resumen del grafo
- `/memoria` — episodios y contexto reciente
- `/debug` — pasos internos del razonamiento on/off
- `/plan` — último plan metacognitivo
- `/ajustes` — pesos de estrategias (nivel 4)
- `/reflexion` — autorreflexión (nivel 5)
- `/curiosidad` — qué exploraría VALERIA ahora
- `/neurogenesis` — crecimiento, plasticidad y poda del grafo
- `/holistico` — analiza el código del proyecto
- `/rag` — estado de documentos PDF ingeridos
- `/promover` — pasar fragmentos RAG a hechos del grafo
- `/salir` — apagar

**Uso**
- Preguntar: `¿qué es valeria?`
- Enseñar: `la microglía es parte del sistema glial`
"""


async def manejar_comando(orch: "OrquestadorPrincipal", texto: str) -> str | None:
    """Devuelve respuesta si es comando; None si es mensaje normal."""
    raw = texto.strip()
    low = raw.lower()

    if low in ("/salir", "/exit", "/quit", "salir"):
        orch.running = False
        return ""
    if low in ("/ayuda", "/help", "ayuda"):
        return AYUDA.strip()
    if low in ("/estado", "/status"):
        return await cmd_estado(orch)
    if low in ("/hechos", "/facts"):
        return await cmd_hechos(orch)
    if low in ("/grafo", "/graph"):
        return await cmd_grafo(orch)
    if low in ("/memoria", "/memory"):
        return await cmd_memoria(orch)
    if low in ("/plan",):
        return cmd_plan(orch)
    if low in ("/ajustes", "/ajuste"):
        return cmd_ajustes(orch)
    if low in ("/reflexion", "/reflexión", "/autorreflexion"):
        return cmd_reflexion(orch)
    if low in ("/curiosidad", "/curious", "/explorar"):
        return cmd_curiosidad(orch)
    if low in ("/neurogenesis", "/neuro", "/plasticidad"):
        return cmd_neurogenesis(orch)
    if low in ("/holistico", "/holístico", "/analyze", "/codigo"):
        return cmd_holistico(orch)
    if low in ("/rag", "/docs", "/documentos"):
        return cmd_rag(orch)
    if low in ("/mm", "/imagenes", "/multimodal"):
        return cmd_mm(orch)
    if low in ("/promover", "/promocion", "/aprender_docs"):
        return cmd_promover(orch)
    if low == "/debug":
        orch._debug = not orch._debug
        return f"Debug **{'on' if orch._debug else 'off'}**."
    if low.startswith("/aprender ") or low.startswith("/learn "):
        from NUCLEO_BIOMIMETICO.pipeline_mensaje import procesar_mensaje

        return await procesar_mensaje(orch, raw.split(" ", 1)[1].strip())
    return None


async def cmd_estado(orch: "OrquestadorPrincipal") -> str:
    lineas = [
        f"**Consciencia:** {orch.estado_consciencia}",
        f"**Ciclos background:** {orch._ciclo_count}",
        f"**Debug:** {'on' if orch._debug else 'off'}",
    ]
    if orch.gestor_recursos:
        r = orch.gestor_recursos.obtener_estado()
        lineas.append(f"**CPU / RAM:** {r['cpu_percent']:.0f}% / {r['ram_percent']:.0f}%")
    if orch.coordinador:
        est = orch.coordinador.estado()
        mem = est.get("memoria", {})
        raz = est.get("razonamiento", {})
        lineas.append(
            f"**Memoria:** trabajo={mem.get('trabajo', 0)} · "
            f"episódica={mem.get('episodica', 0)}"
        )
        grafo = raz.get("grafo") or {}
        if grafo:
            lineas.append(f"**Grafo:** {grafo.get('total_hechos', 0)} hechos")
    meta = orch.meta_monitor.estado()
    if meta.get("registros"):
        lineas.append(
            f"**Metacognición:** {meta['registros']} registros · "
            f"conf. media {meta.get('confianza_media')} · "
            f"aprendizajes {meta.get('aprendizajes', 0)}"
        )
    if orch._ultimo_plan:
        lineas.append(f"**Último plan:** {' → '.join(orch._ultimo_plan.estrategias)}")
    aj = orch.meta_ajuste.estado()
    if aj.get("total_ajustes"):
        top = max(aj["pesos"], key=lambda k: aj["pesos"][k])
        lineas.append(
            f"**Ajuste:** {aj['total_ajustes']} updates · prefiere *{top}* "
            f"({aj['pesos'][top]:.2f})"
        )
    cur = orch.curiosidad.estado()
    lineas.append(
        f"**Curiosidad:** recompensa {cur['recompensa']['total']} · "
        f"entidades nuevas {cur['perceptual']['entidades_distintas']}"
    )
    ng = orch.neurogenesis.estado()
    lineas.append(
        f"**Neurogénesis:** +{ng['crecimiento']['nuevas_conexiones']} conexiones · "
        f"{ng['plasticidad']['refuerzos']} refuerzos · {ng['poda']['podados']} podas"
    )
    return "\n".join(lineas)


async def cmd_hechos(orch: "OrquestadorPrincipal", limite: int = 25) -> str:
    agente = orch._agente("razonamiento")
    if not agente or not hasattr(agente, "grafo"):
        return "Razonamiento no disponible."
    hechos = list(getattr(agente.grafo, "_hechos", []))
    if not hechos:
        return "Grafo vacío."
    aprendidos = [h for h in hechos if getattr(h, "origen", "") == "usuario"]
    base = [h for h in hechos if getattr(h, "origen", "") != "usuario"]
    muestra = (aprendidos[-10:] + base[: max(0, limite - len(aprendidos))])[:limite]
    lineas = [f"**Hechos** ({len(hechos)} total, mostrando {len(muestra)})", ""]
    for h in muestra:
        lineas.append(
            f"- `{h.sujeto}` —*{h.relacion}*→ `{h.objeto}` [{getattr(h, 'origen', '?')}]"
        )
    return "\n".join(lineas)


async def cmd_grafo(orch: "OrquestadorPrincipal") -> str:
    agente = orch._agente("razonamiento")
    if not agente:
        return "Razonamiento no disponible."
    est = agente.estado().get("grafo") or {}
    return (
        f"**Grafo**\n"
        f"- Hechos: **{est.get('total_hechos', 0)}**\n"
        f"- Sujetos: **{est.get('sujetos_distintos', 0)}**\n"
        f"- Relaciones: **{est.get('relaciones_distintas', 0)}**"
    )


async def cmd_memoria(orch: "OrquestadorPrincipal") -> str:
    mem = orch._agente("memoria")
    if not mem:
        return "Memoria no disponible."
    ctx = await mem.procesar({"accion": "contexto_reciente", "n": 5})
    lineas = [
        f"**Trabajo:** {len(ctx.get('trabajo') or [])} turnos recientes",
        f"**Episódica total:** {mem.estado().get('episodica', 0)}",
        "",
    ]
    for ep in (ctx.get("episodios_recientes") or [])[-5:]:
        c = str(ep.get("contenido", ""))[:80]
        lineas.append(f"- {c}")
    return "\n".join(lineas)


def cmd_promover(orch: "OrquestadorPrincipal") -> str:
    rag = getattr(orch, "rag", None)
    raz = orch._agente("razonamiento")
    if rag is None or raz is None or not hasattr(raz, "grafo"):
        return "RAG o razonamiento no disponible."
    if rag.almacen.total() == 0:
        return "No hay fragmentos RAG. Subí un PDF primero."
    pr = rag.promover_a_grafo(raz.grafo)
    try:
        raz.grafo.guardar(raz._ruta_persistencia)
    except Exception:
        pass
    lineas = [
        "**Promoción RAG → grafo**",
        f"- Intentos de extracción: **{pr.get('intentos', 0)}**",
        f"- Hechos agregados: **{pr.get('agregados', 0)}**",
    ]
    for ej in pr.get("ejemplos") or []:
        lineas.append(f"- `{ej}`")
    if not pr.get("agregados"):
        lineas.append(
            "\nNo se extrajeron afirmaciones claras. "
            "Los PDFs narrativos a veces no traen frases tipo «X es un Y»."
        )
    return "\n".join(lineas)


def cmd_mm(orch: "OrquestadorPrincipal") -> str:
    mem = getattr(orch, "mem_mm", None)
    if mem is None:
        return "Memoria multimodal no disponible."
    return mem.listar()


def cmd_rag(orch: "OrquestadorPrincipal") -> str:
    rag = getattr(orch, "rag", None)
    if rag is None:
        return "RAG no inicializado."
    n = rag.almacen.total()
    fuentes = sorted({c.get("fuente", "?") for c in rag.almacen.chunks})
    lineas = [
        "**RAG (documentos)**",
        f"- Chunks: **{n}**",
        f"- Fuentes: {', '.join(fuentes) if fuentes else '—'}",
        "",
        "Subí un PDF desde Streamlit (Multimodal) para ingerirlo.",
    ]
    return "\n".join(lineas)


def cmd_holistico(orch: "OrquestadorPrincipal") -> str:
    informe = orch.holistico.analizar()
    return orch.holistico.informe_markdown(informe)


def cmd_neurogenesis(orch: "OrquestadorPrincipal") -> str:
    raz = orch._agente("razonamiento")
    extra = ""
    if raz is not None and hasattr(raz, "grafo"):
        topo = orch.neurogenesis.topologia.analizar(raz.grafo)
        home = orch.neurogenesis.homeostasis.evaluar(topo.get("hechos", 0))
        extra = (
            f"\n**Topología**\n"
            f"- Hechos: {topo.get('hechos')} · Nodos: {topo.get('nodos')}\n"
            f"- Densidad relativa: {topo.get('densidad_relativa')}\n"
            f"- Homeostasis: **{home.get('estado')}**\n"
        )
        if topo.get("relaciones_top"):
            extra += "- Relaciones: " + ", ".join(
                f"{r}({n})" for r, n in topo["relaciones_top"][:4]
            )
    est = orch.neurogenesis.estado()
    lineas = [
        "**Neurogénesis artificial**",
        "",
        f"Ciclos mantenimiento: **{est['ciclos']}**",
        f"Nuevas conexiones: **{est['crecimiento']['nuevas_conexiones']}**",
        f"Refuerzos plásticos: **{est['plasticidad']['refuerzos']}**",
        f"Podas: **{est['poda']['podados']}**",
        extra,
    ]
    if est["crecimiento"].get("ultimas"):
        lineas.append("\n**Último crecimiento**")
        for u in est["crecimiento"]["ultimas"][-3:]:
            lineas.append(f"- {u}")
    return "\n".join(lineas)


def cmd_curiosidad(orch: "OrquestadorPrincipal") -> str:
    lagunas = [
        r.texto_usuario
        for r in orch.meta_monitor.historial
        if (r.necesita_mas_datos or r.confianza < 0.35) and not r.fue_aprendizaje
    ]
    sujetos: list[str] = []
    raz = orch._agente("razonamiento")
    if raz is not None and hasattr(raz, "grafo"):
        sujetos = list(getattr(raz.grafo, "_por_sujeto", {}).keys())[:20]
    sugerencias = orch.curiosidad.generar(lagunas, sujetos, max_total=5)
    if not sugerencias:
        return "Ahora mismo no tengo impulsos de curiosidad. Seguí hablando y vuelvo a indagar."
    lineas = ["**Curiosidad computacional**", "", "Si pudiera preguntar yo, preguntaría:", ""]
    for i, s in enumerate(sugerencias, 1):
        lineas.append(f"{i}. *({s['tipo']})* {s['pregunta']}")
    rew = orch.curiosidad.recompensa.estado()
    lineas.append("")
    lineas.append(f"Recompensa intrínseca de sesión: **{rew['total']}**")
    return "\n".join(lineas)


def cmd_ajustes(orch: "OrquestadorPrincipal") -> str:
    est = orch.meta_ajuste.estado()
    lineas = ["**Ajustes metacognitivos (nivel 4)**", "", "**Pesos de estrategias**"]
    for k, v in sorted(est["pesos"].items(), key=lambda x: -x[1]):
        bar = "█" * int(v * 4) + "░" * max(0, 10 - int(v * 4))
        lineas.append(f"- `{k}`: {v:.2f}  {bar}")
    lineas.append(f"\nUmbral pedir enseñanza: **{est['umbral_pedir_ensenanza']:.2f}**")
    lineas.append(f"Total ajustes: **{est['total_ajustes']}**")
    if est.get("ultimos_ajustes"):
        lineas.append("\n**Últimos ajustes**")
        for a in est["ultimos_ajustes"]:
            sign = "+" if a["delta"] >= 0 else ""
            lineas.append(f"- {a['estrategia']}: {sign}{a['delta']} ({a['motivo']})")
    return "\n".join(lineas)


def cmd_reflexion(orch: "OrquestadorPrincipal") -> str:
    grafo_est = None
    mem_est = None
    raz = orch._agente("razonamiento")
    mem = orch._agente("memoria")
    if raz:
        grafo_est = raz.estado().get("grafo")
    if mem:
        mem_est = mem.estado()
    out = orch.meta_reflexion.reflexionar(
        orch.meta_monitor, orch.meta_ajuste, grafo_est, mem_est
    )
    return out["texto"]


def cmd_plan(orch: "OrquestadorPrincipal") -> str:
    if not orch._ultimo_plan:
        return "Aún no hay plan (escribí una pregunta primero)."
    p = orch._ultimo_plan
    return (
        f"**Plan metacognitivo (nivel 3)**\n"
        f"- Intención: **{p.intencion}**\n"
        f"- Entidad: **{p.entidad or '—'}**\n"
        f"- Estrategias: **{' → '.join(p.estrategias)}**\n"
        f"- Motivo: {p.motivo}"
    )
