# Grafo de experiencia de VALERIA

No guarda biografías del usuario como “vida de VALERIA”.
Guarda **lo que ella aprendió** de documentos y conversaciones, y **cómo se conecta**.

## Tipos de nodo

| Tipo | Campos mínimos | Ejemplo |
|------|----------------|---------|
| `Documento` | id, titulo, origen, fecha | PDF M3 comunicación |
| `Conversacion` | id, resumen, fecha | chat sobre no sonar a tutorial |
| `Hecho` | id, texto, fuente_id, fuente_tipo | "asertividad = decir sin agredir" |
| `Concepto` | id, nombre | asertividad, liderazgo |
| `Tarea` | id, descripcion | explicar algo con claridad |

## Tipos de arista

| Relación | De → A | Uso |
|----------|--------|-----|
| `EXTRAIDO_DE` | Hecho → Documento/Conversacion | procedencia |
| `MENCIONA` | Hecho → Concepto | indexar temas |
| `RELACIONADO_CON` | Hecho → Hecho | mismo tema, matiz, ejemplo |
| `ACLARA` | Hecho → Hecho | uno precisa al otro |
| `EJEMPLIFICA` | Hecho → Hecho | caso concreto |
| `CONTRASTA` | Hecho → Hecho | tensión / opuesto |
| `SIRVE_PARA` | Hecho/Concepto → Tarea | transferencia a una tarea |
| `PREPARA_PARA` | Concepto → Concepto | cadena de aprendizaje |

## Experiencia = camino

```text
Documento_A ─EXTRAIDO_DE─ Hecho_1 ─RELACIONADO_CON─ Hecho_2 ─SIRVE_PARA─ Tarea_X
                 ↑
            Conversacion_B
```

Al pedir una tarea, se recupera un **hilo** (2–6 nodos) y se inyecta al system del chat v16.

## IDs sugeridos

- `doc_...` `conv_...` `hecho_...` `concepto_...` `tarea_...`
- ISO fecha en cada alta.

## Qué no hacer

- No inventar hechos no presentes en la fuente.
- No mezclar “opinión del chat” con hecho citado sin marcar `fuente_tipo=conversacion`.
- No unificar extractor + personalidad en un solo LoRA.
