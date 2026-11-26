"""Revisa que los JSON de datos sean consistentes.

Uso: python pruebas/validar_datos.py
Sale con código 1 si hay errores (los avisos no cuentan como error).
"""
import json
import os
import sys

CARPETA_DATOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "datos")
MINIMO_CANDIDATOS = 50


def leer(nombre):
    with open(os.path.join(CARPETA_DATOS, nombre), encoding="utf-8") as archivo:
        return json.load(archivo)


def atributos_de(candidatos):
    """Unión de todos los atributos que aparecen en los candidatos."""
    atributos = set()
    for hechos in candidatos.values():
        atributos.update(hechos)
    return atributos


def quitar_no(condicion):
    return condicion[3:] if condicion.startswith("no:") else condicion


def completar(candidato, atributos):
    """Mundo cerrado: lo que no está definido cuenta como false."""
    return {a: bool(candidato.get(a, False)) for a in atributos}


def validar_categoria(nombre, candidatos, reglas, preguntas, errores, avisos):
    atributos = atributos_de(candidatos)
    conclusiones = [r["entonces"] for r in reglas]

    if len(candidatos) < MINIMO_CANDIDATOS:
        avisos.append(f"{nombre}: solo hay {len(candidatos)} candidatos (meta: {MINIMO_CANDIDATOS})")

    # Cada atributo necesita su pregunta; las conclusiones de las reglas no se preguntan
    for atributo in sorted(atributos):
        if atributo not in preguntas:
            errores.append(f"{nombre}: falta la pregunta de '{atributo}'")

    # Las reglas solo pueden usar atributos existentes o conclusiones de otras reglas
    conocidos = atributos | set(conclusiones)
    ids = set()
    for regla in reglas:
        if regla["id"] in ids:
            errores.append(f"{nombre}: id de regla repetido {regla['id']}")
        ids.add(regla["id"])
        for condicion in regla["si"]:
            if quitar_no(condicion) not in conocidos:
                errores.append(f"{nombre}: {regla['id']} usa '{condicion}', que no existe")
        if regla["entonces"] in atributos:
            avisos.append(f"{nombre}: {regla['id']} concluye '{regla['entonces']}', que ya es un atributo")

    # Atributos que no dividen a los candidatos (todos sí o todos no)
    for atributo in sorted(atributos):
        valores = [bool(c.get(atributo, False)) for c in candidatos.values()]
        if (all(valores) or not any(valores)) and atributo != "es_ser_vivo":
            avisos.append(f"{nombre}: '{atributo}' no divide a los candidatos")

    # D10: dos candidatos con los mismos atributos no se pueden distinguir
    vistos = {}
    for nombre_candidato, hechos in candidatos.items():
        firma = tuple(sorted(completar(hechos, atributos).items()))
        if firma in vistos:
            errores.append(f"{nombre}: '{nombre_candidato}' es idéntico a '{vistos[firma]}'")
        vistos[firma] = nombre_candidato


def main():
    preguntas = leer("preguntas.json")
    animales, paises = leer("animales.json"), leer("paises.json")
    reglas_animales, reglas_paises = leer("reglas_animales.json"), leer("reglas_paises.json")
    errores, avisos = [], []

    validar_categoria("animales", animales, reglas_animales, preguntas, errores, avisos)
    validar_categoria("paises", paises, reglas_paises, preguntas, errores, avisos)

    # Modo mixto: unir ambas categorías y volver a buscar candidatos idénticos
    repetidos = set(animales) & set(paises)
    for nombre in sorted(repetidos):
        errores.append(f"mixto: '{nombre}' está en animales y en países")
    mixto = {**animales, **paises}
    validar_categoria("mixto", mixto, reglas_animales + reglas_paises, preguntas, errores, avisos)

    # Preguntas que ningún atributo usa
    usadas = atributos_de(mixto)
    for clave in sorted(set(preguntas) - usadas):
        avisos.append(f"preguntas: '{clave}' no se usa en ningún lado")

    # En el mixto se pierde el aviso duplicado de atributos que no dividen; se quita ruido
    avisos = list(dict.fromkeys(avisos))

    for aviso in avisos:
        print("AVISO:", aviso)
    for error in errores:
        print("ERROR:", error)
    print(f"\n{len(animales)} animales, {len(paises)} países, "
          f"{len(reglas_animales)} + {len(reglas_paises)} reglas, {len(preguntas)} preguntas.")
    print(f"{len(errores)} errores, {len(avisos)} avisos.")
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
