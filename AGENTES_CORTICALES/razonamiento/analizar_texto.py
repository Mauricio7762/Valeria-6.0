"""Análisis de texto con LoRA valeria_analisis_vN (no escribe en el grafo)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from loguru import logger

_ROOT = Path(__file__).resolve().parent.parent.parent
_BASE = "meta-llama/Llama-3.2-1B-Instruct"

_SYSTEM = (
    "Analizá el texto en español. Respondé ÚNICAMENTE un JSON con claves: "
    "proposito, estructura, tono, ideas_principales (array), ideas_secundarias (array), "
    "tesis (string o null), argumentos (array), sesgos_posibles (array). "
    "Sin markdown ni texto extra. "
    "proposito DEBE ser uno de: explicar, informar, convencer, criticar, vender, social. "
    "tono DEBE ser uno de: neutral, academico, persuasivo, informal, emotivo, tecnico. "
    "estructura DEBE ser uno de: definicion, enumeracion, argumento, causa-efecto, "
    "secuencia, saludo, comparacion, descripcion, problema-solucion. "
    "No inventes ideas que no estén en el texto. "
    "argumentos solo si hay justificación explícita; si no, []. "
    "tesis null si el texto solo describe o saluda."
)

_model = None
_tokenizer = None
_loaded_path: str | None = None


def _resolver_adapter() -> Path | None:
    encontrados: dict[int, Path] = {}
    for base in [_ROOT / "MODELOS", _ROOT]:
        if not base.exists():
            continue
        for p in base.iterdir():
            if not p.is_dir():
                continue
            m = re.fullmatch(r"valeria_analisis_v(\d+)", p.name)
            if not m:
                continue
            ver = int(m.group(1))
            if (p / "adapter_config.json").exists() and (
                (p / "adapter_model.safetensors").exists()
                or list(p.glob("adapter_model*.safetensors"))
            ):
                encontrados[ver] = p.resolve()
    if not encontrados:
        return None
    return encontrados[max(encontrados)]


def cargar(adapter: str | Path | None = None) -> bool:
    global _model, _tokenizer, _loaded_path
    if _model is not None and adapter is None:
        return True
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
    except ImportError as e:
        logger.warning(f"analizar_texto: deps ausentes ({e})")
        return False

    path = Path(adapter) if adapter else _resolver_adapter()
    if path is None:
        logger.warning("analizar_texto: no hay valeria_analisis_vN")
        return False
    if not path.is_absolute():
        path = _ROOT / path
    path = path.resolve()
    if not (path / "adapter_config.json").exists():
        logger.warning(f"analizar_texto: falta config en {path}")
        return False

    try:
        use_cuda = torch.cuda.is_available()
        dtype = torch.float16 if use_cuda else torch.float32
        tok_src = str(path) if (path / "tokenizer.json").exists() else _BASE
        _tokenizer = AutoTokenizer.from_pretrained(tok_src, trust_remote_code=True)
        if _tokenizer.pad_token is None:
            _tokenizer.pad_token = _tokenizer.eos_token
        kwargs: dict[str, Any] = {"torch_dtype": dtype, "trust_remote_code": True}
        if use_cuda:
            kwargs["device_map"] = "auto"
        base = AutoModelForCausalLM.from_pretrained(_BASE, **kwargs)
        _model = PeftModel.from_pretrained(base, str(path))
        _model.eval()
        _loaded_path = str(path)
        logger.info(f"analizar_texto cargado: {path}")
        return True
    except Exception as e:
        logger.exception(f"analizar_texto load: {e}")
        _model = None
        _tokenizer = None
        return False


def _parse_json(text: str) -> dict | None:
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def analizar_texto(texto: str, max_new_tokens: int = 350) -> dict[str, Any]:
    """
    Devuelve dict con claves de análisis, o {"error": "...", "raw": "..."}.
    """
    if not (texto or "").strip():
        return {"error": "Texto vacío"}
    if _model is None and not cargar():
        return {"error": "No se pudo cargar valeria_analisis_vN (¿está en MODELOS/?)"}

    assert _model is not None and _tokenizer is not None
    try:
        import torch

        messages = [
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": f"Analizá el siguiente texto.\nTexto: {texto.strip()}",
            },
        ]
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
        raw = _tokenizer.decode(gen, skip_special_tokens=True).strip()
        parsed = _parse_json(raw)
        if parsed is None:
            return {"error": "No se pudo parsear JSON", "raw": raw}
        return parsed
    except Exception as e:
        logger.warning(f"analizar_texto generate: {e}")
        return {"error": str(e)}


def formatear_analisis(data: dict[str, Any]) -> str:
    """Texto legible para el chat."""
    if data.get("error"):
        msg = f"No pude analizar: {data['error']}"
        if data.get("raw"):
            msg += f"\n\nSalida cruda:\n{data['raw'][:500]}"
        return msg

    lineas = ["**Análisis del texto**", ""]
    if data.get("proposito"):
        lineas.append(f"- **Propósito:** {data['proposito']}")
    if data.get("estructura"):
        lineas.append(f"- **Estructura:** {data['estructura']}")
    if data.get("tono"):
        lineas.append(f"- **Tono:** {data['tono']}")
    if data.get("tesis"):
        lineas.append(f"- **Tesis:** {data['tesis']}")
    elif data.get("tesis") is None and "tesis" in data:
        lineas.append("- **Tesis:** (ninguna)")

    for clave, titulo in (
        ("ideas_principales", "Ideas principales"),
        ("ideas_secundarias", "Ideas secundarias"),
        ("argumentos", "Argumentos"),
        ("sesgos_posibles", "Sesgos posibles"),
    ):
        items = data.get(clave) or []
        if isinstance(items, list) and items:
            lineas.append(f"- **{titulo}:**")
            for it in items:
                lineas.append(f"  - {it}")

    return "\n".join(lineas)
