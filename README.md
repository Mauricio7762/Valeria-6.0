# VALERIA 6.0 — Sistema Biomimético Multimodal Completo

> **Cerebro Humano Digital**  
> Arquitectura biomimética estricta con Sistema Glial artificial, 7 Agentes Corticales y despliegue por capas.

---

## Visión General

VALERIA 6.0 no es un simple modelo de lenguaje ni un sistema multiagente convencional.  
Es la implementación de un **Cerebro Humano Digital** que replica la complejidad, eficiencia y resiliencia del cerebro biológico mediante biomímesis computacional estricta.

### Componentes principales

| Capa | Nombre |
|------|--------|
| **0** | Fundación (Infraestructura + CI/CD) |
| **1** | Núcleo Biomimético + Sistema Glial |
| **2** | 7 Agentes Corticales + razonamiento simbólico |
| **3** | Metacognición, Curiosidad, Neurogénesis, RAG, Holístico |
| **4** | Interfaces (Streamlit + API) |

> Estado detallado de cada capa (código + tests): sección **[Estado actual del desarrollo](#estado-actual-del-desarrollo)** más abajo.  
> Guía rápida de ejecución: **[DOCS/COMO_CORRER.md](DOCS/COMO_CORRER.md)**

---

## Arquitectura

```
VALERIA 6.0 = CEREBRO HUMANO DIGITAL
├── NÚCLEO BIOMIMÉTICO + SISTEMA GLIAL   ← Tronco Encefálico e Infraestructura
├── 7 AGENTES CORTICALES                 ← Neuronas y Cortezas Especializadas
├── SISTEMAS AVANZADOS                   ← Funciones Cognitivas Superiores
├── PROCESAMIENTO MULTIMODAL             ← Sistemas Sensoriales
├── SISTEMAS DE SOPORTE                  ← Sistemas Corporales/Vitales
├── JERARQUÍA DE MEMORIA                 ← Plasticidad y Almacenamiento
└── INTERFACES                           ← Sistema de Comunicación
```

### Sistema Glial Computacional (Novedad clave)

Representa el ~50% del cerebro biológico encargado del soporte. Las glías no “piensan”, pero hacen que el pensamiento sea posible, estable y eficiente:

- **Astrocitos** → Regulación de carga, atención y homeostasis cognitiva
- **Oligodendrocitos** → Mielinización (caché de rutas frecuentes)
- **Microglía** → Limpieza, poda y defensa (sistema inmune cognitivo)
- **Glía Radial** → Soporte estructural y reconfiguración (neurogénesis)

---

## Aprendizaje desde texto y PDF

VALERIA puede **aprender hechos** y guardarlos en el grafo de conocimiento a partir de texto libre o de un PDF con texto seleccionable.

### Flujo

```
Texto o PDF
  → segmentar ideas (oraciones / conectores)
  → extractor (regex + LoRA, si está disponible)
  → limpiar sujeto
  → grafo.agregar_hecho
  → persistencia
```

### Archivos

| Archivo | Rol |
|---------|-----|
| `AGENTES_CORTICALES/razonamiento/aprender_texto.py` | Texto → ideas → hechos → grafo |
| `AGENTES_CORTICALES/razonamiento/aprender_pdf.py` | PDF → texto → `aprender_texto` |
| `AGENTES_CORTICALES/razonamiento/extractor_llm.py` | LoRA extractor de triples |
| `NUCLEO_BIOMIMETICO/pipeline_mensaje.py` | Comandos `/aprender` y `/aprender_pdf` |

### Dependencia extra

```bash
pip install pypdf
```

(`loguru` y el resto ya entran por `requirements.txt` si aplica.)

### Comandos de chat

```text
/aprender La microglía forma parte del sistema glial.
/aprender Los astrocitos regulan la atención, mientras que la microglía limpia contextos. Ayer hizo calor.

/aprender_pdf /ruta/al/archivo.pdf
/pdf /ruta/al/archivo.pdf
```

También se aceptan prefijos: `aprendé esto` / `aprende esto`.

**Nota:** los PDF escaneados (solo imagen) no tienen texto extraíble hasta sumar OCR. El extractor LoRA vive en `MODELOS/valeria_extractor_vN` (usar la versión más reciente).

---

## Desarrollo por Capas + Despliegue Automático

El proyecto se desarrolla y despliega de forma progresiva:

1. Cada capa se implementa de forma independiente.
2. Una vez que pasa tests y criterios de aceptación, se activa automáticamente.
3. Se utiliza feature flags + configuración YAML para encender/apagar capas.
4. Pipeline CI/CD (GitHub Actions) se encargará del despliegue automático.

---

## Estructura del repositorio

```
valeria-6.0/
├── CONFIGURACION/               # YAML de configuración
├── NUCLEO_BIOMIMETICO/          # Orquestador, Sistema Glial, pipeline de mensaje
├── AGENTES_CORTICALES/          # 7 agentes + razonamiento simbólico (Route C)
├── SISTEMAS_AVANZADOS/          # Metacognición, Curiosidad, Neurogénesis, RAG, Holístico
├── PROCESAMIENTO_MULTIMODAL/    # Normalización de texto/imagen/audio de entrada
├── INTERFACES/                  # Streamlit + API (FastAPI)
├── MODELOS/                     # Adapters LoRA (chat + extractor)
├── ENTRENAMIENTO/               # Datasets y scripts SFT
├── DATA/                        # Persistencia (grafo, chunks RAG, memoria) — gitignored
├── TESTS/                       # Suite de pytest
├── DOCS/                        # Guías (cómo correr, conocimiento, visión RAG)
└── .github/workflows/           # CI
```

Carpetas mencionadas en versiones anteriores de este documento (PERSONALIDAD, HERRAMIENTAS,
ORQUESTACION_EXTERNA, DASHBOARD_ORQUESTADOR, SISTEMA_SCHEDULING, MODELO, ALMACENAMIENTO,
SCRIPTS, PLUGINS, UTILS, DOCKER/) son ideas para capas futuras, no existen todavía —
se agregan a esta lista recién cuando tengan código real adentro.

---

## Inicio rápido

```bash
# Clonar
git clone https://github.com/Mauricio7762/Valeria-6.0.git
cd Valeria-6.0

# Instalar dependencias
pip install -r requirements.txt
pip install pypdf

# Copiar variables de entorno
cp .env.example .env

# Ejecutar (chat en terminal)
export PYTHONPATH=.
python -m NUCLEO_BIOMIMETICO.orquestador_principal
```

> Guía completa (Streamlit, API HTTP, tests, comandos de chat): **[DOCS/COMO_CORRER.md](DOCS/COMO_CORRER.md)**

---

## Estado actual del desarrollo

| Capa | Código | Tests |
|------|--------|-------|
| **0** — Fundación (infraestructura + CI/CD) | ✅ | CI corre en cada push (`.github/workflows/test.yml`) |
| **1** — Núcleo Biomimético + Sistema Glial | ✅ | ✅ `TESTS/test_sistema_glial/` |
| **2** — Agentes Corticales + razonamiento simbólico | ✅ | ✅ `TESTS/test_agentes_corticales/` |
| **3** — Metacognición, Curiosidad, Neurogénesis, RAG, Holístico | ✅ | ✅ `TESTS/test_sistemas_avanzados/` |
| **4** — Interfaces (Streamlit + API) | ✅ básica | ⚠️ sin tests automatizados todavía |

**Reciente (aprendizaje):**

| Capacidad | Estado |
|-----------|--------|
| Extractor LoRA (texto → triples) | ✅ `MODELOS/valeria_extractor_vN` |
| `/aprender` texto → grafo | ✅ |
| `/aprender_pdf` → grafo | ✅ (PDF con texto; sin OCR aún) |

Pendiente conocido:

- Los feature flags por capa (`layers.*` en `CONFIGURACION/valeria_config.yaml`) todavía no los lee ningún módulo — hoy funcionan como documentación, no como interruptor real.
- Interfaces (Streamlit/API) no tienen tests automatizados.
- Multimodal (imagen/audio) normaliza a texto pero sin modelos de visión/audio reales conectados.
- PDF escaneados: falta OCR.
- Capa de análisis crítico del texto (propósito, tono, sesgos): planificada, separada del extractor de hechos.

---

## Licencia

Proyecto privado. Todos los derechos reservados.

---

**VALERIA 6.0** — *El pensamiento que se construye a sí mismo.*
