.PHONY: help install install-dev lint test run clean docker-build docker-run

help:
	@echo "VALERIA 6.0 - Comandos disponibles:"
	@echo "  make install       Instalar dependencias base"
	@echo "  make install-dev   Instalar con dependencias de desarrollo"
	@echo "  make lint          Ejecutar linter (ruff)"
	@echo "  make test          Ejecutar tests"
	@echo "  make run           Ejecutar orquestador principal"
	@echo "  make clean         Limpiar archivos temporales"
	@echo "  make docker-build  Construir imagen Docker"
	@echo "  make docker-run    Ejecutar contenedor"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

lint:
	ruff check .
	ruff format --check .

test:
	pytest TESTS/ -v --cov=. --cov-report=term-missing

run:
	python -m NUCLEO_BIOMIMETICO.orquestador_principal

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .coverage htmlcov/

docker-build:
	docker build -t valeria-6.0:latest -f DOCKER/Dockerfile .

docker-run:
	docker run --rm -it --env-file .env -p 8000:8000 -p 8501:8501 valeria-6.0:latest
