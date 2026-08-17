"""
Normalizador de entradas multimodales
=====================================
Convierte texto / imagen / audio en una representación unificada
para Percepción → Razonamiento. Sin modelos pesados: metadatos +
texto derivado (nombre, tamaño, caption manual).
"""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any


class NormalizadorEntrada:
    """
    tipos soportados:
      - texto
      - imagen (archivo o bytes + nombre)
      - audio (archivo o bytes + nombre)
    """

    def normalizar_texto(self, texto: str, idioma: str = "es") -> dict[str, Any]:
        t = (texto or "").strip()
        return {
            "tipo": "texto",
            "contenido": t,
            "texto_para_razonar": t,
            "longitud": len(t),
            "idioma": idioma,
            "modalidades": ["texto"],
        }

    def normalizar_imagen(
        self,
        *,
        nombre: str = "imagen",
        tamaño_bytes: int = 0,
        caption: str | None = None,
        ruta: str | None = None,
        mime: str | None = None,
    ) -> dict[str, Any]:
        mime = mime or mimetypes.guess_type(nombre)[0] or "image/unknown"
        partes = [
            f"[Imagen recibida: {nombre}]",
            f"tipo={mime}",
            f"tamaño={tamaño_bytes} bytes",
        ]
        if ruta:
            partes.append(f"ruta={ruta}")
        if caption:
            partes.append(f"descripción del usuario: {caption}")
        else:
            partes.append(
                "sin descripción visual automática aún "
                "(Capa 4: se puede conectar CLIP/visión más adelante)"
            )
        texto = " ".join(partes)
        return {
            "tipo": "imagen",
            "contenido": caption or nombre,
            "texto_para_razonar": texto,
            "nombre": nombre,
            "mime": mime,
            "tamaño_bytes": tamaño_bytes,
            "ruta": ruta,
            "caption": caption,
            "modalidades": ["imagen", "texto"] if caption else ["imagen"],
        }

    def normalizar_audio(
        self,
        *,
        nombre: str = "audio",
        tamaño_bytes: int = 0,
        transcripcion: str | None = None,
        ruta: str | None = None,
        mime: str | None = None,
    ) -> dict[str, Any]:
        mime = mime or mimetypes.guess_type(nombre)[0] or "audio/unknown"
        partes = [
            f"[Audio recibido: {nombre}]",
            f"tipo={mime}",
            f"tamaño={tamaño_bytes} bytes",
        ]
        if transcripcion:
            partes.append(f"transcripción: {transcripcion}")
        else:
            partes.append(
                "sin transcripción automática aún "
                "(Capa 4: se puede conectar Whisper más adelante)"
            )
        texto = " ".join(partes)
        return {
            "tipo": "audio",
            "contenido": transcripcion or nombre,
            "texto_para_razonar": texto,
            "nombre": nombre,
            "mime": mime,
            "tamaño_bytes": tamaño_bytes,
            "ruta": ruta,
            "transcripcion": transcripcion,
            "modalidades": ["audio", "texto"] if transcripcion else ["audio"],
        }

    def desde_upload(
        self,
        nombre: str,
        datos: bytes,
        caption: str | None = None,
        guardar_en: Path | None = None,
    ) -> dict[str, Any]:
        mime = mimetypes.guess_type(nombre)[0] or ""
        ruta = None
        if guardar_en is not None:
            guardar_en.mkdir(parents=True, exist_ok=True)
            dest = guardar_en / Path(nombre).name
            dest.write_bytes(datos)
            ruta = str(dest)

        if mime.startswith("image/"):
            auto = None
            fuente = None
            if not caption:
                try:
                    from PROCESAMIENTO_MULTIMODAL.vision_caption import caption_imagen
                    res = caption_imagen(datos, mime=mime or "image/jpeg")
                    auto = res.get("caption")
                    fuente = res.get("fuente")
                    if not auto and res.get("info_basica"):
                        auto = res["info_basica"]
                except Exception:
                    pass
            final_cap = caption or auto
            out = self.normalizar_imagen(
                nombre=nombre,
                tamaño_bytes=len(datos),
                caption=final_cap,
                ruta=ruta,
                mime=mime,
            )
            if fuente:
                out["caption_fuente"] = fuente
            out["caption_manual"] = bool(caption)
            return out
        if mime.startswith("audio/"):
            return self.normalizar_audio(
                nombre=nombre,
                tamaño_bytes=len(datos),
                transcripcion=caption,  # caption como transcripción manual
                ruta=ruta,
                mime=mime,
            )
        # fallback: tratar como texto si es .txt
        if nombre.lower().endswith(".txt"):
            try:
                return self.normalizar_texto(datos.decode("utf-8", errors="replace"))
            except Exception:
                pass
        return self.normalizar_texto(
            caption or f"Archivo recibido: {nombre} ({len(datos)} bytes, {mime or 'tipo desconocido'})"
        )
