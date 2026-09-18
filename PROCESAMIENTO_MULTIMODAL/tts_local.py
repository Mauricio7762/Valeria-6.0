"""
Síntesis de voz local (TTS) para VALERIA
========================================
Prioridad:
  1) piper  — offline, liviano, voces en español
  2) edge-tts — gratis, voces neurales es-AR / es-ES (requiere red, sin API key de pago)

Variables de entorno:

  VALERIA_TTS_PROVIDER=piper|edge|auto   (default: auto)
  VALERIA_TTS_VOICE=es_ES-sharvard-medium   # piper
  VALERIA_TTS_EDGE_VOICE=es-AR-ElenaNeural  # edge-tts (Argentina)
  VALERIA_TTS_OUT_DIR=DATA/MEMORY/audio_out

Instalación:
  pip install piper-tts
  # o: pip install edge-tts

  Voces piper (ejemplo):
  https://github.com/rhasspy/piper/blob/master/VOICES.md
  Descargar .onnx + .onnx.json a DATA/TTS/ o ruta en VALERIA_PIPER_MODEL
"""

from __future__ import annotations

import asyncio
import os
import re
import wave
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv

    _root = Path(__file__).resolve().parents[1]
    load_dotenv(_root / ".env", override=False)
except ImportError:
    pass

_ROOT = Path(__file__).resolve().parents[1]


def _out_dir() -> Path:
    raw = os.environ.get("VALERIA_TTS_OUT_DIR") or "DATA/MEMORY/audio_out"
    p = Path(raw)
    if not p.is_absolute():
        p = _ROOT / p
    p.mkdir(parents=True, exist_ok=True)
    return p


def _slug(texto: str, max_len: int = 40) -> str:
    t = re.sub(r"\s+", "_", (texto or "").strip().lower())
    t = re.sub(r"[^a-z0-9_áéíóúñü]", "", t)[:max_len]
    return t or "voz"


def _provider() -> str:
    p = (os.environ.get("VALERIA_TTS_PROVIDER") or "auto").strip().lower()
    if p in ("auto", ""):
        return "auto"
    if p in ("piper", "edge", "edge-tts"):
        return "edge" if p.startswith("edge") else p
    return "auto"


def _tts_piper(texto: str, out_path: Path) -> dict[str, Any]:
    """Piper offline. Requiere modelo .onnx configurado."""
    try:
        from piper import PiperVoice
    except ImportError:
        return {
            "ok": False,
            "error": "pip install piper-tts",
            "provider": "piper",
        }

    model = os.environ.get("VALERIA_PIPER_MODEL") or ""
    if not model:
        # buscar en DATA/TTS/
        tts_dir = _ROOT / "DATA" / "TTS"
        candidatos = list(tts_dir.glob("*.onnx")) if tts_dir.exists() else []
        if not candidatos:
            return {
                "ok": False,
                "error": (
                    "Falta modelo Piper. Descargá una voz es_ES o es_MX "
                    "(.onnx + .onnx.json) a DATA/TTS/ o definí VALERIA_PIPER_MODEL"
                ),
                "provider": "piper",
            }
        model = str(candidatos[0])

    model_path = Path(model)
    if not model_path.is_absolute():
        model_path = _ROOT / model_path
    if not model_path.exists():
        return {
            "ok": False,
            "error": f"No existe modelo Piper: {model_path}",
            "provider": "piper",
        }

    try:
        voice = PiperVoice.load(str(model_path))
        with wave.open(str(out_path), "wb") as wav_file:
            voice.synthesize(texto, wav_file)
        return {
            "ok": True,
            "path": str(out_path),
            "provider": "piper",
            "model": str(model_path.name),
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "provider": "piper"}


def _tts_edge(texto: str, out_path: Path) -> dict[str, Any]:
    """edge-tts: voces neurales es-AR sin API key (usa red)."""
    try:
        import edge_tts
    except ImportError:
        return {
            "ok": False,
            "error": "pip install edge-tts",
            "provider": "edge",
        }

    voice = (
        os.environ.get("VALERIA_TTS_EDGE_VOICE")
        or "es-AR-ElenaNeural"
    )
    # mp3 por defecto de edge
    if out_path.suffix.lower() == ".wav":
        out_path = out_path.with_suffix(".mp3")

    async def _run() -> None:
        communicate = edge_tts.Communicate(texto, voice)
        await communicate.save(str(out_path))

    try:
        asyncio.run(_run())
        return {
            "ok": True,
            "path": str(out_path),
            "provider": "edge",
            "voice": voice,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "provider": "edge"}


def sintetizar(
    texto: str,
    *,
    nombre: str | None = None,
    provider: str | None = None,
) -> dict[str, Any]:
    """
    Genera audio a partir de texto.
    Devuelve {ok, path?, provider, error?}.
    """
    texto = (texto or "").strip()
    if not texto:
        return {"ok": False, "error": "Texto vacío"}

    # límite práctico para no generar audios enormes
    if len(texto) > 2000:
        texto = texto[:2000] + "…"

    prov = (provider or _provider()).lower()
    if prov in ("edge-tts",):
        prov = "edge"

    base = _out_dir() / f"{nombre or _slug(texto)}"
    intentos: list[str] = []
    if prov == "piper":
        intentos = ["piper"]
    elif prov == "edge":
        intentos = ["edge"]
    else:  # auto: piper offline primero, luego edge
        intentos = ["piper", "edge"]

    ultimo: dict[str, Any] = {"ok": False, "error": "Sin proveedor TTS"}
    for p in intentos:
        if p == "piper":
            out = base.with_suffix(".wav")
            ultimo = _tts_piper(texto, out)
        else:
            out = base.with_suffix(".mp3")
            ultimo = _tts_edge(texto, out)
        if ultimo.get("ok"):
            return ultimo
    return ultimo


def listar_voces_edge_es() -> list[str]:
    """Voces en español útiles (edge-tts). Requiere red en el listado real."""
    return [
        "es-AR-ElenaNeural",
        "es-AR-TomasNeural",
        "es-ES-ElviraNeural",
        "es-ES-AlvaroNeural",
        "es-MX-DaliaNeural",
        "es-MX-JorgeNeural",
    ]
