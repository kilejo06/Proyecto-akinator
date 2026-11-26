"""Juega solo contra todos los candidatos y mide los resultados.

Uso: python pruebas/simulacion.py
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from base_conocimiento import MODOS, cargar_base
from comparacion import comparar

LIMITE = 20
REPETICIONES_CON_RUIDO = 5
PROB_NO_SE = 0.3


def imprimir_tabla(titulo, **opciones):
    resultados = []
    for modo in MODOS:
        base = cargar_base(modo)
        resultados += [(modo, fila) for fila in comparar(base, list(base.candidatos), LIMITE, **opciones)]
    print(f"\n{titulo}\n")
    print("| Modo | Método | % aciertos | % óptimas | Preguntas | Puntaje | Tiempo (ms) |")
    print("|---|---|---|---|---|---|---|")
    for modo, r in resultados:
        print(f"| {modo} | {r['metodo']} | {r['aciertos']:.1f} | {r['optimas']:.1f} | {r['preguntas']:.2f} "
              f"| {r['puntaje']:.1f} | {r['tiempo_ms']:.2f} |")
    print("\n| Modo | Método | Nodos generados | Reglas evaluadas | Reglas disparadas | Hechos inferidos "
          "| Hipótesis probadas | Memoria (candidatos / hechos) |")
    print("|---|---|---|---|---|---|---|---|")
    for modo, r in resultados:
        print(f"| {modo} | {r['metodo']} | {r['nodos_generados']:.1f} | {r['reglas_evaluadas']:.1f} "
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
