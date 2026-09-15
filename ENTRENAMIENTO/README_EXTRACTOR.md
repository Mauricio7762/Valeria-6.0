# Extractor de hechos (texto → grafo)

## Qué es
LoRA dedicado que lee texto libre y devuelve JSON:
```json
[{"sujeto":"microglia","relacion":"es_parte_de","objeto":"sistema_glial"}]
```

## Archivos
| Archivo | Uso |
|---------|-----|
| `dataset_extractor_hechos.jsonl` | ~400 ejemplos SFT |
| `generar_dataset_extractor.py` | Regenerar dataset desde semilla |
| `train_extractor_sft.py` | Fine-tune → `MODELOS/valeria_extractor_v1` |
| `../AGENTES_CORTICALES/razonamiento/extractor_llm.py` | Inferencia + híbrido regex |

## Colab (rápido)
```python
%cd /content/Valeria-6.0
!python ENTRENAMIENTO/train_extractor_sft.py \
  --dataset ENTRENAMIENTO/dataset_extractor_hechos.jsonl \
  --output MODELOS/valeria_extractor_v1 \
  --epochs 3 --batch-size 2 --grad-accum 8 --lr 1e-4
# borrar checkpoints antes de push:
!rm -rf MODELOS/valeria_extractor_v1/checkpoint-*
```

## Probar
```python
from AGENTES_CORTICALES.razonamiento.extractor_llm import extraer_hechos_hibrido
print(extraer_hechos_hibrido(
  "La microglía forma parte del sistema glial y limpia contextos obsoletos."
))
```

## Integración
- `extraer_hecho` (regex) para frases plantilla
- `extraer_hechos_llm` / `extraer_hechos_hibrido` para texto libre
- Luego `grafo.agregar_hecho(sujeto, relacion, objeto)`
