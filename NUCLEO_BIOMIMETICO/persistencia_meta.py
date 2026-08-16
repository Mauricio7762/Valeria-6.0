"""
Persistencia de metacognición y curiosidad entre sesiones.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
_RUTA = _ROOT / "DATA" / "MEMORY" / "semantica" / "meta_estado.json"


def guardar_estado_meta(ajuste: Any, curiosidad: Any, ruta: Path | None = None) -> None:
    path = ruta or _RUTA
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "pesos": dict(ajuste.prefs.pesos),
        "umbral_pedir_ensenanza": ajuste.prefs.umbral_pedir_ensenanza,
        "total_ajustes": ajuste.prefs.total_ajustes,
        "recompensa_total": curiosidad.recompensa.total,
    }
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def cargar_estado_meta(ajuste: Any, curiosidad: Any, ruta: Path | None = None) -> bool:
    path = ruta or _RUTA
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    pesos = data.get("pesos") or {}
    for k, v in pesos.items():
        try:
            ajuste.prefs.pesos[k] = float(v)
        except (TypeError, ValueError):
            pass
    if "umbral_pedir_ensenanza" in data:
        try:
            ajuste.prefs.umbral_pedir_ensenanza = float(data["umbral_pedir_ensenanza"])
        except (TypeError, ValueError):
            pass
    if "total_ajustes" in data:
        try:
            ajuste.prefs.total_ajustes = int(data["total_ajustes"])
        except (TypeError, ValueError):
            pass
    if "recompensa_total" in data:
        try:
            curiosidad.recompensa.total = float(data["recompensa_total"])
        except (TypeError, ValueError):
            pass
    return True
