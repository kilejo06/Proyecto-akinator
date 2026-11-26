"""Encadenamiento hacia adelante y hacia atrás."""


def literal(atributo, valor):
    return atributo if valor else "no:" + atributo


def valor_literal(lit, hechos):
    """True o False si el hecho ya se conoce, None si no."""
    atributo = lit.removeprefix("no:")
    if atributo not in hechos:
        return None
    return hechos[atributo] == (lit == atributo)


def encadenamiento_adelante(hechos, reglas, objetivo=None):
    """Algoritmo forward: un contador de antecedentes por regla y una pila de hechos por procesar.

    Un hecho falso entra a la pila como el literal "no:atributo". Si se da un objetivo, se detiene al deducirlo.
    """
    hechos = dict(hechos)
    conteo = [len(regla["si"]) for regla in reglas]
    pila = [literal(a, v) for a, v in hechos.items()]
    activadas, evaluadas = [], []
    if objetivo is not None and valor_literal(objetivo, hechos):
        return hechos, activadas, evaluadas
    while pila:
        a = pila.pop()
        for i, regla in enumerate(reglas):
            if a not in regla["si"] or regla["entonces"] in hechos:
                continue
            evaluadas.append(regla["id"])
            conteo[i] -= 1
            if conteo[i] == 0:
                c = regla["entonces"]
                hechos[c] = True
                activadas.append(regla)
                if c == objetivo:
                    return hechos, activadas, evaluadas
                pila.append(c)
    return hechos, activadas, evaluadas


class Consulta:
    """La base que recorren or_search y and_search; guarda los atributos por preguntar que va encontrando."""

    def __init__(self, hechos, reglas, preguntadas):
        self.hechos = hechos
        self.reglas = reglas
        self.preguntadas = preguntadas
        self.pendientes = []

    def reglas_aplicables(self, consecuente):
        return [regla for regla in self.reglas if regla["entonces"] == consecuente]


def or_search(base, consecuente, camino):
    valor = valor_literal(consecuente, base.hechos)
    if valor is not None:
        return valor
    if consecuente in camino:
        return False
    atributo = consecuente.removeprefix("no:")
    if consecuente != atributo and base.reglas_aplicables(atributo):
        # Negación de algo deducido: es cierta si ninguna regla lo prueba y no queda nada por preguntar
        antes = len(base.pendientes)
        if or_search(base, atributo, camino + [consecuente]):
            return False
        return len(base.pendientes) == antes
    candidatos = base.reglas_aplicables(consecuente)
    if not candidatos:
        # Hoja sin reglas: hay que preguntarla, salvo que ya se preguntó y respondieron "no sé"
        if atributo not in base.preguntadas:
            base.pendientes.append(atributo)
        return False
    for regla in candidatos:
        if and_search(base, regla["si"], camino + [consecuente]):
            return True
    return False


def and_search(base, literales, camino):
    for p in literales:
        if not or_search(base, p, camino):
            return False
    return True


def atributo_a_probar(atributo, hipotesis, estado, base):
    """Busca hacia atrás el valor que la hipótesis tiene en el atributo y devuelve la primera hoja por preguntar."""
    consulta = Consulta(estado.hechos_conocidos, base.reglas, estado.preguntas_hechas)
    or_search(consulta, literal(atributo, base.candidatos[hipotesis][atributo]), [])
    return consulta.pendientes[0] if consulta.pendientes else None


def atributos_que_separan(hipotesis, estado, base):
    datos = base.candidatos
    otros = [c for c in estado.candidatos if c != hipotesis]
    separados = {}
    for atributo, valor in datos[hipotesis].items():
        cuantos = sum(datos[c][atributo] != valor for c in otros)
        if cuantos:
            separados[atributo] = cuantos
    return separados


def encadenamiento_atras(hipotesis, estado, base):
    """Devuelve el atributo a preguntar para confirmar la hipótesis, o None si ya se puede adivinar."""
    separados = atributos_que_separan(hipotesis, estado, base)
    estado.metricas["nodos_generados"] += len(separados)
    for atributo in sorted(separados, key=lambda a: (-separados[a], a)):
        pendiente = atributo_a_probar(atributo, hipotesis, estado, base)
        if pendiente:
            return pendiente
    return None


def explicar_atras(hipotesis, estado, base):
    """Por qué encadenamiento_atras eligió su atributo: objetivo, regla seguida y candidatos que separa."""
    separados = atributos_que_separan(hipotesis, estado, base)
    for atributo in sorted(separados, key=lambda a: (-separados[a], a)):
        pendiente = atributo_a_probar(atributo, hipotesis, estado, base)
        if pendiente:
            regla = None
            if pendiente != atributo:
                regla = next(r["id"] for r in base.reglas if r["entonces"] == atributo)
            return {"hipotesis": hipotesis, "objetivo": atributo, "regla": regla, "separa": separados[atributo]}
    return None


def filtrar_candidatos(nombres, datos, hechos):
    restantes, descartados = [], []
    for nombre in nombres:
        contradice = any(datos[nombre][atributo] != valor
                         for atributo, valor in hechos.items())
        (descartados if contradice else restantes).append(nombre)
    return restantes, descartados
