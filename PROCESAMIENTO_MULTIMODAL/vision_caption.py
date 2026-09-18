"""
Caption automático de imágenes
==============================
Proveedores:
  local  → Qwen2.5-VL-3B-Instruct (español, sin API)
  openai | groq | kimi → API OpenAI-compatible

Variables de entorno:

  VALERIA_VISION_PROVIDER=local|openai|groq|kimi
  VALERIA_VISION_LOCAL_MODEL=Qwen/Qwen2.5-VL-3B-Instruct

  OPENAI_API_KEY / VALERIA_VISION_API_KEY
  GROQ_API_KEY
  KIMI_API_KEY / MOONSHOT_API_KEY
  OPENAI_BASE_URL
  VALERIA_VISION_MODEL
"""

from __future__ import annotations

import base64
import io
import os
from pathlib import Path
from typing import Any

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

_PROMPT_ES = (
    "Describí la imagen en español rioplatense, breve y concreto. "
    "Mencioná lo importante: personas, objetos, texto visible, escena. "
    "No uses inglés."
)

_LOCAL_QWEN: dict[str, Any] | None = None


def _pil_info(datos: bytes) -> str:
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(datos))
        return f"imagen {img.size[0]}x{img.size[1]} modo={img.mode}"
    except Exception:
        return f"imagen {len(datos)} bytes"


def _resolver_provider() -> str:
    provider = (
        os.environ.get("VALERIA_VISION_PROVIDER")
        or os.environ.get("VISION_PROVIDER")
        or ""
    ).strip().lower()
    if provider in ("moonshot", "moonshot-v1"):
        provider = "kimi"
    if provider in ("qwen", "qwen2.5", "qwen2_5"):
        provider = "local"
    if provider:
        return provider

    if os.environ.get("GROQ_API_KEY"):
        return "groq"
    if os.environ.get("KIMI_API_KEY") or os.environ.get("MOONSHOT_API_KEY"):
        return "kimi"
    if os.environ.get("OPENAI_API_KEY") or os.environ.get("VALERIA_VISION_API_KEY"):
        return "openai"
    return "local"


def _resolver_api_config(provider: str) -> tuple[str | None, str, str, str]:
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


def _caption_qwen_local_path(ruta: str | Path, prompt: str | None = None) -> dict[str, Any]:
    """Caption local con Qwen2.5-VL (español)."""
    global _LOCAL_QWEN
    try:
        import torch
        from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
        from qwen_vl_utils import process_vision_info
    except ImportError as e:
        return {
            "ok": False,
            "caption": None,
            "provider": "local",
            "error": (
                "Faltan deps locales: pip install transformers accelerate "
                f"qwen-vl-utils pillow torch ({e})"
            ),
        }

    model_id = (
        os.environ.get("VALERIA_VISION_LOCAL_MODEL")
        or "Qwen/Qwen2.5-VL-3B-Instruct"
    )
    device = "cuda" if torch.cuda.is_available() else "cpu"
    prompt = (prompt or _PROMPT_ES).strip()
    ruta = str(Path(ruta).resolve())
    if not Path(ruta).is_file():
        return {
            "ok": False,
            "caption": None,
            "provider": "local",
            "error": f"No existe archivo: {ruta}",
        }

    try:
        if _LOCAL_QWEN is None or _LOCAL_QWEN.get("model_id") != model_id:
            dtype = torch.float16 if device == "cuda" else torch.float32
            kwargs: dict[str, Any] = {
                "torch_dtype": dtype,
                "trust_remote_code": True,
            }
            if device == "cuda":
                kwargs["device_map"] = "auto"
            model = Qwen2_5_VLForConditionalGeneration.from_pretrained(model_id, **kwargs)
            if device == "cpu":
                model = model.to("cpu")
            processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
            _LOCAL_QWEN = {
                "model": model,
                "processor": processor,
                "device": device,
                "model_id": model_id,
            }

        model = _LOCAL_QWEN["model"]
        processor = _LOCAL_QWEN["processor"]

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": f"file://{ruta}"},
                    {"type": "text", "text": prompt},
                ],
            }
        ]
        text = processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        with torch.no_grad():
            out_ids = model.generate(**inputs, max_new_tokens=180, do_sample=False)

        trimmed = [o[len(i) :] for i, o in zip(inputs["input_ids"], out_ids)]
        caption = processor.batch_decode(
            trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0].strip()

        if not caption:
            return {
                "ok": False,
                "caption": None,
                "provider": "local",
                "error": "Caption vacío",
            }
        return {
            "ok": True,
            "caption": caption,
            "provider": "local",
            "model": model_id,
        }
    except Exception as e:
        return {
            "ok": False,
            "caption": None,
            "provider": "local",
            "error": str(e),
        }


def _caption_qwen_local_bytes(datos: bytes, prompt: str | None = None) -> dict[str, Any]:
    import tempfile

    suffix = ".jpg"
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(datos))
        fmt = (img.format or "JPEG").upper()
        suffix = ".png" if fmt == "PNG" else ".jpg"
    except Exception:
        pass

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(datos)
        path = tmp.name
    try:
        return _caption_qwen_local_path(path, prompt=prompt)
    finally:
        try:
            Path(path).unlink(missing_ok=True)
        except Exception:
            pass


def _caption_api(datos: bytes, mime: str = "image/jpeg") -> tuple[str | None, str]:
    try:
        import httpx
    except ImportError:
        return None, "httpx-missing"

    provider = _resolver_provider()
    if provider == "local":
        return None, "local"

    api_key, base, model, provider = _resolver_api_config(provider)
    if not api_key:
        return None, f"{provider}:sin-api-key"

    b64 = base64.b64encode(datos).decode("ascii")
    data_url = f"data:{mime};base64,{b64}"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _PROMPT_ES},
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


def caption_imagen(datos: bytes, mime: str = "image/jpeg") -> dict[str, Any]:
    """Devuelve {caption, fuente, provider, info_basica, error?}."""
    info = _pil_info(datos)
    provider = _resolver_provider()

    if provider == "local":
        local = _caption_qwen_local_bytes(datos)
        if local.get("ok") and local.get("caption"):
            return {
                "caption": local["caption"],
                "fuente": "local",
                "provider": "local-qwen",
                "model": local.get("model"),
                "info_basica": info,
            }
        # fallback API si hay key
        cap, prov = _caption_api(datos, mime)
        if cap:
            return {
                "caption": cap,
                "fuente": "api",
                "provider": prov,
                "info_basica": info,
                "local_error": local.get("error"),
            }
        return {
            "caption": info,
            "fuente": "pil" if info else "ninguna",
            "provider": "local-qwen",
            "info_basica": info,
            "error": local.get("error"),
        }

    cap, prov = _caption_api(datos, mime)
    if cap:
        return {"caption": cap, "fuente": "api", "provider": prov, "info_basica": info}

    # API falló → intentar local
    local = _caption_qwen_local_bytes(datos)
    if local.get("ok") and local.get("caption"):
        return {
            "caption": local["caption"],
            "fuente": "local",
            "provider": "local-qwen",
            "model": local.get("model"),
            "info_basica": info,
            "api_error": prov,
        }

    return {
        "caption": info,
        "fuente": "pil" if info else "ninguna",
        "provider": prov if isinstance(prov, str) else None,
        "info_basica": info,
        "error": local.get("error"),
    }


def caption_desde_ruta(ruta: str | Path, prompt: str | None = None) -> dict[str, Any]:
    """Caption desde path de archivo (útil para /aprender imagen o tests)."""
    path = Path(ruta)
    info = ""
    try:
        datos = path.read_bytes()
        info = _pil_info(datos)
    except Exception as e:
        return {"ok": False, "caption": None, "error": str(e), "provider": None}

    provider = _resolver_provider()
    if provider == "local":
        r = _caption_qwen_local_path(path, prompt=prompt)
        if r.get("ok"):
            return {**r, "info_basica": info}
        cap, prov = _caption_api(datos, "image/jpeg")
        if cap:
            return {
                "ok": True,
                "caption": cap,
                "provider": prov,
                "fuente": "api",
                "info_basica": info,
                "local_error": r.get("error"),
            }
        return {**r, "info_basica": info}

    cap, prov = _caption_api(datos, "image/jpeg")
    if cap:
        return {
            "ok": True,
            "caption": cap,
            "provider": prov,
            "fuente": "api",
            "info_basica": info,
        }
    r = _caption_qwen_local_path(path, prompt=prompt)
    return {**r, "info_basica": info, "api_error": prov}
