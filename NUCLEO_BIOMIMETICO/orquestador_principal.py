"""
Orquestador Principal (Formación Reticular)
==========================================
Coordinación global y estado de consciencia de VALERIA 6.0.
Es el punto de entrada principal del sistema.
"""

from __future__ import annotations

import asyncio
import signal
import sys
from pathlib import Path
from typing import Any

from loguru import logger
from rich.console import Console
from rich.panel import Panel

# Añadir raíz del proyecto al path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

console = Console()


class OrquestadorPrincipal:
    """
    Formación Reticular de VALERIA.
    Responsable de:
    - Arranque ordenado del sistema
    - Coordinación global entre subsistemas
    - Mantenimiento del estado de consciencia
    - Apagado graceful
    """

    def __init__(self) -> None:
        self.running = False
        self.estado_consciencia = "inicializando"
        self.subsistemas: dict[str, Any] = {}
        self._setup_logging()
        self._setup_signals()

    def _setup_logging(self) -> None:
        """Configura el sistema de logs."""
        logger.remove()
        logger.add(
            sys.stderr,
            level="INFO",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
                   "<level>{message}</level>",
        )
        log_dir = ROOT / "LOGS"
        log_dir.mkdir(exist_ok=True)
        logger.add(
            log_dir / "valeria_system.log",
            rotation="10 MB",
            retention="30 days",
            level="DEBUG",
        )

    def _setup_signals(self) -> None:
        """Manejo de señales para apagado graceful."""
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._signal_handler)

    def _signal_handler(self, signum: int, frame: Any) -> None:
        logger.warning(f"Señal recibida ({signum}). Iniciando apagado graceful...")
        self.running = False

    async def inicializar(self) -> None:
        """Arranque ordenado de todos los subsistemas de la Capa 0/1."""
        console.print(Panel.fit(
            "[bold cyan]VALERIA 6.0[/bold cyan]\n"
            "[dim]Cerebro Humano Digital — Capa 0 (Fundación)[/dim]",
            border_style="cyan",
        ))

        logger.info("Iniciando Orquestador Principal (Formación Reticular)...")

        # Aquí se cargarán las capas según feature flags
        # Por ahora solo Capa 0
        self.estado_consciencia = "despierto"
        self.running = True
        logger.success("Orquestador Principal listo. Estado de consciencia: DESPIERTO")

    async def ciclo_principal(self) -> None:
        """Loop principal de coordinación."""
        logger.info("Entrando en ciclo principal de orquestación...")
        while self.running:
            # En capas posteriores aquí se coordinará:
            # - Sistema Glial
            # - Agentes Corticales
            # - Metacognición
            # etc.
            await asyncio.sleep(1)

        await self.apagar()

    async def apagar(self) -> None:
        """Apagado ordenado."""
        logger.info("Iniciando secuencia de apagado...")
        self.estado_consciencia = "durmiendo"
        # Aquí se apagarán los subsistemas en orden inverso
        logger.success("VALERIA 6.0 apagada correctamente.")
        console.print("[bold green]Sistema apagado de forma segura.[/bold green]")

    async def run(self) -> None:
        """Punto de entrada asíncrono."""
        await self.inicializar()
        await self.ciclo_principal()


def main() -> None:
    """Entry point síncrono."""
    orquestador = OrquestadorPrincipal()
    try:
        asyncio.run(orquestador.run())
    except KeyboardInterrupt:
        logger.info("Interrupción por teclado.")
    except Exception as e:
        logger.exception(f"Error fatal en Orquestador Principal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
