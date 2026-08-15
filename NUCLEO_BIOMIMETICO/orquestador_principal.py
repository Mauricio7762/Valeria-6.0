"""
Orquestador Principal (Formación Reticular)
==========================================
Capa 2: Núcleo + Sistema Glial + Agentes Corticales.
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
        logger.add(
            sys.stderr,
            level="INFO",
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        )
        log_dir = ROOT / "LOGS"
        log_dir.mkdir(exist_ok=True)
        logger.add(
            log_dir / "valeria_system.log",
            rotation="10 MB",
            retention="30 days",
            level="DEBUG",
            encoding="utf-8",
        )

    def _setup_signals(self) -> None:
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, self._signal_handler)
            except (ValueError, OSError):
                pass

    def _signal_handler(self, signum: int, frame: Any) -> None:
        logger.warning(f"Señal {signum} recibida → apagado graceful")
        self.running = False

    def _cargar_config(self) -> dict[str, Any]:
        config_path = ROOT / "CONFIGURACION" / "valeria_config.yaml"
        glial_path = ROOT / "CONFIGURACION" / "sistema_glial_config.yaml"
        config: dict[str, Any] = {}

        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            logger.info(f"Configuración cargada: {config_path.name}")

        if glial_path.exists():
            with open(glial_path, encoding="utf-8") as f:
                config["sistema_glial"] = yaml.safe_load(f) or {}
            logger.info(f"Configuración glial cargada: {glial_path.name}")

        return config

    def _mostrar_banner(self) -> None:
        console.print(
            Panel.fit(
                "[bold cyan]VALERIA 6.0[/bold cyan]\n"
                "[dim]Cerebro Humano Digital[/dim]\n"
                "[green]Capa 2 — Núcleo + Glial + Agentes Corticales[/green]",
                border_style="cyan",
                padding=(1, 4),
            )
        )

    def _mostrar_estado(self) -> None:
        table = Table(title="Estado del Sistema", show_header=True, header_style="bold magenta")
        table.add_column("Componente", style="cyan")
        table.add_column("Estado", style="green")

        table.add_row("Consciencia", self.estado_consciencia.upper())
        table.add_row("Ciclos", str(self._ciclo_count))

        if self.gestor_recursos:
            res = self.gestor_recursos.obtener_estado()
            table.add_row("CPU", f"{res['cpu_percent']:.1f}%")
            table.add_row("RAM", f"{res['ram_percent']:.1f}%")

        if self.sistema_glial:
            glial = self.sistema_glial.estado()
            table.add_row("Sistema Glial", "ACTIVO" if glial.get("enabled") else "OFF")

        if self.coordinador:
            estados = self.coordinador.estado()
            activos = sum(1 for a in estados.values() if a.get("enabled"))
            table.add_row("Agentes Corticales", f"{activos}/7 activos")

        console.print(table)

    async def inicializar(self) -> None:
        self._mostrar_banner()
        logger.info("Iniciando Orquestador Principal (Formación Reticular)...")

        self.config = self._cargar_config()

        self.gestor_recursos = GestorRecursos(self.config.get("resources", {}))
        logger.success("Gestor de Recursos listo")

        self.sistema_glial = SistemaGlial(self.config.get("sistema_glial", {}))
        logger.success("Sistema Glial listo")

        self.coordinador = CoordinadorAgentes(self.config.get("agentes", {}))
        logger.success("Coordinador de Agentes Corticales listo (7 agentes)")

        self.estado_consciencia = "despierto"
        self.running = True
        logger.success("Orquestador → estado: DESPIERTO")
        self._mostrar_estado()

    async def ciclo_principal(self) -> None:
        logger.info("Entrando en ciclo principal de orquestación...")
        intervalo = self.config.get("homeostasis", {}).get("check_interval_seconds", 5)

        while self.running:
            self._ciclo_count += 1

            # 1. Recursos
            if self.gestor_recursos and self.gestor_recursos.esta_bajo_presion():
                logger.warning("⚠️  Sistema bajo presión de recursos")

            # 2. Sistema Glial
            if self.sistema_glial:
                await self.sistema_glial.tick()

            # 3. Agentes Corticales
            if self.coordinador:
                await self.coordinador.tick()

                # Cada 15 ciclos hacemos una pequeña demo de comunicación entre agentes
                if self._ciclo_count % 15 == 0:
                    await self._demo_ciclo_agentes()

            if self._ciclo_count % 10 == 0:
                logger.info(f"Ciclo #{self._ciclo_count} | Consciencia: {self.estado_consciencia}")

            await asyncio.sleep(intervalo)

        await self.apagar()

    async def _demo_ciclo_agentes(self) -> None:
        """Pequeña demostración de que los agentes están vivos y se comunican."""
        if not self.coordinador:
            return

        # Percepción recibe un estímulo
        await self.coordinador.enviar("percepcion", {
            "tipo": "texto",
            "contenido": f"Estímulo de ciclo {self._ciclo_count}",
        })

        # Emocional evalúa
        emo = await self.coordinador.enviar("emocional", {
            "contenido": "todo bien, sistema estable",
        })

        # Monitor registra
        await self.coordinador.enviar("monitor", {
            "tipo": "reporte",
        })

        # Memoria guarda un episodio
        await self.coordinador.enviar("memoria", {
            "accion": "guardar_episodica",
            "contenido": f"Ciclo {self._ciclo_count} completado",
            "meta": {"emocional": emo.get("estado_afectivo")},
        })

        logger.info(
            f"Agentes → Emoción: {emo.get('estado_afectivo')} "
            f"({emo.get('intensidad')}) | Demo ciclo OK"
        )

    async def apagar(self) -> None:
        logger.info("Iniciando secuencia de apagado...")
        self.estado_consciencia = "durmiendo"
        logger.success("VALERIA 6.0 apagada correctamente.")
        console.print("\n[bold green]✓ Sistema apagado de forma segura.[/bold green]\n")

    async def run(self) -> None:
        await self.inicializar()
        await self.ciclo_principal()


def main() -> None:
    orquestador = OrquestadorPrincipal()
    try:
        asyncio.run(orquestador.run())
    except KeyboardInterrupt:
        logger.info("Interrupción por teclado.")
    except Exception as e:
        logger.exception(f"Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
