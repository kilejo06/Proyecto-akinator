"""Ejecuta los métodos sobre la misma instancia y resume sus métricas."""
import csv
import random

from agente import resumen_metricas
from automatico import usuario_automatico
from main import jugar

SEMILLA = 42
METODOS = (("Heurística mitad", "heuristica", "mitad", "Heur. mitad"),
           ("Heurística entropía", "heuristica", "entropia", "Heur. entropía"),
           ("Encadenamiento adelante", "adelante", "mitad", "Adelante"),
           ("Encadenamiento atrás", "atras", "mitad", "Atrás"))
PROMEDIADAS = ("preguntas", "puntaje", "tiempo", "nodos_generados", "reglas_evaluadas", "reglas_disparadas",
               "hechos_inferidos", "hipotesis_probadas", "max_candidatos", "max_hechos", "minimo_teorico")
COLUMNAS_CSV = ("metodo", "partidas", "aciertos", "optimas", "preguntas", "minimo_teorico", "tiempo_ms",
                "nodos_generados", "reglas_evaluadas", "reglas_disparadas", "hechos_inferidos",
                "hipotesis_probadas", "max_candidatos", "max_hechos", "puntaje")


def comparar_metodo(base, secretos, metodo, limite_preguntas, prob_no_se=0.0, mentir=False, repeticiones=1,
                    semilla=SEMILLA):
    """Juega un método contra cada secreto y devuelve el promedio de todas sus métricas."""
    nombre, clave, heuristica, corto = metodo
    azar = random.Random(semilla)
    partidas = aciertos = optimas = 0
    suma = dict.fromkeys(PROMEDIADAS, 0)
    for secreto in secretos:
        for _ in range(repeticiones):
            mentir_en = azar.randint(0, 5) if mentir else None
            responder = usuario_automatico(base, secreto, azar, prob_no_se, mentir_en)
            estado, motivo = jugar(base, clave, heuristica, responder, lambda c, s=secreto: c == s,
                                   limite_preguntas=limite_preguntas)
            resumen = resumen_metricas(estado, motivo)
            partidas += 1
            aciertos += resumen["encontro"]
            optimas += resumen["optima"]
            for columna in PROMEDIADAS:
                suma[columna] += resumen[columna]
    fila = {columna: valor / partidas for columna, valor in suma.items()}
    fila.update(metodo=nombre, corto=corto, partidas=partidas, aciertos=100 * aciertos / partidas,
                optimas=100 * optimas / partidas, tiempo_ms=fila["tiempo"] * 1000)
    return fila


def comparar(base, secretos, limite_preguntas, prob_no_se=0.0, mentir=False, repeticiones=1, semilla=SEMILLA):
    """Juega cada método contra cada secreto y devuelve una fila por método."""
    return [comparar_metodo(base, secretos, metodo, limite_preguntas, prob_no_se, mentir, repeticiones, semilla)
            for metodo in METODOS]


def guardar_csv(ruta, filas):
    with open(ruta, "w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(COLUMNAS_CSV)
        for fila in filas:
            escritor.writerow([f"{fila[c]:.3f}" if isinstance(fila[c], float) else fila[c] for c in COLUMNAS_CSV])
