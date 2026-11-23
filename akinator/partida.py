"""Partida paso a paso: quien la maneja decide cuándo llega cada respuesta."""
from agente import (ACERTO, LIMITE, LIMITE_PREGUNTAS, SIN_CANDIDATOS, adivinar, crear_estado,
                    debe_parar, elegir_hipotesis, procesar_respuesta)
from motor_inferencia import encadenamiento_atras

UMBRAL_ATRAS = 3


def elegir_atributo(estado, base, heuristica, hipotesis, umbral_atras):
    if len(estado.candidatos) <= umbral_atras:
        return encadenamiento_atras(hipotesis, estado, base)
    return heuristica(estado, base)


class Partida:
    def __init__(self, base, heuristica, limite_preguntas=LIMITE_PREGUNTAS, umbral_atras=UMBRAL_ATRAS):
        self.base = base
        self.heuristica = heuristica
        self.umbral_atras = umbral_atras
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
            atributo = elegir_atributo(self.estado, self.base, self.heuristica, hipotesis,
                                       self.umbral_atras)
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
