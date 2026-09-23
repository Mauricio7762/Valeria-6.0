"""
Generador del dataset para valeria_analisis_v4.
Formato de salida por ejemplo: PALABRAS_CLAVE / PRINCIPAL / SECUNDARIA(s) / NADA.

Este mismo SYS_IDEAS_V4 es el que hay que copiar LITERAL en la celda de
inferencia del notebook principal (pipeline_ideas), para que entrenamiento
e inferencia nunca se desincronicen.
"""
import json
from pathlib import Path

SYS_IDEAS_V4 = (
    "Analizá el texto en español. Respondé SOLO así:\n"
    "PALABRAS_CLAVE: <4 a 6 términos separados por coma>\n"
    "PRINCIPAL: <una oración>\n"
    "SECUNDARIA: <oración>\n"
    "Si es tapa, índice, bibliografía o no aporta: NADA.\n"
    "No inventes. Solo lo del texto."
)

def ej(texto, keywords, principal, secundarias=None):
    out = f"PALABRAS_CLAVE: {keywords}\nPRINCIPAL: {principal}"
    for s in (secundarias or []):
        out += f"\nSECUNDARIA: {s}"
    return {
        "instruction": f"Texto:\n{texto}\n\nExtraé ideas.",
        "system": SYS_IDEAS_V4,
        "output": out,
    }

def ej_nada(texto):
    return {"instruction": f"Texto:\n{texto}\n\nExtraé ideas.", "system": SYS_IDEAS_V4, "output": "NADA"}


DATASET = []

# ---------- Nivel 1: párrafos simples, una sola idea clara ----------
DATASET += [
    ej(
        "El reciclaje de plástico reduce la cantidad de residuos que terminan en "
        "rellenos sanitarios y océanos. Cada botella reprocesada evita que se fabrique "
        "una nueva desde cero, ahorrando petróleo y energía en el proceso.",
        "reciclaje, plástico, residuos, energía",
        "El reciclaje de plástico reduce residuos y ahorra recursos frente a fabricar plástico nuevo.",
        ["Reciclar una botella evita usar petróleo y energía adicionales."],
    ),
    ej(
        "Dormir menos de seis horas por noche de forma sostenida afecta la memoria y "
        "la capacidad de concentración al día siguiente. Los especialistas recomiendan "
        "mantener horarios regulares de sueño, incluso los fines de semana.",
        "sueño, memoria, concentración, horarios",
        "Dormir poco de forma sostenida perjudica la memoria y la concentración.",
        ["Mantener horarios de sueño regulares es la recomendación principal de los especialistas."],
    ),
    ej(
        "Las raíces de los árboles no solo absorben agua: también estabilizan el suelo "
        "y evitan la erosión en zonas de pendiente. Por eso, la deforestación en laderas "
        "suele derivar en derrumbes durante la temporada de lluvias.",
        "raíces, árboles, erosión, deforestación",
        "Las raíces de los árboles estabilizan el suelo y previenen la erosión.",
        ["Deforestar laderas aumenta el riesgo de derrumbes cuando llueve."],
    ),
    ej(
        "Un lenguaje de programación interpretado ejecuta el código línea por línea en "
        "tiempo real, sin necesidad de compilarlo antes. Esto facilita probar cambios "
        "rápido, aunque suele ser más lento que un programa ya compilado.",
        "interpretado, código, compilación, velocidad",
        "Un lenguaje interpretado ejecuta el código directamente, sin compilarlo antes.",
        ["Es más fácil de probar rápido pero más lento que un programa compilado."],
    ),
    ej(
        "El café retrasa la sensación de sueño porque bloquea los receptores de "
        "adenosina, la sustancia que el cerebro acumula a lo largo del día para "
        "señalar cansancio. Por eso tomarlo muy tarde puede complicar el descanso.",
        "café, adenosina, sueño, cerebro",
        "El café retrasa el sueño porque bloquea los receptores de adenosina en el cerebro.",
        ["Tomar café tarde en el día puede dificultar el descanso nocturno."],
    ),
]

# ---------- Nivel 2: párrafos con cita textual — la idea es una síntesis, NO la cita copiada ----------
DATASET += [
    ej(
        'El entrenador repitió varias veces durante la conferencia: "no hay equipo '
        'grande sin trabajo silencioso". Con esa frase buscaba explicar por qué '
        'prioriza los entrenamientos de resistencia por sobre las tácticas vistosas, '
        'algo que varios jugadores cuestionaron al principio de la temporada.',
        "entrenador, trabajo silencioso, resistencia, tácticas",
        "El entrenador defiende priorizar el trabajo de resistencia por sobre la táctica vistosa.",
        ["Algunos jugadores cuestionaron ese enfoque al comienzo de la temporada."],
    ),
    ej(
        'En su diario, la autora anotó: "hoy entendí que escribir no es encontrar las '
        'palabras correctas, sino animarse a las incorrectas primero". Esa idea marcó '
        'un quiebre en su forma de trabajar: dejó de corregir mientras escribía y '
        'empezó a separar el borrador de la revisión.',
        "escritura, borrador, revisión, proceso creativo",
        "La autora concluyó que escribir bien requiere primero animarse a escribir mal.",
        ["A partir de esa idea separó el momento de borrador del momento de revisión."],
    ),
    ej(
        'Un cartel a la entrada del taller advertía: "acá no se improvisa con la '
        'electricidad". La frase resumía la política del lugar: ningún aprendiz podía '
        'tocar una instalación sin que un electricista matriculado supervisara el '
        'trabajo paso a paso.',
        "taller, electricidad, seguridad, supervisión",
        "El taller exige que un electricista matriculado supervise todo trabajo eléctrico de los aprendices.",
        ["La política de seguridad no permite que nadie improvise con instalaciones eléctricas."],
    ),
]

# ---------- Nivel 3: enumeraciones repetitivas — la salida tiene que sintetizar, no listar ----------
DATASET += [
    ej(
        "Mal alimentados, mal pagados, mal dormidos, mal atendidos: así describía el "
        "informe las condiciones de los trabajadores temporarios en la cosecha. Mal, "
        "mal y mal, insistía el texto, como si repetir la palabra bastara para que "
        "alguien finalmente actuara al respecto.",
        "trabajadores temporarios, condiciones laborales, cosecha, informe",
        "El informe denuncia las malas condiciones laborales de los trabajadores temporarios de la cosecha.",
        ["La repetición insistente busca que finalmente se tomen medidas al respecto."],
    ),
    ej(
        "Ruido, ruido y más ruido: eso es lo único que el vecino reportó a la "
        "administración durante meses, sin obtener respuesta. Ruido de obra, ruido de "
        "música, ruido de motores, ruido a cualquier hora, detallaba cada reclamo, "
        "cada vez con menos esperanza de que lo escucharan.",
        "ruido, vecino, reclamos, administración",
        "Un vecino reclamó durante meses por el ruido constante sin recibir respuesta de la administración.",
        ["Los reclamos detallaban distintas fuentes de ruido a toda hora, cada vez con menos esperanza."],
    ),
    ej(
        "Cansado, cansado, siempre cansado. Así se sentía después de cada turno "
        "doble: cansado al llegar, cansado al irse, cansado incluso los días libres, "
        "hasta que decidió pedir que le redujeran las horas.",
        "cansancio, turno doble, trabajo, decisión",
        "El cansancio acumulado por los turnos dobles lo llevó a pedir que le redujeran las horas de trabajo.",
        ["Sentía el mismo cansancio constante incluso en los días libres."],
    ),
]

# ---------- Nivel 4: párrafos con dos ideas claras (principal + secundaria real) ----------
DATASET += [
    ej(
        "La biblioteca del barrio amplió su horario los sábados, algo que los vecinos "
        "venían pidiendo hace tiempo. Además, sumó una sala de lectura silenciosa "
        "separada del sector infantil, para que los chicos puedan hacer ruido sin "
        "molestar a quienes estudian.",
        "biblioteca, horario, sala silenciosa, sector infantil",
        "La biblioteca del barrio amplió su horario de atención los sábados por pedido de los vecinos.",
        ["Se creó una sala de lectura silenciosa separada del sector infantil."],
    ),
    ej(
        "El equipo de desarrollo decidió migrar la base de datos a un motor más "
        "moderno para mejorar los tiempos de respuesta. En paralelo, aprovecharon el "
        "cambio para documentar por primera vez toda la arquitectura del sistema.",
        "base de datos, migración, documentación, arquitectura",
        "El equipo migró la base de datos a un motor más moderno para mejorar los tiempos de respuesta.",
        ["Aprovecharon la migración para documentar la arquitectura completa del sistema."],
    ),
]

# ---------- Nivel 5: NADA — tapa, índice, bibliografía, fragmentos sin contenido ----------
DATASET += [
    ej_nada("ÍNDICE\n\nCapítulo 1 ................ 9\nCapítulo 2 ................ 34\nCapítulo 3 ................ 58"),
    ej_nada("Primera edición: marzo de 2019\nISBN 978-84-000-0000-0\nImpreso en España"),
    ej_nada(
        "BIBLIOGRAFÍA\n\nGarcía, J. (2015). Introducción al tema. Madrid: Editorial X.\n"
        "Pérez, M. (2018). Estudios complementarios. Buenos Aires: Editorial Y."
    ),
    ej_nada("© Todos los derechos reservados. Queda prohibida la reproducción total o parcial de esta obra sin autorización."),
    ej_nada("Página en blanco intencionalmente."),
]

# ---------- Nivel 6: distractores — mucho texto de relleno alrededor de una sola idea ----------
DATASET += [
    ej(
        "Era una tarde como cualquier otra, el sol pegaba fuerte y la calle estaba "
        "vacía a esa hora. Nadie caminaba, ni un auto pasaba, todo parecía detenido. "
        "En medio de ese silencio, el técnico terminó de explicar que el corte de luz "
        "del barrio se debía a una sobrecarga en el transformador principal, no a un "
        "problema en las casas particulares. Después de eso, siguió el silencio, la "
        "calle vacía, la tarde que no cambiaba.",
        "corte de luz, transformador, sobrecarga, técnico",
        "El corte de luz del barrio se debió a una sobrecarga en el transformador principal, no en las casas.",
        [],
    ),
]

path = Path("/mnt/user-data/outputs/dataset_valeria_analisis_v4.jsonl")
path.parent.mkdir(parents=True, exist_ok=True)
with path.open("w", encoding="utf-8") as f:
    for row in DATASET:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

print(f"OK: {len(DATASET)} ejemplos escritos en {path}")
