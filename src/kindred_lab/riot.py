"""Cliente mínimo de la API de Riot (match-v5) con caché en disco.

La clave se lee de la variable de entorno RIOT_API_KEY (developer.riotgames.com; la de desarrollo
caduca cada 24 h). Cada partida y su timeline se descargan una sola vez a data/raw/riot/.
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from . import config


def secretos(ruta: Path | None = None) -> dict:
    """Contenido de secretos.json (vacío si no existe)."""
    ruta = ruta or config.SECRETOS
    return json.loads(ruta.read_text(encoding="utf-8-sig")) if ruta.exists() else {}


def clave_api() -> str:
    """La variable de entorno RIOT_API_KEY manda; si no está, se lee secretos.json."""
    clave = (os.environ.get("RIOT_API_KEY") or secretos().get("riot_api_key") or "").strip()
    if not clave or clave.startswith("RGAPI-xxxx"):
        raise ValueError("Falta la clave de Riot: ponla en secretos.json (riot_api_key) "
                         "o en la variable RIOT_API_KEY. Se genera en developer.riotgames.com.")
    return clave


def _get(url: str, reintentos: int = 3):
    req = urllib.request.Request(url, headers={"X-Riot-Token": clave_api(), "User-Agent": "kindred-lab"})
    for intento in range(reintentos + 1):
        try:
            with urllib.request.urlopen(req, timeout=config.TIMEOUT_S) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and intento < reintentos:
                time.sleep(int(e.headers.get("Retry-After", "5")) + 1)
                continue
            if e.code in (401, 403):
                raise ValueError("Riot rechazó la clave (401/403): probablemente caducó; genera otra.") from e
            if e.code == 404:
                raise FileNotFoundError(f"No encontrado en Riot: {url}") from e
            raise


def puuid(riot_id: str, region: str | None = None) -> str:
    """'Nombre#TAG' -> puuid."""
    nombre, _, tag = riot_id.partition("#")
    if not tag:
        raise ValueError("El Riot ID debe tener el formato Nombre#TAG.")
    base = f"https://{region or config.RIOT_REGION}.api.riotgames.com"
    ruta = f"/riot/account/v1/accounts/by-riot-id/{urllib.parse.quote(nombre)}/{urllib.parse.quote(tag)}"
    return _get(base + ruta)["puuid"]


def ids_partidas(puuid_: str, cantidad: int = 20, cola: int = config.COLA_SOLO_DUO,
                 region: str | None = None) -> list[str]:
    """La API da como máximo 100 ids por consulta; se pide por páginas hasta juntar `cantidad`."""
    base = f"https://{region or config.RIOT_REGION}.api.riotgames.com"
    ids: list[str] = []
    while len(ids) < cantidad:
        pagina = min(100, cantidad - len(ids))
        q = urllib.parse.urlencode({"queue": cola, "start": len(ids), "count": pagina})
        nuevos = _get(f"{base}/lol/match/v5/matches/by-puuid/{puuid_}/ids?{q}")
        ids.extend(nuevos)
        if len(nuevos) < pagina:          # ya no hay más partidas
            break
    return ids


def _con_cache(match_id: str, sufijo: str, ruta_api: str, raw_dir: Path | None, region: str | None):
    ruta = (raw_dir or config.RIOT_RAW) / f"{match_id}{sufijo}.json"
    if ruta.exists():
        return json.loads(ruta.read_text(encoding="utf-8"))
    datos = _get(f"https://{region or config.RIOT_REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}{ruta_api}")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    return datos


def partida(match_id: str, raw_dir: Path | None = None, region: str | None = None) -> dict:
    return _con_cache(match_id, "", "", raw_dir, region)


def timeline(match_id: str, raw_dir: Path | None = None, region: str | None = None) -> dict:
    return _con_cache(match_id, ".timeline", "/timeline", raw_dir, region)
