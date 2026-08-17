# Visión y RAG (PDF)

## Visión (caption de imágenes)

Orden de intento:
1. **API** si existe `OPENAI_API_KEY` o `VALERIA_VISION_API_KEY`
   - Opcional: `OPENAI_BASE_URL`, `VALERIA_VISION_MODEL` (default `gpt-4o-mini`)
2. **BLIP local** si tenés `transformers` + `torch` + `pillow`
3. **PIL** solo tamaño/formato

```bash
export OPENAI_API_KEY=sk-...
# o compatible:
export OPENAI_BASE_URL=https://api.otro.com/v1
export VALERIA_VISION_API_KEY=...
```

En Streamlit: subí una imagen; si hay API, el caption se genera solo.

## RAG (PDF)

```bash
pip install pypdf
```

1. Streamlit → Multimodal → subir **.pdf** → Enviar archivo  
2. Se parte en fragmentos y se guarda en `DATA/MEMORY/rag/chunks.json`  
3. Las preguntas siguientes recuperan fragmentos relevantes  
4. Comando `/rag` — cuántos chunks y fuentes  

Sin embeddings ni GPU: recuperación por palabras clave (eficiente y local).
