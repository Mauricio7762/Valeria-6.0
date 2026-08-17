"""Carga el archivo .env de la raíz del repositorio (una sola vez)."""

from __future__ import annotations

from pathlib import Path

_cargado = False


def cargar_env(override: bool = False) -> Path | None:
    global _cargado
    if _cargado and not override:
        return None
    root = Path(__file__).resolve().parents[1]
    env_path = root / ".env"
    try:
        from dotenv import load_dotenv
    except ImportError:
        return env_path if env_path.exists() else None
    if env_path.exists():
        load_dotenv(env_path, override=override)
        _cargado = True
        return env_path
    # también intentar cwd
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        load_dotenv(cwd_env, override=override)
        _cargado = True
        return cwd_env
    _cargado = True
    return None
