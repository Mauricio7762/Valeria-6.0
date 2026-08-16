"""
Orquestador Principal (Formación Reticular)
==========================================
Capa 2+3 inicio: chat + memoria rica + NLG + metacognición básica.
"""

from __future__ import annotations

import asyncio
import signal
import sys
from pathlib import Path
from typing import Any

import yaml
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from NUCLEO_BIOMIMETICO.gestor_recursos import GestorRecursos
from NUCLEO_BIOMIMETICO.SISTEMA_GLIAL.sistema_glial import SistemaGlial
from AGENTES_CORTICALES.coordinador_agentes import CoordinadorAgentes
from SISTEMAS_AVANZADOS.METACOGNICION import (
    MonitorMetacognitivo,
    EvaluadorMetacognitivo,
    PlanificadorMetacognitivo,
    AjustadorMetacognitivo,
    AutorreflexionMetacognitiva,
)
from AGENTES_CORTICALES.razonamiento.puente_memoria import sugerir_promocion
from SISTEMAS_AVANZADOS.CURIOSIDAD_COMPUTACIONAL import ExploradorAutonomo
from SISTEMAS_AVANZADOS.NEUROGENESIS_ARTIFICIAL import CoordinadorNeurogenesis
from SISTEMAS_AVANZADOS.ANALIZADOR_HOLISTICO_CODIGO import OrquestadorHolistico

console = Console()

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
- `/salir` — apagar

**Uso**
- Preguntar: `¿qué es valeria?`
- Enseñar: `la microglía es parte del sistema glial`
"""


class OrquestadorPrincipal:
    def __init__(self) -> None:
        self.running = False
        self.estado_consciencia = "apagado"
        self.config: dict[str, Any] = {}
        self.gestor_recursos: GestorRecursos | None = None
        self.sistema_glial: SistemaGlial | None = None
        self.coordinador: CoordinadorAgentes | None = None
        self.meta_monitor = MonitorMetacognitivo()
        self.meta_eval = EvaluadorMetacognitivo()
        self.meta_plan = PlanificadorMetacognitivo()
        self.meta_ajuste = AjustadorMetacognitivo()
        self.meta_reflexion = AutorreflexionMetacognitiva()
        self.curiosidad = ExploradorAutonomo()
        self.neurogenesis = CoordinadorNeurogenesis()
        self.holistico = OrquestadorHolistico(ROOT)
        self._ciclo_count = 0
        self._debug = False
        self._ultimo_plan = None
        self._setup_logging()
        self._setup_signals()

    def _setup_logging(self) -> None:
        logger.remove()
        log_dir = ROOT / "LOGS"
        log_dir.mkdir(exist_ok=True)
        logger.add(
            log_dir / "valeria_system.log",
            rotation="10 MB",
            retention="30 days",
            level="DEBUG",
            encoding="utf-8",
        )
        logger.add(sys.stderr, level="ERROR")

    def _setup_signals(self) -> None:
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, self._signal_handler)
            except (ValueError, OSError):
                pass

    def _signal_handler(self, signum: int, frame: Any) -> None:
        self.running = False

    def _cargar_config(self) -> dict[str, Any]:
        config: dict[str, Any] = {}
        for name in ("valeria_config.yaml", "sistema_glial_config.yaml"):
            path = ROOT / "CONFIGURACION" / name
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                if "glial" in name:
                    config["sistema_glial"] = data
                else:
                    config.update(data)
        return config

    def _agente(self, nombre: str):
        if not self.coordinador:
            return None
        return self.coordinador.agentes.get(nombre)

    async def inicializar(self) -> None:
        console.print(
            Panel.fit(
                "[bold cyan]VALERIA 6.0[/bold cyan]\n"
                "[dim]Chat · Meta · Curiosidad · Neurogénesis[/dim]\n"
                "[green]/ayuda para comandos[/green]",
                border_style="cyan",
                padding=(1, 4),
            )
        )
        self.config = self._cargar_config()
        self.gestor_recursos = GestorRecursos(self.config.get("resources", {}))
        self.sistema_glial = SistemaGlial(self.config.get("sistema_glial", {}))
        self.coordinador = CoordinadorAgentes(self.config.get("agentes", {}))
        raz0 = self.coordinador.agentes.get("razonamiento")
        if raz0 is not None:
            raz0.neurogenesis = self.neurogenesis
        self.estado_consciencia = "despierto"
        self.running = True

        n_hechos = 0
        n_ep = 0
        raz = self._agente("razonamiento")
        mem = self._agente("memoria")
        if raz:
            n_hechos = raz.estado().get("grafo", {}).get("total_hechos", 0)
        if mem:
            n_ep = mem.estado().get("episodica", 0)

        console.print(
            f"[bold green]✓[/bold green] Despierta · "
            f"[dim]{n_hechos} hechos · {n_ep} episodios · /ayuda[/dim]\n"
        )

    async def _mantenimiento_background(self) -> None:
        intervalo = self.config.get("homeostasis", {}).get("check_interval_seconds", 8)
        while self.running:
            self._ciclo_count += 1
            if self.sistema_glial:
                await self.sistema_glial.tick()
            if self.coordinador:
                await self.coordinador.tick()
                # Neurogénesis: plasticidad / poda periódica
                if self._ciclo_count % 5 == 0:
                    raz = self.coordinador.agentes.get("razonamiento")
                    mic = None
                    if self.sistema_glial:
                        mic = getattr(self.sistema_glial, "microglia", None)
                    if raz is not None and hasattr(raz, "grafo"):
                        self.neurogenesis.ciclo_mantenimiento(raz.grafo, microglia=mic)
            await asyncio.sleep(intervalo)

    async def _procesar_mensaje_usuario(self, texto: str) -> str:
        if not self.coordinador:
            return "Sistema de agentes no disponible."

        # Percepción + emoción + memoria episódica
        await self.coordinador.enviar("percepcion", {"tipo": "texto", "contenido": texto})
        emo = await self.coordinador.enviar("emocional", {"contenido": texto})
        await self.coordinador.enviar(
            "memoria",
            {
                "accion": "guardar_episodica",
                "contenido": texto,
                "meta": {"origen": "usuario", "emocional": emo.get("estado_afectivo")},
            },
        )

        # Recuperar contexto episódico relevante
        ctx = await self.coordinador.enviar(
            "memoria", {"accion": "recuperar", "clave": texto}
        )

        # Plan metacognitivo (nivel 3) según NLP + estado del grafo
        raz_agente = self._agente("razonamiento")
        plan_estrategias = None
        if raz_agente is not None:
            analisis = raz_agente.nlp.analizar(texto)
            entidad = analisis.entidad_principal
            from AGENTES_CORTICALES.razonamiento.grafo_conocimiento import normalizar
            ent_norm = normalizar(entidad) if entidad else None
            tiene_ent = bool(ent_norm and raz_agente.grafo.existe(ent_norm))
            tiene_causas = False
            if ent_norm:
                tiene_causas = bool(raz_agente.grafo.buscar(relacion="causa", objeto=ent_norm))
            plan = self.meta_plan.planificar(
                intencion=analisis.intencion,
                entidad=entidad,
                grafo_tiene_entidad=tiene_ent,
                grafo_tiene_causas=tiene_causas,
                hay_episodios_relacionados=bool(ctx.get("encontrados")),
            )
            plan_estrategias = self.meta_ajuste.reordenar_plan(plan.estrategias)
            plan.estrategias = plan_estrategias  # reflejar orden ajustado
            self._ultimo_plan = plan

        razon = await self.coordinador.enviar(
            "razonamiento",
            {"pregunta": texto, "plan_estrategias": plan_estrategias},
        )

        # Promover hechos repetidos en episódica → grafo (aprendizaje silencioso)
        mem_agente = self._agente("memoria")
        if mem_agente is not None and raz_agente is not None:
            episodios = getattr(mem_agente, "episodica", [])
            for hecho, n in sugerir_promocion(episodios, min_repeticiones=2):
                raz_agente.grafo.agregar_hecho(
                    hecho.sujeto, hecho.relacion, hecho.objeto,
                    confianza=min(0.85, 0.5 + 0.1 * n),
                    origen="usuario",
                )
            if episodios:
                try:
                    raz_agente.grafo.guardar(raz_agente._ruta_persistencia)
                except Exception:
                    pass

        if any(p in texto.lower() for p in ("quiero", "necesito", "objetivo", "planificar")):
            await self.coordinador.enviar(
                "planificacion", {"accion": "nuevo_objetivo", "objetivo": texto}
            )

        # Metacognición
        reg = self.meta_monitor.registrar(texto, razon)
        self.meta_ajuste.ajustar_desde_registro(reg)
        # Curiosidad: observar entidad/intención del turno
        _ent = None
        _int = reg.intencion
        raz_ag = self._agente("razonamiento")
        if raz_ag is not None:
            try:
                _ent = raz_ag.nlp.analizar(texto).entidad_principal
            except Exception:
                pass
        self.curiosidad.observar_turno(_ent, _int, reg)
        evaluacion = self.meta_eval.evaluar(reg, str(razon.get("conclusion") or ""))
        # Umbral dinámico de pedir enseñanza (nivel 4)
        if (
            not reg.fue_aprendizaje
            and reg.confianza < self.meta_ajuste.prefs.umbral_pedir_ensenanza
            and not evaluacion.get("nota_usuario")
        ):
            evaluacion = dict(evaluacion)
            evaluacion["nota_usuario"] = (
                "Si querés, enseñame el hecho con «X es un Y» o «X es parte de Y»."
            )
            evaluacion["calidad"] = evaluacion.get("calidad") or "insuficiente"


        respuesta = self._formatear_respuesta(razon, emo, evaluacion, ctx)

        # Guardar respuesta en memoria de trabajo
        await self.coordinador.enviar(
            "memoria",
            {
                "accion": "guardar_respuesta",
                "contenido": razon.get("conclusion") or respuesta[:200],
                "meta": {"estrategia": razon.get("estrategia"), "confianza": razon.get("confianza")},
            },
        )
        return respuesta

    def _formatear_respuesta(
        self,
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

        # Meta discreta
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

        if self._debug:
            pasos = razon.get("razonamiento") or []
            if pasos:
                lineas.append("")
                lineas.append("**Pasos internos**")
                for p in pasos:
                    lineas.append(f"- {p}")
            if ctx and ctx.get("encontrados"):
                lineas.append("")
                lineas.append(f"**Memoria episódica:** {ctx['encontrados']} recuerdo(s) relacionados")

        return "\n".join(lineas)

    async def _cmd_estado(self) -> str:
        lineas = [
            f"**Consciencia:** {self.estado_consciencia}",
            f"**Ciclos background:** {self._ciclo_count}",
            f"**Debug:** {'on' if self._debug else 'off'}",
        ]
        if self.gestor_recursos:
            r = self.gestor_recursos.obtener_estado()
            lineas.append(f"**CPU / RAM:** {r['cpu_percent']:.0f}% / {r['ram_percent']:.0f}%")
        if self.coordinador:
            est = self.coordinador.estado()
            mem = est.get("memoria", {})
            raz = est.get("razonamiento", {})
            lineas.append(
                f"**Memoria:** trabajo={mem.get('trabajo', 0)} · "
                f"episódica={mem.get('episodica', 0)}"
            )
            grafo = raz.get("grafo") or {}
            if grafo:
                lineas.append(f"**Grafo:** {grafo.get('total_hechos', 0)} hechos")
        meta = self.meta_monitor.estado()
        if meta.get("registros"):
            lineas.append(
                f"**Metacognición:** {meta['registros']} registros · "
                f"conf. media {meta.get('confianza_media')} · "
                f"aprendizajes {meta.get('aprendizajes', 0)}"
            )
        if self._ultimo_plan:
            lineas.append(
                f"**Último plan:** {' → '.join(self._ultimo_plan.estrategias)}"
            )
        aj = self.meta_ajuste.estado()
        if aj.get("total_ajustes"):
            top = max(aj["pesos"], key=lambda k: aj["pesos"][k])
            lineas.append(
                f"**Ajuste:** {aj['total_ajustes']} updates · prefiere *{top}* "
                f"({aj['pesos'][top]:.2f})"
            )
        cur = self.curiosidad.estado()
        lineas.append(
            f"**Curiosidad:** recompensa {cur['recompensa']['total']} · "
            f"entidades nuevas {cur['perceptual']['entidades_distintas']}"
        )
        ng = self.neurogenesis.estado()
        lineas.append(
            f"**Neurogénesis:** +{ng['crecimiento']['nuevas_conexiones']} conexiones · "
            f"{ng['plasticidad']['refuerzos']} refuerzos · {ng['poda']['podados']} podas"
        )
        return "\n".join(lineas)

    async def _cmd_hechos(self, limite: int = 25) -> str:
        agente = self._agente("razonamiento")
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

    async def _cmd_grafo(self) -> str:
        agente = self._agente("razonamiento")
        if not agente:
            return "Razonamiento no disponible."
        est = agente.estado().get("grafo") or {}
        return (
            f"**Grafo**\n"
            f"- Hechos: **{est.get('total_hechos', 0)}**\n"
            f"- Sujetos: **{est.get('sujetos_distintos', 0)}**\n"
            f"- Relaciones: **{est.get('relaciones_distintas', 0)}**"
        )

    async def _cmd_memoria(self) -> str:
        mem = self._agente("memoria")
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

    def _cmd_holistico(self) -> str:
        informe = self.holistico.analizar()
        return self.holistico.informe_markdown(informe)

    def _cmd_neurogenesis(self) -> str:

        raz = self._agente("razonamiento")
        extra = ""
        if raz is not None and hasattr(raz, "grafo"):
            topo = self.neurogenesis.topologia.analizar(raz.grafo)
            home = self.neurogenesis.homeostasis.evaluar(topo.get("hechos", 0))
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
        est = self.neurogenesis.estado()
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

    def _cmd_curiosidad(self) -> str:

        lagunas = [
            r.texto_usuario
            for r in self.meta_monitor.historial
            if (r.necesita_mas_datos or r.confianza < 0.35) and not r.fue_aprendizaje
        ]
        sujetos: list[str] = []
        raz = self._agente("razonamiento")
        if raz is not None and hasattr(raz, "grafo"):
            sujetos = list(getattr(raz.grafo, "_por_sujeto", {}).keys())[:20]
        sugerencias = self.curiosidad.generar(lagunas, sujetos, max_total=5)
        if not sugerencias:
            return "Ahora mismo no tengo impulsos de curiosidad. Seguí hablando y vuelvo a indagar."
        lineas = ["**Curiosidad computacional**", "", "Si pudiera preguntar yo, preguntaría:", ""]
        for i, s in enumerate(sugerencias, 1):
            lineas.append(f"{i}. *({s['tipo']})* {s['pregunta']}")
        rew = self.curiosidad.recompensa.estado()
        lineas.append("")
        lineas.append(f"Recompensa intrínseca de sesión: **{rew['total']}**")
        return "\n".join(lineas)

    def _cmd_ajustes(self) -> str:

        est = self.meta_ajuste.estado()
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
                lineas.append(
                    f"- {a['estrategia']}: {sign}{a['delta']} ({a['motivo']})"
                )
        return "\n".join(lineas)

    def _cmd_reflexion(self) -> str:
        grafo_est = None
        mem_est = None
        raz = self._agente("razonamiento")
        mem = self._agente("memoria")
        if raz:
            grafo_est = raz.estado().get("grafo")
        if mem:
            mem_est = mem.estado()
        out = self.meta_reflexion.reflexionar(
            self.meta_monitor, self.meta_ajuste, grafo_est, mem_est
        )
        return out["texto"]

    def _cmd_plan(self) -> str:

        if not self._ultimo_plan:
            return "Aún no hay plan (escribí una pregunta primero)."
        p = self._ultimo_plan
        return (
            f"**Plan metacognitivo (nivel 3)**\n"
            f"- Intención: **{p.intencion}**\n"
            f"- Entidad: **{p.entidad or '—'}**\n"
            f"- Estrategias: **{' → '.join(p.estrategias)}**\n"
            f"- Motivo: {p.motivo}"
        )

    async def _manejar_comando(self, texto: str) -> str | None:
        raw = texto.strip()
        low = raw.lower()

        if low in ("/salir", "/exit", "/quit", "salir"):
            console.print("[yellow]Apagando...[/yellow]")
            self.running = False
            return ""
        if low in ("/ayuda", "/help", "ayuda"):
            return AYUDA.strip()
        if low in ("/estado", "/status"):
            return await self._cmd_estado()
        if low in ("/hechos", "/facts"):
            return await self._cmd_hechos()
        if low in ("/grafo", "/graph"):
            return await self._cmd_grafo()
        if low in ("/memoria", "/memory"):
            return await self._cmd_memoria()
        if low in ("/plan",):
            return self._cmd_plan()
        if low in ("/ajustes", "/ajuste"):
            return self._cmd_ajustes()
        if low in ("/reflexion", "/reflexión", "/autorreflexion"):
            return self._cmd_reflexion()
        if low in ("/curiosidad", "/curious", "/explorar"):
            return self._cmd_curiosidad()
        if low in ("/neurogenesis", "/neuro", "/plasticidad"):
            return self._cmd_neurogenesis()
        if low in ("/holistico", "/holístico", "/analyze", "/codigo"):
            return self._cmd_holistico()
        if low == "/debug":
            self._debug = not self._debug
            return f"Debug **{'on' if self._debug else 'off'}**."
        if low.startswith("/aprender ") or low.startswith("/learn "):
            return await self._procesar_mensaje_usuario(raw.split(" ", 1)[1].strip())
        return None

    async def bucle_chat(self) -> None:
        bg = asyncio.create_task(self._mantenimiento_background())
        try:
            while self.running:
                try:
                    texto = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: console.input("[bold cyan]Tú > [/bold cyan]")
                    )
                except EOFError:
                    break
                texto = (texto or "").strip()
                if not texto:
                    continue

                cmd = await self._manejar_comando(texto)
                if cmd is not None:
                    if cmd:
                        console.print()
                        console.print(
                            Panel(Markdown(cmd), title="[bold green]VALERIA[/bold green]", border_style="green")
                        )
                        console.print()
                    continue

                with console.status("[dim]Pensando...[/dim]", spinner="dots"):
                    respuesta = await self._procesar_mensaje_usuario(texto)
                console.print()
                console.print(
                    Panel(Markdown(respuesta), title="[bold green]VALERIA[/bold green]", border_style="green")
                )
                console.print()
        finally:
            self.running = False
            bg.cancel()
            try:
                await bg
            except asyncio.CancelledError:
                pass

    async def run(self) -> None:
        await self.inicializar()
        await self.bucle_chat()
        self.estado_consciencia = "durmiendo"
        console.print("\n[bold green]✓ VALERIA apagada.[/bold green]\n")


def main() -> None:
    try:
        asyncio.run(OrquestadorPrincipal().run())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
