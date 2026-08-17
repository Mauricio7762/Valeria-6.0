"""RAG liviano: PDF → chunks → recuperación por palabras clave."""

from .ingesta_pdf import IngestaPDF
from .almacen_chunks import AlmacenChunks
from .retriever import RetrieverRAG

__all__ = ["IngestaPDF", "AlmacenChunks", "RetrieverRAG"]
