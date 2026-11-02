"""Extra (no forma parte de la elección de runas): objetivos de cada partida.

Lee las timelines que `partidas importar` ya guardó (no descarga nada) y cuenta, para tu equipo y el
enemigo: dragones, larvas del vacío, heraldo, Atakhan, Barón, torres, inhibidores y placas, además de
quién tomó el primer dragón y el primer Barón. Sirve para ver dónde se va el oro en las partidas largas.
"""

MONSTRUOS = {"DRAGON": "dragones", "HORDE": "larvas", "RIFTHERALD": "heraldo",
             "BARON_NASHOR": "baron", "ATAKHAN": "atakhan"}
CATEGORIAS = ["dragones", "larvas", "heraldo", "atakhan", "baron", "torres", "inhibidores", "placas"]


def _equipo_de(partida: dict) -> dict[int, int]:
    return {p["participantId"]: p["teamId"] for p in partida["info"]["participants"]}


def contar(partida: dict, timeline: dict, yo: dict, minuto: int | None = None) -> dict:
    """{'dragones': (nuestros, suyos), ..., 'primer_dragon': ('nosotros'|'ellos', min), 'primer_baron': ...}"""
    mi_equipo = yo["teamId"]
    equipos = _equipo_de(partida)
    limite = minuto * 60_000 if minuto else None
    cuenta = {c: [0, 0] for c in CATEGORIAS}
    primero = {"dragones": None, "baron": None}

    for f in timeline["info"]["frames"]:
        for e in f["events"]:
            if limite is not None and e.get("timestamp", 0) >= limite:
                continue
            tipo = e.get("type")
            if tipo == "ELITE_MONSTER_KILL":
                cat = MONSTRUOS.get(e.get("monsterType"))
                if not cat:
                    continue
                equipo = e.get("killerTeamId") or equipos.get(e.get("killerId"))
                if equipo is None:
                    continue
                lado = 0 if equipo == mi_equipo else 1
            elif tipo == "BUILDING_KILL":
                cat = {"TOWER_BUILDING": "torres", "INHIBITOR_BUILDING": "inhibidores"}.get(e.get("buildingType"))
                if not cat:
                    continue
                lado = 0 if e.get("teamId") != mi_equipo else 1     # teamId = dueño del edificio destruido
            elif tipo == "TURRET_PLATE_DESTROYED":
                cat = "placas"
                lado = 0 if e.get("teamId") != mi_equipo else 1
            else:
                continue
            cuenta[cat][lado] += 1
            if cat in primero and primero[cat] is None:
                primero[cat] = ("nosotros" if lado == 0 else "ellos", round(e["timestamp"] / 60_000))

    salida = {c: tuple(v) for c, v in cuenta.items()}
    salida["primer_dragon"] = primero["dragones"]
    salida["primer_baron"] = primero["baron"]
    salida["resultado"] = "victoria" if yo["win"] else "derrota"
    salida["match_id"] = partida["metadata"]["matchId"]
    return salida


def totales(filas: list[dict]) -> dict:
    """Diferencia media (nuestros - suyos) por categoría en victorias y derrotas, y quién ganó con el primer Barón/dragón."""
    def dif_media(xs, cat):
        return round(sum(f[cat][0] - f[cat][1] for f in xs) / len(xs), 1) if xs else None

    salida = {}
    for res in ("victoria", "derrota"):
        xs = [f for f in filas if f["resultado"] == res]
        salida[res] = {"partidas": len(xs), **{c: dif_media(xs, c) for c in CATEGORIAS}}

    for obj in ("primer_baron", "primer_dragon"):
        d = {}
        for quien in ("nosotros", "ellos"):
            xs = [f for f in filas if f[obj] and f[obj][0] == quien]
            d[quien] = (len(xs), sum(1 for f in xs if f["resultado"] == "victoria"))
        salida[obj] = d
    return salida
