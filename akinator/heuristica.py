"""Elegir la mejor pregunta."""
import math

from agente import atributos_utiles


def contar_division(atributo, nombres, datos, pesos=None):
    si = no = 0
    for nombre in nombres:
        peso = pesos.get(nombre, 1) if pesos else 1
        if datos[nombre][atributo]:
            si += peso
        else:
            no += peso
    return si, no


def entropia(si, no):
    p = si / (si + no)
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


def heuristica_mitad(estado, base, pesos=None):
    utiles = atributos_utiles(estado, base)
    if not utiles:
        return None
    estado.metricas["nodos_generados"] += len(utiles)

    def desbalance(atributo):
        si, no = contar_division(atributo, estado.candidatos, base.candidatos, pesos)
        return abs(si - no)

    return min(utiles, key=desbalance)


def heuristica_entropia(estado, base, pesos=None):
    utiles = atributos_utiles(estado, base)
    if not utiles:
        return None
    estado.metricas["nodos_generados"] += len(utiles)

    def ganancia(atributo):
        si, no = contar_division(atributo, estado.candidatos, base.candidatos, pesos)
        return entropia(si, no)

    return max(utiles, key=ganancia)


HEURISTICAS = {
    "mitad": heuristica_mitad,
    "entropia": heuristica_entropia,
}
