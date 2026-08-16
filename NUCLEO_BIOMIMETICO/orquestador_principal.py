"""
Orquestador Principal (Formación Reticular)
==========================================
Capa 2 — Modo Interactivo (chat pulido).
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
from rich.table import Table
from rich.markdown import Markdown

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from NUCLEO_BIOMIMETICO.gestor_recursos import GestorRecursos
from NUCLEO_BIOMIMETICO.SISTEMA_GLIAL.sistema_glial import SistemaGlial
from AGENTES_CORTICALES.coordinador_agentes import CoordinadorAgentes

console = Console()

AYUDA = """
**Comandos**
- `/ayuda` — esta ayuda
- `/estado` — consciencia, ciclos, emoción, hechos
- `/hechos` — lista hechos del grafo (semilla + aprendidos)
- `/grafo` — resumen del grafo de conocimiento
- `/debug` — activa/desactiva pasos internos del razonamiento
- `/salir` — apaga VALERIA

**Uso normal**
- Pregunta: `¿qué es la microglía?`
- Enseña: `la microglía es parte del sistema glial`
"""


class OrquestadorPrincipal:
    def __init__(self) -> None:
        self.running = False
        self.estado_consciencia = "apagado"
        self.config: dict[str, Any] = {}
        self.gestor_recursos: GestorRecursos | None = None
        self.sistema_glial: SistemaGlial | None = None
        self.coordinador: CoordinadorAgentes | None = None
        self._ciclo_count = 0
        self._debug = False  # mostrar pasos internos
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
        # Solo errores en pantalla para no ensuciar el chat
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

    async def inicializar(self) -> None:
        console.print(
            Panel.fit(
                "[bold cyan]VALERIA 6.0[/bold cyan]\n"
                "[dim]Cerebro Humano Digital — Chat[/dim]\n"
                "[green]Escribe una pregunta o enséñale un hecho.  /ayuda[/green]",
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
        if self.coordinador:
            est = self.coordinador.agentes["razonamiento"].estado()
            n_hechos = est.get("grafo", {}).get("total_hechos", 0)

        console.print(
            f"[bold green]✓[/bold green] Despierta · "
            f"[dim]{n_hechos} hechos en el grafo · /ayuda para comandos[/dim]\n"
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

    def _agente_razonamiento(self):
        if not self.coordinador:
            return None
        return self.coordinador.agentes.get("razonamiento")

    async def _procesar_mensaje_usuario(self, texto: str) -> str:
        if not self.coordinador:
            return "Sistema de agentes no disponible."

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
        razon = await self.coordinador.enviar("razonamiento", {"pregunta": texto})

        if any(p in texto.lower() for p in ("quiero", "necesito", "objetivo", "planificar")):
            await self.coordinador.enviar(
                "planificacion", {"accion": "nuevo_objetivo", "objetivo": texto}
            )

        return self._formatear_respuesta(razon, emo)

    def _formatear_respuesta(self, razon: dict[str, Any], emo: dict[str, Any]) -> str:
        """Respuesta limpia por defecto; con /debug incluye pasos internos."""
        conclusion = (razon.get("conclusion") or "").strip()
        if not conclusion:
            conclusion = "No pude formar una conclusión clara."

        lineas = [conclusion]

        # Metadatos discretos
        estrategia = razon.get("estrategia")
        confianza = razon.get("confianza")
        intencion = razon.get("intencion")
        meta_bits = []
        if estrategia:
            meta_bits.append(str(estrategia))
        if confianza is not None:
            try:
                meta_bits.append(f"confianza {float(confianza):.0%}")
            except (TypeError, ValueError):
                pass
        if intencion and intencion not in ("general",):
            meta_bits.append(str(intencion))

        estado = emo.get("estado_afectivo")
        if estado and estado != "neutral":
            meta_bits.append(f"ánimo {estado}")

        if meta_bits:
            lineas.append("")
            lineas.append("*" + " · ".join(meta_bits) + "*")

        if self._debug:
            pasos = razon.get("razonamiento") or []
            if pasos:
                lineas.append("")
                lineas.append("**Pasos internos**")
                for p in pasos:
                    lineas.append(f"- {p}")

        return "\n".join(lineas)

    async def _cmd_estado(self) -> str:
        lineas = [
            f"**Consciencia:** {self.estado_consciencia}",
            f"**Ciclos en background:** {self._ciclo_count}",
            f"**Debug:** {'on' if self._debug else 'off'}",
        ]
        if self.gestor_recursos:
            r = self.gestor_recursos.obtener_estado()
            lineas.append(f"**CPU / RAM:** {r['cpu_percent']:.0f}% / {r['ram_percent']:.0f}%")
        if self.coordinador:
            est = self.coordinador.estado()
            emo = est.get("emocional", {})
            mem = est.get("memoria", {})
            raz = est.get("razonamiento", {})
            lineas.append(f"**Mensajes memoria:** {mem.get('mensajes_procesados', 0)}")
            lineas.append(f"**Mensajes razonamiento:** {raz.get('mensajes_procesados', 0)}")
            grafo = raz.get("grafo") or {}
            if grafo:
                lineas.append(
                    f"**Grafo:** {grafo.get('total_hechos', 0)} hechos, "
                    f"{grafo.get('sujetos_distintos', 0)} sujetos"
                )
            ult = emo.get("ultimo_resultado")
            if ult:
                lineas.append(f"**Última emoción:** {ult}")
        return "\n".join(lineas)

    async def _cmd_hechos(self, limite: int = 25) -> str:
        agente = self._agente_razonamiento()
        if not agente or not hasattr(agente, "grafo"):
            return "Agente de razonamiento no disponible."
        hechos = list(getattr(agente.grafo, "_hechos", []))
        if not hechos:
            return "El grafo está vacío."
        # Priorizar aprendidos del usuario al final de la lista visual
        aprendidos = [h for h in hechos if getattr(h, "origen", "") == "usuario"]
        base = [h for h in hechos if getattr(h, "origen", "") != "usuario"]
        ordenados = aprendidos[-limite:] + base[: max(0, limite - len(aprendidos))]
        lineas = [f"**Hechos** (mostrando {min(len(hechos), limite)} de {len(hechos)})", ""]
        for h in ordenados[:limite]:
            origen = getattr(h, "origen", "?")
            lineas.append(
                f"- `{h.sujeto}` —*{h.relacion}*→ `{h.objeto}` "
                f"[{origen}]"
            )
        return "\n".join(lineas)

    async def _cmd_grafo(self) -> str:
        agente = self._agente_razonamiento()
        if not agente:
            return "Agente de razonamiento no disponible."
        est = agente.estado().get("grafo") or {}
        return (
            f"**Grafo de conocimiento**\n"
            f"- Hechos: **{est.get('total_hechos', 0)}**\n"
            f"- Sujetos distintos: **{est.get('sujetos_distintos', 0)}**\n"
            f"- Relaciones distintas: **{est.get('relaciones_distintas', 0)}**\n"
            f"- Persistencia: `DATA/MEMORY/semantica/grafo_conocimiento.json`"
        )

    async def _manejar_comando(self, texto: str) -> str | None:
        """Devuelve respuesta si es comando; None si es mensaje normal."""
        raw = texto.strip()
        low = raw.lower()

        if low in ("/salir", "/exit", "/quit", "salir"):
            console.print("[yellow]Apagando VALERIA...[/yellow]")
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

        if low in ("/debug",):
            self._debug = not self._debug
            return f"Debug **{'activado' if self._debug else 'desactivado'}**."

        # /aprender <afirmación>
        if low.startswith("/aprender ") or low.startswith("/learn "):
            afirmacion = raw.split(" ", 1)[1].strip()
            if not afirmacion:
                return "Uso: `/aprender la microglía es parte del sistema glial`"
            return await self._procesar_mensaje_usuario(afirmacion)

        return None

    async def bucle_chat(self) -> None:
        bg_task = asyncio.create_task(self._mantenimiento_background())
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

                cmd_resp = await self._manejar_comando(texto)
                if cmd_resp is not None:
                    if cmd_resp:
                        console.print()
                        console.print(
                            Panel(
                                Markdown(cmd_resp),
                                title="[bold green]VALERIA[/bold green]",
                                border_style="green",
                            )
                        )
                        console.print()
                    continue

                with console.status("[dim]Pensando...[/dim]", spinner="dots"):
                    respuesta = await self._procesar_mensaje_usuario(texto)

                console.print()
                console.print(
                    Panel(
                        Markdown(respuesta),
                        title="[bold green]VALERIA[/bold green]",
                        border_style="green",
                    )
                )
                console.print()
        finally:
            self.running = False
            bg_task.cancel()
            try:
                await bg_task
            except asyncio.CancelledError:
                pass

    async def run(self) -> None:
        await self.inicializar()
        await self.bucle_chat()
        self.estado_consciencia = "durmiendo"
        console.print("\n[bold green]✓ VALERIA apagada de forma segura.[/bold green]\n")


def main() -> None:
    try:
        asyncio.run(OrquestadorPrincipal().run())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(f"Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
