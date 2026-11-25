"""Interfaz gráfica estilo Akinator: elige el tipo de juego, juega y ajusta."""
import itertools
import math
import random
import tkinter as tk

import ajustes as config
from agente import SIN_CANDIDATOS
from base_conocimiento import cargar_base, leer_json
from gui_dibujo import FONDOS, ORO, TINTA, aclarar, dibujar_fondo, dibujar_mago, mezclar, rect_redondo
from partida import Partida
from utils import nombre_legible, texto_regla

MODOS = (("animales", "Animales"), ("paises", "Países"), ("mixto", "Mixto"))
OPCIONES_METODO = (("heuristica", "Heurística"), ("adelante", "Adelante"), ("atras", "Atrás"))
AYUDA_METODO = {
    "heuristica": "Elijo cada pregunta con una heurística.",
    "adelante": "Pregunto en el orden de los datos y deduzco con las reglas.",
    "atras": "Parto de una hipótesis y pregunto lo necesario para confirmarla.",
}
OPCIONES_HEURISTICA = (("mitad", "Mitad"), ("entropia", "Entropía"), ("aleatoria", "Aleatoria"))
OPCIONES_FONDO = (("noche", "Noche"), ("atardecer", "Atardecer"), ("oceano", "Océano"))
AYUDA_HEURISTICA = {
    "mitad": "Parte a los candidatos lo más cerca de la mitad.",
    "entropia": "Elige la pregunta que más información aporta.",
    "aleatoria": "Elige preguntas al azar. Sirve para comparar.",
}
VERDE, ROJO, GRIS, BLANCO = "#22c55e", "#ef4444", "#64748b", "#ffffff"


class Akinator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Akinator")
        self.geometry("1100x720")
        self.minsize(820, 600)
        self.ajustes = config.cargar()
        self.lienzo = tk.Canvas(self, highlightthickness=0, background="#150f4f")
        self.lienzo.pack(fill="both", expand=True)
        self.vista = "menu"
        self.vista_previa = "menu"
        self.partida = None
        self.accion = None
        self.base = None
        self.total = 1
        self.expresion = "normal"
        self.bloqueado = False
        self.mensaje_temporal = None
        self.razonamiento = []
        self.ultimo_candidato = ""
        self.pendiente = None
        self.refresco = None
        self.vuelo = 0.0
        self.fase = 0.0
        self.estrellas = []
        self.imagen_fondo = None
        self.fondo_dibujado = None
        self.ancho = self.alto = 1
        self.escala = 1.0
        self.contador = itertools.count()
        self.conteos = self.contar_candidatos()
        self.lienzo.bind("<Configure>", self.al_cambiar_tamano)
        self.bind("<Key>", self.al_teclear)
        self.tick()

    # --- Utilidades ----------------------------------------------------------

    def contar_candidatos(self):
        animales, paises = len(leer_json("animales.json")), len(leer_json("paises.json"))
        return {"animales": animales, "paises": paises, "mixto": animales + paises}

    def fuente(self, tamano, negrita=False):
        return ("Segoe UI", max(8, int(tamano * self.escala)), "bold" if negrita else "normal")

    def secundario(self):
        return aclarar(FONDOS[self.ajustes["fondo"]]["panel"], 1.7)

    def al_cambiar_tamano(self, _evento):
        if self.refresco is not None:
            self.after_cancel(self.refresco)
        self.refresco = self.after(60, self.refrescar)

    def refrescar(self):
        self.refresco = None
        ancho, alto = self.lienzo.winfo_width(), self.lienzo.winfo_height()
        if ancho < 100 or alto < 100:
            return
        self.ancho, self.alto = ancho, alto
        self.escala = max(0.6, min(ancho / 1100, alto / 720))
        marca = (ancho, alto, self.ajustes["fondo"])
        if marca != self.fondo_dibujado:
            self.imagen_fondo, self.estrellas = dibujar_fondo(self.lienzo, ancho, alto, self.ajustes["fondo"])
            self.fondo_dibujado = marca
        self.lienzo.delete("ui")
        self.lienzo.delete("mago")
        self.lienzo.configure(cursor="")
        getattr(self, "vista_" + self.vista)()

    def tick(self):
        if self.ajustes["animaciones"]:
            self.fase += 0.12
            nuevo = math.sin(self.fase) * 7 * self.escala
            self.lienzo.move("mago", 0, nuevo - self.vuelo)
            self.vuelo = nuevo
            if self.estrellas and random.random() < 0.5:
                estrella = random.choice(self.estrellas)
                color = self.lienzo.itemcget(estrella, "fill")
                self.lienzo.itemconfigure(estrella, fill="#fde68a" if color == "#ffffff" else "#ffffff")
        self.after(60, self.tick)

    def mago(self, cx, cy, factor=1.0):
        unidad = min(0.072 * self.alto, 0.05 * self.ancho) * factor
        paleta = FONDOS[self.ajustes["fondo"]]
        fondo = mezclar(paleta["arriba"], paleta["abajo"], cy / self.alto)
        dibujar_mago(self.lienzo, cx, cy + self.vuelo, unidad, self.expresion, fondo)

    def texto(self, x, y, texto, tamano, color=BLANCO, negrita=False, ancla="center", ancho=None):
        opciones = {"width": ancho} if ancho else {}
        return self.lienzo.create_text(x, y, text=texto, fill=color, font=self.fuente(tamano, negrita),
                                       anchor=ancla, justify="center" if ancla == "center" else "left",
                                       tags="ui", **opciones)

    def boton(self, x1, y1, x2, y2, texto, color, comando, color_texto=BLANCO, tamano=18, subtitulo=None):
        lienzo, etiqueta = self.lienzo, f"b{next(self.contador)}"
        radio = min(x2 - x1, y2 - y1) * 0.3
        rect_redondo(lienzo, x1, y1 + 5, x2, y2 + 5, radio, fill=aclarar(color, 0.55), outline="", tags="ui")
        forma = rect_redondo(lienzo, x1, y1, x2, y2, radio, fill=color, outline=aclarar(color, 1.25), width=2,
                             tags=("ui", etiqueta))
        centro_y = (y1 + y2) / 2 - (0.17 * (y2 - y1) if subtitulo else 0)
        lienzo.create_text((x1 + x2) / 2, centro_y, text=texto, fill=color_texto,
                           font=self.fuente(tamano, True), tags=("ui", etiqueta))
        if subtitulo:
            lienzo.create_text((x1 + x2) / 2, (y1 + y2) / 2 + 0.24 * (y2 - y1), text=subtitulo, fill=color_texto,
                               font=self.fuente(12), tags=("ui", etiqueta))
        lienzo.tag_bind(etiqueta, "<Button-1>", lambda _: comando())
        lienzo.tag_bind(etiqueta, "<Enter>", lambda _: (lienzo.itemconfigure(forma, fill=aclarar(color, 1.15)),
                                                         lienzo.configure(cursor="hand2")))
        lienzo.tag_bind(etiqueta, "<Leave>", lambda _: (lienzo.itemconfigure(forma, fill=color),
                                                         lienzo.configure(cursor="")))

    # --- Menú -------------------------------------------------------------------

    def vista_menu(self):
        w, h = self.ancho, self.alto
        self.texto(w / 2 + 4, 0.13 * h + 4, "AKINATOR", 60, "#0b0630", True)
        self.texto(w / 2, 0.13 * h, "AKINATOR", 60, ORO, True)
        self.texto(w / 2, 0.225 * h, "Piensa en un animal o en un país y yo lo adivinaré", 17)
        self.mago(w / 2, 0.43 * h, 1.1)
        self.texto(w / 2, 0.655 * h, "¿Qué tipo de juego quieres?", 19, BLANCO, True)
        ancho_tarjeta, hueco = 0.24 * w, 0.025 * w
        inicio = w / 2 - (3 * ancho_tarjeta + 2 * hueco) / 2
        for numero, (clave, nombre) in enumerate(MODOS):
            x1 = inicio + numero * (ancho_tarjeta + hueco)
            self.boton(x1, 0.70 * h, x1 + ancho_tarjeta, 0.83 * h, nombre, ORO, lambda c=clave: self.empezar(c),
                       TINTA, 24, f"{self.conteos[clave]} candidatos")
        self.boton(w / 2 - 0.17 * w, 0.89 * h, w / 2 - 0.01 * w, 0.96 * h, "Ajustes", self.secundario(),
                   self.abrir_ajustes, tamano=15)
        self.boton(w / 2 + 0.01 * w, 0.89 * h, w / 2 + 0.17 * w, 0.96 * h, "Salir", self.secundario(),
                   self.destroy, tamano=15)

    # --- Partida ----------------------------------------------------------------

    def empezar(self, modo):
        self.cancelar_pausa()
        self.base = cargar_base(modo)
        self.total = len(self.base.candidatos)
        a = self.ajustes
        self.partida = Partida(self.base, a["metodo"], a["heuristica"], a["limite"])
        self.razonamiento = []
        self.siguiente()

    def siguiente(self):
        self.accion = self.partida.siguiente()
        tipo = self.accion["tipo"]
        if tipo == "pregunta":
            self.vista, self.expresion = "pregunta", "normal"
        elif tipo == "adivinar":
            self.vista, self.expresion = "adivinar", "sorprendido"
        else:
            self.vista = "fin"
            self.expresion = "feliz" if self.partida.estado.acerto else "triste"
        self.refrescar()

    def responder(self, valor):
        if self.bloqueado or self.vista != "pregunta":
            return
        estado = self.partida.estado
        puntos_antes = estado.puntos
        respondida = self.accion["pregunta"]
        activadas, descartados = self.partida.responder(valor)
        etiqueta = {"si": "Sí", "no": "No", "no_se": "No sé"}[valor]
        self.razonamiento = {"titulo": f"Respondiste «{etiqueta}» a: {respondida}",
                             "reglas": "; ".join(texto_regla(r) for r in activadas),
                             "descartados": descartados, "delta": estado.puntos - puntos_antes}
        self.pensar(self.siguiente, "Hmm... déjame pensar", "pensando")

    def confirmar(self, acerto):
        if self.bloqueado or self.vista != "adivinar":
            return
        self.ultimo_candidato = self.accion["candidato"]
        puntos_antes = self.partida.estado.puntos
        self.partida.confirmar(acerto)
        if acerto:
            self.razonamiento = []
            self.siguiente()
        else:
            self.razonamiento = {"titulo": f"Fallé con {nombre_legible(self.ultimo_candidato)}",
                                 "reglas": "", "descartados": [self.ultimo_candidato],
                                 "delta": self.partida.estado.puntos - puntos_antes}
            self.pensar(self.siguiente, "Vaya... déjame intentarlo otra vez", "triste")

    def pensar(self, despues, texto, expresion):
        if not self.ajustes["animaciones"]:
            despues()
            return
        self.bloqueado, self.expresion, self.mensaje_temporal = True, expresion, texto
        self.refrescar()
        self.pendiente = self.after(650, lambda: self.terminar_pausa(despues))

    def terminar_pausa(self, despues):
        self.pendiente = None
        self.bloqueado = False
        self.mensaje_temporal = None
        despues()

    def cancelar_pausa(self):
        if self.pendiente is not None:
            self.after_cancel(self.pendiente)
        self.pendiente = None
        self.bloqueado = False
        self.mensaje_temporal = None

    def ir_menu(self):
        self.cancelar_pausa()
        self.vista, self.expresion = "menu", "normal"
        self.refrescar()

    def al_teclear(self, evento):
        tecla = evento.keysym.lower()
        if self.vista == "pregunta":
            valor = {"s": "si", "y": "si", "n": "no", "d": "no_se"}.get(tecla)
            if valor:
                self.responder(valor)
        elif self.vista == "adivinar" and tecla in ("s", "y", "n"):
            self.confirmar(tecla != "n")
        if tecla == "escape" and self.vista in ("pregunta", "adivinar", "fin", "ajustes"):
            self.volver() if self.vista == "ajustes" else self.ir_menu()

    # --- Escena de juego -------------------------------------------------------

    def barra_superior(self, centro):
        w, h = self.ancho, self.alto
        self.boton(0.02 * w, 0.03 * h, 0.14 * w, 0.09 * h, "Menú", self.secundario(), self.ir_menu, tamano=13)
        self.boton(0.86 * w, 0.03 * h, 0.98 * w, 0.09 * h, "Ajustes", self.secundario(), self.abrir_ajustes,
                   tamano=13)
        self.texto(w / 2, 0.06 * h, centro, 18, BLANCO, True)
        if self.ajustes["puntaje"] and self.partida:
            self.texto(0.80 * w, 0.06 * h, f"Puntaje: {self.partida.estado.puntos}", 13, "#fde68a", True, "e")

    def burbuja(self, lineas):
        """lineas: lista de (texto, tamaño, color). El mago queda a la izquierda de la burbuja."""
        w, h = self.ancho, self.alto
        x1, y1, x2, y2 = 0.38 * w, 0.14 * h, 0.95 * w, 0.50 * h
        self.mago(0.19 * w, 0.46 * h)
        rect_redondo(self.lienzo, x1 + 4, y1 + 6, x2 + 4, y2 + 6, 30 * self.escala, fill="#0b0630", outline="",
                     stipple="gray50", tags="ui")
        rect_redondo(self.lienzo, x1, y1, x2, y2, 30 * self.escala, fill=BLANCO, outline="", tags="ui")
        self.lienzo.create_polygon(x1 + 3, y1 + 0.10 * h, x1 - 0.045 * w, y1 + 0.16 * h, x1 + 3, y1 + 0.20 * h,
                                   fill=BLANCO, outline="", tags="ui")
        for numero, (texto, tamano, color) in enumerate(lineas):
            y = y1 + (numero + 1) * (y2 - y1) / (len(lineas) + 1)
            self.texto((x1 + x2) / 2, y, texto, tamano, color, tamano > 18, ancho=(x2 - x1) - 0.06 * w)

    def fila_botones(self, y1, y2, definiciones):
        w = self.ancho
        inicio, fin, hueco = 0.38 * w, 0.95 * w, 0.015 * w
        ancho = (fin - inicio - hueco * (len(definiciones) - 1)) / len(definiciones)
        for numero, (texto, color, comando) in enumerate(definiciones):
            x1 = inicio + numero * (ancho + hueco)
            self.boton(x1, y1, x1 + ancho, y2, texto, color, comando, tamano=20)

    def barra_progreso(self):
        w, h = self.ancho, self.alto
        estado = self.partida.estado
        certeza = 1 - (len(estado.candidatos) - 1) / max(1, self.total - 1)
        certeza = max(0.0, min(1.0, certeza))
        self.texto(0.08 * w, 0.765 * h, "Qué tan cerca estoy de adivinar", 13, BLANCO, False, "w")
        x1, x2, y1, y2 = 0.08 * w, 0.92 * w, 0.79 * h, 0.82 * h
        rect_redondo(self.lienzo, x1, y1, x2, y2, (y2 - y1) / 2, fill=aclarar(FONDOS[self.ajustes["fondo"]]["panel"], 0.6),
                     outline="", tags="ui")
        if certeza > 0.02:
            rect_redondo(self.lienzo, x1, y1, x1 + (x2 - x1) * certeza, y2, (y2 - y1) / 2, fill=ORO, outline="",
                         tags="ui")
        self.texto(x2, 0.765 * h, f"{int(certeza * 100)}%   ·   quedan {len(estado.candidatos)} candidatos",
                   13, BLANCO, False, "e")

    def panel_razonamiento(self):
        if not self.ajustes["razonamiento"]:
            return
        w, h = self.ancho, self.alto
        panel = FONDOS[self.ajustes["fondo"]]["panel"]
        rect_redondo(self.lienzo, 0.05 * w, 0.84 * h, 0.95 * w, 0.985 * h, 18 * self.escala,
                     fill=panel, outline=aclarar(panel, 1.8), width=2, tags="ui")
        estado = self.partida.estado
        datos = self.razonamiento
        if not datos:
            self.texto(0.07 * w, 0.912 * h, "Aquí verás qué reglas se activan, a quién descarto, "
                       "quiénes quedan y cómo cambia el puntaje.", 12, BLANCO, False, "w", 0.86 * w)
            return
        cabecera = datos["titulo"]
        if self.ajustes["puntaje"]:
            cabecera += f"   ·   Puntaje {datos['delta']:+d} (total {estado.puntos})".replace("-", "−")
        self.texto(0.07 * w, 0.862 * h, cabecera, 12, "#fde68a", True, "w", 0.86 * w)
        if datos["reglas"]:
            self.texto(0.07 * w, 0.893 * h, "Reglas activadas: " + datos["reglas"], 11, "#a5f3fc", False, "w",
                       0.86 * w)
        descartados = self.lista_nombres(datos["descartados"], "ninguno")
        restantes = self.lista_nombres(estado.candidatos, "ninguno")
        y = 0.925 * h
        self.texto(0.07 * w, y, f"Descartados ahora ({len(datos['descartados'])}): {descartados}", 11,
                   "#fca5a5", False, "nw", 0.41 * w)
        self.texto(0.52 * w, y, f"Candidatos restantes ({len(estado.candidatos)}): {restantes}", 11,
                   "#86efac", False, "nw", 0.41 * w)

    def lista_nombres(self, nombres, vacio, maximo=8):
        if not nombres:
            return vacio
        visibles = ", ".join(nombre_legible(n) for n in nombres[:maximo])
        resto = len(nombres) - maximo
        return visibles + (f" y {resto} más" if resto > 0 else "")

    def vista_pregunta(self):
        estado = self.partida.estado
        self.barra_superior(f"Pregunta {estado.num_preguntas + 1} de {estado.limite_preguntas}")
        self.burbuja([(self.mensaje_temporal or self.accion["pregunta"], 26, TINTA)])
        self.fila_botones(0.57 * self.alto, 0.71 * self.alto, [
            ("Sí", VERDE, lambda: self.responder("si")), ("No", ROJO, lambda: self.responder("no")),
            ("No sé", GRIS, lambda: self.responder("no_se"))])
        self.barra_progreso()
        self.panel_razonamiento()

    def vista_adivinar(self):
        self.barra_superior("¡Creo que ya lo sé!")
        if self.mensaje_temporal:
            self.burbuja([(self.mensaje_temporal, 26, TINTA)])
        else:
            self.burbuja([("Creo que estás pensando en...", 18, "#6b5fa5"),
                          (nombre_legible(self.accion["candidato"]).upper(), 38, TINTA)])
        self.fila_botones(0.57 * self.alto, 0.71 * self.alto, [
            ("¡Sí, es correcto!", VERDE, lambda: self.confirmar(True)),
            ("No, no es", ROJO, lambda: self.confirmar(False))])
        self.barra_progreso()
        self.panel_razonamiento()

    def vista_fin(self):
        estado = self.partida.estado
        w, h = self.ancho, self.alto
        self.barra_superior("Fin de la partida")
        if estado.acerto:
            titulo = "¡Lo adiviné!"
            detalle = f"Era {nombre_legible(self.ultimo_candidato)}. ¡Qué buena partida!"
        elif self.partida.motivo == SIN_CANDIDATOS:
            titulo, detalle = "No conozco nada así...", "Tus respuestas no encajan con nadie que yo conozca."
        else:
            titulo, detalle = "Me has vencido", "No logré adivinar a tiempo. ¿Revancha?"
        resumen = f"Preguntas: {estado.num_preguntas}"
        if self.ajustes["puntaje"]:
            resumen += f"   ·   Puntaje final: {estado.puntos}"
        self.burbuja([(titulo, 36, TINTA), (detalle, 17, "#6b5fa5"), (resumen, 15, "#6b5fa5")])
        self.boton(0.38 * w, 0.57 * h, 0.665 * w, 0.71 * h, "Jugar otra vez", ORO,
                   lambda: self.empezar(self.base.modo), TINTA, 20)
        self.boton(0.68 * w, 0.57 * h, 0.95 * w, 0.71 * h, "Menú", self.secundario(), self.ir_menu, tamano=20)

    # --- Ajustes ----------------------------------------------------------------

    def abrir_ajustes(self):
        if self.bloqueado:
            return
        if self.vista != "ajustes":
            self.vista_previa = self.vista
        self.vista = "ajustes"
        self.refrescar()

    def volver(self):
        self.vista = self.vista_previa
        self.refrescar()

    def cambiar(self, clave, valor):
        self.ajustes[clave] = valor
        config.guardar(self.ajustes)
        self.refrescar()

    def restablecer(self):
        self.ajustes = dict(config.POR_DEFECTO)
        config.guardar(self.ajustes)
        self.refrescar()

    def vista_ajustes(self):
        w, h = self.ancho, self.alto
        panel = FONDOS[self.ajustes["fondo"]]["panel"]
        self.texto(w / 2, 0.075 * h, "Ajustes", 36, ORO, True)
        rect_redondo(self.lienzo, 0.12 * w, 0.14 * h, 0.88 * w, 0.855 * h, 28 * self.escala, fill=panel,
                     outline=aclarar(panel, 1.8), width=2, tags="ui")
        a = self.ajustes
        filas = [
            ("Método de razonamiento", "", "selector", "metodo", OPCIONES_METODO),
            ("Heurística", "Solo se usa con el método Heurística", "selector", "heuristica",
             OPCIONES_HEURISTICA),
            ("Límite de preguntas", "Preguntas que puedo hacer antes de rendirme", "contador", "limite", (5, 40)),
            ("Fondo", "El escenario de la partida", "selector", "fondo", OPCIONES_FONDO),
            ("Mostrar razonamiento", "Reglas activadas y candidatos descartados en cada respuesta", "interruptor",
             "razonamiento", None),
            ("Animaciones", "Movimiento del mago y pausas para pensar", "interruptor", "animaciones", None),
            ("Mostrar puntaje", "Puntos que suma o resta el agente", "interruptor", "puntaje", None),
        ]
        alto_fila = 0.095 * h
        for numero, (titulo, ayuda, tipo, clave, datos) in enumerate(filas):
            y = 0.19 * h + numero * alto_fila
            self.texto(0.16 * w, y + 0.012 * h, titulo, 17, BLANCO, True, "w")
            ayuda_texto = {"metodo": AYUDA_METODO[a["metodo"]],
                           "heuristica": AYUDA_HEURISTICA[a["heuristica"]]
                           if a["metodo"] == "heuristica" else ayuda}.get(clave, ayuda)
            self.texto(0.16 * w, y + 0.034 * h, ayuda_texto, 11, aclarar(FONDOS[a["fondo"]]["brillo"], 0.9), False,
                       "nw", 0.40 * w)
            getattr(self, "control_" + tipo)(y, clave, datos)
        self.boton(0.12 * w, 0.89 * h, 0.40 * w, 0.96 * h, "Restablecer", self.secundario(), self.restablecer,
                   tamano=15)
        self.boton(0.60 * w, 0.89 * h, 0.88 * w, 0.96 * h, "Volver", ORO, self.volver, TINTA, 16)

    def control_selector(self, y, clave, opciones):
        w, h = self.ancho, self.alto
        inicio, fin, hueco = 0.58 * w, 0.84 * w, 0.006 * w
        ancho = (fin - inicio - hueco * (len(opciones) - 1)) / len(opciones)
        for numero, (valor, nombre) in enumerate(opciones):
            x1 = inicio + numero * (ancho + hueco)
            elegido = self.ajustes[clave] == valor
            self.boton(x1, y, x1 + ancho, y + 0.06 * h, nombre, ORO if elegido else self.secundario(),
                       lambda v=valor: self.cambiar(clave, v), TINTA if elegido else BLANCO, 14)

    def control_contador(self, y, clave, limites):
        w, h = self.ancho, self.alto
        minimo, maximo = limites
        valor = self.ajustes[clave]
        self.boton(0.62 * w, y, 0.66 * w, y + 0.06 * h, "−", self.secundario(),
                   lambda: self.cambiar(clave, max(minimo, valor - 1)), tamano=18)
        self.texto(0.71 * w, y + 0.03 * h, str(valor), 22, ORO, True)
        self.boton(0.76 * w, y, 0.80 * w, y + 0.06 * h, "+", self.secundario(),
                   lambda: self.cambiar(clave, min(maximo, valor + 1)), tamano=18)

    def control_interruptor(self, y, clave, _datos):
        w, h = self.ancho, self.alto
        activo = self.ajustes[clave]
        x1, x2, y1, y2 = 0.74 * w, 0.80 * w, y + 0.005 * h, y + 0.055 * h
        rect_redondo(self.lienzo, x1, y1, x2, y2, (y2 - y1) / 2, fill=VERDE if activo else GRIS, outline="",
                     tags=("ui", f"i{clave}"))
        radio = (y2 - y1) / 2 - 4
        cx = x2 - (y2 - y1) / 2 if activo else x1 + (y2 - y1) / 2
        self.lienzo.create_oval(cx - radio, (y1 + y2) / 2 - radio, cx + radio, (y1 + y2) / 2 + radio, fill=BLANCO,
                                outline="", tags=("ui", f"i{clave}"))
        self.texto(x2 + 0.015 * w, (y1 + y2) / 2, "Sí" if activo else "No", 14, BLANCO, True, "w")
        self.lienzo.tag_bind(f"i{clave}", "<Button-1>", lambda _: self.cambiar(clave, not activo))
        self.lienzo.tag_bind(f"i{clave}", "<Enter>", lambda _: self.lienzo.configure(cursor="hand2"))
        self.lienzo.tag_bind(f"i{clave}", "<Leave>", lambda _: self.lienzo.configure(cursor=""))


def main():
    Akinator().mainloop()


if __name__ == "__main__":
    main()
