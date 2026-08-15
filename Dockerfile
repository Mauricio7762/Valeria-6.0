# VALERIA 6.0 - Dockerfile base (Capa 0)
FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de configuración de dependencias
COPY pyproject.toml requirements.txt ./

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Crear directorios necesarios
RUN mkdir -p LOGS ALMACENAMIENTO/CACHE ALMACENAMIENTO/temp DATA/MEMORY

# Variables de entorno por defecto
ENV VALERIA_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000 8501

CMD ["python", "-m", "NUCLEO_BIOMIMETICO.orquestador_principal"]
