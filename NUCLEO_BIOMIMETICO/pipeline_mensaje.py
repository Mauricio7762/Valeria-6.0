"""
Pipeline de mensaje de usuario
==============================
Percepción → memoria → plan meta → razonamiento → ajuste → curiosidad → formato.
Incluye /aprender (texto) y /aprender_pdf|/pdf.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, TYPE_CHECKING

from AGENTES_CORTICALES.razonamiento.grafo_conocimiento import normalizar
from AGENTES_CORTICALES.razonamiento.puente_memoria import sugerir_promocion
from AGENTES_CORTICALES.razonamiento.aprender_texto import aprender_texto
from AGENTES_CORTICALES.razonamiento.aprender_pdf import aprender_pdf
from AGENTES_CORTICALES.razonamiento.detector_intencion import detectar_saludo

if TYPE_CHECKING:
    from NUCLEO_BIOMIMETICO.orquestador_principal import OrquestadorPrincipal


def _resolver_mm(orch, texto: str) -> dict:
    mem = getattr(orch, "mem_mm", None)
    if mem is not None:
        hit = mem.buscar_por_nombre(texto)
        if hit is not None:
            return {
                "tipo": hit.tipo,
                "nombre": hit.nombre,
                "caption": hit.caption,
                "texto_para_razonar": hit.texto,
                "contenido": hit.caption or hit.texto,
            }
        if _parece_pregunta_sobre_entrada(texto):
            u = mem.ultima()
            if u is not None:
                return {
                    "tipo": u.tipo,
                    "nombre": u.nombre,
                    "caption": u.caption,
                    "texto_para_razonar": u.texto,
                    "contenido": u.caption or u.texto,
                }
    return dict(getattr(orch, "_ultimo_mm", None) or {})


def _parece_pregunta_sobre_documento(texto: str) -> bool:
    t = (texto or "").lower()
    claves = (
        "documento", "pdf", "archivo", "texto del", "según el", "segun el",
        "de qué trata", "de que trata", "qué dice", "que dice",
        "en el documento", "en el pdf", "resum",
    )
    return any(k in t for k in claves)


def _parece_pregunta_sobre_entrada(texto: str) -> bool:
    t = (texto or "").lower()
    claves = (
        "qué es", "que es", "qué hay", "que hay", "de qué", "de que",
        "describe", "describí", "describi", "imagen", "foto", "archivo",
        "qué se ve", "que se ve", "qué muestra", "que muestra",
        "caption", "contenido", "esa imagen", "esta imagen",
    )
    return any(k in t for k in claves)


def _texto_contexto_mm(mm: dict) -> str:
    tipo = mm.get("tipo") or "archivo"
    caption = (mm.get("caption") or mm.get("transcripcion") or "").strip()
    nombre = Path(str(mm.get("nombre") or "")).name
    partes = [f"[Entrada multimodal reciente: {tipo}]"]
    if nombre:
        partes.append(f"Nombre: {nombre}")
    if caption:
        partes.append(f"Descripción: {caption}")
    return "\n".join(partes)


def _respuesta_desde_mm(mm: dict, pregunta: str) -> str:
    caption = (mm.get("caption") or mm.get("transcripcion") or "").strip()
    nombre = Path(str(mm.get("nombre") or "archivo")).name
    fuente = mm.get("caption_fuente") or mm.get("provider") or ""
    if not caption:
        raw = (mm.get("texto_para_razonar") or mm.get("contenido") or "").strip()
        low = raw.lower()
        for pref in (
            "descripción del usuario:",
            "descripcion del usuario:",
            "descripción:",
            "descripcion:",
        ):
            if pref in low:
                caption = raw[low.find(pref) + len(pref) :].strip()
                for stop in ("[imagen", "tipo=", "tamaño=", "tamano="):
                    pos = caption.lower().find(stop)
                    if pos > 0:
                        caption = caption[:pos].strip()
                break
    if not caption:
        return (
            f"Recibí la imagen **{nombre}**, pero no tengo una descripción útil. "
            "Subila de nuevo con una descripción o configurá la API de visión."
        )
    base = f"Sobre la imagen **{nombre}**: {caption}"
    if fuente:
        base += f"\n\n*Fuente: {fuente}*"
    return base


def _respuesta_desde_rag(hits: list, pregunta: str) -> str:
    if not hits:
        return ""
    lineas = ["Según los documentos que cargaste:", ""]
    for h in hits[:3]:
        frag = (h.get("texto") or "").strip()
        if not frag:
            continue
        fuente = h.get("fuente") or "documento"
        lineas.append(f"**({fuente})**")
        lineas.append(frag[:700])
        lineas.append("")
    lineas.append(f"*Recuperado por RAG · {len(hits)} fragmento(s)*")
    return "\n".join(lineas).strip()


async def procesar_mensaje(orch: "OrquestadorPrincipal", texto: str) -> str:
    return await procesar_entrada(orch, texto, percepcion=None)


async def procesar_entrada(
    orch: "OrquestadorPrincipal",
    texto: str,
    percepcion: dict | None = None,
) -> str:
    if not orch.coordinador:
        return "Sistema de agentes no disponible."

    raw = (texto or "").strip()
    low = raw.lower()

    # --- Saludos / despedidas / cortesías → respuesta directa ---
    # Se abstiene si el texto parece enseñanza o pregunta real
    # (patrón "X es un/una/parte de Y"), así no interfiere con el
    # aprendizaje ni con el razonamiento.
    if percepcion is None:
        resp_saludo = detectar_saludo(raw)
        if resp_saludo is not None:
            await orch.coordinador.enviar("percepcion", {"tipo": "texto", "contenido": raw})
            await orch.coordinador.enviar(
                "memoria",
                {
                    "accion": "guardar_episodica",
                    "contenido": raw,
                    "meta": {"origen": "usuario", "modalidad": "texto", "tipo": "small_talk"},
                },
            )
            return resp_saludo

    # --- /aprender texto libre → grafo ---
    if low.startswith(("/aprender", "aprendé esto", "aprende esto")) and not low.startswith(
        ("/aprender_pdf", "/pdf")
    ):
        cuerpo = re.sub(
            r"^(/aprender|aprendé esto|aprende esto)\s*:?\s*",
            "",
            raw,
            flags=re.IGNORECASE,
        ).strip()
        raz = orch._agente("razonamiento")
        if raz is None or not hasattr(raz, "grafo"):
            return "Agente de razonamiento no disponible."
        hechos = aprender_texto(cuerpo, raz.grafo)
        try:
            raz.grafo.guardar(raz._ruta_persistencia)
        except Exception:
            pass
        if hechos:
            lineas = [
                f"- {h['sujeto']} — {h['relacion']} — {h['objeto']}" for h in hechos
            ]
            return f"Guardé {len(hechos)} hecho(s):\n" + "\n".join(lineas)
        return "No extraje hechos nuevos de ese texto."

    # --- /aprender_pdf | /pdf → grafo ---
    if low.startswith(("/aprender_pdf", "/pdf")):
        resto = re.sub(r"^(/aprender_pdf|/pdf)\s*", "", raw, flags=re.I).strip()
        if not resto:
            return "Uso: /aprender_pdf ruta/al/archivo.pdf"
        raz = orch._agente("razonamiento")
        if raz is None or not hasattr(raz, "grafo"):
            return "Agente de razonamiento no disponible."
        try:
            res = aprender_pdf(resto, raz.grafo)
        except FileNotFoundError as e:
            return str(e)
        except ImportError as e:
            return str(e)
        except Exception as e:
            return f"Error al leer PDF: {e}"
        try:
            raz.grafo.guardar(raz._ruta_persistencia)
        except Exception:
            pass
        hechos = res.get("hechos") or []
        msg = res.get("mensaje") or ""
        if hechos:
            lineas = [
                f"- {h['sujeto']} — {h['relacion']} — {h['objeto']}" for h in hechos
            ]
            return msg + "\n" + "\n".join(lineas)
        return msg + "\nNo extraje hechos nuevos."

    if percepcion:
        await orch.coordinador.enviar(
            "percepcion",
            {"percepcion_normalizada": percepcion, "tipo": percepcion.get("tipo", "texto")},
        )
        texto_razon = str(percepcion.get("texto_para_razonar") or texto)
        try:
            orch._ultimo_mm = dict(percepcion)
            _mem = getattr(orch, "mem_mm", None)
            if _mem is not None:
                _mem.registrar(percepcion)
        except Exception:
            pass
    else:
        await orch.coordinador.enviar("percepcion", {"tipo": "texto", "contenido": texto})
        texto_razon = texto
        mm = _resolver_mm(orch, texto)
        if mm and _parece_pregunta_sobre_entrada(texto):
            ctx_mm = _texto_contexto_mm(mm)
            if ctx_mm:
                texto_razon = ctx_mm + "\n\n[Pregunta del usuario]\n" + texto

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
    rag_hits: list = []
    tipo_perc = (percepcion or {}).get("tipo") if percepcion else None
    usar_rag = tipo_perc not in ("imagen", "audio")
    try:
        rag = getattr(orch, "rag", None)
        if usar_rag and rag is not None and texto_razon:
            rec = rag.recuperar(texto_razon, top_k=5)
            rag_hits = list(rec.get("hits") or [])
            if rec.get("contexto"):
                texto = rec["contexto"] + "\n\n[Pregunta]\n" + texto_razon
    except Exception:
        rag_hits = []

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
            "Si querés, enseñame con «X es un Y», «X es parte de Y», "
            "o /aprender texto / /aprender_pdf ruta.pdf"
        )
        evaluacion["calidad"] = evaluacion.get("calidad") or "insuficiente"

    respuesta = formatear_respuesta(orch, razon, emo, evaluacion, ctx)

    try:
        conf = float(razon.get("confianza") or 0)
    except (TypeError, ValueError):
        conf = 0.0
    sin_hechos = conf < 0.4 or "no tengo hechos" in (razon.get("conclusion") or "").lower()

    if rag_hits and (sin_hechos or _parece_pregunta_sobre_documento(texto)):
        alt = _respuesta_desde_rag(rag_hits, texto_razon)
        if alt:
            respuesta = alt
    else:
        mm = percepcion if percepcion else _resolver_mm(orch, texto)
        es_img = isinstance(mm, dict) and mm.get("tipo") in ("imagen", "audio")
        if es_img and (percepcion or _parece_pregunta_sobre_entrada(texto)):
            alt = _respuesta_desde_mm(mm, texto_razon)
            if alt:
                respuesta = alt

    if sin_hechos and not rag_hits:
        alt_llm = _respuesta_desde_lora(orch, texto_razon, razon, ctx, rag_hits)
        if alt_llm:
            respuesta = alt_llm
            razon = dict(razon)
            razon["estrategia"] = "lora"
            razon["confianza"] = max(conf, 0.35)

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


def _respuesta_desde_lora(
    orch: "OrquestadorPrincipal",
    pregunta: str,
    razon: dict[str, Any],
    ctx: dict[str, Any] | None,
    rag_hits: list,
) -> str | None:
    try:
        from NUCLEO_BIOMIMETICO.llm_lora import get_llm
    except ImportError:
        return None

    llm = getattr(orch, "llm", None) or get_llm()
    if not getattr(llm, "_enabled", True):
        return None

    partes: list[str] = []
    conc = (razon.get("conclusion") or "").strip()
    if conc and "no tengo hechos" not in conc.lower():
        partes.append(f"Conclusión simbólica previa: {conc}")
    if ctx and ctx.get("encontrados"):
        partes.append(f"Memoria episódica: {ctx['encontrados']} recuerdo(s) relacionados.")
    for h in (rag_hits or [])[:2]:
        frag = (h.get("texto") or "").strip()[:400]
        if frag:
            partes.append(f"Documento: {frag}")

    contexto = "\n".join(partes) if partes else None
    texto = llm.generar(pregunta, contexto=contexto, max_new_tokens=220)
    if not texto:
        return None
    return texto + "\n\n*generado por LoRA*"


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
