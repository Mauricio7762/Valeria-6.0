# APIs de visión: OpenAI, Groq y Kimi

## Archivo `.env` (raíz del repo)

```env
VALERIA_VISION_PROVIDER=openai
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
KIMI_API_KEY=sk-...
```

Al arrancar Streamlit, el orquestador o la API se carga **solo** con `cargar_env()` (no hace falta `source .env` si tenés `python-dotenv`).

## Cambiar de proveedor

Solo cambiá una línea:

```env
VALERIA_VISION_PROVIDER=groq
# VALERIA_VISION_PROVIDER=kimi
# VALERIA_VISION_PROVIDER=openai
```

## Defaults de modelo

| Proveedor | Modelo por defecto |
|-----------|--------------------|
| openai | gpt-4o-mini |
| groq | meta-llama/llama-4-scout-17b-16e-instruct |
| kimi | moonshot-v1-8k-vision-preview |

Ajustá con `VALERIA_VISION_MODEL=...` si la consola del proveedor muestra otro nombre.
