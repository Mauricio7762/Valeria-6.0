# Dataset SFT v2 + entrenamiento LoRA

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `dataset_valeria_sft_v2.jsonl` | Dataset limpio nuevo (~270 ejemplos) |
| `dataset_valeria_sft_v2_full.jsonl` | v2 + datasets viejos deduplicados (**recomendado**, ~430+) |
| `generar_dataset_v2.py` | Regenera el v2 base |
| `train_lora_sft.py` | Script de fine-tune con TRL + PEFT |

## Mejoras vs v1

- Más parafrasis por hecho de arquitectura (no una sola plantilla)
- Multihop (glial vs agentes, RAG vs grafo, etc.)
- Conversación y límites
- Enseñanza («X es un Y» → confirmación)
- Conocimiento general ligero para no colapsar solo a VALERIA
- Español más natural (concordancia, artículos)

## Entrenar (GPU recomendada)

```bash
pip install torch transformers peft accelerate trl datasets

export HF_TOKEN=hf_xxx   # modelo gated

python ENTRENAMIENTO/train_lora_sft.py \
  --dataset ENTRENAMIENTO/dataset_valeria_sft_v2_full.jsonl \
  --output MODELOS/valeria_llama_lora_v5 \
  --epochs 3 \
  --batch-size 4 \
  --lr 2e-4
```

Prueba rápida CPU (pocos steps):

```bash
python ENTRENAMIENTO/train_lora_sft.py --max-steps 30 --batch-size 1 --epochs 1
```

## Usar el adapter nuevo

1. Verificá que existan `adapter_model.safetensors` + `adapter_config.json` en `MODELOS/valeria_llama_lora_v5/`
2. En config: `llm_lora.adapter: "MODELOS/valeria_llama_lora_v5"`
3. O en chat: `/lora v5` y `/lora load`

## Hiperparámetros sugeridos

| Recurso | batch | grad accum | epochs | r | notas |
|---------|-------|------------|--------|---|-------|
| GPU 8GB+ | 4 | 4 | 3 | 16 | default del script |
| GPU poca VRAM | 1 | 8 | 3 | 16 | o 4-bit en el script |
| Más capacidad | 4 | 4 | 3–5 | 32 | sumar gate/up/down_proj |

Con ~400 ejemplos, **3 epochs** suele bastar; más epochs → riesgo de memorizar plantillas.
