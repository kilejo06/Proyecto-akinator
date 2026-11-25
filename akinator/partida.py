"""Partida paso a paso: quien la maneja decide cuándo llega cada respuesta."""
from agente import (ACERTO, LIMITE, LIMITE_PREGUNTAS, SIN_CANDIDATOS, adivinar, atributos_utiles,
                    crear_estado, debe_parar, elegir_hipotesis, procesar_respuesta)
from heuristica import HEURISTICAS
from motor_inferencia import encadenamiento_atras

METODOS = ("heuristica", "adelante", "atras")


def elegir_atributo(estado, base, metodo, heuristica, hipotesis):
    if metodo == "atras":
        return encadenamiento_atras(hipotesis, estado, base)
    if metodo == "adelante":
        utiles = atributos_utiles(estado, base)
        return utiles[0] if utiles else None
    return HEURISTICAS[heuristica](estado, base)


class Partida:
    def __init__(self, base, metodo="heuristica", heuristica="mitad", limite_preguntas=LIMITE_PREGUNTAS):
        self.base = base
        self.metodo = metodo
        self.heuristica = heuristica
        self.estado = crear_estado(base, limite_preguntas)
        self.accion = None
        self.motivo = None
        self.terminada = False
        self.motivo_intento = None

    def siguiente(self):
        """Devuelve la acción pendiente: preguntar, adivinar o fin."""
        if self.terminada:
            return self.accion
        motivo = debe_parar(self.estado, self.base)
        if motivo in (ACERTO, SIN_CANDIDATOS):
            return self.terminar(motivo)
        hipotesis = elegir_hipotesis(self.estado)
        atributo = None
        # Al llegar al límite se hace un último intento con la mejor hipótesis
        if motivo is None:
            atributo = elegir_atributo(self.estado, self.base, self.metodo, self.heuristica, hipotesis)
        self.motivo_intento = motivo
        if atributo is None:
            self.accion = {"tipo": "adivinar", "candidato": hipotesis}
        else:
            self.accion = {"tipo": "pregunta", "atributo": atributo,
                           "pregunta": self.base.preguntas[atributo]}
        return self.accion

    def responder(self, respuesta):
        """respuesta: 'si', 'no' o 'no_se'. Devuelve (reglas activadas, descartados)."""
        return procesar_respuesta(self.estado, self.base, self.accion["atributo"], respuesta)

    def confirmar(self, acerto):
        adivinar(self.estado, self.accion["candidato"], lambda _: acerto)
        if self.motivo_intento == LIMITE:
            self.terminar(ACERTO if acerto else LIMITE)
        return acerto

    def terminar(self, motivo):
        self.terminada = True
        self.motivo = debe_parar(self.estado, self.base) or motivo
        self.accion = {"tipo": "fin", "motivo": self.motivo}
        return self.accion
