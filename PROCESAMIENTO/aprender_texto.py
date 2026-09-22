"""
Pipeline: texto/PDF-extraído → hechos (modelo o reglas) → grafo de experiencia.
El modelo extractor se conecta después; acá está el esqueleto + parseo de salida.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

# Ajustá el import según dónde copies el módulo en el repo
try:
    from CONOCIMIENTO.experiencia_store import ExperienciaStore
except ImportError:
    from experiencia_store import ExperienciaStore


SYSTEM_EXTRACTOR = (
    "Extraé hechos concretos del texto. "
    "Cada hecho en una línea con el formato: "
    "HECHO: <oración breve> | CONCEPTOS: <a, b> "
    "Solo español. No inventes. Si no hay hechos, respondé NADA."
)


def parse_salida_extractor(texto_modelo: str) -> list[dict]:
    """Parsea líneas HECHO: ... | CONCEPTOS: a, b"""
    hechos = []
    for line in (texto_modelo or "").splitlines():
        line = line.strip()
        if not line.upper().startswith("HECHO:"):
            # fallback: línea con aspecto de hecho corto
            if len(line) > 20 and not line.startswith("NADA"):
                hechos.append({"texto": line, "conceptos": []})
            continue
        rest = line[6:].strip()
        conceptos: list[str] = []
        if "| CONCEPTOS:" in rest.upper() or "| CONCEPTOS:" in rest:
            # split case-insensitive
            parts = re.split(r"\|\s*CONCEPTOS:\s*", rest, flags=re.I)
            rest = parts[0].strip()
            if len(parts) > 1:
                conceptos = [c.strip() for c in parts[1].split(",") if c.strip()]
        if rest and rest.upper() != "NADA":
            hechos.append({"texto": rest, "conceptos": conceptos})
    return hechos


def aprender_de_texto(
    store: ExperienciaStore,
    texto: str,
    titulo: str,
    origen: str = "pdf",
    extractor_fn: Callable[[str], str] | None = None,
) -> dict:
    """
    extractor_fn(prompt_usuario) -> salida cruda del modelo.
    Si es None, usa heurística por oraciones (solo para pruebas sin GPU).
    """
    doc_id = store.add_documento(titulo=titulo, origen=origen)

    if extractor_fn is None:
        # Heurística débil: oraciones largas como "hechos" candidatos
        crudo = ""
        for sent in re.split(r"(?<=[.!?])\s+", texto):
            sent = sent.strip()
            if len(sent) > 40:
                crudo += f"HECHO: {sent} | CONCEPTOS: \n"
        if not crudo:
            crudo = "NADA"
    else:
        user = f"Texto:\n{texto[:4000]}\n\nExtraé los hechos."
        crudo = extractor_fn(user)

    items = parse_salida_extractor(crudo)
    creados = []
    for it in items:
        hid = store.add_hecho(
            texto=it["texto"],
            fuente_id=doc_id,
            fuente_tipo="documento",
            conceptos=it.get("conceptos") or [],
        )
        links = store.enlazar_hecho_nuevo_con_previos(hid, it["texto"])
        creados.append({"hecho_id": hid, "vinculos": links, "texto": it["texto"]})

    store.save()
    return {"documento_id": doc_id, "hechos": creados, "raw": crudo}


def contexto_para_chat(store: ExperienciaStore, consulta: str) -> str:
    hechos = store.hilo_para_tarea(consulta, max_hechos=5)
    return store.contexto_system(hechos)


if __name__ == "__main__":
    # Demo sin modelo
    root = Path(__file__).resolve().parents[1]
    path = root / "CONOCIMIENTO" / "base_experiencia_demo.json"
    store = ExperienciaStore(path)
    # cargar semilla si existe
    seed = root / "CONOCIMIENTO" / "base_experiencia_semilla.json"
    if seed.exists() and not path.exists():
        store.path = path
        store.data = __import__("json").loads(seed.read_text(encoding="utf-8"))
        store.save()

    texto = (
        "La asertividad permite expresar necesidades con respeto. "
        "Escuchar antes de responder mejora el clima del equipo."
    )
    out = aprender_de_texto(store, texto, titulo="nota_demo", origen="texto")
    print(out)
    print(contexto_para_chat(store, "cómo dar una devolución clara"))
