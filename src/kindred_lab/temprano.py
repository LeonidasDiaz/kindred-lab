"""Extra (no forma parte de la elección de runas): qué pasa en los primeros minutos de tus partidas.

Lee las partidas y timelines que `partidas importar` ya guardó en data/raw/riot/; no descarga nada.
Por partida: muertes de tu equipo antes del minuto N, en cuántas participó el jungla enemigo,
tus muertes, tus participaciones en bajas, la diferencia de oro de equipo en el minuto N y tu daño a
campeones hasta ese minuto (refleja emboscadas aunque no terminen en baja).
"""
import json
from pathlib import Path

from . import config

SMITE = 11   # id del hechizo de invocador Castigo, para detectar al jungla si falta teamPosition


def cargar_cache(match_id: str, raw_dir: Path | None = None) -> tuple[dict, dict] | None:
    base = raw_dir or config.RIOT_RAW
    p, t = base / f"{match_id}.json", base / f"{match_id}.timeline.json"
    if not (p.exists() and t.exists()):
        return None
    return (json.loads(p.read_text(encoding="utf-8")), json.loads(t.read_text(encoding="utf-8")))


def buscar_yo(partida: dict, riot_id: str | None = None, puuid: str | None = None) -> dict:
    """Tu participante: por puuid, o por Riot ID ('Nombre#TAG', sin red).
    Como Riot, no distingue mayúsculas ni espacios ('Nombre Largo' = 'nombrelargo')."""
    def normal(s: str) -> str:
        return s.replace(" ", "").lower()

    for p in partida["info"]["participants"]:
        if puuid and p.get("puuid") == puuid:
            return p
        if riot_id:
            nombre, _, tag = riot_id.partition("#")
            if (normal(p.get("riotIdGameName", "")) == normal(nombre)
                    and normal(p.get("riotIdTagline", "")) == normal(tag)):
                return p
    raise KeyError(f"No te encontré en {partida['metadata']['matchId']} (revisa riot_id en secretos.json).")


def jungla_enemigo(partida: dict, mi_equipo: int) -> dict | None:
    enemigos = [p for p in partida["info"]["participants"] if p["teamId"] != mi_equipo]
    for p in enemigos:
        if p.get("teamPosition") == "JUNGLE":
            return p
    for p in enemigos:
        if SMITE in (p.get("summoner1Id"), p.get("summoner2Id")):
            return p
    return None


def _frame_en(timeline: dict, minuto: int) -> dict | None:
    """Último frame con timestamp <= minuto (los frames vienen cada 60 s)."""
    limite = minuto * 60_000
    frames = [f for f in timeline["info"]["frames"] if f["timestamp"] <= limite + 5_000]
    return frames[-1] if frames else None


def analizar(partida: dict, timeline: dict, yo: dict, minuto: int = 10) -> dict:
    info = partida["info"]
    mi_equipo = yo["teamId"]
    aliados = {p["participantId"] for p in info["participants"] if p["teamId"] == mi_equipo}
    jg = jungla_enemigo(partida, mi_equipo)
    jg_id = jg["participantId"] if jg else None
    limite = minuto * 60_000

    muertes_equipo = con_jungla = mias = bajas_equipo = mis_participaciones = 0
    for f in timeline["info"]["frames"]:
        for e in f["events"]:
            if e["type"] != "CHAMPION_KILL" or e["timestamp"] >= limite:
                continue
            implicados = {e.get("killerId")} | set(e.get("assistingParticipantIds") or [])
            if e["victimId"] in aliados:
                muertes_equipo += 1
                if jg_id is not None and jg_id in implicados:
                    con_jungla += 1
                if e["victimId"] == yo["participantId"]:
                    mias += 1
            else:
                bajas_equipo += 1
                if yo["participantId"] in implicados:
                    mis_participaciones += 1

    oro = dano = None
    frame = _frame_en(timeline, minuto)
    if frame:
        mio = frame["participantFrames"].get(str(yo["participantId"]), {})
        dano = (mio.get("damageStats") or {}).get("totalDamageDoneToChampions")
        pf = frame["participantFrames"]
        oro = sum(v["totalGold"] for k, v in pf.items() if int(k) in aliados) - \
              sum(v["totalGold"] for k, v in pf.items() if int(k) not in aliados)

    return {
        "match_id": partida["metadata"]["matchId"],
        "resultado": "victoria" if yo["win"] else "derrota",
        "jungla_enemigo": jg["championName"] if jg else "?",
        "muertes_equipo": muertes_equipo,
        "con_jungla_enemigo": con_jungla,
        "mias": mias,
        "bajas_equipo": bajas_equipo,
        "mis_participaciones": mis_participaciones,
        "dif_oro": oro,
        "dano_campeones": dano,
    }


def totales(filas: list[dict]) -> dict:
    n = len(filas)
    muertes = sum(f["muertes_equipo"] for f in filas)
    con_jg = sum(f["con_jungla_enemigo"] for f in filas)
    bajas = sum(f["bajas_equipo"] for f in filas)
    part = sum(f["mis_participaciones"] for f in filas)
    con_oro = [f for f in filas if f["dif_oro"] is not None]
    atras = [f for f in con_oro if f["dif_oro"] < 0]
    adelante = [f for f in con_oro if f["dif_oro"] >= 0]

    def victorias(xs):
        return sum(1 for f in xs if f["resultado"] == "victoria")

    def media(xs, campo):
        vals = [f[campo] for f in xs if f.get(campo) is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    ganadas = [f for f in filas if f["resultado"] == "victoria"]
    perdidas = [f for f in filas if f["resultado"] == "derrota"]

    def pct_part(xs):
        b = sum(f["bajas_equipo"] for f in xs)
        return round(100 * sum(f["mis_participaciones"] for f in xs) / b) if b else None

    return {
        "por_resultado": {
            "victoria": {"partidas": len(ganadas), "dano": media(ganadas, "dano_campeones"),
                         "participacion": pct_part(ganadas)},
            "derrota": {"partidas": len(perdidas), "dano": media(perdidas, "dano_campeones"),
                        "participacion": pct_part(perdidas)},
        },
        "partidas": n,
        "muertes_equipo_media": round(muertes / n, 1) if n else 0,
        "pct_con_jungla": round(100 * con_jg / muertes) if muertes else 0,
        "mias_media": round(sum(f["mias"] for f in filas) / n, 1) if n else 0,
        "pct_participacion": round(100 * part / bajas) if bajas else 0,
        "atras": len(atras), "victorias_atras": victorias(atras),
        "adelante": len(adelante), "victorias_adelante": victorias(adelante),
        "dif_oro_media": round(sum(f["dif_oro"] for f in con_oro) / len(con_oro)) if con_oro else None,
    }
