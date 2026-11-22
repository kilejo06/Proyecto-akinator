"""Entrada del usuario e impresión de la traza."""

RESPUESTAS = {
    "si": "si", "sí": "si", "s": "si",
    "no": "no", "n": "no",
    "no se": "no_se", "no sé": "no_se", "ns": "no_se",
}
TEXTO_RESPUESTA = {"si": "sí", "no": "no", "no_se": "no sé"}


def leer_respuesta(texto):
    return RESPUESTAS.get(texto.strip().lower())


def nombre_legible(nombre):
    return nombre.replace("_", " ")


def pedir_respuesta(pregunta):
    while True:
        respuesta = leer_respuesta(input(f"{pregunta} (sí / no / no sé): "))
        if respuesta:
            return respuesta
        print("No entendí, responde sí, no o no sé.")


def pedir_opcion(titulo, opciones):
    print(f"\n{titulo}")
    for numero, texto in enumerate(opciones, 1):
        print(f"  {numero}. {texto}")
    while True:
        eleccion = input("Opción: ").strip()
        if eleccion.isdigit() and 1 <= int(eleccion) <= len(opciones):
            return int(eleccion) - 1
        print("Opción no válida.")


def pedir_si_no(pregunta):
    while True:
        respuesta = leer_respuesta(input(f"{pregunta} (sí / no): "))
        if respuesta in ("si", "no"):
            return respuesta == "si"
        print("Responde sí o no.")


def confirmar_adivinanza(candidato):
    return pedir_si_no(f"¿Estás pensando en {nombre_legible(candidato)}?")


def texto_regla(regla):
    return f"{regla['id']} ({' y '.join(regla['si'])} -> {regla['entonces']})"


def imprimir_traza(estado, base, atributo, respuesta, activadas, descartados):
    print(f"\nPregunta {estado.num_preguntas}: {base.preguntas[atributo]}  -> {TEXTO_RESPUESTA[respuesta]}")
    if activadas:
        print("Reglas activadas: " + "; ".join(texto_regla(r) for r in activadas))
    if descartados:
        print("Descartados: " + ", ".join(nombre_legible(c) for c in descartados))
    restantes = ", ".join(nombre_legible(c) for c in estado.candidatos)
    print(f"Candidatos restantes ({len(estado.candidatos)}): {restantes}")
    print(f"Puntaje actual: {estado.puntos}\n")
