"""Ajustes de la interfaz gráfica, guardados en ajustes.json."""
import json
import os

RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ajustes.json")
HEURISTICAS_VALIDAS = ("mitad", "entropia", "aleatoria")
FONDOS_VALIDOS = ("noche", "atardecer", "oceano")
POR_DEFECTO = {
    "heuristica": "mitad",
    "limite": 20,
    "umbral": 3,
    "fondo": "noche",
    "razonamiento": True,
    "animaciones": True,
    "puntaje": True,
}


def cargar():
    ajustes = dict(POR_DEFECTO)
    try:
        with open(RUTA, encoding="utf-8") as archivo:
            guardados = json.load(archivo)
    except (OSError, ValueError):
        return ajustes
    for clave, valor in guardados.items():
        if clave in ajustes and type(valor) is type(ajustes[clave]):
            ajustes[clave] = valor
    if ajustes["heuristica"] not in HEURISTICAS_VALIDAS:
        ajustes["heuristica"] = POR_DEFECTO["heuristica"]
    if ajustes["fondo"] not in FONDOS_VALIDOS:
        ajustes["fondo"] = POR_DEFECTO["fondo"]
    ajustes["limite"] = max(1, min(40, ajustes["limite"]))
    ajustes["umbral"] = max(0, min(10, ajustes["umbral"]))
    return ajustes


def guardar(ajustes):
    try:
        with open(RUTA, "w", encoding="utf-8") as archivo:
            json.dump(ajustes, archivo, indent=2)
    except OSError:
        pass
