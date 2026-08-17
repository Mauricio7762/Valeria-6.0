"""
Caption automático de imágenes
==============================
Estrategias (en orden):
  1. API OpenAI-compatible con visión (OPENAI_API_KEY + opcional OPENAI_BASE_URL)
  2. Modelo local BLIP vía transformers (si está instalado)
  3. Metadatos PIL (tamaño, modo) sin descripción semántica

Sin claves ni GPU, al menos devuelve info básica de la imagen.
"""

from __future__ import annotations

import base64
import io
import os
from typing import Any


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


def _caption_api(datos: bytes, mime: str = "image/jpeg") -> str | None:
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("VALERIA_VISION_API_KEY")
    if not api_key:
        return None
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("VALERIA_VISION_MODEL", "gpt-4o-mini")
    b64 = base64.standard_b64encode(datos).decode("ascii")
    data_url = f"data:{mime};base64,{b64}"
    try:
        import httpx
    except ImportError:
        return None
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
        "max_tokens": 200,
    }
    try:
        r = httpx.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=60.0,
        )
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def _caption_blip(datos: bytes) -> str | None:
    try:
        from PIL import Image
        from transformers import BlipProcessor, BlipForConditionalGeneration
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
    """
    Devuelve {caption, fuente, info_basica}.
    fuente: api | blip | pil | ninguna
    """
    info = _pil_info(datos)
    for fuente, fn in (
        ("api", lambda: _caption_api(datos, mime)),
        ("blip", lambda: _caption_blip(datos)),
    ):
        try:
            cap = fn()
        except Exception:
            cap = None
        if cap:
            return {"caption": cap, "fuente": fuente, "info_basica": info}
    return {
        "caption": None,
        "fuente": "pil" if info else "ninguna",
        "info_basica": info,
    }
