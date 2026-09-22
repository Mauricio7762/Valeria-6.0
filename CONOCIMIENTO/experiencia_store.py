"""
Almacen simple de experiencia VALERIA (JSON).
Puede migrarse después a SQLite/NetworkX sin cambiar el esquema lógico.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class ExperienciaStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.data: dict[str, Any] = {
            "version": 1,
            "documentos": [],
            "conversaciones": [],
            "conceptos": [],
            "hechos": [],
            "tareas": [],
            "aristas": [],
        }
        if self.path.exists():
            self.load()

    def load(self) -> None:
        self.data = json.loads(self.path.read_text(encoding="utf-8"))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # --- altas ---
    def add_documento(self, titulo: str, origen: str = "pdf") -> str:
        did = _id("doc")
        self.data["documentos"].append(
            {"id": did, "titulo": titulo, "origen": origen, "fecha": _now()}
        )
        return did

    def add_conversacion(self, resumen: str) -> str:
        cid = _id("conv")
        self.data["conversaciones"].append(
            {"id": cid, "resumen": resumen, "fecha": _now()}
        )
        return cid

    def ensure_concepto(self, nombre: str) -> str:
        nombre_n = nombre.strip().lower()
        for c in self.data["conceptos"]:
            if c["nombre"].strip().lower() == nombre_n:
                return c["id"]
        cid = _id("concepto")
        self.data["conceptos"].append({"id": cid, "nombre": nombre.strip()})
        return cid

    def add_hecho(
        self,
        texto: str,
        fuente_id: str,
        fuente_tipo: str,
        conceptos: list[str] | None = None,
    ) -> str:
        hid = _id("hecho")
        self.data["hechos"].append(
            {
                "id": hid,
                "texto": texto.strip(),
                "fuente_id": fuente_id,
                "fuente_tipo": fuente_tipo,
            }
        )
        self.add_arista("EXTRAIDO_DE", hid, fuente_id)
        for nom in conceptos or []:
            cid = self.ensure_concepto(nom)
            self.add_arista("MENCIONA", hid, cid)
        return hid

    def add_tarea(self, descripcion: str) -> str:
        tid = _id("tarea")
        self.data["tareas"].append({"id": tid, "descripcion": descripcion.strip()})
        return tid

    def add_arista(self, tipo: str, desde: str, hasta: str) -> None:
        for a in self.data["aristas"]:
            if a["tipo"] == tipo and a["desde"] == desde and a["hasta"] == hasta:
                return
        self.data["aristas"].append({"tipo": tipo, "desde": desde, "hasta": hasta})

    # --- recuperación simple (keywords) ---
    def hechos_similares(self, texto: str, top_k: int = 5) -> list[dict]:
        tokens = set(re.findall(r"[a-záéíóúñü]{4,}", texto.lower()))
        scored = []
        for h in self.data["hechos"]:
            ht = set(re.findall(r"[a-záéíóúñü]{4,}", h["texto"].lower()))
            score = len(tokens & ht)
            if score:
                scored.append((score, h))
        scored.sort(key=lambda x: -x[0])
        return [h for _, h in scored[:top_k]]

    def hilo_para_tarea(self, descripcion_tarea: str, max_hechos: int = 5) -> list[dict]:
        """Recupera hechos relacionados a una tarea (por keywords + aristas SIRVE_PARA)."""
        base = self.hechos_similares(descripcion_tarea, top_k=max_hechos)
        # ampliar con SIRVE_PARA si hay tareas parecidas
        for t in self.data["tareas"]:
            if any(
                w in t["descripcion"].lower()
                for w in re.findall(r"[a-záéíóúñü]{5,}", descripcion_tarea.lower())
            ):
                for a in self.data["aristas"]:
                    if a["tipo"] == "SIRVE_PARA" and a["hasta"] == t["id"]:
                        h = self.get_hecho(a["desde"])
                        if h and h not in base:
                            base.append(h)
        return base[:max_hechos]

    def get_hecho(self, hid: str) -> dict | None:
        for h in self.data["hechos"]:
            if h["id"] == hid:
                return h
        return None

    def contexto_system(self, hechos: list[dict]) -> str:
        if not hechos:
            return ""
        lineas = ["Hechos de experiencia previa de VALERIA (usar si aplican):"]
        for h in hechos:
            lineas.append(f"- ({h.get('fuente_tipo', '?')}) {h['texto']}")
        return "\n".join(lineas)

    def enlazar_hecho_nuevo_con_previos(self, hecho_id: str, texto: str) -> list[str]:
        """Crea RELACIONADO_CON con hechos similares existentes."""
        vinculados = []
        for h in self.hechos_similares(texto, top_k=3):
            if h["id"] == hecho_id:
                continue
            self.add_arista("RELACIONADO_CON", hecho_id, h["id"])
            vinculados.append(h["id"])
        return vinculados
