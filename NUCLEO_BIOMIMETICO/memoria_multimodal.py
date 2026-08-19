"""Memoria de varias entradas multimodales por nombre."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class EntradaMM:
    id: str
    tipo: str
    nombre: str
    caption: str = ""
    texto: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


class MemoriaMultimodal:
    def __init__(self, max_items: int = 30) -> None:
        self.max_items = max_items
        self.items: list[EntradaMM] = []

    def registrar(self, perc: dict[str, Any]) -> EntradaMM:
        tipo = str(perc.get("tipo") or "archivo")
        nombre = Path(str(perc.get("nombre") or perc.get("contenido") or "archivo")).name
        caption = str(perc.get("caption") or perc.get("transcripcion") or "").strip()
        texto = str(perc.get("texto_para_razonar") or perc.get("contenido") or "").strip()
        if not caption and "descripción del usuario:" in texto.lower():
            low = texto.lower()
            i = low.find("descripción del usuario:")
            caption = texto[i + len("descripción del usuario:") :].strip()
        ent = EntradaMM(
            id=f"{tipo}:{nombre}:{len(self.items)}",
            tipo=tipo,
            nombre=nombre,
            caption=caption,
            texto=texto,
            meta={k: perc.get(k) for k in ("mime", "caption_fuente", "provider") if perc.get(k)},
        )
        self.items.append(ent)
        if len(self.items) > self.max_items:
            self.items = self.items[-self.max_items :]
        return ent

    def ultima(self, tipo: str | None = None) -> EntradaMM | None:
        for it in reversed(self.items):
            if tipo is None or it.tipo == tipo:
                return it
        return None

    def buscar_por_nombre(self, consulta: str) -> EntradaMM | None:
        q = (consulta or "").lower()
        for it in sorted(self.items, key=lambda x: len(x.nombre), reverse=True):
            nom = it.nombre.lower()
            stem = Path(nom).stem.lower()
            if nom and nom in q:
                return it
            if stem and len(stem) > 2 and stem in q:
                return it
        m = re.search(r"(primera|1(?:era)?|segunda|2(?:da)?|última|ultima)\s+imagen", q)
        if m:
            imgs = [x for x in self.items if x.tipo == "imagen"]
            if not imgs:
                return None
            token = m.group(1)
            if token.startswith("prim") or token.startswith("1"):
                return imgs[0]
            if token.startswith("seg") or token.startswith("2"):
                return imgs[1] if len(imgs) > 1 else imgs[-1]
            return imgs[-1]
        return None

    def listar(self) -> str:
        if not self.items:
            return "No hay entradas multimodales en esta sesión."
        lineas = ["**Entradas multimodales de la sesión**", ""]
        for i, it in enumerate(self.items, 1):
            cap = (it.caption or "")[:80]
            lineas.append(f"{i}. `{it.nombre}` ({it.tipo})" + (f" — {cap}" if cap else ""))
        return "\n".join(lineas)
