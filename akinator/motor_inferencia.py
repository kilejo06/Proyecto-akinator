"""Encadenamiento hacia adelante y hacia atrás."""


def cumple_condicion(condicion, hechos):
    if condicion.startswith("no:"):
        return hechos.get(condicion[3:]) is False
    return hechos.get(condicion) is True


def encadenamiento_adelante(hechos, reglas):
    hechos = dict(hechos)
    activadas = []
    evaluadas = []
    hubo_cambio = True
    while hubo_cambio:
        hubo_cambio = False
        for regla in reglas:
            if regla["entonces"] in hechos:
                continue
            evaluadas.append(regla["id"])
            if all(cumple_condicion(c, hechos) for c in regla["si"]):
                hechos[regla["entonces"]] = True
                activadas.append(regla)
                hubo_cambio = True
    return hechos, activadas, evaluadas


def atributo_a_probar(atributo, hipotesis, estado, base):
    """Sigue la regla hacia atrás hasta un atributo que aún se pueda preguntar."""
    if atributo in estado.hechos_conocidos:
        return None
    for regla in base.reglas:
        if regla["entonces"] == atributo and base.candidatos[hipotesis][atributo]:
            for condicion in regla["si"]:
                pendiente = atributo_a_probar(condicion.removeprefix("no:"), hipotesis, estado, base)
                if pendiente:
                    return pendiente
            return None
    return None if atributo in estado.preguntas_hechas else atributo


def encadenamiento_atras(hipotesis, estado, base):
    """Devuelve el atributo a preguntar para confirmar la hipótesis, o None si ya se puede adivinar."""
    datos = base.candidatos
    otros = [c for c in estado.candidatos if c != hipotesis]
    separados = {}
    for atributo, valor in datos[hipotesis].items():
        cuantos = sum(datos[c][atributo] != valor for c in otros)
        if cuantos:
            separados[atributo] = cuantos
    estado.metricas["nodos_generados"] += len(separados)
    for atributo in sorted(separados, key=lambda a: (-separados[a], a)):
        pendiente = atributo_a_probar(atributo, hipotesis, estado, base)
        if pendiente:
            return pendiente
    return None


def filtrar_candidatos(nombres, datos, hechos):
    restantes, descartados = [], []
    for nombre in nombres:
        contradice = any(datos[nombre][atributo] != valor
                         for atributo, valor in hechos.items())
        (descartados if contradice else restantes).append(nombre)
    return restantes, descartados
