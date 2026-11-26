"""Partida paso a paso: quien la maneja decide cuándo llega cada respuesta."""
import time

from agente import (ACERTO, LIMITE, LIMITE_PREGUNTAS, SIN_CANDIDATOS, adivinar, atributos_utiles,
                    crear_estado, debe_parar, elegir_hipotesis, procesar_respuesta,
                    resumen_metricas)
from heuristica import HEURISTICAS, valores_atributos
from motor_inferencia import encadenamiento_atras, explicar_atras

METODOS = ("heuristica", "adelante", "atras")


def elegir_atributo(estado, base, metodo, heuristica, hipotesis):
    if metodo == "atras":
        return encadenamiento_atras(hipotesis, estado, base)
    if metodo == "adelante":
        utiles = atributos_utiles(estado, base)
        estado.metricas["nodos_generados"] += len(utiles)
        return utiles[0] if utiles else None
    return HEURISTICAS[heuristica](estado, base)


class Partida:
    def __init__(self, base, metodo="heuristica", heuristica="mitad", limite_preguntas=LIMITE_PREGUNTAS,
                 detalle=True):
        self.base = base
        self.detalle = detalle
        self.decision = None
        self.metodo = metodo
        self.heuristica = heuristica
        self.estado = crear_estado(base, limite_preguntas)
        self.accion = None
        self.motivo = None
        self.terminada = False
        self.motivo_intento = None
        self.ultima_hipotesis = None
        self.historial = []
        self._guardar_paso("inicio")

    def _guardar_paso(self, tipo, **datos):
        estado = self.estado
        hipotesis = elegir_hipotesis(estado) if estado.candidatos else None
        paso = {
            "numero": len(self.historial), "tipo": tipo, "metodo": self.metodo,
            "atributo": None, "pregunta": None, "respuesta": None,
            "reglas_evaluadas": [], "reglas_disparadas": [], "hechos_nuevos": {},
            "hechos_conocidos": dict(estado.hechos_conocidos), "descartados": [],
            "candidatos": list(estado.candidatos), "hipotesis": hipotesis,
            "candidato_adivinado": None, "acerto": None, "puntos": estado.puntos,
            "metricas": dict(estado.metricas), "decision": None,
        }
        paso.update(datos)
        self.historial.append(paso)

    def siguiente(self):
        """Devuelve la acción pendiente: preguntar, adivinar o fin."""
        inicio = time.perf_counter()
        try:
            accion = self._siguiente()
        finally:
            self.estado.metricas["tiempo"] += time.perf_counter() - inicio
        self.decision = self._decidir(accion) if self.detalle and accion["tipo"] == "pregunta" else None
        return accion

    def _decidir(self, accion):
        """Por qué se eligió esta pregunta, para mostrarlo en la interfaz."""
        atributo = accion["atributo"]
        decision = {"metodo": self.metodo, "atributo": atributo}
        if self.metodo == "heuristica":
            decision["criterio"] = self.heuristica
            decision["valores"] = valores_atributos(self.estado, self.base, self.heuristica)[:5]
        elif self.metodo == "atras":
            decision.update(explicar_atras(elegir_hipotesis(self.estado), self.estado, self.base) or {})
        else:
            orden = list(self.base.candidatos[next(iter(self.base.candidatos))])
            decision["posicion"] = (orden.index(atributo) + 1, len(orden))
        return decision

    def _siguiente(self):
        if self.terminada:
            return self.accion
        motivo = debe_parar(self.estado, self.base)
        if motivo in (ACERTO, SIN_CANDIDATOS):
            return self.terminar(motivo)
        hipotesis = elegir_hipotesis(self.estado)
        if self.metodo == "atras" and hipotesis != self.ultima_hipotesis:
            self.estado.metricas["hipotesis_probadas"] += 1
        self.ultima_hipotesis = hipotesis
        atributo = None
        # Al llegar al límite se hace un último intento con la mejor hipótesis
        if motivo is None:
            atributo = elegir_atributo(self.estado, self.base, self.metodo, self.heuristica, hipotesis)
        self.motivo_intento = motivo
        if atributo is None:
            self.accion = {"tipo": "adivinar", "candidato": hipotesis}
        else:
            self.accion = {"tipo": "pregunta", "atributo": atributo,
                           "pregunta": self.base.preguntas[atributo]}
        return self.accion

    def responder(self, respuesta):
        """respuesta: 'si', 'no' o 'no_se'. Devuelve (reglas activadas, descartados)."""
        inicio = time.perf_counter()
        atributo = self.accion["atributo"]
        activadas, descartados = procesar_respuesta(self.estado, self.base, atributo, respuesta)
        self.estado.metricas["tiempo"] += time.perf_counter() - inicio
        self._guardar_paso(
            "pregunta", atributo=atributo, pregunta=self.accion["pregunta"], respuesta=respuesta,
            reglas_evaluadas=list(dict.fromkeys(self.estado.ultimas_evaluadas)),
            reglas_disparadas=[r["id"] for r in activadas],
            hechos_nuevos={r["entonces"]: True for r in activadas}, descartados=list(descartados),
            decision=self.decision)
        return activadas, descartados

    def confirmar(self, acerto):
        candidato = self.accion["candidato"]
        adivinar(self.estado, candidato, lambda _: acerto)
        self._guardar_paso("adivinar", candidato_adivinado=candidato, acerto=acerto,
                           descartados=[] if acerto else [candidato],
                           decision={"metodo": self.metodo, "adivina": candidato})
        if self.motivo_intento == LIMITE:
            self.terminar(ACERTO if acerto else LIMITE)
        return acerto

    def terminar(self, motivo):
        self.terminada = True
        self.motivo = debe_parar(self.estado, self.base) or motivo
        self.accion = {"tipo": "fin", "motivo": self.motivo}
        self._guardar_paso("fin", acerto=self.estado.acerto, resumen=resumen_metricas(self.estado, self.motivo))
        return self.accion
