"""
Agente Planificación (Prefrontal)
==================================
Objetivos a largo plazo y descomposición de tareas en pasos concretos.

A diferencia de la versión anterior (una plantilla fija de 4 pasos
genéricos para cualquier objetivo), este agente:

1. Reconoce el verbo principal del objetivo ("aprender", "armar",
   "revisar", "probar", "investigar", etc.) y genera pasos orientados
   a esa acción en particular.
2. Si el objetivo tiene varias partes conectadas por "y"/"luego"/
   "después" (ej: "aprender X y armar Y"), las separa y arma pasos
   para cada una.
3. Persiste los objetivos en disco (JSON), así sobreviven a que se
   reinicie el proceso — igual que el grafo de conocimiento.
4. Permite marcar pasos como completados y consultar el estado.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

from .base_agente import BaseAgente

# Repo root: AGENTES_CORTICALES/agente_planificacion.py -> parent.parent
_ROOT = Path(__file__).resolve().parent.parent
_RUTA_OBJETIVOS_DEFAULT = _ROOT / "DATA" / "MEMORY" / "planificacion" / "objetivos.json"

# Separadores entre sub-metas dentro de un mismo objetivo
_CONECTORES = re.compile(
    r"\s*(?:,\s*y\s+|,\s*|\s+y\s+|\s+luego\s+(?:de\s+)?|\s+despu[eé]s\s+(?:de\s+)?)\s*",
    re.IGNORECASE,
)

# Pasos orientados según el verbo principal del objetivo/sub-meta
_PLANTILLAS_VERBO: dict[str, list[str]] = {
    "aprender": [
        "Reunir información o fuentes sobre {tema}",
        "Extraer los hechos clave y enseñárselos a VALERIA",
        "Verificar con una pregunta de prueba que quedó bien aprendido",
    ],
    "armar": [
        "Definir qué partes necesita {tema}",
        "Construir una primera versión simple",
        "Probarla y ajustar lo que falle",
    ],
    "crear": [
        "Definir qué partes necesita {tema}",
        "Construir una primera versión simple",
        "Probarla y ajustar lo que falle",
    ],
    "construir": [
        "Definir qué partes necesita {tema}",
        "Construir una primera versión simple",
        "Probarla y ajustar lo que falle",
    ],
    "revisar": [
        "Revisar {tema} en detalle",
        "Anotar los problemas encontrados",
        "Corregir lo prioritario primero",
    ],
    "probar": [
        "Preparar el escenario de prueba para {tema}",
        "Ejecutar la prueba",
        "Registrar el resultado y qué ajustar",
    ],
    "corregir": [
        "Identificar la causa del problema en {tema}",
        "Aplicar la corrección",
        "Verificar que quedó resuelto",
    ],
    "investigar": [
        "Buscar información confiable sobre {tema}",
        "Comparar y quedarse con lo más relevante",
        "Resumir la conclusión",
    ],
    "organizar": [
        "Listar todo lo que compone {tema}",
        "Agruparlo por prioridad o categoría",
        "Definir el orden de trabajo",
    ],
    "entrenar": [
        "Preparar el dataset para {tema}",
        "Correr el entrenamiento",
        "Evaluar el resultado",
    ],
    "escribir": [
        "Armar un esquema/borrador de {tema}",
        "Escribir el contenido completo",
        "Releer y pulir",
    ],
    "diseñar": [
        "Definir los requisitos de {tema}",
        "Bocetar/armar una primera versión",
        "Ajustar según feedback",
    ],
    "mejorar": [
        "Identificar qué de {tema} anda peor hoy",
        "Aplicar el cambio",
        "Comparar antes/después",
    ],
}

_PLANTILLA_DEFAULT = [
    "Analizar {tema}",
    "Recuperar conocimiento relevante",
    "Generar pasos de acción concretos",
    "Ejecutar y monitorear",
]

_VERBOS_RE = re.compile(
    r"^(?:quiero|necesito|me\s+gustar[ií]a)?\s*"
    r"(aprender|armar|crear|construir|revisar|probar|corregir|investigar|"
    r"organizar|entrenar|escribir|dise[ñn]ar|mejorar)\b\s*(.*)$",
    re.IGNORECASE,
)


def _sub_metas(objetivo: str) -> list[str]:
    partes = [p.strip() for p in _CONECTORES.split(objetivo) if p.strip()]
    return partes or [objetivo.strip()]


def _pasos_para(sub_meta: str) -> list[str]:
    m = _VERBOS_RE.match(sub_meta.strip())
    if m:
        verbo = m.group(1).lower()
        tema = (m.group(2) or sub_meta).strip() or sub_meta
        plantilla = _PLANTILLAS_VERBO.get(verbo, _PLANTILLA_DEFAULT)
        return [p.format(tema=tema) for p in plantilla]
    return [p.format(tema=sub_meta) for p in _PLANTILLA_DEFAULT]


class AgentePlanificacion(BaseAgente):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__("Planificacion", config)
        self.objetivos: list[dict[str, Any]] = []
        self.plan_actual: list[str] = []

        self._ruta_persistencia = Path(
            (self.config or {}).get("ruta_objetivos", _RUTA_OBJETIVOS_DEFAULT)
        )
        n = self._cargar()
        logger.debug(
            f"Planificacion: {n} objetivo(s) cargados desde {self._ruta_persistencia}"
        )

    # ---------- Persistencia (JSON en disco) ----------
    def _guardar(self) -> None:
        ruta = self._ruta_persistencia
        ruta.parent.mkdir(parents=True, exist_ok=True)
        tmp = ruta.with_suffix(ruta.suffix + ".tmp")
        tmp.write_text(
            json.dumps({"objetivos": self.objetivos}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(ruta)  # escritura atómica

    def _cargar(self) -> int:
        ruta = self._ruta_persistencia
        if not ruta.exists():
            return 0
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except Exception:
            return 0
        self.objetivos = datos.get("objetivos") or []
        return len(self.objetivos)

    async def procesar(self, mensaje: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "error": "disabled"}

        accion = mensaje.get("accion", "estado")

        if accion == "nuevo_objetivo":
            resultado = self._nuevo_objetivo(mensaje.get("objetivo") or "")
        elif accion == "listar":
            resultado = self._listar()
        elif accion == "completar_paso":
            resultado = self._completar_paso(mensaje.get("indice"))
        elif accion == "estado":
            resultado = {
                "ok": True,
                "objetivos_activos": len(
                    [o for o in self.objetivos if o.get("estado") != "completado"]
                ),
                "plan_actual": self.plan_actual,
            }
        else:
            resultado = {"ok": True, "msg": "Planificación en espera"}

        self._mensajes_procesados += 1
        self._ultimo_resultado = resultado
        return resultado

    def _nuevo_objetivo(self, objetivo: str) -> dict[str, Any]:
        objetivo = objetivo.strip()
        if not objetivo:
            return {"ok": False, "error": "objetivo vacío"}

        sub_metas = _sub_metas(objetivo)
        pasos: list[dict[str, Any]] = []
        for sm in sub_metas:
            for texto_paso in _pasos_para(sm):
                pasos.append({"texto": texto_paso, "hecho": False})

        entrada = {
            "objetivo": objetivo,
            "estado": "pendiente",
            "creado": datetime.now(timezone.utc).isoformat(),
            "pasos": pasos,
        }
        self.objetivos.append(entrada)
        self.plan_actual = [p["texto"] for p in pasos]
        self._guardar()

        return {
            "ok": True,
            "indice": len(self.objetivos) - 1,
            "objetivo_agregado": objetivo,
            "sub_metas": sub_metas,
            "plan": self.plan_actual,
        }

    def _listar(self) -> dict[str, Any]:
        return {
            "ok": True,
            "objetivos": [
                {
                    "indice": i,
                    "objetivo": o["objetivo"],
                    "estado": o["estado"],
                    "pasos": o["pasos"],
                }
                for i, o in enumerate(self.objetivos)
            ],
        }

    def _completar_paso(self, indice: Any) -> dict[str, Any]:
        try:
            i = int(indice)
        except (TypeError, ValueError):
            return {"ok": False, "error": "Decime el número de objetivo, ej: /completar 0"}
        if i < 0 or i >= len(self.objetivos):
            return {"ok": False, "error": f"No existe el objetivo #{indice}"}

        obj = self.objetivos[i]
        siguiente = next((p for p in obj["pasos"] if not p["hecho"]), None)
        if siguiente is None:
            return {
                "ok": False,
                "error": f'El objetivo "{obj["objetivo"]}" ya estaba completo.',
            }

        siguiente["hecho"] = True
        obj["estado"] = (
            "completado" if all(p["hecho"] for p in obj["pasos"]) else "en_progreso"
        )
        self._guardar()

        return {
            "ok": True,
            "objetivo": obj["objetivo"],
            "paso_completado": siguiente["texto"],
            "estado": obj["estado"],
            "pasos_restantes": sum(1 for p in obj["pasos"] if not p["hecho"]),
        }

    async def tick(self) -> None:
        await super().tick()

    def estado(self) -> dict[str, Any]:
        base = super().estado()
        base["objetivos_totales"] = len(self.objetivos)
        base["objetivos_activos"] = len(
            [o for o in self.objetivos if o.get("estado") != "completado"]
        )
        return base
