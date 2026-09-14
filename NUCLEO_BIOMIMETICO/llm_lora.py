"""
Cargador e inferencia LoRA (Llama-3.2-1B-Instruct + adapters VALERIA)
=====================================================================
Carga perezosa del modelo base + adaptador PEFT. Se usa como generador
neural de respaldo cuando el razonamiento simbólico tiene baja confianza.

Requisitos (opcionales):
  pip install torch transformers peft accelerate bitsandbytes  # bitsandbytes solo GPU
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from loguru import logger

_ROOT = Path(__file__).resolve().parent.parent

# Rutas conocidas de adapters (orden de preferencia al elegir "latest")
_ADAPTER_CANDIDATES = [
    # Ubicación canónica: MODELOS/
    _ROOT / "MODELOS" / "valeria_llama_lora_v4",
    _ROOT / "MODELOS" / "valeria_llama_lora_v3",
    _ROOT / "MODELOS" / "valeria_llama_lora_v2",
    _ROOT / "MODELOS" / "valeria_llama_lora_v1",
    # Alias por si la carpeta se llama "Modelo" (singular)
    _ROOT / "Modelo" / "valeria_llama_lora_v4",
    # Fallback raíz (versiones viejas del repo)
    _ROOT / "valeria_llama_lora_v4",
]

_DEFAULT_BASE = "meta-llama/Llama-3.2-1B-Instruct"

_SYSTEM_PROMPT = (
    "Eres VALERIA, un sistema de IA biomimético (Cerebro Humano Digital). "
    "Respondes en español, de forma clara, concisa y útil. "
    "Si te dan contexto del grafo de conocimiento o de documentos, úsalo. "
    "Si no sabes algo con certeza, dilo. No inventes hechos sobre la arquitectura "
    "de VALERIA que no estén en el contexto."
)


class LLMLora:
    """Singleton de carga e inferencia del adaptador LoRA."""

    def __init__(self) -> None:
        self._model = None
        self._tokenizer = None
        self._loaded = False
        self._load_error: str | None = None
        self._adapter_path: Path | None = None
        self._base_model: str = _DEFAULT_BASE
        self._device: str = "cpu"
        self._enabled = True

    # ------------------------------------------------------------------
    # Configuración
    # ------------------------------------------------------------------
    def configurar(
        self,
        enabled: bool = True,
        adapter: str | Path | None = None,
        base_model: str | None = None,
    ) -> None:
        self._enabled = bool(enabled)
        if base_model:
            self._base_model = base_model
        if adapter:
            p = Path(adapter)
            if not p.is_absolute():
                p = _ROOT / p
            self._adapter_path = p

    def resolver_adapter(self, preferido: str | None = None) -> Path | None:
        """Devuelve la ruta del adapter a usar."""
        if preferido:
            p = Path(preferido)
            if not p.is_absolute():
                p = _ROOT / p
            if (p / "adapter_config.json").exists() or (p / "adapter_model.safetensors").exists():
                return p
            # Alias cortos: v1, v2, v3, v4
            alias = {
                "v1": _ROOT / "MODELOS" / "valeria_llama_lora_v1",
                "v2": _ROOT / "MODELOS" / "valeria_llama_lora_v2",
                "v3": _ROOT / "MODELOS" / "valeria_llama_lora_v3",
                "v4": _ROOT / "MODELOS" / "valeria_llama_lora_v4",
                "latest": None,
            }
            if preferido.lower() in alias:
                if preferido.lower() == "latest":
                    pass  # cae al loop de candidatos
                else:
                    cand = alias[preferido.lower()]
                    if cand and (cand / "adapter_config.json").exists():
                        return cand

        if self._adapter_path and (
            (self._adapter_path / "adapter_config.json").exists()
            or (self._adapter_path / "adapter_model.safetensors").exists()
        ):
            return self._adapter_path

        for cand in _ADAPTER_CANDIDATES:
            if (cand / "adapter_config.json").exists():
                return cand
        return None

    # ------------------------------------------------------------------
    # Carga
    # ------------------------------------------------------------------
    def cargar(self, adapter: str | None = None, force: bool = False) -> bool:
        """Carga base + LoRA. Devuelve True si quedó listo."""
        if self._loaded and not force:
            return True
        if not self._enabled:
            self._load_error = "LLM LoRA deshabilitado en configuración"
            return False

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            from peft import PeftModel
        except ImportError as e:
            self._load_error = (
                f"Dependencias ausentes ({e}). "
                "Instalá: pip install torch transformers peft accelerate"
            )
            logger.warning(self._load_error)
            return False

        ruta = self.resolver_adapter(adapter)
        if ruta is None:
            self._load_error = (
                "No se encontró ningún adapter LoRA. "
                "Esperados en MODELOS/valeria_llama_lora_v1..v4/"
            )
            logger.warning(self._load_error)
            return False

        # Verificar que el .safetensors exista (puede no haberse extraído)
        pesos = ruta / "adapter_model.safetensors"
        if not pesos.exists():
            self._load_error = (
                f"Falta {pesos.name} en {ruta}. "
                "Copiá el archivo del entrenamiento a esa carpeta."
            )
            logger.warning(self._load_error)
            return False

        try:
            logger.info(f"Cargando base {self._base_model} + adapter {ruta.name}...")
            use_cuda = torch.cuda.is_available()
            dtype = torch.float16 if use_cuda else torch.float32
            self._device = "cuda" if use_cuda else "cpu"

            # Tokenizer: preferir el del adapter (local), si no el del base
            tok_src = ruta if (ruta / "tokenizer.json").exists() else self._base_model
            self._tokenizer = AutoTokenizer.from_pretrained(
                str(tok_src),
                trust_remote_code=True,
            )
            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token

            model_kwargs: dict[str, Any] = {
                "torch_dtype": dtype,
                "trust_remote_code": True,
            }
            if use_cuda:
                model_kwargs["device_map"] = "auto"
            else:
                model_kwargs["low_cpu_mem_usage"] = True

            # HF token opcional (modelos gated)
            token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
            if token:
                model_kwargs["token"] = token

            base = AutoModelForCausalLM.from_pretrained(self._base_model, **model_kwargs)
            self._model = PeftModel.from_pretrained(base, str(ruta))
            self._model.eval()

            if not use_cuda:
                self._model.to("cpu")

            self._adapter_path = ruta
            self._loaded = True
            self._load_error = None
            logger.info(
                f"LLM LoRA listo · adapter={ruta.name} · device={self._device}"
            )
            return True
        except Exception as e:
            self._load_error = f"Error al cargar modelo: {e}"
            logger.exception(self._load_error)
            self._model = None
            self._tokenizer = None
            self._loaded = False
            return False

    # ------------------------------------------------------------------
    # Inferencia
    # ------------------------------------------------------------------
    def generar(
        self,
        pregunta: str,
        contexto: str | None = None,
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str | None:
        """
        Genera respuesta en español. Devuelve None si el modelo no está disponible.
        """
        if not self._loaded:
            if not self.cargar():
                return None

        assert self._model is not None and self._tokenizer is not None

        system = _SYSTEM_PROMPT
        if contexto and contexto.strip():
            system += (
                "\n\nContexto disponible (grafo / documentos / memoria):\n"
                + contexto.strip()[:3000]
            )

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": pregunta.strip()},
        ]

        try:
            import torch

            prompt = self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            inputs = self._tokenizer(prompt, return_tensors="pt")
            if self._device == "cuda":
                inputs = {k: v.to("cuda") for k, v in inputs.items()}

            with torch.no_grad():
                out = self._model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=temperature > 0,
                    temperature=max(temperature, 1e-5),
                    top_p=top_p,
                    pad_token_id=self._tokenizer.pad_token_id,
                    eos_token_id=self._tokenizer.eos_token_id,
                )

            # Solo tokens nuevos
            gen_ids = out[0][inputs["input_ids"].shape[-1] :]
            texto = self._tokenizer.decode(gen_ids, skip_special_tokens=True).strip()
            return texto or None
        except Exception as e:
            logger.exception(f"Error en generación LoRA: {e}")
            return None

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------
    def estado(self) -> dict[str, Any]:
        return {
            "enabled": self._enabled,
            "loaded": self._loaded,
            "adapter": str(self._adapter_path.name) if self._adapter_path else None,
            "adapter_path": str(self._adapter_path) if self._adapter_path else None,
            "base_model": self._base_model,
            "device": self._device if self._loaded else None,
            "error": self._load_error,
            "candidates": [
                str(c.relative_to(_ROOT))
                for c in _ADAPTER_CANDIDATES
                if (c / "adapter_config.json").exists()
            ],
        }


# Instancia global (lazy)
_llm: LLMLora | None = None


def get_llm() -> LLMLora:
    global _llm
    if _llm is None:
        _llm = LLMLora()
    return _llm
