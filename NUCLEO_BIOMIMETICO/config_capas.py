"""
Resolución de feature flags por capa (0-4)
============================================
Antes había dos fuentes de verdad que se contradecían y que además
nadie leía: `layers.layer_N_*` en valeria_config.yaml y `LAYER_N_ENABLED`
en .env. Este módulo las une en una sola función con precedencia clara:

    1. Variable de entorno LAYER_N_ENABLED (si está definida) — permite
       apagar una capa en un despliegue puntual sin tocar el YAML.
    2. Valor en CONFIGURACION/valeria_config.yaml (layers.layer_N_*).
    3. Si ninguna de las dos está definida: True (para no romper
       instalaciones viejas que no tengan la clave todavía).
"""

from __future__ import annotations

import os
from typing import Any

# número de capa -> clave correspondiente en el YAML (layers.*)
CLAVES_YAML: dict[int, str] = {
    0: "layer_0_fundacion",
    1: "layer_1_nucleo_glial",
    2: "layer_2_agentes_corticales",
    3: "layer_3_sistemas_avanzados",
    4: "layer_4_multimodal_interfaces",
}

NOMBRES: dict[int, str] = {
    0: "Fundación",
    1: "Núcleo + Sistema Glial",
    2: "Agentes Corticales",
    3: "Sistemas Avanzados (neurogénesis en background + analizador holístico)",
    4: "Multimodal + RAG",
}


def _parse_bool(valor: Any) -> bool | None:
    if isinstance(valor, bool):
        return valor
    if valor is None:
        return None
    s = str(valor).strip().lower()
    if s in ("1", "true", "si", "sí", "yes", "on"):
        return True
    if s in ("0", "false", "no", "off"):
        return False
    return None


def resolver_capas(config: dict[str, Any] | None) -> dict[int, bool]:
    """Devuelve {0: bool, 1: bool, ..., 4: bool} con la precedencia
    env > yaml > True descrita arriba."""
    layers_yaml = (config or {}).get("layers", {}) or {}
    resueltas: dict[int, bool] = {}
    for n, clave in CLAVES_YAML.items():
        env_val = _parse_bool(os.environ.get(f"LAYER_{n}_ENABLED"))
        if env_val is not None:
            resueltas[n] = env_val
            continue
        yaml_val = _parse_bool(layers_yaml.get(clave))
        resueltas[n] = yaml_val if yaml_val is not None else True
    return resueltas


def resumen_capas(layers: dict[int, bool]) -> str:
    lineas = []
    for n in sorted(layers):
        estado = "✅ ON" if layers[n] else "⛔ OFF"
        lineas.append(f"- Capa {n} — {NOMBRES.get(n, '?')}: {estado}")
    return "\n".join(lineas)
