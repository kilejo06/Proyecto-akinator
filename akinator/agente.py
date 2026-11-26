"""Estado, acciones y recompensas del agente."""
import math

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
        self.ultimas_evaluadas = []
        self.candidatos_iniciales = len(self.candidatos)
        self.metricas = {
            "reglas_evaluadas": 0, "reglas_disparadas": 0, "hechos_inferidos": 0,
            "nodos_generados": 0, "hipotesis_probadas": 0,
            "max_candidatos": len(self.candidatos), "max_hechos": 0, "tiempo": 0.0,
        }


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
    estado.hechos_conocidos, activadas, evaluadas = encadenamiento_adelante(estado.hechos_conocidos, base.reglas)
    metricas = estado.metricas
    metricas["reglas_evaluadas"] += len(evaluadas)
    estado.ultimas_evaluadas = evaluadas
    metricas["reglas_disparadas"] += len(activadas)
    metricas["hechos_inferidos"] += len(activadas)
    metricas["max_hechos"] = max(metricas["max_hechos"], len(estado.hechos_conocidos))
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
    "Atributos sin preguntar que separan a los candidatos que quedan; lo que concluye una regla no se pregunta"
    if len(estado.candidatos) < 2:
        return []
    deducidos = {regla["entonces"] for regla in base.reglas}
    utiles = []
    for atributo in base.candidatos[estado.candidatos[0]]:
        if atributo in deducidos or atributo in estado.preguntas_hechas or atributo in estado.hechos_conocidos:
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


def resumen_metricas(estado, motivo):
    """Todas las métricas de la partida en un solo diccionario."""
    minimo = math.ceil(math.log2(estado.candidatos_iniciales)) if estado.candidatos_iniciales > 1 else 0
    return {**estado.metricas, "preguntas": estado.num_preguntas, "puntaje": estado.puntos,
            "minimo_teorico": minimo, "optima": estado.acerto and estado.num_preguntas <= minimo,
            "encontro": estado.acerto, "motivo": motivo}
