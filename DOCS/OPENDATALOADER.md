# OpenDataLoader PDF (opcional)

Mejora la extracción de texto de PDFs complejos (columnas, tablas).

## Instalación en Codespaces

```bash
# Java 11+
sudo apt-get update && sudo apt-get install -y openjdk-17-jre-headless
java -version

pip install -U opendataloader-pdf pypdf
```

## Comportamiento en VALERIA

1. Intenta **opendataloader-pdf**
2. Si falla o no está instalado → **pypdf**
3. Si ambos fallan → 0 chunks (PDF vacío o solo imagen sin OCR)

No hace falta clonar el repo de GitHub; es una dependencia PyPI.

## Verificar

Tras subir un PDF en Streamlit, el toast muestra `motor=opendataloader` o `motor=pypdf`.
