"""Menú principal y bucle del juego."""
from agente import (ACERTO, LIMITE, SIN_CANDIDATOS, SIN_PREGUNTAS_UTILES, adivinar,
                    crear_estado, debe_parar, elegir_hipotesis, procesar_respuesta)
from base_conocimiento import MODOS, cargar_base
from heuristica import HEURISTICAS
from motor_inferencia import encadenamiento_atras
from utils import (confirmar_adivinanza, imprimir_traza, pedir_opcion, pedir_respuesta,
                   pedir_si_no)

UMBRAL_ATRAS = 3


def elegir_atributo(estado, base, heuristica, hipotesis):
    if len(estado.candidatos) <= UMBRAL_ATRAS:
        return encadenamiento_atras(hipotesis, estado, base)
    return heuristica(estado, base)


def jugar(base, heuristica, responder, confirmar, mostrar=None):
    """responder(atributo, pregunta) -> 'si'/'no'/'no_se'; confirmar(candidato) -> bool."""
    estado = crear_estado(base)
    while True:
        motivo = debe_parar(estado, base)
        if motivo in (ACERTO, SIN_CANDIDATOS):
            break
        hipotesis = elegir_hipotesis(estado)
        # Al llegar al límite se hace un último intento con la mejor hipótesis
        atributo = None
        if motivo is None:
            atributo = elegir_atributo(estado, base, heuristica, hipotesis)
        if atributo is None:
            adivinar(estado, hipotesis, confirmar)
            if motivo == LIMITE:
                motivo = ACERTO if estado.acerto else LIMITE
                break
            continue
        respuesta = responder(atributo, base.preguntas[atributo])
        activadas, descartados = procesar_respuesta(estado, base, atributo, respuesta)
        if mostrar:
            mostrar(estado, base, atributo, respuesta, activadas, descartados)
    return estado, debe_parar(estado, base) or motivo


def mostrar_resultado(estado, motivo):
    print("-" * 40)
    if estado.acerto:
        print("¡Lo adiviné!")
    elif motivo == SIN_CANDIDATOS:
        print("No conozco nada que encaje con tus respuestas.")
        input("¿En qué estabas pensando? ")
        print("Gracias, lo tendré en cuenta para la próxima.")
    else:
        print("No logré adivinar.")
    print(f"Preguntas hechas: {estado.num_preguntas} | Puntaje final: {estado.puntos}")


def main():
    nombres_heuristicas = list(HEURISTICAS)
    while True:
        modo = MODOS[pedir_opcion("Modo de juego", ["Animales", "Países", "Mixto"])]
        heuristica = HEURISTICAS[nombres_heuristicas[pedir_opcion(
            "Heurística para elegir preguntas", ["Mitad", "Entropía", "Aleatoria"])]]
        explicar = pedir_si_no("¿Activar el modo explicación?")

        print("\nPiensa en algo y responde sí, no o no sé.\n")
        base = cargar_base(modo)
        estado, motivo = jugar(base, heuristica, lambda _, pregunta: pedir_respuesta(pregunta),
                               confirmar_adivinanza, imprimir_traza if explicar else None)
        mostrar_resultado(estado, motivo)
        if not pedir_si_no("\n¿Jugar otra vez?"):
            break


if __name__ == "__main__":
    main()
