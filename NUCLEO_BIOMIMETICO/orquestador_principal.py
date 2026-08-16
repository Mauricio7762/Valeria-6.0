"""
Orquestador Principal (Formación Reticular)
==========================================
Arranque, background y wiring. Chat → chat_comandos / pipeline_mensaje.
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
from NUCLEO_BIOMIMETICO.chat_comandos import AYUDA, manejar_comando
from NUCLEO_BIOMIMETICO.pipeline_mensaje import procesar_mensaje
from NUCLEO_BIOMIMETICO.persistencia_meta import cargar_estado_meta, guardar_estado_meta
from AGENTES_CORTICALES.coordinador_agentes import CoordinadorAgentes
from SISTEMAS_AVANZADOS.METACOGNICION import (
    MonitorMetacognitivo,
    EvaluadorMetacognitivo,
    PlanificadorMetacognitivo,
    AjustadorMetacognitivo,
    AutorreflexionMetacognitiva,
)
from SISTEMAS_AVANZADOS.CURIOSIDAD_COMPUTACIONAL import ExploradorAutonomo
from SISTEMAS_AVANZADOS.NEUROGENESIS_ARTIFICIAL import CoordinadorNeurogenesis
from SISTEMAS_AVANZADOS.ANALIZADOR_HOLISTICO_CODIGO import OrquestadorHolistico

console = Console()


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
        cargar_estado_meta(self.meta_ajuste, self.curiosidad)

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
                if self._ciclo_count % 5 == 0:
                    raz = self.coordinador.agentes.get("razonamiento")
                    mic = getattr(self.sistema_glial, "microglia", None) if self.sistema_glial else None
                    if raz is not None and hasattr(raz, "grafo"):
                        self.neurogenesis.ciclo_mantenimiento(raz.grafo, microglia=mic)
            if self._ciclo_count % 10 == 0:
                try:
                    guardar_estado_meta(self.meta_ajuste, self.curiosidad)
                except Exception:
                    pass
            await asyncio.sleep(intervalo)

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

                cmd = await manejar_comando(self, texto)
                if cmd is not None:
                    if texto.lower() in ("/salir", "/exit", "/quit", "salir"):
                        console.print("[yellow]Apagando...[/yellow]")
                    if cmd:
                        console.print()
                        console.print(
                            Panel(
                                Markdown(cmd),
                                title="[bold green]VALERIA[/bold green]",
                                border_style="green",
                            )
                        )
                        console.print()
                    continue

                with console.status("[dim]Pensando...[/dim]", spinner="dots"):
                    respuesta = await procesar_mensaje(self, texto)
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
            try:
                guardar_estado_meta(self.meta_ajuste, self.curiosidad)
            except Exception:
                pass
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
