"""Instalación perezosa de dependencias opcionales (PDF, imagen, audio, visión local)."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from typing import Iterable


def _tiene(modulo: str) -> bool:
    return importlib.util.find_spec(modulo) is not None


def _pip_install(*paquetes: str) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", *paquetes],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if proc.returncode != 0:
            return False, (proc.stderr or proc.stdout or "pip falló")[-500:]
        return True, ""
    except Exception as e:
        return False, str(e)


def asegurar_paquetes(
    clave: str, modulos_y_pkgs: tuple[tuple[str, str], ...]
) -> dict:
    """
    modulos_y_pkgs: ((nombre_import, paquete_pip), ...)
    clave: solo para cache (ej. 'pdf', 'imagen')
    """
    faltan: list[str] = []
    for mod, pkg in modulos_y_pkgs:
        if not _tiene(mod):
            faltan.append(pkg)
    seen: set[str] = set()
    uniq: list[str] = []
    for p in faltan:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    if not uniq:
        return {"ok": True, "instalados": [], "mensaje": "dependencias ya disponibles"}
    ok, err = _pip_install(*uniq)
    if not ok:
        return {"ok": False, "instalados": uniq, "mensaje": err}
    siguen = [pkg for mod, pkg in modulos_y_pkgs if not _tiene(mod)]
    if siguen:
        return {
            "ok": False,
            "instalados": uniq,
            "mensaje": f"instalado pero aún no importable: {siguen}",
        }
    return {"ok": True, "instalados": uniq, "mensaje": f"instalado: {', '.join(uniq)}"}


def asegurar_deps_pdf() -> dict:
    return asegurar_paquetes("pdf", (("pypdf", "pypdf"),))


def asegurar_deps_imagen() -> dict:
    """Pillow + httpx para caption por API."""
    return asegurar_paquetes(
        "imagen",
        (
            ("PIL", "pillow"),
            ("httpx", "httpx"),
        ),
    )


def asegurar_deps_vision_local() -> dict:
    """Qwen2.5-VL local (sin API)."""
    return asegurar_paquetes(
        "vision_local",
        (
            ("PIL", "pillow"),
            ("torch", "torch"),
            ("transformers", "transformers"),
            ("accelerate", "accelerate"),
            ("qwen_vl_utils", "qwen-vl-utils"),
        ),
    )


def asegurar_deps_audio() -> dict:
    """httpx (API) + faster-whisper opcional se instala aparte si hace falta."""
    return asegurar_paquetes("audio", (("httpx", "httpx"),))


def asegurar_deps_audio_local() -> dict:
    return asegurar_paquetes(
        "audio_local",
        (("faster_whisper", "faster-whisper"),),
    )
