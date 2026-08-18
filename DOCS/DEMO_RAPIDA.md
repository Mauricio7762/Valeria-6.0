# Demo rápida VALERIA 6.0 (5–8 min)

## Arranque

```bash
cd /workspaces/Valeria-6.0
export PYTHONPATH=.
bash abrir_valeria.sh
# o: python -m streamlit run INTERFACES/STREAMLIT/app.py
```

Abrí el puerto **8501**.

## Guion

1. **Chat:** `¿qué es valeria?`
2. **Enseñar:** `el futsal es un deporte` → `¿qué es el futsal?`
3. **Estado:** botón Estado o `/estado`
4. **PDF:** subir PDF con texto → Enviar → `¿de qué trata el documento?`
5. **Grafo desde PDF:** `/promover` o mirar el toast (+N hechos)
6. **Imagen:** subir imagen + descripción → `¿qué es la imagen?`
7. **Holístico:** `/holistico`

## Checklist

- [ ] Responde sobre VALERIA con la semilla
- [ ] Aprende un hecho enseñado
- [ ] PDF genera chunks (`/rag`)
- [ ] Imagen reutiliza caption/descripción
- [ ] No hay keys en git
