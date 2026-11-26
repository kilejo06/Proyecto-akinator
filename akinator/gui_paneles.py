"""Paneles de estado interno: reglas, hechos, candidatos, algoritmo y cadena de la solución."""
import math
import tkinter.font as tkfont

from gui_dibujo import FONDOS, ORO, TINTA, aclarar, mezclar, rect_redondo
from utils import nombre_legible

PESTANAS = (("reglas", "Reglas"), ("hechos", "Hechos"), ("candidatos", "Candidatos"), ("algoritmo", "Algoritmo"))
RESPUESTAS = {"si": "Sí", "no": "No", "no_se": "No sé"}
COLOR_REGLA = {"ninguna": "#64748b", "evaluada": "#3b82f6", "ahora": "#22c55e", "antes": "#15803d"}
ROJO_DESCARTE, GRIS_DESCARTE = "#dc2626", "#334155"
BLANCO = "#ffffff"
DEDUCIDO = "#f5b301"
PASOS_FADE = 8
PASO = object()
MS_CADENA = 700
MOTIVOS = {"acerto": "acertó", "sin_candidatos": "se quedó sin candidatos", "limite_de_preguntas": "llegó al límite de preguntas",
           "sin_preguntas_utiles": "no quedaron preguntas útiles"}


class PanelesMixin:
    def compacto(self):
        return self.vista == "reproduccion" or self.ajustes["razonamiento"]

    def resumen_paso(self, historial, indice):
        paso, tipo = historial[indice], historial[indice]["tipo"]
        if tipo == "inicio":
            return "Aquí verás qué reglas se activan, a quién descarto, quiénes quedan y cómo cambia el puntaje."
        quien = "El agente respondió" if self.vista == "reproduccion" else "Respondiste"
        if tipo == "pregunta":
            titulo = f"{quien} «{RESPUESTAS[paso['respuesta']]}» a: {paso['pregunta']}"
        elif tipo == "adivinar":
            titulo = f"{'Acerté' if paso['acerto'] else 'Fallé'} con {nombre_legible(paso['candidato_adivinado'])}"
        else:
            titulo = "Fin de la partida"
        if self.ajustes["puntaje"]:
            delta = paso["puntos"] - historial[indice - 1]["puntos"]
            titulo += f"   ·   Puntaje {delta:+d} (total {paso['puntos']})".replace("-", "−")
        return titulo + f"   ·   Descartados: {len(paso['descartados'])}   ·   Quedan: {len(paso['candidatos'])}"

    def panel_detalle(self, historial, indice, decision=PASO):
        w, h = self.ancho, self.alto
        paso = historial[indice]
        self.texto(0.05 * w, 0.518 * h, self.resumen_paso(historial, indice), 11, "#fde68a", True, "w", 0.90 * w)
        pestanas = list(PESTANAS) + ([("solucion", "Solución")] if paso["tipo"] == "fin" else [])
        if self.pestana not in dict(pestanas):
            self.pestana = "reglas"
        ancho, hueco = 0.14 * w, 0.008 * w
        for numero, (clave, nombre) in enumerate(pestanas):
            x = 0.05 * w + numero * (ancho + hueco)
            activa = self.pestana == clave
            self.boton(x, 0.55 * h, x + ancho, 0.60 * h, nombre, ORO if activa else self.secundario(),
                       lambda c=clave: self.elegir_pestana(c, historial), TINTA if activa else BLANCO, 12)
        panel = FONDOS[self.ajustes["fondo"]]["panel"]
        caja = (0.05 * w, 0.615 * h, 0.95 * w, 0.985 * h)
        rect_redondo(self.lienzo, *caja, 16 * self.escala, fill=panel, outline=aclarar(panel, 1.8), width=2,
                     tags="ui")
        interior = (caja[0] + 0.015 * w, caja[1] + 0.012 * h, caja[2] - 0.015 * w, caja[3] - 0.012 * h)
        decision = paso["decision"] if decision is PASO else decision
        if self.pestana == "reglas":
            self.dibujar_reglas(interior, historial, indice)
        elif self.pestana == "hechos":
            self.dibujar_hechos(interior, historial, indice)
        elif self.pestana == "candidatos":
            self.dibujar_candidatos(interior, paso)
        elif self.pestana == "algoritmo":
            self.dibujar_algoritmo(interior, paso, decision)
        else:
            self.dibujar_cadena(interior, historial)

    def elegir_pestana(self, clave, historial):
        self.pestana = clave
        self.detener_cadena()
        if clave == "solucion":
            self.cadena_n = 0
            self.avanzar_cadena(len(self.lineas_cadena(historial)))
        self.refrescar()

    def avanzar_cadena(self, total):
        self.cadena_n += 1
        self.refrescar()
        if self.cadena_n < total:
            self.timer_cadena = self.after(MS_CADENA, lambda: self.avanzar_cadena(total))
        else:
            self.timer_cadena = None

    def detener_cadena(self):
        if self.timer_cadena is not None:
            self.after_cancel(self.timer_cadena)
        self.timer_cadena = None

    def fuente_medida(self, tamano, negrita=False):
        return tkfont.Font(root=self, font=self.fuente(tamano, negrita))

    # --- Reglas -----------------------------------------------------------------

    def dibujar_reglas(self, caja, historial, indice):
        x1, y1, x2, y2 = caja
        paso = historial[indice]
        previas = {r for s in historial[:indice] for r in s["reglas_disparadas"]}
        leyenda = (("ninguna", "no revisada"), ("evaluada", "evaluada, no se cumplió"),
                   ("ahora", "disparada en este paso"), ("antes", "disparada antes"))
        x = x1
        for estado, texto in leyenda:
            self.lienzo.create_rectangle(x, y1 + 3, x + 12 * self.escala, y1 + 3 + 12 * self.escala,
                                         fill=COLOR_REGLA[estado], outline="", tags="ui")
            x += 18 * self.escala
            id_texto = self.texto(x, y1 + 9 * self.escala, texto, 10, BLANCO, False, "w")
            x = self.lienzo.bbox(id_texto)[2] + 22 * self.escala
        reglas = self.base.reglas
        columnas = 1 if len(reglas) <= 14 else 2
        filas = math.ceil(len(reglas) / columnas)
        arriba = y1 + 26 * self.escala
        alto_fila = min(0.045 * self.alto, (y2 - arriba) / filas)
        ancho_columna = (x2 - x1) / columnas
        for numero, regla in enumerate(reglas):
            columna, fila = divmod(numero, filas)
            x, y = x1 + columna * ancho_columna, arriba + fila * alto_fila
            if regla["id"] in paso["reglas_disparadas"]:
                estado = "ahora"
            elif regla["id"] in previas:
                estado = "antes"
            elif regla["id"] in paso["reglas_evaluadas"]:
                estado = "evaluada"
            else:
                estado = "ninguna"
            self.lienzo.create_rectangle(x, y + alto_fila * 0.2, x + 10 * self.escala, y + alto_fila * 0.2 + 10 * self.escala,
                                         fill=COLOR_REGLA[estado], outline="", tags="ui")
            texto = f"{regla['id']}  {' y '.join(regla['si'])} → {regla['entonces']}"
            self.texto(x + 16 * self.escala, y + alto_fila * 0.2 + 5 * self.escala, texto, 10,
                       "#94a3b8" if estado == "ninguna" else BLANCO, estado == "ahora", "w")

    # --- Hechos -----------------------------------------------------------------

    def dibujar_hechos(self, caja, historial, indice):
        x1, y1, x2, y2 = caja
        paso = historial[indice]
        deducidos = {a for s in historial[:indice + 1] for a in s["hechos_nuevos"]}
        nuevos = set(paso["hechos_nuevos"])
        if paso["tipo"] == "pregunta" and paso["respuesta"] != "no_se":
            nuevos.add(paso["atributo"])
        r = 6 * self.escala
        x = x1
        for forma, color, texto in (("c", "#22c55e", "respondiste sí"), ("c", "#ef4444", "respondiste no"),
                                    ("d", DEDUCIDO, "deducido por una regla"), ("n", BLANCO, "borde grueso = nuevo")):
            if forma != "n":
                self.forma_hecho(forma, x + r, y1 + 9 * self.escala, r, color, 1)
                x += 2 * r + 6 * self.escala
            id_texto = self.texto(x, y1 + 9 * self.escala, texto, 10, BLANCO, False, "w")
            x = self.lienzo.bbox(id_texto)[2] + 22 * self.escala
        hechos = paso["hechos_conocidos"]
        if not hechos:
            self.texto(x1, y1 + 40 * self.escala, "Aún no hay hechos: respóndeme algo para empezar.", 12, BLANCO,
                       False, "w")
            return
        medida = self.fuente_medida(11)
        x, y = x1, y1 + 30 * self.escala
        for atributo, valor in hechos.items():
            deducido = atributo in deducidos
            etiqueta = f"{nombre_legible(atributo)}: {'sí' if valor else 'no'}"
            ancho = 2 * r + 6 * self.escala + medida.measure(etiqueta) + 18 * self.escala
            if x + ancho > x2:
                x, y = x1, y + 26 * self.escala
            color = DEDUCIDO if deducido else ("#22c55e" if valor else "#ef4444")
            self.forma_hecho("d" if deducido else "c", x + r, y + r, r, color, 3 if atributo in nuevos else 1)
            self.texto(x + 2 * r + 6 * self.escala, y + r, etiqueta, 11, BLANCO, atributo in nuevos, "w")
            x += ancho

    def forma_hecho(self, forma, cx, cy, r, color, grosor):
        opciones = {"fill": color, "outline": BLANCO if grosor > 1 else aclarar(color, 0.6), "width": grosor,
                    "tags": "ui"}
        if forma == "d":
            self.lienzo.create_polygon(cx, cy - r * 1.25, cx + r * 1.25, cy, cx, cy + r * 1.25, cx - r * 1.25, cy,
                                       **opciones)
        else:
            self.lienzo.create_oval(cx - r, cy - r, cx + r, cy + r, **opciones)

    # --- Candidatos -------------------------------------------------------------

    def dibujar_candidatos(self, caja, paso):
        x1, y1, x2, y2 = caja
        nombres = list(self.base.candidatos)
        columnas = 7 if len(nombres) <= 35 else 10
        filas = math.ceil(len(nombres) / columnas)
        x = x1
        for color, texto in (("#15803d", "activo"), (ROJO_DESCARTE, "descartado ahora"),
                             (GRIS_DESCARTE, "descartado antes"), (ORO, "hipótesis actual")):
            self.lienzo.create_rectangle(x, y1 + 3, x + 12 * self.escala, y1 + 3 + 12 * self.escala,
                                         fill=color, outline="", tags="ui")
            x += 18 * self.escala
            id_texto = self.texto(x, y1 + 9 * self.escala, texto, 10, BLANCO, False, "w")
            x = self.lienzo.bbox(id_texto)[2] + 22 * self.escala
        hueco = 0.005 * self.ancho
        arriba = y1 + 26 * self.escala
        ancho = (x2 - x1 - hueco * (columnas - 1)) / columnas
        alto = min(0.05 * self.alto, (y2 - arriba - hueco * (filas - 1)) / filas)
        recien = []
        for numero, nombre in enumerate(nombres):
            fila, columna = divmod(numero, columnas)
            x, y = x1 + columna * (ancho + hueco), arriba + fila * (alto + hueco)
            if nombre in paso["candidatos"]:
                color, texto = "#15803d", BLANCO
            elif nombre in paso["descartados"]:
                color, texto = ROJO_DESCARTE, BLANCO
            else:
                color, texto = GRIS_DESCARTE, "#94a3b8"
            forma = rect_redondo(self.lienzo, x, y, x + ancho, y + alto, 8 * self.escala, fill=color,
                                 outline=ORO if nombre == paso["hipotesis"] else "", width=3, tags="ui")
            if nombre in paso["descartados"]:
                recien.append(forma)
            self.texto(x + ancho / 2, y + alto / 2, nombre_legible(nombre), 10, texto)
        if recien and self.ajustes["animaciones"]:
            self.animar_descarte(recien, 0)

    def animar_descarte(self, formas, numero):
        for forma in formas:
            self.lienzo.itemconfigure(forma, fill=mezclar(ROJO_DESCARTE, GRIS_DESCARTE, numero / PASOS_FADE))
        if numero < PASOS_FADE:
            self.fade = self.after(110, lambda: self.animar_descarte(formas, numero + 1))
        else:
            self.fade = None

    # --- Algoritmo --------------------------------------------------------------

    def dibujar_algoritmo(self, caja, paso, decision):
        x1, y1, x2, y2 = caja
        mitad = x1 + 0.56 * (x2 - x1)
        linea = 22 * self.escala
        y = y1
        metodo = paso["metodo"]
        nombres = {"heuristica": "Selección por heurística", "adelante": "Encadenamiento hacia adelante",
                   "atras": "Encadenamiento hacia atrás"}
        self.texto(x1, y, nombres[metodo], 13, ORO, True, "nw")
        y += linea * 1.3
        if decision is not None and decision.get("adivina"):
            lineas = [f"Adivino la mejor hipótesis: {nombre_legible(decision['adivina'])}",
                      f"Quedan {len(paso['candidatos'])} candidato(s)"]
            for texto in lineas:
                self.texto(x1, y, texto, 11, BLANCO, False, "nw", mitad - x1 - 10)
                y += linea
        elif decision is None:
            for texto in self.texto_sin_decision(paso):
                self.texto(x1, y, texto, 11, BLANCO, False, "nw", mitad - x1 - 10)
                y += linea
        elif decision["metodo"] == "heuristica":
            criterio = ("|sí − no| (menor es mejor)" if decision["criterio"] == "mitad"
                        else "entropía (mayor es mejor)")
            self.texto(x1, y, f"Heurística {decision['criterio']}: {criterio}", 11, BLANCO, False, "nw",
                       mitad - x1 - 10)
            y += linea * 1.4
            for atributo, valor in decision["valores"]:
                elegido = atributo == decision["atributo"]
                self.texto(x1, y, f"{'►' if elegido else ' '} {nombre_legible(atributo)}", 11,
                           ORO if elegido else BLANCO, elegido, "nw")
                self.texto(x1 + 0.30 * (x2 - x1), y, f"{valor:.3f}" if decision["criterio"] != "mitad"
                           else f"{valor:.0f}", 11, ORO if elegido else BLANCO, elegido, "nw")
                y += linea
        elif decision["metodo"] == "atras":
            lineas = [f"Hipótesis actual: {nombre_legible(decision.get('hipotesis', '—'))}",
                      f"Pregunto: {nombre_legible(decision['atributo'])}"]
            if decision.get("regla"):
                regla = next(r for r in self.base.reglas if r["id"] == decision["regla"])
                lineas.append(f"Siguiendo la regla {regla['id']}: {' y '.join(regla['si'])} → {regla['entonces']}")
            if decision.get("separa") is not None:
                lineas.append(f"Esa propiedad separa a la hipótesis de {decision['separa']} candidato(s)")
            for texto in lineas:
                self.texto(x1, y, texto, 11, BLANCO, False, "nw", mitad - x1 - 10)
                y += linea * (2 if len(texto) > 50 else 1)
        else:
            posicion, total = decision["posicion"]
            lineas = [f"Pregunto: {nombre_legible(decision['atributo'])}",
                      f"Es el atributo {posicion} de {total} en el orden fijo de los datos",
                      "Sin elegir el mejor: sigo el orden y deduzco con las reglas."]
            for texto in lineas:
                self.texto(x1, y, texto, 11, BLANCO, False, "nw", mitad - x1 - 10)
                y += linea * (2 if len(texto) > 50 else 1)
        self.dibujar_metricas((mitad + 10, y1, x2, y2), paso)

    def texto_sin_decision(self, paso):
        if paso["tipo"] == "inicio":
            return ["Aún no se ha tomado ninguna decisión.", f"Candidatos iniciales: {len(paso['candidatos'])}"]
        if paso["tipo"] != "fin":
            return ["Esperando la siguiente decisión del agente."]
        resumen = paso["resumen"]
        return [f"Motivo: {MOTIVOS.get(resumen['motivo'], resumen['motivo'])}",
                f"Longitud: {resumen['preguntas']} preguntas (mínimo teórico {resumen['minimo_teorico']})",
                f"Costo (puntaje): {resumen['puntaje']}", f"¿Óptima?: {'sí' if resumen['optima'] else 'no'}"]

    def dibujar_metricas(self, caja, paso):
        x1, y1, x2, y2 = caja
        m = paso["metricas"]
        self.texto(x1, y1, "Métricas acumuladas", 13, ORO, True, "nw")
        filas = [("Reglas evaluadas", m["reglas_evaluadas"]), ("Reglas disparadas", m["reglas_disparadas"]),
                 ("Hechos inferidos", m["hechos_inferidos"]), ("Nodos generados", m["nodos_generados"]),
                 ("Memoria máx. (candidatos / hechos)", f"{m['max_candidatos']} / {m['max_hechos']}")]
        if paso["metodo"] == "atras":
            filas.append(("Hipótesis probadas", m["hipotesis_probadas"]))
        filas.append(("Tiempo del agente", f"{m['tiempo'] * 1000:.2f} ms"))
        y = y1 + 28 * self.escala
        for nombre, valor in filas:
            self.texto(x1, y, nombre, 11, BLANCO, False, "nw")
            self.texto(x2, y, str(valor), 11, BLANCO, True, "ne")
            y += 21 * self.escala

    # --- Solución ---------------------------------------------------------------

    def lineas_cadena(self, historial):
        reglas = {r["id"]: r for r in self.base.reglas}
        lineas = []
        for paso in historial:
            if paso["tipo"] == "pregunta":
                respuesta = {"si": "sí", "no": "no", "no_se": "no sé"}[paso["respuesta"]]
                texto = f"{nombre_legible(paso['atributo'])} = {respuesta}"
                if paso["reglas_disparadas"]:
                    texto += "   →   " + ";   ".join(f"{i}: {reglas[i]['entonces']}" for i in paso["reglas_disparadas"])
                lineas.append(texto)
            elif paso["tipo"] == "adivinar":
                nombre = nombre_legible(paso["candidato_adivinado"]).upper()
                lineas.append(f"⇒ {nombre}" if paso["acerto"] else f"✘ No era {nombre}")
        return lineas

    def dibujar_cadena(self, caja, historial):
        x1, y1, x2, y2 = caja
        lineas = self.lineas_cadena(historial)
        self.texto(x1, y1, "Cadena de inferencias que llevó a la respuesta", 13, ORO, True, "nw")
        visibles = lineas[:self.cadena_n]
        linea = min(24 * self.escala, (y2 - y1 - 30 * self.escala) / max(1, len(lineas)))
        y = y1 + 28 * self.escala
        for texto in visibles:
            final = texto.startswith("⇒")
            self.texto(x1, y, texto, 13 if final else 11, ORO if final else BLANCO, final, "nw", x2 - x1)
            y += linea
