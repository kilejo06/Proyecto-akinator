"""Modo automático de la interfaz: el agente juega solo y la partida se reproduce paso a paso."""
import math
import random

from automatico import jugar_automatico
from base_conocimiento import cargar_base
from gui_dibujo import ORO, TINTA
from utils import nombre_legible, texto_regla

VELOCIDADES = (("lenta", "Lenta", 2000), ("normal", "Normal", 1000), ("rapida", "Rápida", 400))
MORADO = "#6b5fa5"
VERDE, ROJO = "#22c55e", "#ef4444"
RESPUESTAS = {"si": "Sí", "no": "No", "no_se": "No sé"}


class ReproduccionMixin:
    def abrir_secreto(self, modo):
        self.base = cargar_base(modo)
        self.total = len(self.base.candidatos)
        self.vista, self.expresion = "elegir_secreto", "normal"
        self.refrescar()

    def iniciar_agente(self, secreto=None):
        secreto = secreto or random.choice(list(self.base.candidatos))
        a = self.ajustes
        self.repro = jugar_automatico(self.base, secreto, a["metodo"], a["heuristica"], a["limite"])
        self.secreto = secreto
        self.indice = 0
        self.reproduciendo = False
        self.vista = "reproduccion"
        self.refrescar()

    def vista_elegir_secreto(self):
        w, h = self.ancho, self.alto
        self.barra_superior("¿En qué piensa el agente?")
        metodo = {"heuristica": f"heurística {self.ajustes['heuristica']}", "adelante": "encadenamiento hacia adelante",
                  "atras": "encadenamiento hacia atrás"}[self.ajustes["metodo"]]
        self.texto(w / 2, 0.125 * h, f"Elige el secreto o deja que lo escoja al azar. Método: {metodo}", 13,
                   "#fde68a")
        nombres = sorted(self.base.candidatos, key=nombre_legible)
        columnas = 5 if len(nombres) <= 35 else 7
        filas = math.ceil(len(nombres) / columnas)
        x0, x1, y0, y1, hueco = 0.06 * w, 0.94 * w, 0.17 * h, 0.82 * h, 0.008 * w
        ancho = (x1 - x0 - hueco * (columnas - 1)) / columnas
        alto = (y1 - y0 - hueco * (filas - 1)) / filas
        for numero, nombre in enumerate(nombres):
            fila, columna = divmod(numero, columnas)
            x = x0 + columna * (ancho + hueco)
            y = y0 + fila * (alto + hueco)
            self.boton(x, y, x + ancho, y + alto, nombre_legible(nombre), self.secundario(),
                       lambda n=nombre: self.iniciar_agente(n), tamano=12)
        self.boton(0.35 * w, 0.88 * h, 0.65 * w, 0.955 * h, "Al azar", ORO, self.iniciar_agente, TINTA, 17)

    def paso_actual(self):
        return self.repro.historial[self.indice]

    def vista_reproduccion(self):
        historial = self.repro.historial
        paso = self.paso_actual()
        self.expresion = {"pregunta": "pensando", "adivinar": "sorprendido", "inicio": "normal"}.get(
            paso["tipo"], "feliz" if paso["acerto"] else "triste")
        self.barra_superior(f"Paso {self.indice + 1} de {len(historial)}", paso["puntos"])
        self.burbuja(self.lineas_paso(paso))
        self.controles(len(historial) - 1)
        self.barra_progreso(paso["candidatos"])
        self.panel_razonamiento(self.datos_paso(paso), paso["candidatos"], paso["puntos"])

    def lineas_paso(self, paso):
        secreto = f"El agente piensa en: {nombre_legible(self.secreto)}"
        tipo = paso["tipo"]
        if tipo == "inicio":
            return [(secreto, 15, MORADO), ("¡Empecemos!", 34, TINTA),
                    (f"Tengo {len(paso['candidatos'])} candidatos", 16, MORADO)]
        if tipo == "pregunta":
            return [(secreto, 13, MORADO), (paso["pregunta"], 24, TINTA),
                    (f"Respondió: {RESPUESTAS[paso['respuesta']]}", 20, MORADO)]
        if tipo == "adivinar":
            veredicto = "¡Correcto!" if paso["acerto"] else "No era. Sigo preguntando"
            return [(secreto, 13, MORADO), ("Creo que estás pensando en...", 16, MORADO),
                    (nombre_legible(paso["candidato_adivinado"]).upper(), 34, TINTA), (veredicto, 18, MORADO)]
        resumen = paso["resumen"]
        titulo = "¡Lo adiviné!" if paso["acerto"] else "No lo logré"
        detalle = f"Preguntas: {resumen['preguntas']}   ·   Puntaje final: {resumen['puntaje']}"
        return [(secreto, 13, MORADO), (titulo, 34, TINTA), (detalle, 16, MORADO)]

    def datos_paso(self, paso):
        tipo = paso["tipo"]
        if tipo == "inicio":
            return None
        anterior = self.repro.historial[self.indice - 1]
        reglas = {r["id"]: r for r in self.base.reglas}
        if tipo == "pregunta":
            titulo = f"El agente respondió «{RESPUESTAS[paso['respuesta']]}» a: {paso['pregunta']}"
        elif tipo == "adivinar":
            titulo = f"{'Acertó' if paso['acerto'] else 'Falló'} con {nombre_legible(paso['candidato_adivinado'])}"
        else:
            titulo = "Fin de la partida"
        return {"titulo": titulo, "reglas": "; ".join(texto_regla(reglas[i]) for i in paso["reglas_disparadas"]),
                "descartados": paso["descartados"], "delta": paso["puntos"] - anterior["puntos"]}

    def controles(self, ultimo):
        w, h = self.ancho, self.alto
        alternar = "⏸ Pausar" if self.reproduciendo else "▶ Iniciar"
        self.fila_botones(0.555 * h, 0.635 * h, [
            ("⏮", self.secundario(), lambda: self.ir_a(0)),
            ("◀ Atrás", self.secundario(), lambda: self.ir_a(self.indice - 1)),
            (alternar, ORO if not self.reproduciendo else ROJO, self.alternar_reproduccion),
            ("Adelante ▶", self.secundario(), lambda: self.ir_a(self.indice + 1)),
            ("⏭", self.secundario(), lambda: self.ir_a(ultimo))], tamano=14)
        self.texto(0.38 * w, 0.685 * h, "Velocidad", 13, "#ffffff", True, "w")
        inicio, fin, hueco = 0.50 * w, 0.95 * w, 0.01 * w
        ancho = (fin - inicio - 2 * hueco) / 3
        for numero, (clave, nombre, _) in enumerate(VELOCIDADES):
            x = inicio + numero * (ancho + hueco)
            elegido = self.velocidad == clave
            self.boton(x, 0.66 * h, x + ancho, 0.715 * h, nombre, ORO if elegido else self.secundario(),
                       lambda c=clave: self.cambiar_velocidad(c), TINTA if elegido else "#ffffff", 12)

    def ms_por_paso(self):
        return next(ms for clave, _, ms in VELOCIDADES if clave == self.velocidad)

    def cambiar_velocidad(self, clave):
        self.velocidad = clave
        self.refrescar()

    def ir_a(self, indice):
        self.detener_reproduccion()
        self.indice = max(0, min(len(self.repro.historial) - 1, indice))
        self.refrescar()

    def alternar_reproduccion(self):
        if self.reproduciendo:
            self.detener_reproduccion()
        else:
            if self.indice >= len(self.repro.historial) - 1:
                self.indice = 0
            self.reproduciendo = True
            self.pendiente = self.after(self.ms_por_paso(), self.avanzar_solo)
        self.refrescar()

    def avanzar_solo(self):
        self.pendiente = None
        if not self.reproduciendo or self.vista != "reproduccion":
            return
        self.indice += 1
        if self.indice < len(self.repro.historial) - 1:
            self.pendiente = self.after(self.ms_por_paso(), self.avanzar_solo)
        else:
            self.reproduciendo = False
        self.refrescar()

    def detener_reproduccion(self):
        if self.pendiente is not None:
            self.after_cancel(self.pendiente)
        self.pendiente = None
        self.reproduciendo = False

    def al_teclear_reproduccion(self, tecla):
        if tecla == "space":
            self.alternar_reproduccion()
        elif tecla == "left":
            self.ir_a(self.indice - 1)
        elif tecla == "right":
            self.ir_a(self.indice + 1)
