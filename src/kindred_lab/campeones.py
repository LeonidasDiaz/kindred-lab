"""Tipos de campeón de Data Dragon (Fighter, Mage...), guardados para que los análisis no descarguen nada.

Son informativos: Data Dragon pone a Jhin como Marksman y Mage, así que el tipo no dice qué daño hace un campeón.
"""
import json
from pathlib import Path

from . import config, ddragon

ARCHIVO_DDRAGON = "champion.json"


def generar(dd: dict, version: str) -> dict:
    return {"version": version,
            "campeones": {id_: {"nombre": c["name"], "tipos": c["tags"]} for id_, c in sorted(dd.items())}}


def ruta_procesada(out_dir: Path | None = None) -> Path:
    return (out_dir or config.CAMPEONES_DIR) / "campeones_latest.json"


def cargar(out_dir: Path | None = None) -> dict:
    ruta = ruta_procesada(out_dir)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe {ruta}. Ejecuta primero: python -m kindred_lab objetos actualizar")
    return json.loads(ruta.read_text(encoding="utf-8"))


def actualizar(version: str, idioma: str = config.IDIOMA, raw_dir: Path | None = None,
               out_dir: Path | None = None) -> Path:
    """Guarda los campeones del parche, salvo que ya estén guardados los de uno más nuevo."""
    ruta = ruta_procesada(out_dir)
    if ruta.exists():
        guardada = json.loads(ruta.read_text(encoding="utf-8"))["version"]
        if ddragon.clave_version(guardada) > ddragon.clave_version(version):
            return ruta
    datos = generar(ddragon.descargar(version, idioma, ARCHIVO_DDRAGON, raw_dir=raw_dir)["data"], version)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


def tipos(datos: dict, campeon: str) -> list[str]:
    """Tipos de un campeón, sin distinguir mayúsculas: la API dice FiddleSticks y Data Dragon, Fiddlesticks."""
    buscado = campeon.lower()
    for id_, c in datos["campeones"].items():
        if id_.lower() == buscado:
            return c["tipos"]
    return []
