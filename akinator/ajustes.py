"""Ajustes de la interfaz gráfica, guardados en ajustes.json."""
import json
import os

RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ajustes.json")
METODOS_VALIDOS = ("heuristica", "adelante", "atras")
HEURISTICAS_VALIDAS = ("mitad", "entropia")
FONDOS_VALIDOS = ("noche", "atardecer", "oceano")
POR_DEFECTO = {
    "metodo": "heuristica",
    "heuristica": "mitad",
    "limite": 20,
    "fondo": "noche",
    "razonamiento": True,
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
    if ajustes["metodo"] not in METODOS_VALIDOS:
        ajustes["metodo"] = POR_DEFECTO["metodo"]
    if ajustes["heuristica"] not in HEURISTICAS_VALIDAS:
        ajustes["heuristica"] = POR_DEFECTO["heuristica"]
    if ajustes["fondo"] not in FONDOS_VALIDOS:
        ajustes["fondo"] = POR_DEFECTO["fondo"]
    ajustes["limite"] = max(1, min(40, ajustes["limite"]))
    return ajustes


def guardar(ajustes):
    try:
        with open(RUTA, "w", encoding="utf-8") as archivo:
            json.dump(ajustes, archivo, indent=2)
    except OSError:
        pass
