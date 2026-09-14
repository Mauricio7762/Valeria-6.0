#!/usr/bin/env python3
"""
Fine-tune LoRA SFT para VALERIA sobre Llama-3.2-1B-Instruct

Requisitos:
  pip install torch transformers peft accelerate trl datasets

Uso típico (GPU):
  export HF_TOKEN=hf_xxx   # si el base está gated
  python ENTRENAMIENTO/train_lora_sft.py \\
    --dataset ENTRENAMIENTO/dataset_valeria_sft_v2_full.jsonl \\
    --output MODELOS/valeria_llama_lora_v5 \\
    --epochs 3 --batch-size 4 --lr 2e-4

CPU (lento, solo prueba):
  python ENTRENAMIENTO/train_lora_sft.py --epochs 1 --batch-size 1 --max-steps 50
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
            line = line.strip()
            if not line:
                continue
            o = json.loads(line)
            inst = (o.get("instruction") or o.get("input") or "").strip()
            out = (o.get("output") or o.get("response") or "").strip()
            if inst and out:
                rows.append({"instruction": inst, "output": out})
    return rows


def format_chat(example: dict, tokenizer) -> dict:
    """Aplica chat template de Llama-3 Instruct."""
    messages = [
        {
            "role": "system",
            "content": (
                "Eres VALERIA, un sistema de IA biomimético. "
                "Respondés en español, claro y conciso. "
                "Si no sabés algo con certeza, lo decís."
            ),
        },
        {"role": "user", "content": example["instruction"]},
        {"role": "assistant", "content": example["output"]},
    ]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
    )
    return {"text": text}


def main() -> None:
    parser = argparse.ArgumentParser(description="SFT LoRA VALERIA")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("ENTRENAMIENTO/dataset_valeria_sft_v2_full.jsonl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("MODELOS/valeria_llama_lora_v5"),
    )
    parser.add_argument("--base-model", default="meta-llama/Llama-3.2-1B-Instruct")
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--grad-accum", type=int, default=4)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--max-seq-len", type=int, default=512)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--max-steps", type=int, default=-1, help="-1 = usar epochs")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import LoraConfig
    from trl import SFTTrainer, SFTConfig

    rows = load_jsonl(args.dataset)
    if not rows:
        raise SystemExit(f"Dataset vacío: {args.dataset}")
    print(f"Ejemplos: {len(rows)} <- {args.dataset}")

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    ds = Dataset.from_list(rows)
    ds = ds.map(lambda ex: format_chat(ex, tokenizer), remove_columns=ds.column_names)

    use_cuda = torch.cuda.is_available()
    model_kwargs = {
        "trust_remote_code": True,
        "torch_dtype": torch.float16 if use_cuda else torch.float32,
    }
    if use_cuda:
        # 4-bit opcional: descomentar si tenés bitsandbytes y poca VRAM
        # model_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True)
        model_kwargs["device_map"] = "auto"

    print(f"Cargando base {args.base_model} (cuda={use_cuda})...")
    model = AutoModelForCausalLM.from_pretrained(args.base_model, **model_kwargs)
    model.config.use_cache = False

    peft_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        # Para más capacidad descomentá:
        # target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"],
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
        max_steps=args.max_steps,
        seed=args.seed,
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

    print("Entrenando...")
    trainer.train()
    trainer.save_model(str(args.output))
    tokenizer.save_pretrained(str(args.output))
    print(f"Adapter guardado en {args.output}")
    print("Para usarlo: poné en valeria_config.yaml")
    print(f'  llm_lora.adapter: "{args.output.as_posix()}"')
    print("o en el chat: /lora v5  (si agregás el alias en llm_lora.py)")


if __name__ == "__main__":
    main()
