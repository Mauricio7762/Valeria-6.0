"""
VALERIA 6.0 — Interfaz Streamlit
================================
Chat con historial, atajos, estado y exportación.

Uso:
  streamlit run INTERFACES/STREAMLIT/app.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
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

HISTORIAL_PATH = ROOT / "DATA" / "MEMORY" / "episodica" / "chat_ui.json"


def _run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
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


def _cargar_historial_disco() -> list[dict]:
    if not HISTORIAL_PATH.exists():
        return []
    try:
        data = json.loads(HISTORIAL_PATH.read_text(encoding="utf-8"))
        return list(data.get("messages", []))[-100:]
    except (json.JSONDecodeError, OSError):
        return []


def _guardar_historial_disco(messages: list[dict]) -> None:
    HISTORIAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated": datetime.utcnow().isoformat() + "Z",
        "messages": messages[-100:],
    }
    tmp = HISTORIAL_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(HISTORIAL_PATH)


def _mensaje_bienvenida() -> dict:
    return {
        "role": "assistant",
        "content": (
            "Hola. Soy **VALERIA 6.0**.\n\n"
            "Preguntame algo, enseñame un hecho («X es parte de Y») "
            "o usá los atajos del panel izquierdo."
        ),
    }


def main() -> None:
    st.set_page_config(
        page_title="VALERIA 6.0",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Estilo suave
    st.markdown(
        """
        <style>
        .stChatMessage { max-width: 900px; }
        div[data-testid="stSidebar"] { min-width: 280px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("🧠 VALERIA 6.0")
    st.caption("Cerebro Humano Digital — Chat · Meta · Curiosidad · Neurogénesis")

    orch = get_orquestador()

    if "messages" not in st.session_state:
        disc = _cargar_historial_disco()
        st.session_state.messages = disc if disc else [_mensaje_bienvenida()]
    if "pending_cmd" not in st.session_state:
        st.session_state.pending_cmd = None

    # ----- Sidebar -----
    with st.sidebar:
        st.header("Sistema")
        st.success(f"Consciencia: **{orch.estado_consciencia}**")

        c1, c2 = st.columns(2)
        if orch.gestor_recursos:
            try:
                r = orch.gestor_recursos.obtener_estado()
                c1.metric("CPU", f"{r['cpu_percent']:.0f}%")
                c2.metric("RAM", f"{r['ram_percent']:.0f}%")
            except Exception:
                c1.caption("CPU n/d")
                c2.caption("RAM n/d")

        raz = orch._agente("razonamiento")
        mem = orch._agente("memoria")
        if raz:
            g = raz.estado().get("grafo") or {}
            st.metric("Hechos (grafo)", g.get("total_hechos", 0))
        if mem:
            st.metric("Episodios", mem.estado().get("episodica", 0))

        st.divider()
        st.subheader("Atajos")
        atajos = [
            ("Estado", "/estado"),
            ("Hechos", "/hechos"),
            ("Grafo", "/grafo"),
            ("Memoria", "/memoria"),
            ("Plan", "/plan"),
            ("Ajustes", "/ajustes"),
            ("Reflexión", "/reflexion"),
            ("Curiosidad", "/curiosidad"),
            ("Neurogénesis", "/neurogenesis"),
            ("Holístico", "/holistico"),
            ("Ayuda", "/ayuda"),
        ]
        cols = st.columns(2)
        for i, (label, cmd) in enumerate(atajos):
            if cols[i % 2].button(label, use_container_width=True, key=f"btn_{label}"):
                st.session_state.pending_cmd = cmd

        st.divider()
        orch._debug = st.toggle("Debug (pasos internos)", value=orch._debug)

        b1, b2 = st.columns(2)
        if b1.button("Limpiar chat", use_container_width=True):
            st.session_state.messages = [_mensaje_bienvenida()]
            _guardar_historial_disco(st.session_state.messages)
            st.rerun()
        if b2.button("Guardar chat", use_container_width=True):
            _guardar_historial_disco(st.session_state.messages)
            st.toast("Historial guardado en disco")

        # Export
        export = "\n\n".join(
            f"**{m['role']}:** {m['content']}" for m in st.session_state.messages
        )
        st.download_button(
            "Exportar chat (.md)",
            data=export,
            file_name=f"valeria_chat_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=True,
        )

        with st.expander("Ayuda de comandos"):
            st.markdown(AYUDA)

        st.caption("VALERIA 6.0 · UI Streamlit")

    # ----- Chat -----
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_text = None
    if st.session_state.pending_cmd:
        user_text = st.session_state.pending_cmd
        st.session_state.pending_cmd = None
    else:
        user_text = st.chat_input("Mensaje o comando (/estado, /holistico…)")

    if not user_text:
        return

    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        with st.spinner("Pensando…"):
            try:
                cmd = _run(manejar_comando(orch, user_text))
                if cmd is not None:
                    respuesta = cmd if cmd else "_(sin salida)_"
                else:
                    respuesta = _run(procesar_mensaje(orch, user_text))
            except Exception as e:
                respuesta = f"**Error:** `{type(e).__name__}: {e}`"
        st.markdown(respuesta)

    st.session_state.messages.append({"role": "assistant", "content": respuesta})
    try:
        _guardar_historial_disco(st.session_state.messages)
    except Exception:
        pass
    st.rerun()


if __name__ == "__main__":
    main()
