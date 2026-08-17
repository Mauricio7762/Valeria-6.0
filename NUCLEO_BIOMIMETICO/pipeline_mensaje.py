"""
Pipeline de mensaje de usuario
==============================
Percepción → memoria → plan meta → razonamiento → ajuste → curiosidad → formato.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from AGENTES_CORTICALES.razonamiento.grafo_conocimiento import normalizar
from AGENTES_CORTICALES.razonamiento.puente_memoria import sugerir_promocion

if TYPE_CHECKING:
    from NUCLEO_BIOMIMETICO.orquestador_principal import OrquestadorPrincipal


async def procesar_mensaje(orch: "OrquestadorPrincipal", texto: str) -> str:
    return await procesar_entrada(orch, texto, percepcion=None)


async def procesar_entrada(
    orch: "OrquestadorPrincipal",
    texto: str,
    percepcion: dict | None = None,
) -> str:
    if not orch.coordinador:
        return "Sistema de agentes no disponible."

    if percepcion:
        await orch.coordinador.enviar(
            "percepcion",
            {"percepcion_normalizada": percepcion, "tipo": percepcion.get("tipo", "texto")},
        )
        texto_razon = str(percepcion.get("texto_para_razonar") or texto)
    else:
        await orch.coordinador.enviar("percepcion", {"tipo": "texto", "contenido": texto})
        texto_razon = texto

    emo = await orch.coordinador.enviar("emocional", {"contenido": texto_razon})
    await orch.coordinador.enviar(
        "memoria",
        {
            "accion": "guardar_episodica",
            "contenido": texto_razon,
            "meta": {
                "origen": "usuario",
                "emocional": emo.get("estado_afectivo"),
                "modalidad": (percepcion or {}).get("tipo", "texto"),
            },
        },
    )
    texto = texto_razon

    # RAG: enriquecer con fragmentos de PDFs ingeridos
    try:
        rag = getattr(orch, "rag", None)
        if rag is not None and texto:
            ctx = rag.recuperar(texto, top_k=3)
            if ctx.get("contexto"):
                texto = ctx["contexto"] + "\n\n[Pregunta]\n" + texto
    except Exception:
        pass

    ctx = await orch.coordinador.enviar("memoria", {"accion": "recuperar", "clave": texto})

    raz_agente = orch._agente("razonamiento")
    plan_estrategias = None
    if raz_agente is not None:
        analisis = raz_agente.nlp.analizar(texto)
        entidad = analisis.entidad_principal
        ent_norm = normalizar(entidad) if entidad else None
        tiene_ent = bool(ent_norm and raz_agente.grafo.existe(ent_norm))
        tiene_causas = False
        if ent_norm:
            tiene_causas = bool(raz_agente.grafo.buscar(relacion="causa", objeto=ent_norm))
        plan = orch.meta_plan.planificar(
            intencion=analisis.intencion,
            entidad=entidad,
            grafo_tiene_entidad=tiene_ent,
            grafo_tiene_causas=tiene_causas,
            hay_episodios_relacionados=bool(ctx.get("encontrados")),
        )
        plan_estrategias = orch.meta_ajuste.reordenar_plan(plan.estrategias)
        plan.estrategias = plan_estrategias
        orch._ultimo_plan = plan

    razon = await orch.coordinador.enviar(
        "razonamiento",
        {"pregunta": texto, "plan_estrategias": plan_estrategias},
    )

    mem_agente = orch._agente("memoria")
    if mem_agente is not None and raz_agente is not None:
        episodios = getattr(mem_agente, "episodica", [])
        for hecho, n in sugerir_promocion(episodios, min_repeticiones=2):
            raz_agente.grafo.agregar_hecho(
                hecho.sujeto,
                hecho.relacion,
                hecho.objeto,
                confianza=min(0.85, 0.5 + 0.1 * n),
                origen="usuario",
            )
        if episodios:
            try:
                raz_agente.grafo.guardar(raz_agente._ruta_persistencia)
            except Exception:
                pass

    if any(p in texto.lower() for p in ("quiero", "necesito", "objetivo", "planificar")):
        await orch.coordinador.enviar(
            "planificacion", {"accion": "nuevo_objetivo", "objetivo": texto}
        )

    reg = orch.meta_monitor.registrar(texto, razon)
    orch.meta_ajuste.ajustar_desde_registro(reg)

    _ent = None
    _int = reg.intencion
    if raz_agente is not None:
        try:
            _ent = raz_agente.nlp.analizar(texto).entidad_principal
        except Exception:
            pass
    orch.curiosidad.observar_turno(_ent, _int, reg)

    evaluacion = orch.meta_eval.evaluar(reg, str(razon.get("conclusion") or ""))
    if (
        not reg.fue_aprendizaje
        and reg.confianza < orch.meta_ajuste.prefs.umbral_pedir_ensenanza
        and not evaluacion.get("nota_usuario")
    ):
        evaluacion = dict(evaluacion)
        evaluacion["nota_usuario"] = (
            "Si querés, enseñame el hecho con «X es un Y» o «X es parte de Y»."
        )
        evaluacion["calidad"] = evaluacion.get("calidad") or "insuficiente"

    respuesta = formatear_respuesta(orch, razon, emo, evaluacion, ctx)

    await orch.coordinador.enviar(
        "memoria",
        {
            "accion": "guardar_respuesta",
            "contenido": razon.get("conclusion") or respuesta[:200],
            "meta": {
                "estrategia": razon.get("estrategia"),
                "confianza": razon.get("confianza"),
            },
        },
    )
    return respuesta


def formatear_respuesta(
    orch: "OrquestadorPrincipal",
    razon: dict[str, Any],
    emo: dict[str, Any],
    evaluacion: dict[str, Any],
    ctx: dict[str, Any] | None = None,
) -> str:
    conclusion = (razon.get("conclusion") or "").strip()
    if not conclusion:
        conclusion = "No pude formar una conclusión clara."

    lineas = [conclusion]
    nota = (evaluacion.get("nota_usuario") or "").strip()
    if nota:
        lineas.append("")
        lineas.append(nota)

    bits = []
    if razon.get("estrategia"):
        bits.append(str(razon["estrategia"]))
    try:
        conf = float(razon.get("confianza") or 0)
        bits.append(f"confianza {conf:.0%}")
    except (TypeError, ValueError):
        pass
    calidad = evaluacion.get("calidad")
    if calidad and calidad not in ("buena", "aprendizaje"):
        bits.append(f"calidad {calidad}")
    estado = emo.get("estado_afectivo")
    if estado and estado != "neutral":
        bits.append(f"ánimo {estado}")
    if bits:
        lineas.append("")
        lineas.append("*" + " · ".join(bits) + "*")

    if orch._debug:
        pasos = razon.get("razonamiento") or []
        if pasos:
            lineas.append("")
            lineas.append("**Pasos internos**")
            for p in pasos:
                lineas.append(f"- {p}")
        if ctx and ctx.get("encontrados"):
            lineas.append("")
            lineas.append(
                f"**Memoria episódica:** {ctx['encontrados']} recuerdo(s) relacionados"
            )

    return "\n".join(lineas)
