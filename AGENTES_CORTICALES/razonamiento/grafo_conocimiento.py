"""
Grafo de Conocimiento
=====================
Almacén de hechos (sujeto, relación, objeto) en memoria, con índice
por sujeto y por relación para consultas rápidas. Es la base sobre la
que operan los motores de inferencia deductiva y abductiva.

No depende de ChromaDB/Redis: pensado para correr en Termux sin
servicios externos. Persiste a un archivo JSON simple en disco.
"""

from __future__ import annotations

import json
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


def normalizar(texto: str) -> str:
    """minúsculas, sin tildes/diacríticos, espacios recortados — para que
    'microglía' y 'microglia' (o 'MICROGLIA') apunten al mismo nodo."""
    texto = texto.strip().lower()
    descompuesto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


@dataclass(frozen=True)
class Hecho:
    sujeto: str
    relacion: str
    objeto: str
    confianza: float = 1.0
    origen: str = "base"  # "base" | "usuario" | "inferido"

    def as_tupla(self) -> tuple[str, str, str]:
        return (self.sujeto, self.relacion, self.objeto)


class GrafoConocimiento:
    def __init__(self) -> None:
        self._hechos: list[Hecho] = []
        # Índices para consulta O(1) por sujeto y por relación
        self._por_sujeto: dict[str, list[Hecho]] = {}
        self._por_relacion: dict[str, list[Hecho]] = {}

    def agregar_hecho(
        self,
        sujeto: str,
        relacion: str,
        objeto: str,
        confianza: float = 1.0,
        origen: str = "usuario",
    ) -> Hecho:
        sujeto = normalizar(sujeto)
        relacion = normalizar(relacion)
        objeto = normalizar(objeto)

        existente = self.buscar(sujeto, relacion, objeto)
        if existente:
            return existente[0]

        hecho = Hecho(sujeto, relacion, objeto, confianza, origen)
        self._hechos.append(hecho)
        self._por_sujeto.setdefault(sujeto, []).append(hecho)
        self._por_relacion.setdefault(relacion, []).append(hecho)
        return hecho

    def buscar(
        self,
        sujeto: str | None = None,
        relacion: str | None = None,
        objeto: str | None = None,
    ) -> list[Hecho]:
        candidatos = self._hechos
        if sujeto is not None:
            candidatos = self._por_sujeto.get(normalizar(sujeto), [])
        elif relacion is not None:
            candidatos = self._por_relacion.get(normalizar(relacion), [])

        resultado = candidatos
        if relacion is not None:
            r = normalizar(relacion)
            resultado = [h for h in resultado if h.relacion == r]
        if objeto is not None:
            o = normalizar(objeto)
            resultado = [h for h in resultado if h.objeto == o]
        return resultado

    def relacionados(self, sujeto: str) -> list[Hecho]:
        return list(self._por_sujeto.get(normalizar(sujeto), []))

    def existe(self, sujeto: str) -> bool:
        return normalizar(sujeto) in self._por_sujeto

    def total_hechos(self) -> int:
        return len(self._hechos)

    def estado(self) -> dict[str, Any]:
        return {
            "total_hechos": len(self._hechos),
            "sujetos_distintos": len(self._por_sujeto),
            "relaciones_distintas": len(self._por_relacion),
        }

    # ---------- Persistencia (JSON en disco) ----------
    def guardar(self, ruta: str | Path) -> None:
        ruta = Path(ruta)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        datos = {"hechos": [asdict(h) for h in self._hechos]}
        tmp = ruta.with_suffix(ruta.suffix + ".tmp")
        tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(ruta)  # escritura atómica: evita corromper el archivo si se corta a mitad

    def cargar(self, ruta: str | Path) -> int:
        """Carga hechos desde disco (suma a lo que ya haya en memoria). Devuelve cuántos agregó."""
        ruta = Path(ruta)
        if not ruta.exists():
            return 0
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return 0

        agregados = 0
        for h in datos.get("hechos", []):
            antes = self.total_hechos()
            self.agregar_hecho(
                h.get("sujeto", ""),
                h.get("relacion", ""),
                h.get("objeto", ""),
                confianza=h.get("confianza", 1.0),
                origen=h.get("origen", "usuario"),
            )
            if self.total_hechos() > antes:
                agregados += 1
        return agregados
