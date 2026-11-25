"""Juega solo contra todos los candidatos y mide los resultados.

Uso: python pruebas/simulacion.py
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from agente import resumen_metricas
from automatico import usuario_automatico
from base_conocimiento import MODOS, cargar_base
from main import jugar

SEMILLA = 42
REPETICIONES_CON_RUIDO = 5
PROB_NO_SE = 0.3
METODOS_SIMULADOS = (("Heurística mitad", "heuristica", "mitad"),
                     ("Heurística entropía", "heuristica", "entropia"),
                     ("Encadenamiento adelante", "adelante", "mitad"),
                     ("Encadenamiento atrás", "atras", "mitad"))


CLAVES = ("preguntas", "puntaje", "tiempo", "nodos_generados", "reglas_evaluadas", "reglas_disparadas",
          "hechos_inferidos", "hipotesis_probadas", "max_candidatos", "max_hechos")


def simular(modo, metodo, heuristica, repeticiones=1, prob_no_se=0.0, mentir=False):
    azar = random.Random(SEMILLA)
    base = cargar_base(modo)
    partidas = aciertos = optimas = 0
    suma = dict.fromkeys(CLAVES, 0)
    for secreto in base.candidatos:
        for _ in range(repeticiones):
            mentir_en = azar.randint(0, 5) if mentir else None
            responder = usuario_automatico(base, secreto, azar, prob_no_se, mentir_en)
            estado, motivo = jugar(base, metodo, heuristica, responder, lambda c, s=secreto: c == s)
            resumen = resumen_metricas(estado, motivo)
            partidas += 1
            aciertos += resumen["encontro"]
            optimas += resumen["optima"]
            for clave in CLAVES:
                suma[clave] += resumen[clave]
    promedios = {clave: valor / partidas for clave, valor in suma.items()}
    promedios["tiempo"] *= 1000
    return {"aciertos": 100 * aciertos / partidas, "optimas": 100 * optimas / partidas, **promedios}


def imprimir_tabla(titulo, **opciones):
    resultados = [(modo, nombre, simular(modo, metodo, heuristica, **opciones))
                  for modo in MODOS for nombre, metodo, heuristica in METODOS_SIMULADOS]
    print(f"\n{titulo}\n")
    print("| Modo | Método | % aciertos | % óptimas | Preguntas | Puntaje | Tiempo (ms) |")
    print("|---|---|---|---|---|---|---|")
    for modo, nombre, r in resultados:
        print(f"| {modo} | {nombre} | {r['aciertos']:.1f} | {r['optimas']:.1f} | {r['preguntas']:.2f} "
              f"| {r['puntaje']:.1f} | {r['tiempo']:.2f} |")
    print("\n| Modo | Método | Nodos generados | Reglas evaluadas | Reglas disparadas | Hechos inferidos "
          "| Hipótesis probadas | Memoria (candidatos / hechos) |")
    print("|---|---|---|---|---|---|---|---|")
    for modo, nombre, r in resultados:
        print(f"| {modo} | {nombre} | {r['nodos_generados']:.1f} | {r['reglas_evaluadas']:.1f} "
              f"| {r['reglas_disparadas']:.1f} | {r['hechos_inferidos']:.1f} | {r['hipotesis_probadas']:.1f} "
              f"| {r['max_candidatos']:.0f} / {r['max_hechos']:.1f} |")


def main():
    imprimir_tabla("Usuario sin errores")
    imprimir_tabla(f"Usuario que responde 'no sé' el {PROB_NO_SE:.0%} de las veces",
                   repeticiones=REPETICIONES_CON_RUIDO, prob_no_se=PROB_NO_SE)
    imprimir_tabla("Usuario que miente en una respuesta",
                   repeticiones=REPETICIONES_CON_RUIDO, mentir=True)


if __name__ == "__main__":
    main()
