"""Carga los JSON y guarda hechos y reglas."""
import json
import os

from motor_inferencia import encadenamiento_adelante

CARPETA_DATOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")
MODOS = ("animales", "paises", "mixto")


class BaseConocimiento:
    def __init__(self, modo, candidatos, reglas, preguntas):
        self.modo = modo
        self.candidatos = candidatos
        self.reglas = reglas
        self.preguntas = preguntas


def leer_json(nombre):
    with open(os.path.join(CARPETA_DATOS, nombre), encoding="utf-8") as archivo:
        return json.load(archivo)


def completar_candidato(hechos, atributos, reglas):
    # Mundo cerrado: lo no definido es False; lo no deducido también
    completo = {a: bool(hechos.get(a, False)) for a in atributos}
    completo, _ = encadenamiento_adelante(completo, reglas)
    for regla in reglas:
        completo.setdefault(regla["entonces"], False)
    return completo


def cargar_base(modo):
    if modo not in MODOS:
        raise ValueError(f"Modo desconocido '{modo}'. Opciones: {', '.join(MODOS)}")

    candidatos, reglas = {}, []
    if modo in ("animales", "mixto"):
        candidatos.update(leer_json("animales.json"))
        reglas += leer_json("reglas_animales.json")
    if modo in ("paises", "mixto"):
        candidatos.update(leer_json("paises.json"))
        reglas += leer_json("reglas_paises.json")

    atributos = list(dict.fromkeys(a for hechos in candidatos.values() for a in hechos))

    completos = {nombre: completar_candidato(hechos, atributos, reglas)
                 for nombre, hechos in candidatos.items()}
    return BaseConocimiento(modo, completos, reglas, leer_json("preguntas.json"))
