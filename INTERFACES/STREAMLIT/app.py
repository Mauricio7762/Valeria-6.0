"""
VALERIA 6.0 — Interfaz Streamlit
================================
Chat, estado del sistema y accesos rápidos a comandos.

Uso:
  pip install streamlit
  streamlit run INTERFACES/STREAMLIT/app.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from NUCLEO_BIOMIMETICO.orquestador_principal import OrquestadorPrincipal
from NUCLEO_BIOMIMETICO.chat_comandos import manejar_comando, AYUDA
from NUCLEO_BIOMIMETICO.pipeline_mensaje import procesar_mensaje
from NUCLEO_BIOMIMETICO.gestor_recursos import GestorRecursos
from NUCLEO_BIOMIMETICO.SISTEMA_GLIAL.sistema_glial import SistemaGlial
from AGENTES_CORTICALES.coordinador_agentes import CoordinadorAgentes


def _run(coro):
    """Ejecuta corrutinas desde Streamlit (thread principal)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Streamlit a veces ya tiene loop: usar otro
            return asyncio.run(coro)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@st.cache_resource
def get_orquestador() -> OrquestadorPrincipal:
    orch = OrquestadorPrincipal()
    orch.config = orch._cargar_config()
    orch.gestor_recursos = GestorRecursos(orch.config.get("resources", {}))
    orch.sistema_glial = SistemaGlial(orch.config.get("sistema_glial", {}))
    orch.coordinador = CoordinadorAgentes(orch.config.get("agentes", {}))
    raz = orch.coordinador.agentes.get("razonamiento")
    if raz is not None:
        raz.neurogenesis = orch.neurogenesis
    orch.estado_consciencia = "despierto"
    orch.running = True
    return orch


def main() -> None:
    st.set_page_config(
        page_title="VALERIA 6.0",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🧠 VALERIA 6.0")
    st.caption("Cerebro Humano Digital — Chat · Meta · Curiosidad · Neurogénesis")

    orch = get_orquestador()

    # Sidebar
    with st.sidebar:
        st.header("Sistema")
        st.write(f"**Consciencia:** {orch.estado_consciencia}")
        if orch.gestor_recursos:
            try:
                r = orch.gestor_recursos.obtener_estado()
                st.metric("CPU", f"{r['cpu_percent']:.0f}%")
                st.metric("RAM", f"{r['ram_percent']:.0f}%")
            except Exception:
                pass

        raz = orch._agente("razonamiento")
        if raz:
            g = raz.estado().get("grafo") or {}
            st.metric("Hechos en grafo", g.get("total_hechos", 0))

        st.divider()
        st.subheader("Atajos")
        col1, col2 = st.columns(2)
        atajos = {
            "Estado": "/estado",
            "Hechos": "/hechos",
            "Grafo": "/grafo",
            "Memoria": "/memoria",
            "Ajustes": "/ajustes",
            "Reflexión": "/reflexion",
            "Curiosidad": "/curiosidad",
            "Neurogénesis": "/neurogenesis",
            "Holístico": "/holistico",
            "Ayuda": "/ayuda",
        }
        if "pending_cmd" not in st.session_state:
            st.session_state.pending_cmd = None

        keys = list(atajos.keys())
        for i, label in enumerate(keys):
            target = col1 if i % 2 == 0 else col2
            if target.button(label, use_container_width=True, key=f"btn_{label}"):
                st.session_state.pending_cmd = atajos[label]

        st.divider()
        st.checkbox("Debug (pasos internos)", key="debug_ui", value=orch._debug)
        orch._debug = st.session_state.get("debug_ui", False)

        with st.expander("Ayuda de comandos"):
            st.markdown(AYUDA)

    # Historial de chat
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Hola. Soy **VALERIA 6.0**. "
                    "Preguntame algo, enseñame un hecho "
                    "(«X es parte de Y») o usá los atajos del panel."
                ),
            }
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Entrada: atajo pendiente o chat input
    user_text = None
    if st.session_state.pending_cmd:
        user_text = st.session_state.pending_cmd
        st.session_state.pending_cmd = None
    else:
        user_text = st.chat_input("Escribí un mensaje o comando (/estado, /holistico…)")

    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        with st.chat_message("assistant"):
            with st.spinner("Pensando…"):
                try:
                    cmd = _run(manejar_comando(orch, user_text))
                    if cmd is not None:
                        respuesta = cmd if cmd else "_(comando sin salida)_"
                    else:
                        respuesta = _run(procesar_mensaje(orch, user_text))
                except Exception as e:
                    respuesta = f"Error: `{e}`"
            st.markdown(respuesta)

        st.session_state.messages.append({"role": "assistant", "content": respuesta})
        st.rerun()


if __name__ == "__main__":
    main()
