# Cómo correr VALERIA 6.0

## Requisitos

- Python **3.11+**
- pip

## Instalación mínima

Desde la **raíz del repositorio**:

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

pip install -r requirements.txt
```

Si el install completo falla, lo esencial:

```bash
pip install loguru rich pyyaml psutil pydantic pytest pytest-asyncio streamlit fastapi "uvicorn[standard]"
```

## 1. Chat en terminal

```bash
export PYTHONPATH=.
python -m NUCLEO_BIOMIMETICO.orquestador_principal
```

Comandos: `/ayuda` `/estado` `/hechos` `/holistico` `/salir`

## 2. Interfaz Streamlit (UI)

```bash
export PYTHONPATH=.
streamlit run INTERFACES/STREAMLIT/app.py
```

URL por defecto: http://localhost:8501  
En Codespaces: abrí el puerto **8501**.

## 3. API HTTP (FastAPI)

```bash
export PYTHONPATH=.
uvicorn INTERFACES.API.main:app --host 0.0.0.0 --port 8000
```

- Docs interactivos: http://localhost:8000/docs  
- Salud: `GET /salud`  
- Chat:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"mensaje":"¿qué es valeria?"}'
```

| Método | Ruta | Uso |
|--------|------|-----|
| GET | `/salud` | Ping |
| GET | `/estado` | Estado |
| GET | `/hechos` | Grafo |
| GET | `/ayuda` | Comandos |
| POST | `/chat` | Mensaje o comando |

## 4. Tests

```bash
export PYTHONPATH=.
pytest TESTS/ -q
```

CI en cada push a `main`: `.github/workflows/tests.yml`

## Estructura

| Ruta | Rol |
|------|-----|
| `NUCLEO_BIOMIMETICO/` | Orquestador, glía, pipeline |
| `AGENTES_CORTICALES/` | Agentes + razonamiento |
| `SISTEMAS_AVANZADOS/` | Meta, curiosidad, neurogénesis |
| `INTERFACES/` | Streamlit + API |
| `DATA/MEMORY/` | Persistencia |
| `CONFIGURACION/` | YAML |
| `TESTS/` | Pytest |

## Demo rápida (2 min)

1. `¿qué es valeria?`
2. `¿qué función tiene la microglía?`
3. `el futsal es un deporte`
4. `/hechos` · `/estado` · `/holistico`

## Notas

- Redis/Chroma **no** son necesarios en el modo actual.
- La semilla de conocimiento se carga al iniciar el razonamiento.
- Las **preguntas** no se guardan como hechos; las **afirmaciones** sí.
