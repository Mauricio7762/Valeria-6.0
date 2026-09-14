# Integración LoRA (respaldo neural)

VALERIA prioriza el **grafo simbólico**. Cuando la confianza del razonador es baja
(`< 0.4` o mensaje "no tengo hechos") **y** no hay hits de RAG, se intenta generar
con el adaptador LoRA (Llama-3.2-1B-Instruct + PEFT).

## Instalación

```bash
pip install torch transformers peft accelerate
# Si el base model está gated:
export HF_TOKEN=hf_xxxxx
```

Opcional desde el proyecto:

```bash
pip install -e ".[llm]"
```

## Archivos de pesos

Asegurate de tener en el repo (además de `adapter_config.json`):

- `MODELOS/valeria_llama_lora_v4/adapter_model.safetensors`  (preferido)
- también `MODELOS/valeria_llama_lora_v{1,2,3}/adapter_model.safetensors`

El tokenizer puede vivir en la misma carpeta del adapter.

## Configuración

`CONFIGURACION/valeria_config.yaml`:

```yaml
llm_lora:
  enabled: true
  adapter: "MODELOS/valeria_llama_lora_v4"   # o alias v1|v2|v3|v4|latest
  base_model: "meta-llama/Llama-3.2-1B-Instruct"
  preload: false   # true = cargar al arrancar
```

## Comandos de chat

- `/lora` — estado
- `/lora v4` — cambiar adapter y recargar
- `/lora load` — forzar carga
- `/lora on` / `/lora off` — habilitar / deshabilitar

## Flujo

1. Agente de razonamiento simbólico responde.
2. Si confianza alta → se usa esa respuesta.
3. Si hay RAG útil → se usa RAG.
4. Si no → se llama a `LLMLora.generar()` con contexto opcional.
5. La respuesta neural lleva el pie `*generado por LoRA*`.

## Notas

- Primera carga puede tardar (descarga del base model ~1B + merge LoRA).
- En CPU es usable pero lento; GPU (CUDA) recomendada.
- Si faltan dependencias o pesos, VALERIA sigue en modo solo simbólico sin romperse.
