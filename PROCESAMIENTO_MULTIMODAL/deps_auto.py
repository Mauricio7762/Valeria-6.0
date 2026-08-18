"""
Instalación perezosa de dependencias al procesar archivos.

Al subir un PDF o una imagen, VALERIA intenta asegurar los paquetes
mínimos con pip (en el entorno actual). No reemplaza un `pip install`
completo del proyecto; es ayuda para Codespaces / demos.
"""

from __future__ import annotations

import importlib
import subprocess
import sys
from functools import lru_cache
from typing import Iterable


def _pip_install(*packages: str) -> tuple[bool, str]:
    if not packages:
        return True, ""
    cmd = [sys.executable, "-m", "pip", "install", "-q", *packages]
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if r.returncode != 0:
            err = (r.stderr or r.stdout or "pip falló").strip()
            return False, err[-500:]
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "timeout instalando paquetes"
    except Exception as e:
        return False, str(e)


def _tiene(modulo: str) -> bool:
    try:
        importlib.import_module(modulo)
        return True
    except ImportError:
        return False


@lru_cache(maxsize=16)
def asegurar_paquetes(clave: str, modulos_y_pkgs: tuple[tuple[str, str], ...]) -> dict:
    """
    modulos_y_pkgs: ((nombre_import, paquete_pip), ...)
    clave: solo para cache (ej. 'pdf', 'imagen')
    """
    faltan: list[str] = []
    for mod, pkg in modulos_y_pkgs:
        if not _tiene(mod):
            faltan.append(pkg)
    # únicos preservando orden
    seen: set[str] = set()
    uniq: list[str] = []
    for p in faltan:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    if not uniq:
        return {"ok": True, "instalados": [], "mensaje": "dependencias ya disponibles"}
    ok, err = _pip_install(*uniq)
    # invalidar no es trivial con lru; el import se reintenta
    if not ok:
        return {"ok": False, "instalados": uniq, "mensaje": err}
    # verificar
    siguen = [pkg for mod, pkg in modulos_y_pkgs if not _tiene(mod)]
    if siguen:
        return {
            "ok": False,
            "instalados": uniq,
            "mensaje": f"instalado pero aún no importable: {siguen}",
        }
    return {"ok": True, "instalados": uniq, "mensaje": f"instalado: {', '.join(uniq)}"}


def asegurar_deps_pdf() -> dict:
    """pypdf obligatorio; opendataloader-pdf opcional (no auto por peso/Java)."""
    return asegurar_paquetes(
        "pdf",
        (("pypdf", "pypdf"),),
    )


def asegurar_deps_imagen() -> dict:
    """Pillow + httpx para caption por API."""
    return asegurar_paquetes(
        "imagen",
        (
            ("PIL", "pillow"),
            ("httpx", "httpx"),
        ),
    )


def asegurar_deps_audio() -> dict:
    """Por ahora no hay decoder pesado; httpx por si hay API futura."""
    return asegurar_paquetes("audio", (("httpx", "httpx"),))
