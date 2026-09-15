"""
Extractor de hechos por LLM/LoRA
================================
Texto libre → lista de {sujeto, relacion, objeto} para el grafo.

Uso:
  from AGENTES_CORTICALES.razonamiento.extractor_llm import extraer_hechos_llm
  hechos = extraer_hechos_llm("La microglía forma parte del sistema glial.")

Si no hay adapter o falla, devuelve [] (el caller puede usar extraer_hecho regex).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from loguru import logger

_ROOT = Path(__file__).resolve().parent.parent.parent
_RELACIONES = {
    "es_un",
    "es_parte_de",
    "tiene_funcion",
    "tiene_proposito",
    "tiene_propiedad",
    "tiene",
    "causa",
    "es",
}

_SYSTEM = (
    "Extraé hechos estructurados del texto en español. "
    "Devolvé SOLO un JSON array. Cada elemento: "
    '{"sujeto":"...","relacion":"...","objeto":"..."}. '
    "Relaciones permitidas: es_un, es_parte_de, tiene_funcion, tiene_proposito, "
    "tiene_propiedad, tiene, causa, es. "
    "Sujeto/objeto en minúsculas sin artículos; módulos con guiones bajos. "
    "Si no hay hechos, devolvé []."
)

_model = None
_tokenizer = None
_loaded_path: str | None = None


def _resolver_extractor_adapter() -> Path | None:
    """Busca MODELOS/valeria_extractor_vN (mayor N) o fallback chat LoRA."""
    import re as _re

    encontrados: dict[int, Path] = {}
    for base in [_ROOT / "MODELOS", _ROOT]:
        if not base.exists():
            continue
        for p in base.iterdir():
            if not p.is_dir():
                continue
            m = _re.fullmatch(r"valeria_extractor_v(\d+)", p.name)
            if not m:
                continue
            ver = int(m.group(1))
            if (p / "adapter_config.json").exists() and (
                p / "adapter_model.safetensors"
            ).exists():
                encontrados[ver] = p.resolve()
    if encontrados:
        return encontrados[max(encontrados)]

    # Fallback: último LoRA de chat (peor que un extractor dedicado)
    chat: dict[int, Path] = {}
    for base in [_ROOT / "MODELOS", _ROOT]:
        if not base.exists():
            continue
        for p in base.iterdir():
            if not p.is_dir():
                continue
            m = _re.fullmatch(r"valeria_llama_lora_v(\d+)", p.name)
            if not m:
                continue
            ver = int(m.group(1))
            if (p / "adapter_config.json").exists() and (
                p / "adapter_model.safetensors"
            ).exists():
                chat[ver] = p.resolve()
    if chat:
        return chat[max(chat)]
    return None


def cargar(adapter: str | Path | None = None, base_model: str = "meta-llama/Llama-3.2-1B-Instruct") -> bool:
    global _model, _tokenizer, _loaded_path
    if _model is not None and adapter is None:
        return True
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
    except ImportError as e:
        logger.warning(f"extractor_llm: deps ausentes ({e})")
        return False

    path = Path(adapter) if adapter else _resolver_extractor_adapter()
    if path is None:
        logger.warning("extractor_llm: no hay adapter")
        return False
    if not path.is_absolute():
        path = _ROOT / path
    path = path.resolve()
    if not (path / "adapter_config.json").exists():
        logger.warning(f"extractor_llm: falta config en {path}")
        return False

    try:
        use_cuda = torch.cuda.is_available()
        dtype = torch.float16 if use_cuda else torch.float32
        tok_src = str(path) if (path / "tokenizer.json").exists() else base_model
        _tokenizer = AutoTokenizer.from_pretrained(tok_src, trust_remote_code=True)
        if _tokenizer.pad_token is None:
            _tokenizer.pad_token = _tokenizer.eos_token
        kwargs: dict[str, Any] = {"torch_dtype": dtype, "trust_remote_code": True}
        if use_cuda:
            kwargs["device_map"] = "auto"
        base = AutoModelForCausalLM.from_pretrained(base_model, **kwargs)
        _model = PeftModel.from_pretrained(base, str(path))
        _model.eval()
        _loaded_path = str(path)
        logger.info(f"extractor_llm cargado: {path}")
        return True
    except Exception as e:
        logger.exception(f"extractor_llm load error: {e}")
        _model = None
        _tokenizer = None
        return False


def _parse_json_array(text: str) -> list[dict]:
    text = text.strip()
    # quitar fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    # buscar primer [...]
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    out = []
    for item in data:
        if not isinstance(item, dict):
            continue
        s = str(item.get("sujeto") or "").strip().lower()
        r = str(item.get("relacion") or "").strip().lower()
        o = str(item.get("objeto") or "").strip().lower()
        if not s or not r or not o:
            continue
        if r not in _RELACIONES:
            # mapear aliases comunes
            aliases = {
                "parte_de": "es_parte_de",
                "es_parte": "es_parte_de",
                "funcion": "tiene_funcion",
                "propósito": "tiene_proposito",
                "proposito": "tiene_proposito",
            }
            r = aliases.get(r, r)
        if r not in _RELACIONES:
            continue
        s = re.sub(r"^(el|la|los|las|un|una)_?", "", s)
        s = s.replace(" ", "_")
        out.append({"sujeto": s, "relacion": r, "objeto": o.replace(" ", "_") if r in ("es_un", "es_parte_de", "es") else o})
    return out


def extraer_hechos_llm(
    texto: str,
    max_new_tokens: int = 256,
    forzar_carga: bool = False,
) -> list[dict[str, str]]:
    """Devuelve lista de triples. [] si no hay modelo o no hay hechos."""
    if not texto or not texto.strip():
        return []
    if _model is None:
        if not cargar():
            return []
    assert _model is not None and _tokenizer is not None

    messages = [
        {"role": "system", "content": _SYSTEM},
        {
            "role": "user",
            "content": f"Extraé hechos (sujeto, relación, objeto) del siguiente texto.\nTexto: {texto.strip()}",
        },
    ]
    try:
        import torch

        prompt = _tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = _tokenizer(prompt, return_tensors="pt")
        device = next(_model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            out = _model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=_tokenizer.pad_token_id,
                eos_token_id=_tokenizer.eos_token_id,
            )
        gen = out[0][inputs["input_ids"].shape[-1] :]
        text = _tokenizer.decode(gen, skip_special_tokens=True)
        return _parse_json_array(text)
    except Exception as e:
        logger.warning(f"extractor_llm generate: {e}")
        return []


def extraer_hechos_hibrido(texto: str) -> list[dict[str, str]]:
    """Regex primero (rápido/preciso en plantillas); si vacío, LLM."""
    from .extractor_hechos import extraer_hecho

    h = extraer_hecho(texto)
    if h is not None:
        return [
            {
                "sujeto": h.sujeto.replace(" ", "_"),
                "relacion": h.relacion,
                "objeto": h.objeto.replace(" ", "_")
                if h.relacion in ("es_un", "es_parte_de", "es")
                else h.objeto,
            }
        ]
    return extraer_hechos_llm(texto)
