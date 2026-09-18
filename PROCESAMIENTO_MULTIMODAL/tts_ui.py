"""
Reproducción automática de TTS en Streamlit (sin botón Play).
=============================================================
Uso en el chat, después de mostrar la respuesta de texto:

    from PROCESAMIENTO_MULTIMODAL.tts_ui import hablar_auto
    st.markdown(respuesta)
    hablar_auto(respuesta)

Variables:
  VALERIA_TTS_AUTO=1   (default activo si no se define; poné 0 para silenciar)
"""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

try:
    import streamlit as st
except ImportError:
    st = None  # type: ignore


def _auto_enabled() -> bool:
    return (os.environ.get("VALERIA_TTS_AUTO") or "1").strip() not in (
        "0",
        "false",
        "False",
        "no",
        "off",
    )


def hablar_auto(texto: str, *, mostrar_player: bool = False) -> dict[str, Any]:
    """
    Genera audio y lo reproduce solo en la página (autoplay).
    Si mostrar_player=True, también deja el control st.audio visible.
    """
    if not _auto_enabled():
        return {"ok": False, "skipped": True, "reason": "VALERIA_TTS_AUTO desactivado"}

    if st is None:
        return {"ok": False, "error": "streamlit no instalado"}

    texto = (texto or "").strip()
    if not texto:
        return {"ok": False, "error": "Texto vacío"}

    try:
        from PROCESAMIENTO_MULTIMODAL.tts_local import sintetizar
    except ImportError as e:
        return {"ok": False, "error": f"tts_local no disponible: {e}"}

    r = sintetizar(texto)
    if not r.get("ok") or not r.get("path"):
        return r

    path = Path(r["path"])
    try:
        data = path.read_bytes()
    except Exception as e:
        return {"ok": False, "error": f"No se pudo leer audio: {e}", **r}

    suffix = path.suffix.lower()
    mime = "audio/wav" if suffix == ".wav" else "audio/mp3"
    b64 = base64.b64encode(data).decode("ascii")

    # Autoplay oculto: suena solo, sin pedir Play
    st.markdown(
        f"""
        <audio autoplay playsinline style="display:none">
          <source src="data:{mime};base64,{b64}" type="{mime}">
        </audio>
        """,
        unsafe_allow_html=True,
    )

    if mostrar_player:
        st.audio(data, format=mime)

    return {**r, "autoplay": True, "bytes": len(data)}
