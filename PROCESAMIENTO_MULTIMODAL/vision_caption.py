"""
Caption automático de imágenes
==============================
Proveedores OpenAI-compatible: openai | groq | kimi

Variables de entorno (también vía archivo .env en la raíz del repo):

  VALERIA_VISION_PROVIDER=openai|groq|kimi

  OPENAI_API_KEY / VALERIA_VISION_API_KEY
  GROQ_API_KEY
  KIMI_API_KEY / MOONSHOT_API_KEY

  OPENAI_BASE_URL          (opcional, sobrescribe la base del proveedor)
  VALERIA_VISION_MODEL     (opcional, sobrescribe el modelo)
"""

from __future__ import annotations

import base64
import io
import os
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
        "model": "gpt-4o-mini",
        "key_env": "OPENAI_API_KEY",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "key_env": "GROQ_API_KEY",
    },
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k-vision-preview",
        "key_env": "KIMI_API_KEY",
    },
}


def _resolver_config() -> tuple[str | None, str, str, str]:
    """(api_key, base_url, model, provider_name)"""
    provider = (
        os.environ.get("VALERIA_VISION_PROVIDER")
        or os.environ.get("VISION_PROVIDER")
        or ""
    ).strip().lower()

    if not provider:
        if os.environ.get("GROQ_API_KEY"):
            provider = "groq"
        elif os.environ.get("KIMI_API_KEY") or os.environ.get("MOONSHOT_API_KEY"):
            provider = "kimi"
        elif os.environ.get("OPENAI_API_KEY") or os.environ.get("VALERIA_VISION_API_KEY"):
            provider = "openai"
        else:
            provider = "openai"

    if provider in ("moonshot", "moonshot-v1"):
        provider = "kimi"

    meta = _PROVIDERS.get(provider, _PROVIDERS["openai"])
    base = (os.environ.get("OPENAI_BASE_URL") or meta["base_url"]).rstrip("/")
    model = os.environ.get("VALERIA_VISION_MODEL") or meta["model"]

    if provider == "groq":
        key = os.environ.get("GROQ_API_KEY") or os.environ.get("VALERIA_VISION_API_KEY")
    elif provider == "kimi":
        key = (
            os.environ.get("KIMI_API_KEY")
            or os.environ.get("MOONSHOT_API_KEY")
            or os.environ.get("VALERIA_VISION_API_KEY")
        )
    else:
        key = os.environ.get("OPENAI_API_KEY") or os.environ.get("VALERIA_VISION_API_KEY")

    return key, base, model, provider


def _pil_info(datos: bytes) -> str | None:
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        img = Image.open(io.BytesIO(datos))
        return f"imagen {img.format or '?'} {img.size[0]}x{img.size[1]} modo={img.mode}"
    except Exception:
        return None


def _caption_api(datos: bytes, mime: str = "image/jpeg") -> tuple[str | None, str]:
    api_key, base, model, provider = _resolver_config()
    if not api_key:
        return None, provider

    try:
        import httpx
    except ImportError:
        return None, provider

    b64 = base64.standard_b64encode(datos).decode("ascii")
    data_url = f"data:{mime};base64,{b64}"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Describe la imagen en español, en 1-3 frases. "
                            "Sé concreto: objetos, texto visible, diagrama si lo hay."
                        ),
                    },
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        "max_tokens": 300,
    }
    try:
        r = httpx.post(
            f"{base}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=90.0,
        )
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip(), provider
    except Exception as e:
        return None, f"{provider}:error:{type(e).__name__}"


def _caption_blip(datos: bytes) -> str | None:
    try:
        from PIL import Image
        from transformers import BlipForConditionalGeneration, BlipProcessor
        import torch
    except ImportError:
        return None
    try:
        img = Image.open(io.BytesIO(datos)).convert("RGB")
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        inputs = processor(img, return_tensors="pt")
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=50)
        return processor.decode(out[0], skip_special_tokens=True)
    except Exception:
        return None


def caption_imagen(datos: bytes, mime: str = "image/jpeg") -> dict[str, Any]:
    """Devuelve {caption, fuente, provider, info_basica}."""
    info = _pil_info(datos)

    cap, prov = _caption_api(datos, mime)
    if cap:
        return {"caption": cap, "fuente": "api", "provider": prov, "info_basica": info}

    blip = _caption_blip(datos)
    if blip:
        return {
            "caption": blip,
            "fuente": "blip",
            "provider": "local-blip",
            "info_basica": info,
        }

    return {
        "caption": info,
        "fuente": "pil" if info else "ninguna",
        "provider": prov if isinstance(prov, str) else None,
        "info_basica": info,
    }
