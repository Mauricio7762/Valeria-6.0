#!/usr/bin/env python3
"""
Fine-tune LoRA dedicado a extracción de hechos (texto → JSON triples).

  python ENTRENAMIENTO/train_extractor_sft.py \
    --dataset ENTRENAMIENTO/dataset_extractor_hechos.jsonl \
    --output MODELOS/valeria_extractor_v1

En Colab: mismas deps que el train de chat; output_dir sin checkpoints grandes
si después subís a GitHub (borrá checkpoint-* antes del push).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from datasets import Dataset


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            o = json.loads(line)
            inst = (o.get("instruction") or "").strip()
            out = (o.get("output") or "").strip()
            if inst and out is not None:
                rows.append({"instruction": inst, "output": out})
    return rows


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", type=Path, default=Path("ENTRENAMIENTO/dataset_extractor_hechos.jsonl"))
    p.add_argument("--output", type=Path, default=Path("MODELOS/valeria_extractor_v1"))
    p.add_argument("--base-model", default="meta-llama/Llama-3.2-1B-Instruct")
    p.add_argument("--epochs", type=float, default=3)
    p.add_argument("--batch-size", type=int, default=2)
    p.add_argument("--grad-accum", type=int, default=8)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--max-seq-len", type=int, default=512)
    p.add_argument("--lora-r", type=int, default=32)
    p.add_argument("--lora-alpha", type=int, default=64)
    args = p.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig
    from trl import SFTTrainer, SFTConfig

    rows = load_jsonl(args.dataset)
    print(f"Ejemplos: {len(rows)}")
    assert len(rows) >= 10

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    system = (
        "Extraé hechos estructurados del texto en español. "
        "Devolvé SOLO un JSON array con sujeto, relacion, objeto. "
        "Si no hay hechos, []."
    )

    def fmt(ex):
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": ex["instruction"]},
            {"role": "assistant", "content": ex["output"]},
        ]
        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=False
        )
        return {"text": text}

    ds = Dataset.from_list(rows).map(fmt, remove_columns=list(rows[0].keys()))

    use_cuda = torch.cuda.is_available()
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.float16 if use_cuda else torch.float32,
        device_map="auto" if use_cuda else None,
        trust_remote_code=True,
    )
    model.config.use_cache = False

    peft_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
    )

    args.output.mkdir(parents=True, exist_ok=True)
    sft_args = SFTConfig(
        output_dir=str(args.output),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        logging_steps=5,
        save_strategy="epoch",
        bf16=use_cuda and torch.cuda.is_bf16_supported(),
        fp16=use_cuda and not torch.cuda.is_bf16_supported(),
        max_length=args.max_seq_len,
        dataset_text_field="text",
        report_to="none",
        packing=False,
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_args,
        train_dataset=ds,
        peft_config=peft_config,
        processing_class=tokenizer,
    )
    trainer.train()
    trainer.save_model(str(args.output))
    tokenizer.save_pretrained(str(args.output))

    # Aviso: borrar checkpoint-* antes de push a GitHub
    print(f"Guardado en {args.output}")
    print("Antes de GitHub: rm -rf MODELOS/valeria_extractor_v1/checkpoint-*")


if __name__ == "__main__":
    main()
