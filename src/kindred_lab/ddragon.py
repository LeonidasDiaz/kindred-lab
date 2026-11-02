"""Cliente mínimo de Data Dragon con caché en disco.

Cada archivo descargado se guarda en data/raw/ddragon/<version>/<idioma>/<archivo>.
Si ya existe, se lee del disco y no se vuelve a pedir: así cada parche se descarga una sola vez
y siempre puedes reconstruir los datos procesados sin red.
"""
import json
import urllib.request
from pathlib import Path

from . import config


def _get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "kindred-lab"})
    with urllib.request.urlopen(req, timeout=config.TIMEOUT_S) as r:
        return json.load(r)


def versiones() -> list[str]:
    """Lista de versiones publicadas, la más reciente primero."""
    return _get_json(f"{config.DDRAGON_BASE}/api/versions.json")


def ultima_version() -> str:
    return versiones()[0]


def ruta_cache(version: str, idioma: str, archivo: str, raw_dir: Path | None = None) -> Path:
    return (raw_dir or config.RAW) / version / idioma / archivo


def descargar(version: str, idioma: str, archivo: str, raw_dir: Path | None = None, forzar: bool = False):
    """Devuelve el JSON de cdn/<version>/data/<idioma>/<archivo>, usando la caché si existe."""
    ruta = ruta_cache(version, idioma, archivo, raw_dir)
    if ruta.exists() and not forzar:
        return json.loads(ruta.read_text(encoding="utf-8"))
    datos = _get_json(f"{config.DDRAGON_BASE}/cdn/{version}/data/{idioma}/{archivo}")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    return datos


def versiones_en_cache(raw_dir: Path | None = None) -> list[str]:
    """Versiones que ya tienes descargadas, de la más vieja a la más nueva."""
    base = raw_dir or config.RAW
    if not base.exists():
        return []
    return sorted((p.name for p in base.iterdir() if p.is_dir()), key=clave_version)


def clave_version(v: str) -> tuple[int, ...]:
    """'16.20.1' -> (16, 20, 1), para ordenar versiones numéricamente."""
    return tuple(int(x) for x in v.split(".") if x.isdigit())
