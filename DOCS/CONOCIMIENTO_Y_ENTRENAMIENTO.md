# ¿Cuándo entrenar un modelo? ¿Cómo registrar conocimiento de forma eficiente?

VALERIA 6.0 hoy **no es un modelo de deep learning que se “entrena” con gradientes**.  
Es un sistema **simbólico + orquestado**: el conocimiento vive sobre todo en un **grafo de hechos** y en memorias (episódica / semántica).

## Las 3 formas de “saber” (de más barata a más cara)

### 1. Registro simbólico (lo que ya hace VALERIA) — **más eficiente ahora**
- Afirmaciones: `la microglía es parte del sistema glial`
- Semilla: `base_conocimiento_semilla.py`
- Persistencia: `DATA/MEMORY/semantica/grafo_conocimiento.json`

**Ventajas:** inmediato, interpretable, sin GPU, se audita, se edita a mano.  
**Límite:** no generaliza como un LLM; solo razona sobre lo que está en el grafo (y CBR débil).

**Cuándo usarlo:** casi siempre, en esta etapa del proyecto.

### 2. Memoria + recuperación (RAG) — **siguiente salto de eficiencia**
- Guardar textos/documentos
- Embeddings + búsqueda de fragmentos relevantes
- El razonador (simbólico o un LLM) usa esos fragmentos

**Ventajas:** mucho conocimiento sin “entrenar”; actualizable.  
**Cuándo:** cuando quieras manuales, PDFs o historial largo sin meter todo en el grafo.

### 3. Entrenar / ajustar un modelo neuronal (fine-tune, LoRA, etc.) — **más adelante**
Implica:
- Dataset (miles–millones de ejemplos según el objetivo)
- Arquitectura base (p. ej. un LLM o un encoder de visión)
- Cómputo (GPU) y evaluación
- “Parámetros” = pesos de la red, no los hechos del grafo

**Cuándo tiene sentido empezar:**
- Cuando el grafo + reglas se queden cortos (lenguaje abierto, visión real, audio real)
- Cuando tengas **datos propios** de calidad (diálogos de VALERIA, correcciones, pares pregunta→respuesta)
- Cuando definas un objetivo medible (p. ej. “clasificar intención con 90% accuracy”)

**No hace falta** entrenar un modelo para que VALERIA “recuerde” arquitectura o hechos de dominio: eso es grafo/semilla/RAG.

## Cómo registra conocimiento VALERIA hoy (eficiente)

| Mecanismo | Qué guarda | Persistente |
|-----------|------------|-------------|
| Extractor de hechos | Afirmaciones → (sujeto, relación, objeto) | Sí (JSON) |
| Semilla | Hechos de diseño del sistema | En código |
| Episódica | Turnos de conversación | Sí |
| Meta (ajustes) | Pesos de estrategias | Sí |
| Neurogénesis | Refuerza/poda aristas del grafo | En grafo |
| Multimodal (nuevo) | Metadatos + caption → texto para razonar | Archivo + episodio |

## Recomendación práctica para este proyecto

1. **Seguir cargando conocimiento en el grafo** (semilla + enseñanza + promoción desde episodios).  
2. Cuando el volumen de texto crezca → **RAG** (embeddings), sin entrenar aún.  
3. Multimodal “de verdad” (describir imágenes / transcribir audio) → **modelos preentrenados** (CLIP, Whisper) por API o local, aún sin fine-tune.  
4. Fine-tune solo si necesitás un estilo o dominio muy propio y ya tenés datos.

En resumen: **ahora el camino eficiente es simbolismo + datos estructurados**; **entrenar parámetros de una red** es una fase posterior, cuando el cuello de botella sea percepción o lenguaje abierto, no el registro de hechos.
