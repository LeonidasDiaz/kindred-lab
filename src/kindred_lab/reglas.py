"""Reglas de runas (reglas/kindred_runas.json): carga y validación contra el parche guardado.

La validación evita que una regla apunte a una runa que no existe o que cambió de clave en un parche.
"""
import json
from pathlib import Path

from . import config

RUTA_REGLAS = config.RAIZ / "reglas" / "kindred_runas.json"
CAMPOS_RUNA = ("incluye", "piedra_angular", "fila_1", "fila_2", "fila_3")


def cargar(ruta: Path | None = None) -> dict:
    return json.loads((ruta or RUTA_REGLAS).read_text(encoding="utf-8"))


def claves_usadas(reglas: dict) -> set[str]:
    """Todas las claves de runa que aparecen en las reglas (sin árboles)."""
    usadas = {v for k, v in reglas.get("fijas", {}).items() if k != "arbol_principal"}

    def recorrer(nodo):
        if isinstance(nodo, dict):
            for k, v in nodo.items():
                if k == "incluye":
                    usadas.update(v)
                elif k in CAMPOS_RUNA:
                    usadas.add(v)
                else:
                    recorrer(v)
        elif isinstance(nodo, list):
            for x in nodo:
                recorrer(x)

    recorrer(reglas.get("preguntas", []))
    recorrer(reglas.get("excepciones", []))
    return usadas


def claves_arbol_usadas(reglas: dict) -> set[str]:
    arboles = {reglas.get("fijas", {}).get("arbol_principal")}

    def recorrer(nodo):
        if isinstance(nodo, dict):
            for k, v in nodo.items():
                if k == "secundaria":
                    arboles.add(v)
                else:
                    recorrer(v)
        elif isinstance(nodo, list):
            for x in nodo:
                recorrer(x)

    recorrer(reglas.get("preguntas", []))
    return {a for a in arboles if a}


def validar(reglas: dict, datos_runas: dict) -> list[str]:
    """Devuelve una lista de problemas; vacía si todo existe en el parche."""
    claves = {r["clave"]: r for r in datos_runas["runas"].values()}
    problemas = []
    for c in sorted(claves_usadas(reglas)):
        if c not in claves:
            parecidas = [k for k in claves if c.lower()[:5] in k.lower()]
            pista = f" ¿Quisiste decir {', '.join(parecidas)}?" if parecidas else ""
            problemas.append(f"La runa '{c}' no existe en el parche {datos_runas['version']}.{pista}")
    for a in sorted(claves_arbol_usadas(reglas)):
        if a not in datos_runas["arboles"]:
            problemas.append(f"El árbol '{a}' no existe en el parche {datos_runas['version']}.")
    return problemas
