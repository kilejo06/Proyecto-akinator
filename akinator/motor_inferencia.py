"""Encadenamiento hacia adelante y hacia atrás."""


def cumple_condicion(condicion, hechos):
    if condicion.startswith("no:"):
        return hechos.get(condicion[3:]) is False
    return hechos.get(condicion) is True


def encadenamiento_adelante(hechos, reglas):
    hechos = dict(hechos)
    activadas = []
    hubo_cambio = True
    while hubo_cambio:
        hubo_cambio = False
        for regla in reglas:
            if regla["entonces"] in hechos:
                continue
            if all(cumple_condicion(c, hechos) for c in regla["si"]):
                hechos[regla["entonces"]] = True
                activadas.append(regla)
                hubo_cambio = True
    return hechos, activadas
