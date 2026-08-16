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
)
from AGENTES_CORTICALES.razonamiento.puente_memoria import sugerir_promocion

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
                "[dim]Chat · Memoria · Metacognición (inicio Capa 3)[/dim]\n"
                "[green]/ayuda para comandos[/green]",
                border_style="cyan",
                padding=(1, 4),
            )
        )
        self.config = self._cargar_config()
        self.gestor_recursos = GestorRecursos(self.config.get("resources", {}))
        self.sistema_glial = SistemaGlial(self.config.get("sistema_glial", {}))
        self.coordinador = CoordinadorAgentes(self.config.get("agentes", {}))
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
            plan_estrategias = plan.estrategias
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
        evaluacion = self.meta_eval.evaluar(reg, str(razon.get("conclusion") or ""))

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
