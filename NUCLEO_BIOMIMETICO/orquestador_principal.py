"""
Orquestador Principal (Formación Reticular)
==========================================
Capa 2 + Modo Interactivo: puedes hablarle a VALERIA.
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


class OrquestadorPrincipal:
    def __init__(self) -> None:
        self.running = False
        self.estado_consciencia = "apagado"
        self.config: dict[str, Any] = {}
        self.gestor_recursos: GestorRecursos | None = None
        self.sistema_glial: SistemaGlial | None = None
        self.coordinador: CoordinadorAgentes | None = None
        self._ciclo_count = 0
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
        logger.add(sys.stderr, level="WARNING")

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

    def _mostrar_banner(self) -> None:
        console.print(
            Panel.fit(
                "[bold cyan]VALERIA 6.0[/bold cyan]\n"
                "[dim]Cerebro Humano Digital — Modo Interactivo[/dim]\n"
                "[green]Escribe algo y presiona Enter. Comandos: /estado  /salir[/green]",
                border_style="cyan",
                padding=(1, 4),
            )
        )

    async def inicializar(self) -> None:
        self._mostrar_banner()
        self.config = self._cargar_config()
        self.gestor_recursos = GestorRecursos(self.config.get("resources", {}))
        self.sistema_glial = SistemaGlial(self.config.get("sistema_glial", {}))
        self.coordinador = CoordinadorAgentes(self.config.get("agentes", {}))
        self.estado_consciencia = "despierto"
        self.running = True
        console.print("[bold green]✓ VALERIA despierta. Puedes hablarle.[/bold green]\n")

    async def _mantenimiento_background(self) -> None:
        intervalo = self.config.get("homeostasis", {}).get("check_interval_seconds", 5)
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

        await self.coordinador.enviar("percepcion", {"tipo": "texto", "contenido": texto})
        emo = await self.coordinador.enviar("emocional", {"contenido": texto})
        await self.coordinador.enviar("memoria", {
            "accion": "guardar_episodica",
            "contenido": texto,
            "meta": {"origen": "usuario", "emocional": emo.get("estado_afectivo")},
        })
        razon = await self.coordinador.enviar("razonamiento", {"pregunta": texto})

        if any(p in texto.lower() for p in ("quiero", "necesito", "objetivo", "plan", "hacer")):
            await self.coordinador.enviar("planificacion", {
                "accion": "nuevo_objetivo",
                "objetivo": texto,
            })

        estado = emo.get("estado_afectivo", "neutral")
        intensidad = emo.get("intensidad", 0.3)
        modulacion = emo.get("modulacion", "tono neutro")
        conclusion = razon.get("conclusion", "")
        pasos = razon.get("razonamiento", [])

        respuesta = (
            f"**Estado afectivo:** {estado} ({intensidad})\n"
            f"**Modulación:** {modulacion}\n\n"
            f"{conclusion}\n\n"
            f"*Pasos internos:*\n"
        )
        for p in pasos:
            respuesta += f"- {p}\n"
        return respuesta

    async def _mostrar_estado_rapido(self) -> None:
        if not self.coordinador:
            return
        estados = self.coordinador.estado()
        emo = estados.get("emocional", {})
        mem = estados.get("memoria", {})
        table = Table(title="Estado rápido", show_header=False)
        table.add_column("Campo", style="cyan")
        table.add_column("Valor")
        table.add_row("Consciencia", self.estado_consciencia)
        table.add_row("Ciclos background", str(self._ciclo_count))
        table.add_row("Emoción", str(emo.get("ultimo_resultado", "—")))
        table.add_row("Mensajes Memoria", str(mem.get("mensajes_procesados", 0)))
        console.print(table)

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

                if texto.lower() in ("/salir", "/exit", "/quit", "salir"):
                    console.print("[yellow]Apagando VALERIA...[/yellow]")
                    self.running = False
                    break

                if texto.lower() in ("/estado", "/status"):
                    await self._mostrar_estado_rapido()
                    continue

                with console.status("[dim]VALERIA pensando...[/dim]"):
                    respuesta = await self._procesar_mensaje_usuario(texto)

                console.print()
                console.print(Panel(Markdown(respuesta), title="[bold green]VALERIA[/bold green]", border_style="green"))
                console.print()
        finally:
            self.running = False
            bg_task.cancel()
            try:
                await bg_task
            except asyncio.CancelledError:
                pass

    async def apagar(self) -> None:
        self.estado_consciencia = "durmiendo"
        console.print("\n[bold green]✓ VALERIA apagada de forma segura.[/bold green]\n")

    async def run(self) -> None:
        await self.inicializar()
        await self.bucle_chat()
        await self.apagar()


def main() -> None:
    orquestador = OrquestadorPrincipal()
    try:
        asyncio.run(orquestador.run())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(f"Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
