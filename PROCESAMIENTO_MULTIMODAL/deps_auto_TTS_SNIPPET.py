# Agregar estas funciones a PROCESAMIENTO_MULTIMODAL/deps_auto.py

def asegurar_deps_tts_piper() -> dict:
    return asegurar_paquetes("tts_piper", (("piper", "piper-tts"),))


def asegurar_deps_tts_edge() -> dict:
    return asegurar_paquetes("tts_edge", (("edge_tts", "edge-tts"),))
