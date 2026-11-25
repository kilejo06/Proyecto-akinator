"""Juega solo contra todos los candidatos y mide los resultados.

Uso: python pruebas/simulacion.py
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from base_conocimiento import MODOS, cargar_base
from main import jugar

SEMILLA = 42
REPETICIONES_CON_RUIDO = 5
PROB_NO_SE = 0.3
METODOS_SIMULADOS = (("Heurística mitad", "heuristica", "mitad"),
                     ("Heurística entropía", "heuristica", "entropia"),
                     ("Heurística aleatoria", "heuristica", "aleatoria"),
                     ("Encadenamiento adelante", "adelante", "mitad"),
                     ("Encadenamiento atrás", "atras", "mitad"))


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


def simular(modo, metodo, heuristica, repeticiones=1, prob_no_se=0.0, mentir=False):
    azar = random.Random(SEMILLA)
    random.seed(SEMILLA)
    base = cargar_base(modo)
    partidas = aciertos = preguntas = puntos = 0
    for secreto in base.candidatos:
        for _ in range(repeticiones):
            mentir_en = azar.randint(0, 5) if mentir else None
            responder = usuario_automatico(base, secreto, azar, prob_no_se, mentir_en)
            estado, _ = jugar(base, metodo, heuristica, responder, lambda c, s=secreto: c == s)
            partidas += 1
            aciertos += estado.acerto
            preguntas += estado.num_preguntas
            puntos += estado.puntos
    return {"aciertos": 100 * aciertos / partidas, "preguntas": preguntas / partidas,
            "puntos": puntos / partidas}


def imprimir_tabla(titulo, **opciones):
    print(f"\n{titulo}\n")
    print("| Modo | Método | % aciertos | Promedio preguntas | Puntaje promedio |")
    print("|---|---|---|---|---|")
    for modo in MODOS:
        for nombre, metodo, heuristica in METODOS_SIMULADOS:
            r = simular(modo, metodo, heuristica, **opciones)
            print(f"| {modo} | {nombre} | {r['aciertos']:.1f} | {r['preguntas']:.2f} | {r['puntos']:.1f} |")


def main():
    imprimir_tabla("Usuario sin errores")
    imprimir_tabla(f"Usuario que responde 'no sé' el {PROB_NO_SE:.0%} de las veces",
                   repeticiones=REPETICIONES_CON_RUIDO, prob_no_se=PROB_NO_SE)
    imprimir_tabla("Usuario que miente en una respuesta",
                   repeticiones=REPETICIONES_CON_RUIDO, mentir=True)


if __name__ == "__main__":
    main()
