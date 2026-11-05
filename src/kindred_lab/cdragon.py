"""Estadísticas de fin de partida de cada runa, desde Community Dragon (perks.json del cliente).

Cada runa trae textos como "Total de daño: @eogvar1@" o "Tiempo completado: @eogvar1@:@eogvar2@":
dicen qué var1/var2/var3 de la API de Riot es cada número de la pantalla de fin de partida.
Se descarga una vez y se guarda en data/raw/cdragon/perks_<idioma>.json.
"""
import json
import re
import urllib.request
from pathlib import Path

from . import config

_VAR = re.compile(r"@eogvar(\d)@")


def descargar(idioma: str = "es_mx", raw_dir: Path | None = None, forzar: bool = False) -> list:
    ruta = (raw_dir or config.CDRAGON_RAW) / f"perks_{idioma}.json"
    if ruta.exists() and not forzar:
        return json.loads(ruta.read_text(encoding="utf-8"))
    req = urllib.request.Request(config.CDRAGON_PERKS.format(idioma=idioma), headers={"User-Agent": "kindred-lab"})
    with urllib.request.urlopen(req, timeout=config.TIMEOUT_S) as r:
        datos = json.load(r)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    return datos


def descargar_items(version: str, raw_dir: Path | None = None, forzar: bool = False) -> dict:
    """items.cdtb.bin.json de los archivos del juego ('16.22.1' -> carpeta '16.22'). Pesa unos 15 MB por parche."""
    parche = ".".join(version.split(".")[:2])
    ruta = (raw_dir or config.CDRAGON_RAW) / f"items_{parche}.json"
    if ruta.exists() and not forzar:
        return json.loads(ruta.read_text(encoding="utf-8"))
    req = urllib.request.Request(config.CDRAGON_ITEMS.format(parche=parche), headers={"User-Agent": "kindred-lab"})
    with urllib.request.urlopen(req, timeout=config.TIMEOUT_S) as r:
        datos = json.load(r)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    return datos


def _linea(desc: str) -> str:
    """Primera línea del texto, sin HTML."""
    desc = re.split(r"<br\s*/?>", desc)[0]
    return re.sub(r"<[^>]+>", "", desc).strip()


def estadisticas(perks: list) -> dict[int, list[dict]]:
    """{id_runa: [{"etiqueta": "Total de daño", "vars": ["var1"], "tiempo": False}, ...]}"""
    salida = {}
    for p in perks:
        stats = []
        for desc in p.get("endOfGameStatDescs") or []:
            linea = _linea(desc)
            vars_ = [f"var{n}" for n in _VAR.findall(linea)]
            if not vars_:
                continue
            stats.append({"etiqueta": linea.split(":")[0].strip(),
                          "vars": vars_,
                          "tiempo": bool(re.search(r"@eogvar\d@:@eogvar\d@", linea)),
                          "porcentaje": linea.lower().startswith("porcentaje")})
        if stats:
            salida[p["id"]] = stats
    return salida


def formatear(sel: dict, stat: dict) -> str:
    """Valor de una estadística tal como sale en pantalla ('3545', '10:40')."""
    if stat["tiempo"] and len(stat["vars"]) >= 2:
        return f"{int(sel.get(stat['vars'][0], 0))}:{int(sel.get(stat['vars'][1], 0)):02d}"
    valor = f"{round(sel.get(stat['vars'][0], 0)):d}"
    return valor + "%" if stat.get("porcentaje") else valor


def todas(sel: dict, stats: list[dict]) -> str:
    """Todas las estadísticas de una runa: 'Total de vida restaurada 1532; Total de oro adicional otorgado 620'."""
    return "; ".join(f"{s['etiqueta']} {formatear(sel, s)}" for s in stats)
