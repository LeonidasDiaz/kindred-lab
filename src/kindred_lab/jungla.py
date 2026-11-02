"""Extra (no forma parte de la elección de runas): lo que depende de ti como jungla.

Lee las partidas y timelines guardadas (no descarga nada). Por partida:
- Visión: puntuación por minuto, balizas de control compradas, centinelas destruidos y cuántos centinelas
  pusiste tú en los 90 s previos a cada dragón o Barón.
- Muertes caras: tus muertes en los 90 s previos a un dragón o Barón que tomó el enemigo.
- Dónde mueres: tu jungla, la jungla enemiga, el río, un carril o una base (aproximado por coordenadas).
Con `muertes`, el detalle de una partida: cada muerte con minuto, zona, quién te mató y si fue cara.
"""
VENTANA_MS = 90_000
OBJETIVOS_CAROS = {"DRAGON", "BARON_NASHOR"}
ZONAS = ["tu jungla", "jungla enemiga", "río", "carril", "base"]
SIN_CAMPEON = "(sin campeón)"         # killerId 0: torre, súbditos o monstruo


def zona(x: float, y: float, mi_equipo: int) -> str:
    """Zona aproximada de la Grieta (0-14870; base azul abajo a la izquierda, equipo 100 = azul)."""
    if (x < 4500 and y < 4500) or (x > 10300 and y > 10300):
        return "base"
    if (x < 2200 or y > 12600 or y < 2200 or x > 12600) or abs(x - y) < 1300:
        return "carril"
    if abs((x + y) - 14870) < 1400:
        return "río"
    lado_azul = (x + y) < 14870
    return "tu jungla" if lado_azul == (mi_equipo == 100) else "jungla enemiga"


def _objetivos(partida: dict, eventos: list[dict], mi_equipo: int) -> list[tuple]:
    """(timestamp, monsterType, es_nuestro) de cada dragón o Barón."""
    equipos = {p["participantId"]: p["teamId"] for p in partida["info"]["participants"]}
    objetivos = []
    for e in eventos:
        if e.get("type") == "ELITE_MONSTER_KILL" and e.get("monsterType") in OBJETIVOS_CAROS:
            equipo = e.get("killerTeamId") or equipos.get(e.get("killerId"))
            if equipo is not None:
                objetivos.append((e["timestamp"], e["monsterType"], equipo == mi_equipo))
    return objetivos


def _objetivo_perdido(t: int, objetivos: list[tuple]) -> str | None:
    """El dragón o Barón que tomó el enemigo en los 90 s siguientes a t (None si no hubo: muerte no cara)."""
    for t_obj, tipo, nuestro in objetivos:
        if not nuestro and t_obj - VENTANA_MS <= t < t_obj:
            return tipo
    return None


def analizar(partida: dict, timeline: dict, yo: dict, duracion_min: float | None = None) -> dict:
    pid, mi_equipo = yo["participantId"], yo["teamId"]
    eventos = [e for f in timeline["info"]["frames"] for e in f["events"]]
    objetivos = _objetivos(partida, eventos, mi_equipo)

    mis_centinelas = [e["timestamp"] for e in eventos
                      if e.get("type") == "WARD_PLACED" and e.get("creatorId") == pid
                      and e.get("wardType") not in (None, "UNDEFINED")]
    centinelas_antes = sum(1 for t_obj, _, _ in objetivos for t in mis_centinelas if t_obj - VENTANA_MS <= t < t_obj)

    mis_muertes = [e for e in eventos if e.get("type") == "CHAMPION_KILL" and e.get("victimId") == pid]
    caras = sum(1 for m in mis_muertes if _objetivo_perdido(m["timestamp"], objetivos))
    donde = {z: 0 for z in ZONAS}
    for m in mis_muertes:
        pos = m.get("position")
        if pos:
            donde[zona(pos["x"], pos["y"], mi_equipo)] += 1

    vision = yo.get("visionScore")
    return {
        "match_id": partida["metadata"]["matchId"],
        "resultado": "victoria" if yo["win"] else "derrota",
        "vision_min": round(vision / duracion_min, 2) if vision is not None and duracion_min else None,
        "balizas": yo.get("visionWardsBoughtInGame"),
        "destruidos": yo.get("wardsKilled"),
        "objetivos": len(objetivos),
        "centinelas_antes": centinelas_antes,
        "muertes": len(mis_muertes),
        "muertes_caras": caras,
        "donde": donde,
    }


def muertes(partida: dict, timeline: dict, yo: dict) -> list[dict]:
    """Tus muertes en orden: minuto (m:ss), zona, campeón que te mató y si fue cara (con qué objetivo)."""
    pid, mi_equipo = yo["participantId"], yo["teamId"]
    campeones = {p["participantId"]: p.get("championName", "?") for p in partida["info"]["participants"]}
    eventos = [e for f in timeline["info"]["frames"] for e in f["events"]]
    objetivos = _objetivos(partida, eventos, mi_equipo)
    salida = []
    for m in sorted((e for e in eventos if e.get("type") == "CHAMPION_KILL" and e.get("victimId") == pid),
                    key=lambda e: e["timestamp"]):
        seg = m["timestamp"] // 1000
        pos = m.get("position")
        salida.append({
            "minuto": f"{seg // 60}:{seg % 60:02d}",
            "zona": zona(pos["x"], pos["y"], mi_equipo) if pos else "?",
            "asesino": campeones.get(m.get("killerId"), SIN_CAMPEON),
            "cara": _objetivo_perdido(m["timestamp"], objetivos),
        })
    return salida


def totales(filas: list[dict]) -> dict:
    def media(xs, campo):
        vals = [f[campo] for f in xs if f.get(campo) is not None]
        return round(sum(vals) / len(vals), 2) if vals else None

    salida = {}
    for res in ("victoria", "derrota"):
        xs = [f for f in filas if f["resultado"] == res]
        obj = sum(f["objetivos"] for f in xs)
        salida[res] = {
            "partidas": len(xs),
            "vision_min": media(xs, "vision_min"),
            "balizas": media(xs, "balizas"),
            "destruidos": media(xs, "destruidos"),
            "centinelas_por_objetivo": round(sum(f["centinelas_antes"] for f in xs) / obj, 2) if obj else None,
            "muertes": media(xs, "muertes"),
            "muertes_caras": media(xs, "muertes_caras"),
            "donde": {z: sum(f["donde"][z] for f in xs) for z in ZONAS},
        }
    return salida
