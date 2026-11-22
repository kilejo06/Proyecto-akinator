"""Estado, acciones y recompensas del agente."""
from motor_inferencia import encadenamiento_adelante, filtrar_candidatos

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


def elegir_hipotesis(estado):
    return min(estado.candidatos, key=lambda c: (-estado.puntajes[c], c))


def procesar_respuesta(estado, base, atributo, respuesta):
    """respuesta: 'si', 'no' o 'no_se'. Devuelve (reglas activadas, candidatos descartados)."""
    registrar_pregunta(estado, atributo)
    if respuesta == "no_se":
        return [], []
    valor = respuesta == "si"
    estado.hechos_conocidos[atributo] = valor
    for candidato in estado.candidatos:
        estado.puntajes[candidato] += 1 if base.candidatos[candidato][atributo] == valor else -1
    estado.hechos_conocidos, activadas = encadenamiento_adelante(estado.hechos_conocidos, base.reglas)
    estado.candidatos, descartados = filtrar_candidatos(estado.candidatos, base.candidatos, estado.hechos_conocidos)
    return activadas, descartados


def adivinar(estado, candidato, confirmar):
    """confirmar(candidato) -> bool; separa la lógica del juego de input/print."""
    acerto = confirmar(candidato)
    if acerto:
        registrar_acierto(estado)
    else:
        registrar_fallo(estado, candidato)
    return acerto


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
