# API VALERIA 6.0

```bash
export PYTHONPATH=.
pip install fastapi "uvicorn[standard]" loguru rich pyyaml psutil
uvicorn INTERFACES.API.main:app --host 0.0.0.0 --port 8000
```

Abrí http://localhost:8000/docs

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/salud` | Ping |
| GET | `/estado` | Estado del sistema |
| GET | `/hechos` | Grafo resumido |
| GET | `/ayuda` | Comandos |
| POST | `/chat` | `{"mensaje":"..."}` |
