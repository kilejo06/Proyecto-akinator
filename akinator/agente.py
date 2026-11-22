"""Estado, acciones y recompensas del agente."""

PUNTOS_ACIERTO = 100
PUNTOS_PREGUNTA = -2
PUNTOS_FALLO = -25
LIMITE_PREGUNTAS = 20

ACERTO = "acerto"
SIN_CANDIDATOS = "sin_candidatos"
SIN_PREGUNTAS_UTILES = "sin_preguntas_utiles"
LIMITE = "limite_de_preguntas"


class Estado:
    def __init__(self, nombres_candidatos, limite_preguntas=LIMITE_PREGUNTAS):
        self.hechos_conocidos = {}
        self.candidatos = list(nombres_candidatos)
        self.preguntas_hechas = []
        self.num_preguntas = 0
        self.puntos = 0
        self.limite_preguntas = limite_preguntas
        # sí = +1, no = -1, no sé = 0; para elegir la hipótesis más probable
        self.puntajes = {nombre: 0 for nombre in nombres_candidatos}
        self.acerto = False


def crear_estado(base, limite_preguntas=LIMITE_PREGUNTAS):
    return Estado(base.candidatos, limite_preguntas)


def registrar_pregunta(estado, atributo):
    estado.preguntas_hechas.append(atributo)
    estado.num_preguntas += 1
    estado.puntos += PUNTOS_PREGUNTA


def registrar_acierto(estado):
    estado.acerto = True
    estado.puntos += PUNTOS_ACIERTO


def registrar_fallo(estado, candidato):
    estado.puntos += PUNTOS_FALLO
    if candidato in estado.candidatos:
        estado.candidatos.remove(candidato)
    estado.puntajes.pop(candidato, None)


def atributos_utiles(estado, base):
    "Atributos sin preguntar que separan a los candidatos que quedan"
    if len(estado.candidatos) < 2:
        return []
    utiles = []
    for atributo in base.candidatos[estado.candidatos[0]]:
        if atributo in estado.preguntas_hechas or atributo in estado.hechos_conocidos:
            continue
        if len({base.candidatos[c][atributo] for c in estado.candidatos}) > 1:
            utiles.append(atributo)
    return utiles


def debe_parar(estado, base):
    "Devuelve el motivo de parada, o None si el juego sigue"
    if estado.acerto:
        return ACERTO
    if not estado.candidatos:
        return SIN_CANDIDATOS
    if estado.num_preguntas >= estado.limite_preguntas:
        return LIMITE
    if len(estado.candidatos) > 1 and not atributos_utiles(estado, base):
        return SIN_PREGUNTAS_UTILES
    return None
