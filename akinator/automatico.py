"""Usuario simulado y partidas completas sin intervención."""
import random

from partida import Partida


def usuario_automatico(base, secreto, azar, prob_no_se=0.0, mentir_en=None):
    contador = {"preguntas": 0}

    def responder(atributo, _pregunta):
        numero = contador["preguntas"]
        contador["preguntas"] += 1
        if azar.random() < prob_no_se:
            return "no_se"
        verdad = base.candidatos[secreto][atributo]
        return "si" if verdad != (numero == mentir_en) else "no"

    return responder


def jugar_automatico(base, secreto, metodo, heuristica, limite_preguntas, prob_no_se=0.0, mentir_en=None,
                     semilla=42):
    """Juega una partida completa sin usuario y devuelve la Partida con su historial."""
    responder = usuario_automatico(base, secreto, random.Random(semilla), prob_no_se, mentir_en)
    partida = Partida(base, metodo, heuristica, limite_preguntas)
    while True:
        accion = partida.siguiente()
        if accion["tipo"] == "fin":
            return partida
        if accion["tipo"] == "adivinar":
            partida.confirmar(accion["candidato"] == secreto)
        else:
            partida.responder(responder(accion["atributo"], accion["pregunta"]))
