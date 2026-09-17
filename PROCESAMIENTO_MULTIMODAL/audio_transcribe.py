"""
Transcripción automática de audio
==================================
Mismo patrón que vision_caption.py: proveedor API OpenAI-compatible
con fallback a un modelo local liviano, para que VALERIA nunca dependa
de una sola vía.

Proveedores API (comparten las mismas claves que ya usa vision_caption,
así no hay que configurar nada nuevo si ya tenés OpenAI o Groq):

  VALERIA_AUDIO_PROVIDER=openai|groq

  OPENAI_API_KEY / VALERIA_AUDIO_API_KEY
  GROQ_API_KEY

  OPENAI_BASE_URL          (opcional, sobrescribe la base del proveedor)
  VALERIA_AUDIO_MODEL      (opcional, sobrescribe el modelo)

Fallback local: faster-whisper (modelo "tiny" por defecto — liviano,
corre en CPU). Se instala aparte con `pip install faster-whisper`,
no es una dependencia obligatoria del proyecto.

  VALERIA_AUDIO_MODEL_LOCAL=tiny|base|small   (default: tiny)
"""

from __future__ import annotations

import mimetypes
import os
import tempfile
from pathlib import Path
from typing import Any

# Cargar .env de la raíz del repo si existe (no pisa variables ya definidas)
try:
    from dotenv import load_dotenv

    _root = Path(__file__).resolve().parents[1]
    load_dotenv(_root / ".env", override=False)
except ImportError:
    pass

_PROVIDERS: dict[str, dict[str, str]] = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "whisper-1",
        "key_env": "OPENAI_API_KEY",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "whisper-large-v3-turbo",
        "key_env": "GROQ_API_KEY",
    },
}

# Cache del modelo local en memoria: cargarlo es lento, no queremos
# repetirlo en cada transcripción dentro del mismo proceso.
_MODELO_LOCAL_CACHE: dict[str, Any] = {}


def _resolver_config() -> tuple[str | None, str, str, str]:
    """(api_key, base_url, model, provider_name)"""
    provider = (
        os.environ.get("VALERIA_AUDIO_PROVIDER") or os.environ.get("AUDIO_PROVIDER") or ""
    ).strip().lower()

    if not provider:
        if os.environ.get("GROQ_API_KEY"):
            provider = "groq"
        elif os.environ.get("OPENAI_API_KEY") or os.environ.get("VALERIA_AUDIO_API_KEY"):
            provider = "openai"
        else:
            provider = "openai"

    meta = _PROVIDERS.get(provider, _PROVIDERS["openai"])
    base = (os.environ.get("OPENAI_BASE_URL") or meta["base_url"]).rstrip("/")
    model = os.environ.get("VALERIA_AUDIO_MODEL") or meta["model"]

    if provider == "groq":
        key = os.environ.get("GROQ_API_KEY") or os.environ.get("VALERIA_AUDIO_API_KEY")
    else:
        key = os.environ.get("OPENAI_API_KEY") or os.environ.get("VALERIA_AUDIO_API_KEY")

    return key, base, model, provider


def _info_basica(datos: bytes, mime: str) -> str | None:
    try:
        import mutagen
    except ImportError:
        return None
    try:
        import io

        f = mutagen.File(io.BytesIO(datos))
        if f is None or f.info is None:
            return None
        dur = getattr(f.info, "length", None)
        partes = [f"audio {mime or '?'}"]
        if dur:
            partes.append(f"{dur:.1f}s")
        return " ".join(partes)
    except Exception:
        return None


def _transcribir_api(datos: bytes, mime: str, nombre: str) -> tuple[str | None, str]:
    api_key, base, model, provider = _resolver_config()
    if not api_key:
        return None, provider

    try:
        import httpx
    except ImportError:
        return None, provider

    try:
        files = {"file": (nombre, datos, mime or "audio/wav")}
        data = {"model": model, "language": "es"}
        r = httpx.post(
            f"{base}/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            data=data,
            files=files,
            timeout=120.0,
        )
        r.raise_for_status()
        texto = (r.json().get("text") or "").strip()
        return (texto or None), provider
    except Exception as e:
        return None, f"{provider}:error:{type(e).__name__}"


def _modelo_local():
    tamano = os.environ.get("VALERIA_AUDIO_MODEL_LOCAL", "tiny")
    if tamano not in _MODELO_LOCAL_CACHE:
        from faster_whisper import WhisperModel  # import perezoso: dep opcional

        _MODELO_LOCAL_CACHE[tamano] = WhisperModel(tamano, device="cpu", compute_type="int8")
    return _MODELO_LOCAL_CACHE[tamano]


def _transcribir_local(datos: bytes, mime: str) -> str | None:
    try:
        modelo = _modelo_local()
    except ImportError:
        return None
    except Exception:
        return None

    try:
        sufijo = mimetypes.guess_extension(mime or "") or ".wav"
        with tempfile.NamedTemporaryFile(suffix=sufijo, delete=True) as f:
            f.write(datos)
            f.flush()
            segmentos, _info = modelo.transcribe(f.name, language="es", beam_size=1)
            texto = " ".join(s.text.strip() for s in segmentos).strip()
            return texto or None
    except Exception:
        return None


def transcribir_audio(datos: bytes, mime: str = "audio/wav", nombre: str = "audio.wav") -> dict[str, Any]:
    """Devuelve {transcripcion, fuente, provider, info_basica}."""
    info = _info_basica(datos, mime)

    texto, prov = _transcribir_api(datos, mime, nombre)
    if texto:
        return {
            "transcripcion": texto,
            "fuente": "api",
            "provider": prov,
            "info_basica": info,
        }

    local = _transcribir_local(datos, mime)
    if local:
        return {
            "transcripcion": local,
            "fuente": "local",
            "provider": "local-whisper",
            "info_basica": info,
        }

    return {
        "transcripcion": None,
        "fuente": "metadata" if info else "ninguna",
        "provider": prov if isinstance(prov, str) else None,
        "info_basica": info,
    }
