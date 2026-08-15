"""
Orquestador Principal (Formación Reticular)
==========================================
Coordinación global y estado de consciencia de VALERIA 6.0.
Capa 1: Versión funcional con Sistema Glial integrado.
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

# Raíz del proyecto
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from NUCLEO_BIOMIMETICO.gestor_recursos import GestorRecursos
from NUCLEO_BIOMIMETICO.SISTEMA_GLIAL.sistema_glial import SistemaGlial

console = Console()


class OrquestadorPrincipal:
    """
    Formación Reticular de VALERIA.
    - Arranque ordenado
    - Coordinación global
    - Estado de consciencia
    - Ciclos del Sistema Glial
    - Apagado graceful
    """

    def __init__(self) -> None:
        self.running = False
        self.estado_consciencia = "apagado"
        self.config: dict[str, Any] = {}
        self.gestor_recursos: GestorRecursos | None = None
        self.sistema_glial: SistemaGlial | None = None
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
        """Carga valeria_config.yaml y sistema_glial_config.yaml."""
        config_path = ROOT / "CONFIGURACION" / "valeria_config.yaml"
        glial_path = ROOT / "CONFIGURACION" / "sistema_glial_config.yaml"

        config: dict[str, Any] = {}
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            logger.info(f"Configuración cargada: {config_path.name}")
        else:
            logger.warning("No se encontró valeria_config.yaml → usando defaults")

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
                "[green]Capa 1 — Núcleo Biomimético + Sistema Glial[/green]",
                border_style="cyan",
                padding=(1, 4),
            )
        )

    def _mostrar_estado(self) -> None:
        """Tabla de estado en consola."""
        table = Table(title="Estado del Sistema", show_header=True, header_style="bold magenta")
        table.add_column("Componente", style="cyan")
        table.add_column("Estado", style="green")

        table.add_row("Consciencia", self.estado_consciencia.upper())
        table.add_row("Ciclos ejecutados", str(self._ciclo_count))

        if self.gestor_recursos:
            res = self.gestor_recursos.obtener_estado()
            table.add_row("CPU", f"{res['cpu_percent']:.1f}%")
            table.add_row("RAM", f"{res['ram_percent']:.1f}%")

        if self.sistema_glial:
            glial = self.sistema_glial.estado()
            table.add_row("Sistema Glial", "ACTIVO" if glial.get("enabled") else "INACTIVO")
            table.add_row("Astrocitos", "OK" if glial.get("astrocitos", {}).get("enabled") else "OFF")
            table.add_row("Microglía", "OK" if glial.get("microglia", {}).get("enabled") else "OFF")

        console.print(table)

    async def inicializar(self) -> None:
        """Arranque ordenado de todos los subsistemas."""
        self._mostrar_banner()
        logger.info("Iniciando Orquestador Principal (Formación Reticular)...")

        self.config = self._cargar_config()

        recursos_cfg = self.config.get("resources", {})
        self.gestor_recursos = GestorRecursos(recursos_cfg)
        logger.success("Gestor de Recursos listo")

        glial_cfg = self.config.get("sistema_glial", {})
        self.sistema_glial = SistemaGlial(glial_cfg)
        logger.success("Sistema Glial listo")

        self.estado_consciencia = "despierto"
        self.running = True
        logger.success("Orquestador Principal → estado: DESPIERTO")
        self._mostrar_estado()

    async def ciclo_principal(self) -> None:
        """Loop principal de coordinación + mantenimiento glial."""
        logger.info("Entrando en ciclo principal de orquestación...")
        intervalo = self.config.get("homeostasis", {}).get("check_interval_seconds", 5)

        while self.running:
            self._ciclo_count += 1

            if self.gestor_recursos and self.gestor_recursos.esta_bajo_presion():
                logger.warning("⚠️  Sistema bajo presión de recursos")

            if self.sistema_glial:
                await self.sistema_glial.tick()

            if self._ciclo_count % 10 == 0:
                logger.info(f"Ciclo #{self._ciclo_count} | Consciencia: {self.estado_consciencia}")
                if self.gestor_recursos:
                    res = self.gestor_recursos.obtener_estado()
                    logger.debug(f"Recursos → CPU: {res['cpu_percent']:.1f}% | RAM: {res['ram_percent']:.1f}%")

            await asyncio.sleep(intervalo)

        await self.apagar()

    async def apagar(self) -> None:
        """Apagado ordenado."""
        logger.info("Iniciando secuencia de apagado...")
        self.estado_consciencia = "durmiendo"
        if self.sistema_glial:
            logger.info("Deteniendo Sistema Glial...")
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
