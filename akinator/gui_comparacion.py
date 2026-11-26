"""Ventana de comparación: los 4 métodos sobre la misma instancia, con tabla y gráfica de barras."""
from base_conocimiento import cargar_base
from comparacion import METODOS, comparar_metodo
from gui_dibujo import FONDOS, ORO, TINTA, aclarar, rect_redondo
from utils import nombre_legible

MODOS_COMPARACION = (("animales", "Animales"), ("paises", "Países"), ("mixto", "Mixto"))
USUARIOS = (("sin_errores", "Sin errores"), ("no_se", "30 % no sé"), ("miente", "Miente 1 vez"))
REPETICIONES_TODOS, REPETICIONES_UNO, PROB_NO_SE = 5, 30, 0.3
BLANCO = "#ffffff"
COLORES_METODOS = ("#f5b301", "#22c55e", "#3b82f6", "#ec4899")
# clave, encabezado, ancho relativo, formato, mejor ("min", "max" o None)
COLUMNAS = (
    ("metodo", "Método", 0.15, "{}", None), ("aciertos", "% aciertos", 0.07, "{:.1f}", "max"),
    ("preguntas", "Preguntas", 0.07, "{:.2f}", "min"), ("minimo_teorico", "Mínimo", 0.06, "{:.1f}", None),
    ("optimas", "% óptima", 0.07, "{:.1f}", "max"), ("tiempo_ms", "Tiempo ms", 0.08, "{:.2f}", "min"),
    ("nodos_generados", "Nodos gen.", 0.08, "{:.1f}", "min"), ("reglas_evaluadas", "Reglas eval.", 0.08, "{:.1f}", "min"),
    ("reglas_disparadas", "Reglas disp.", 0.08, "{:.1f}", None), ("hechos_inferidos", "Hechos inf.", 0.07, "{:.1f}", None),
    ("memoria", "Memoria", 0.10, "{}", None), ("puntaje", "Puntaje", 0.07, "{:.1f}", "max"),
)
METRICAS_GRAFICA = (("preguntas", "Preguntas", "min"), ("tiempo_ms", "Tiempo", "min"), ("nodos_generados", "Nodos", "min"),
                    ("reglas_evaluadas", "Reglas eval.", "min"), ("puntaje", "Puntaje", "max"),
                    ("aciertos", "% aciertos", "max"))


class ComparacionMixin:
    def abrir_comparacion(self):
        self.vista = "comparacion"
        self.refrescar()

    def detener_comparacion(self):
        if self.cmp_timer is not None:
            self.after_cancel(self.cmp_timer)
        self.cmp_timer = None
        if self.cmp_corriendo:
            self.cmp_corriendo, self.cmp_filas, self.cmp_estado = False, [], "Comparación cancelada."

    def base_comparacion(self):
        if self.cmp_modo not in self.cmp_bases:
            self.cmp_bases[self.cmp_modo] = cargar_base(self.cmp_modo)
        return self.cmp_bases[self.cmp_modo]

    def cambiar_opcion_cmp(self, clave, valor):
        if self.cmp_corriendo:
            return
        setattr(self, clave, valor)
        if clave == "cmp_modo":
            self.cmp_secreto = None
        self.cmp_filas, self.cmp_estado = [], ""
        self.refrescar()

    def mover_secreto(self, paso):
        if self.cmp_corriendo:
            return
        nombres = sorted(self.base_comparacion().candidatos)
        if self.cmp_secreto is None:
            indice = 0 if paso > 0 else len(nombres) - 1
        else:
            indice = (nombres.index(self.cmp_secreto) + paso) % len(nombres)
        self.cambiar_opcion_cmp("cmp_secreto", nombres[indice])

    def ejecutar_comparacion(self):
        if self.cmp_corriendo:
            return
        base = self.base_comparacion()
        secretos = list(base.candidatos) if self.cmp_secreto is None else [self.cmp_secreto]
        ruido = self.cmp_usuario != "sin_errores"
        repeticiones = (REPETICIONES_TODOS if self.cmp_secreto is None else REPETICIONES_UNO) if ruido else 1
        self.cmp_trabajo = (base, secretos, {"prob_no_se": PROB_NO_SE if self.cmp_usuario == "no_se" else 0.0,
                                            "mentir": self.cmp_usuario == "miente", "repeticiones": repeticiones})
        self.cmp_filas, self.cmp_pendientes, self.cmp_corriendo = [], list(METODOS), True
        self.siguiente_metodo()

    def siguiente_metodo(self):
        if not self.cmp_pendientes:
            self.cmp_corriendo, self.cmp_timer, self.cmp_estado = False, None, self.descripcion_instancia()
            self.refrescar()
            return
        metodo = self.cmp_pendientes.pop(0)
        self.cmp_estado = f"Comparando... {len(self.cmp_filas) + 1} de {len(METODOS)}: {metodo[0]}"
        self.refrescar()
        self.cmp_timer = self.after(40, lambda: self.correr_metodo(metodo))

    def correr_metodo(self, metodo):
        base, secretos, opciones = self.cmp_trabajo
        self.cmp_filas.append(comparar_metodo(base, secretos, metodo, self.ajustes["limite"], **opciones))
        self.siguiente_metodo()

    def descripcion_instancia(self):
        base = self.base_comparacion()
        modo = dict(MODOS_COMPARACION)[self.cmp_modo]
        secreto = "todos" if self.cmp_secreto is None else nombre_legible(self.cmp_secreto)
        usuario = dict(USUARIOS)[self.cmp_usuario].lower()
        return (f"{modo} · {len(base.candidatos)} candidatos · secreto: {secreto} · usuario: {usuario} "
                f"· límite {self.ajustes['limite']} preguntas")

    # --- Dibujo -----------------------------------------------------------------

    def selector_cmp(self, y, etiqueta, opciones, actual, clave, x_etiqueta, x1, x2):
        w, h = self.ancho, self.alto
        self.texto(x_etiqueta * w, y + 0.025 * h, etiqueta, 13, BLANCO, True, "w")
        hueco = 0.006 * w
        ancho = ((x2 - x1) * w - hueco * (len(opciones) - 1)) / len(opciones)
        for numero, (valor, nombre) in enumerate(opciones):
            x = x1 * w + numero * (ancho + hueco)
            elegido = actual == valor
            self.boton(x, y, x + ancho, y + 0.05 * h, nombre, ORO if elegido else self.secundario(),
                       lambda v=valor: self.cambiar_opcion_cmp(clave, v), TINTA if elegido else BLANCO, 12)

    def vista_comparacion(self):
        w, h = self.ancho, self.alto
        self.barra_superior("Comparar métodos")
        self.selector_cmp(0.115 * h, "Instancia", MODOS_COMPARACION, self.cmp_modo, "cmp_modo", 0.05, 0.14, 0.50)
        self.selector_cmp(0.115 * h, "Usuario", USUARIOS, self.cmp_usuario, "cmp_usuario", 0.53, 0.61, 0.95)
        y = 0.185 * h
        self.texto(0.05 * w, y + 0.025 * h, "Secreto", 13, BLANCO, True, "w")
        elegido = self.cmp_secreto is None
        self.boton(0.14 * w, y, 0.22 * w, y + 0.05 * h, "Todos", ORO if elegido else self.secundario(),
                   lambda: self.cambiar_opcion_cmp("cmp_secreto", None), TINTA if elegido else BLANCO, 12)
        self.boton(0.23 * w, y, 0.27 * w, y + 0.05 * h, "◀", self.secundario(), lambda: self.mover_secreto(-1),
                   tamano=12)
        self.texto(0.35 * w, y + 0.025 * h, "(elige uno)" if elegido else nombre_legible(self.cmp_secreto), 12,
                   "#a5f3fc" if elegido else BLANCO, not elegido)
        self.boton(0.43 * w, y, 0.47 * w, y + 0.05 * h, "▶", self.secundario(), lambda: self.mover_secreto(1),
                   tamano=12)
        self.boton(0.61 * w, y, 0.95 * w, y + 0.05 * h, "Comparando..." if self.cmp_corriendo else "Comparar",
                   ORO, self.ejecutar_comparacion, TINTA, 14)
        self.texto(0.05 * w, 0.265 * h, self.cmp_estado or self.descripcion_instancia(), 11, "#fde68a", False, "w",
                   0.90 * w)
        self.dibujar_tabla()
        self.dibujar_grafica()

    def valor_columna(self, fila, clave):
        if clave == "memoria":
            return f"{fila['max_candidatos']:.0f} / {fila['max_hechos']:.1f}"
        return fila[clave]

    def dibujar_tabla(self):
        w, h = self.ancho, self.alto
        panel = self.paleta_fondo()["panel"]
        x0, ancho_total, y0 = 0.05 * w, 0.90 * w, 0.29 * h
        alto_fila, alto_cabecera = 0.052 * h, 0.055 * h
        rect_redondo(self.lienzo, x0, y0, x0 + ancho_total, y0 + alto_cabecera + 4 * alto_fila + 6, 14 * self.escala,
                     fill=panel, outline=aclarar(panel, 1.8), width=2, tags="ui")
        x = x0
        posiciones = []
        for clave, encabezado, relativo, _, _ in COLUMNAS:
            ancho = relativo * ancho_total
            posiciones.append((x, ancho))
            self.texto(x + ancho / 2, y0 + alto_cabecera / 2, encabezado, 9, "#fde68a", True, ancho=ancho - 4)
            x += ancho
        mejores = {}
        for clave, _, _, _, criterio in COLUMNAS:
            if criterio and len(self.cmp_filas) == len(METODOS):
                valores = [fila[clave] for fila in self.cmp_filas]
                mejores[clave] = min(valores) if criterio == "min" else max(valores)
        for numero, metodo in enumerate(METODOS):
            y = y0 + alto_cabecera + numero * alto_fila
            self.lienzo.create_line(x0 + 10, y, x0 + ancho_total - 10, y, fill=aclarar(panel, 1.6), tags="ui")
            fila = self.cmp_filas[numero] if numero < len(self.cmp_filas) else None
            for (x, ancho), (clave, _, _, formato, _) in zip(posiciones, COLUMNAS):
                if clave == "metodo":
                    self.lienzo.create_rectangle(x + 8, y + alto_fila / 2 - 5, x + 18, y + alto_fila / 2 + 5,
                                                 fill=COLORES_METODOS[numero], outline="", tags="ui")
                    self.texto(x + 24, y + alto_fila / 2, metodo[3], 11, BLANCO, True, "w")
                    continue
                if fila is None:
                    self.texto(x + ancho / 2, y + alto_fila / 2, "·", 11, "#64748b")
                    continue
                valor = self.valor_columna(fila, clave)
                mejor = clave in mejores and abs(fila[clave] - mejores[clave]) < 1e-9
                if mejor:
                    rect_redondo(self.lienzo, x + 4, y + 5, x + ancho - 4, y + alto_fila - 5, 8 * self.escala,
                                 fill=ORO, outline="", tags="ui")
                self.texto(x + ancho / 2, y + alto_fila / 2, formato.format(valor), 11, TINTA if mejor else BLANCO,
                           mejor)

    def paleta_fondo(self):
        return FONDOS[self.ajustes["fondo"]]

    def dibujar_grafica(self):
        w, h = self.ancho, self.alto
        panel = self.paleta_fondo()["panel"]
        self.texto(0.05 * w, 0.625 * h, "Gráfica", 13, BLANCO, True, "w")
        hueco = 0.006 * w
        inicio, fin = 0.13 * w, 0.95 * w
        ancho = (fin - inicio - hueco * (len(METRICAS_GRAFICA) - 1)) / len(METRICAS_GRAFICA)
        for numero, (clave, nombre, _) in enumerate(METRICAS_GRAFICA):
            x = inicio + numero * (ancho + hueco)
            elegido = self.cmp_metrica == clave
            self.boton(x, 0.60 * h, x + ancho, 0.65 * h, nombre, ORO if elegido else self.secundario(),
                       lambda c=clave: self.elegir_metrica(c), TINTA if elegido else BLANCO, 11)
        x1, y1, x2, y2 = 0.05 * w, 0.67 * h, 0.95 * w, 0.975 * h
        rect_redondo(self.lienzo, x1, y1, x2, y2, 14 * self.escala, fill=panel, outline=aclarar(panel, 1.8), width=2,
                     tags="ui")
        if len(self.cmp_filas) < len(METODOS):
            self.texto((x1 + x2) / 2, (y1 + y2) / 2, "La gráfica aparece cuando termina la comparación.", 13,
                       "#a5f3fc")
            return
        clave = self.cmp_metrica
        criterio = next(c for k, _, c in METRICAS_GRAFICA if k == clave)
        valores = [fila[clave] for fila in self.cmp_filas]
        minimo = sum(f["minimo_teorico"] for f in self.cmp_filas) / len(self.cmp_filas)
        techo = max(valores + ([minimo] if clave == "preguntas" else [])) * 1.18 or 1
        base_y, tope_y = y2 - 0.075 * h, y1 + 0.06 * h
        self.lienzo.create_line(x1 + 20, base_y, x2 - 20, base_y, fill=aclarar(panel, 1.8), tags="ui")
        ranura = (x2 - x1 - 40) / len(valores)
        mejor = min(valores) if criterio == "min" else max(valores)
        for numero, fila in enumerate(self.cmp_filas):
            valor = fila[clave]
            cx = x1 + 20 + ranura * (numero + 0.5)
            alto = (base_y - tope_y) * valor / techo
            self.lienzo.create_rectangle(cx - ranura * 0.28, base_y - alto, cx + ranura * 0.28, base_y,
                                         fill=COLORES_METODOS[numero], outline="", tags="ui")
            es_mejor = abs(valor - mejor) < 1e-9
            self.texto(cx, base_y - alto - 12 * self.escala, f"{valor:.2f}" + (" ★" if es_mejor else ""), 12,
                       ORO if es_mejor else BLANCO, True)
            self.texto(cx, base_y + 0.035 * h, fila["corto"], 11, BLANCO, True)
        if clave == "preguntas":
            y = base_y - (base_y - tope_y) * minimo / techo
            self.lienzo.create_line(x1 + 20, y, x2 - 20, y, fill="#fca5a5", dash=(6, 4), width=2, tags="ui")
            self.texto(x1 + 24, y1 + 16 * self.escala, f"┄┄ mínimo teórico: {minimo:.1f} preguntas", 11, "#fca5a5",
                       False, "w")

    def elegir_metrica(self, clave):
        self.cmp_metrica = clave
        self.refrescar()
