"""Menú principal y bucle del juego."""
from agente import LIMITE_PREGUNTAS, SIN_CANDIDATOS
from base_conocimiento import MODOS, cargar_base
from heuristica import HEURISTICAS
from partida import METODOS, Partida
from utils import (confirmar_adivinanza, imprimir_traza, pedir_opcion, pedir_respuesta,
                   pedir_si_no)


def jugar(base, metodo, heuristica, responder, confirmar, mostrar=None, limite_preguntas=LIMITE_PREGUNTAS):
    """responder(atributo, pregunta) -> 'si'/'no'/'no_se'; confirmar(candidato) -> bool."""
    partida = Partida(base, metodo, heuristica, limite_preguntas, detalle=False)
    while True:
        accion = partida.siguiente()
        if accion["tipo"] == "fin":
            return partida.estado, partida.motivo
        if accion["tipo"] == "adivinar":
            partida.confirmar(confirmar(accion["candidato"]))
            continue
        respuesta = responder(accion["atributo"], accion["pregunta"])
        activadas, descartados = partida.responder(respuesta)
        if mostrar:
            mostrar(partida.estado, base, accion["atributo"], respuesta, activadas, descartados)


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
        metodo = METODOS[pedir_opcion("Método de razonamiento", [
            "Selección por heurística", "Encadenamiento hacia adelante", "Encadenamiento hacia atrás"])]
        heuristica = "mitad"
        if metodo == "heuristica":
            heuristica = nombres_heuristicas[pedir_opcion(
                "Heurística para elegir preguntas", ["Mitad", "Entropía"])]
        explicar = pedir_si_no("¿Activar el modo explicación?")

        print("\nPiensa en algo y responde sí, no o no sé.\n")
        base = cargar_base(modo)
        estado, motivo = jugar(base, metodo, heuristica, lambda _, pregunta: pedir_respuesta(pregunta),
                               confirmar_adivinanza, imprimir_traza if explicar else None)
        mostrar_resultado(estado, motivo)
        if not pedir_si_no("\n¿Jugar otra vez?"):
            break


if __name__ == "__main__":
    main()
