"""Dibujo de la interfaz: fondo, personaje y botones, todo sobre un lienzo."""
import math
import random
import tkinter as tk

FONDOS = {
    "noche": {"arriba": "#150f4f", "abajo": "#6d28d9", "panel": "#1d1466", "brillo": "#c4b5fd"},
    "atardecer": {"arriba": "#4a1942", "abajo": "#ea580c", "panel": "#4a1d3f", "brillo": "#fed7aa"},
    "oceano": {"arriba": "#022c44", "abajo": "#0d9488", "panel": "#06364d", "brillo": "#99f6e4"},
}
ORO = "#f5b301"
TINTA = "#1f1147"


def a_rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def a_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(v))) for v in rgb)


def mezclar(color_a, color_b, t):
    return a_hex(tuple(a + (b - a) * t for a, b in zip(a_rgb(color_a), a_rgb(color_b))))


def aclarar(color, factor):
    return a_hex(tuple(v * factor for v in a_rgb(color)))


def degradado(ancho, alto, arriba, abajo):
    imagen = tk.PhotoImage(width=ancho, height=alto)
    for y in range(alto):
        imagen.put(mezclar(arriba, abajo, y / max(1, alto - 1)), to=(0, y, ancho, y + 1))
    return imagen


def rect_redondo(lienzo, x1, y1, x2, y2, radio, **opciones):
    puntos = [x1 + radio, y1, x2 - radio, y1, x2, y1, x2, y1 + radio, x2, y2 - radio, x2, y2,
              x2 - radio, y2, x1 + radio, y2, x1, y2, x1, y2 - radio, x1, y1 + radio, x1, y1]
    return lienzo.create_polygon(puntos, smooth=True, **opciones)


def estrella(cx, cy, radio):
    puntos = []
    for i in range(10):
        r = radio if i % 2 == 0 else radio * 0.45
        angulo = -math.pi / 2 + i * math.pi / 5
        puntos += [cx + r * math.cos(angulo), cy + r * math.sin(angulo)]
    return puntos


def dibujar_fondo(lienzo, ancho, alto, nombre, semilla=7):
    """Degradado con estrellas y destellos. Devuelve (imagen, ids de estrellas)."""
    paleta = FONDOS[nombre]
    lienzo.delete("fondo")
    imagen = degradado(ancho, alto, paleta["arriba"], paleta["abajo"])
    lienzo.create_image(0, 0, anchor="nw", image=imagen, tags="fondo")
    azar = random.Random(semilla)
    for _ in range(7):
        x, y, r = azar.random() * ancho, azar.random() * alto, (0.05 + azar.random() * 0.1) * alto
        base = mezclar(paleta["arriba"], paleta["abajo"], y / alto)
        lienzo.create_oval(x - r, y - r, x + r, y + r, fill=mezclar(base, paleta["brillo"], 0.09), outline="",
                           tags="fondo")
    estrellas = []
    for _ in range(70):
        x, y, r = azar.random() * ancho, azar.random() * alto * 0.85, 1 + azar.random() * 2.2
        color = "#ffffff" if azar.random() < 0.7 else "#fde68a"
        estrellas.append(lienzo.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="", tags="fondo"))
    lienzo.tag_lower("fondo")
    return imagen, estrellas


def dibujar_mago(lienzo, cx, cy, u, expresion, fondo):
    """Mago de cuento hecho con formas. u es la unidad de tamaño; fondo es el color detrás del halo."""
    kw = {"tags": ("mago",)}
    for radio, mezcla in ((2.8, 0.10), (2.2, 0.18)):
        lienzo.create_oval(cx - radio * u, cy + 0.2 * u - radio * u, cx + radio * u, cy + 0.2 * u + radio * u,
                           fill=mezclar(fondo, "#ffffff", mezcla), outline="", **kw)
    lienzo.create_polygon(cx - 0.6 * u, cy + 0.5 * u, cx + 0.6 * u, cy + 0.5 * u, cx + 1.25 * u, cy + 2.6 * u,
                          cx - 1.25 * u, cy + 2.6 * u, fill="#5b21b6", outline="#3b0f7a", width=2, **kw)
    lienzo.create_polygon(cx - 0.9 * u, cy + 1.25 * u, cx + 0.9 * u, cy + 1.25 * u, cx + 0.95 * u, cy + 1.45 * u,
                          cx - 0.95 * u, cy + 1.45 * u, fill=ORO, outline="", **kw)
    for lado in (-1, 1):
        lienzo.create_oval(cx + lado * 1.05 * u - 0.28 * u, cy + 0.95 * u - 0.45 * u,
                           cx + lado * 1.05 * u + 0.28 * u, cy + 0.95 * u + 0.45 * u,
                           fill="#6d28d9", outline="#3b0f7a", width=2, **kw)
        lienzo.create_oval(cx + lado * 1.12 * u - 0.2 * u, cy + 1.3 * u - 0.2 * u,
                           cx + lado * 1.12 * u + 0.2 * u, cy + 1.3 * u + 0.2 * u,
                           fill="#f1c27d", outline="", **kw)
    ox, oy = cx + 1.75 * u, cy + 1.2 * u
    lienzo.create_oval(ox - 0.5 * u, oy - 0.5 * u, ox + 0.5 * u, oy + 0.5 * u, fill="#a5f3fc",
                       outline="#22d3ee", width=3, **kw)
    lienzo.create_oval(ox - 0.3 * u, oy - 0.33 * u, ox - 0.1 * u, oy - 0.13 * u, fill="#ffffff", outline="", **kw)
    lienzo.create_polygon(cx - 0.55 * u, cy + 0.2 * u, cx + 0.55 * u, cy + 0.2 * u, cx + 0.4 * u, cy + 1.0 * u,
                          cx, cy + 1.55 * u, cx - 0.4 * u, cy + 1.0 * u, fill="#f5f5f4", outline="#d6d3d1",
                          width=2, **kw)
    lienzo.create_oval(cx - 0.6 * u, cy - 0.6 * u, cx + 0.6 * u, cy + 0.6 * u, fill="#f1c27d",
                       outline="#c8964f", width=2, **kw)
    lienzo.create_polygon(cx - 0.95 * u, cy - 0.3 * u, cx + 0.95 * u, cy - 0.3 * u, cx + 0.4 * u, cy - 1.4 * u,
                          cx + 0.75 * u, cy - 2.2 * u, cx - 0.15 * u, cy - 1.6 * u, fill="#4c1d95",
                          outline="#2e1065", width=2, **kw)
    lienzo.create_polygon(cx - 0.97 * u, cy - 0.5 * u, cx + 0.97 * u, cy - 0.5 * u, cx + 0.95 * u, cy - 0.28 * u,
                          cx - 0.95 * u, cy - 0.28 * u, fill=ORO, outline="", **kw)
    lienzo.create_polygon(estrella(cx + 0.1 * u, cy - 1.0 * u, 0.2 * u), fill=ORO, outline="", **kw)
    _cara(lienzo, cx, cy, u, expresion)


def _cara(lienzo, cx, cy, u, expresion):
    kw = {"tags": ("mago",)}
    ancho = max(2, int(u * 0.07))
    for lado in (-1, 1):
        ex, ey = cx + lado * 0.24 * u, cy - 0.05 * u
        if expresion == "feliz":
            lienzo.create_arc(ex - 0.13 * u, ey - 0.1 * u, ex + 0.13 * u, ey + 0.16 * u, start=0, extent=180,
                              style="arc", outline=TINTA, width=ancho, **kw)
            continue
        desplazamiento = {"pensando": (0.04, -0.05), "triste": (0, 0.05)}.get(expresion, (0, 0))
        radio = 0.17 if expresion == "sorprendido" else 0.12
        lienzo.create_oval(ex - radio * u, ey - radio * u, ex + radio * u, ey + radio * u, fill="#ffffff",
                           outline=TINTA, width=1, **kw)
        px, py = ex + desplazamiento[0] * u, ey + desplazamiento[1] * u
        lienzo.create_oval(px - 0.06 * u, py - 0.06 * u, px + 0.06 * u, py + 0.06 * u, fill=TINTA, outline="", **kw)
        alto_ceja = 0.26 if expresion != "pensando" or lado == 1 else 0.36
        inclinacion = {"triste": 0.07 * lado, "sorprendido": -0.04}.get(expresion, -0.02)
        lienzo.create_line(ex - 0.13 * u, ey - (alto_ceja - inclinacion) * u, ex + 0.13 * u,
                           ey - (alto_ceja + inclinacion) * u, fill="#7c5a2a", width=ancho, **kw)
    if expresion == "feliz":
        lienzo.create_arc(cx - 0.22 * u, cy + 0.12 * u, cx + 0.22 * u, cy + 0.46 * u, start=200, extent=140,
                          style="chord", fill="#9f1239", outline="#7f1d1d", **kw)
    elif expresion == "triste":
        lienzo.create_arc(cx - 0.18 * u, cy + 0.32 * u, cx + 0.18 * u, cy + 0.58 * u, start=20, extent=140,
                          style="arc", outline="#7f1d1d", width=ancho, **kw)
    elif expresion == "sorprendido":
        lienzo.create_oval(cx - 0.08 * u, cy + 0.22 * u, cx + 0.08 * u, cy + 0.4 * u, fill="#9f1239",
                           outline="#7f1d1d", **kw)
    else:
        lienzo.create_line(cx - 0.13 * u, cy + 0.3 * u, cx + 0.13 * u, cy + 0.3 * u, fill="#7f1d1d", width=ancho,
                           capstyle="round", **kw)
