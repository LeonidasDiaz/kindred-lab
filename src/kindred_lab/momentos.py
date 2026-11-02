"""Extra (no forma parte de la elección de runas): en qué tramo de la partida se tuerce.

Parte cada partida en tramos de 5 minutos y, por tramo, cuenta tus muertes, tus muertes en tu jungla,
las bajas de tu equipo en las que participaste y cuánto oro ganó o perdió tu equipo frente al enemigo
en ese tramo. Comparar victorias y derrotas tramo a tramo muestra cuándo empiezan a separarse.
Lee las timelines guardadas; no descarga nada.
"""
from .jungla import zona

TRAMO_MIN = 5
TRAMOS = [(i, i + TRAMO_MIN) for i in range(0, 35, TRAMO_MIN)]      # 0-5 ... 30-35


def _dif_oro(timeline: dict, minuto: int, aliados: set[int]) -> int | None:
    limite = minuto * 60_000 + 5_000
    frames = [f for f in timeline["info"]["frames"] if f["timestamp"] <= limite]
    if not frames or frames[-1]["timestamp"] < (minuto - 1) * 60_000:
        return None                                      # la partida ya había terminado
    pf = frames[-1]["participantFrames"]
    return (sum(v["totalGold"] for k, v in pf.items() if int(k) in aliados)
            - sum(v["totalGold"] for k, v in pf.items() if int(k) not in aliados))


def analizar(partida: dict, timeline: dict, yo: dict) -> dict:
    pid, mi_equipo = yo["participantId"], yo["teamId"]
    aliados = {p["participantId"] for p in partida["info"]["participants"] if p["teamId"] == mi_equipo}
    fin_ms = timeline["info"]["frames"][-1]["timestamp"]
    tramos = []
    for ini, fin in TRAMOS:
        if fin_ms < ini * 60_000 + 60_000:               # la partida no llegó a este tramo
            break
        muertes = en_mi_jungla = participaciones = 0
        for f in timeline["info"]["frames"]:
            for e in f["events"]:
                if e.get("type") != "CHAMPION_KILL" or not (ini * 60_000 <= e["timestamp"] < fin * 60_000):
                    continue
                if e.get("victimId") == pid:
                    muertes += 1
                    pos = e.get("position")
                    if pos and zona(pos["x"], pos["y"], mi_equipo) == "tu jungla":
                        en_mi_jungla += 1
                elif e.get("victimId") not in aliados:
                    if pid == e.get("killerId") or pid in (e.get("assistingParticipantIds") or []):
                        participaciones += 1
        antes, despues = _dif_oro(timeline, ini, aliados) if ini else 0, _dif_oro(timeline, fin, aliados)
        cambio = despues - antes if antes is not None and despues is not None else None
        tramos.append({"tramo": f"{ini}-{fin}", "muertes": muertes, "en_mi_jungla": en_mi_jungla,
                       "participaciones": participaciones, "oro_fin": despues, "cambio_oro": cambio})
    return {"match_id": partida["metadata"]["matchId"],
            "resultado": "victoria" if yo["win"] else "derrota", "tramos": tramos}


def totales(filas: list[dict]) -> dict:
    """Por tramo y resultado: partidas que llegaron, medias por partida y en cuántas el oro se volteó en contra."""
    salida = {}
    for ini, fin in TRAMOS:
        nombre = f"{ini}-{fin}"
        salida[nombre] = {}
        for res in ("victoria", "derrota"):
            xs = [t for f in filas if f["resultado"] == res for t in f["tramos"] if t["tramo"] == nombre]

            def media(campo, xs=xs):
                vals = [t[campo] for t in xs if t[campo] is not None]
                return round(sum(vals) / len(vals), 2) if vals else None

            salida[nombre][res] = {"partidas": len(xs), "muertes": media("muertes"),
                                   "en_mi_jungla": media("en_mi_jungla"),
                                   "participaciones": media("participaciones"),
                                   "cambio_oro": media("cambio_oro"), "oro_fin": media("oro_fin")}
    # Tramo en el que cada derrota quedó atrás en oro por primera vez, para no volver a ir adelante.
    volteo = {f"{i}-{j}": 0 for i, j in TRAMOS}
    nunca = 0
    for f in filas:
        if f["resultado"] != "derrota":
            continue
        oros = [(t["tramo"], t["oro_fin"]) for t in f["tramos"] if t["oro_fin"] is not None]
        quedo = None
        for k, (tramo, oro) in enumerate(oros):
            if oro < 0 and all(o < 0 for _, o in oros[k:]):
                quedo = tramo
                break
        if quedo:
            volteo[quedo] += 1
        else:
            nunca += 1
    salida["volteo_derrotas"] = volteo
    salida["derrotas_sin_volteo"] = nunca
    return salida
