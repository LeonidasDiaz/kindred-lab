"""Extra (no forma parte de la elección de runas): auditoría de tus objetos defensivos.

Lee las partidas y timelines guardadas (no descarga nada). Por partida:
- Perfil de tus muertes: % físico, mágico y verdadero, solo del daño en tus muertes (victimDamageReceived).
- Amenaza principal: quién metió más daño en tus muertes, su tipo de Data Dragon y su diferencia de oro contigo.
- Defensivos: cuál y en qué minuto, comparados con las muertes ANTERIORES a la compra y con las reglas actuales.
- Retraso: minutos entre tu 2ª muerte contra el mismo enemigo y el primer defensivo que sirva contra él, y hasta el
  primer componente que sirva (la respuesta más rápida posible, aunque no alcance para el objeto completo).
- Efecto: muertes cada 10 min antes y después, junto a la base (la tasa del periodo en esos mismos minutos).

El atacante sale de participantId: el campo name a veces no coincide, y spellName y spellSlot solo sirven de detalle.
El daño viene ya reducido por tu armadura y resistencia, así que comprar armadura baja por sí solo el % físico
posterior: por eso la coincidencia nunca mira lo que pasó después de comprar. No calcula % de victorias por objeto.
"""
import re
from collections import Counter, defaultdict
from statistics import median

from . import campeones as datos_campeones
from .jungla import SIN_CAMPEON

PRECIO_MINIMO = 900            # debajo de esto un objeto sin mejora no es defensivo completo (Escudo de Doran)
UMBRAL_SI, UMBRAL_PARCIAL = 50, 35
VIDA_PARCIAL = 0.5             # desglose que suma menos de esta parte de tu vida máxima: se marca "parcial"
MIN_DESPUES_MS = 180_000       # con menos tiempo después de comprar, la tasa no dice nada
TRAMO_MS = 300_000
DECENA_MS = 600_000
PARCHE_CORTE = (16, 20)        # las partidas anteriores son de otra época: no se mezclan
PERIODOS = ("antes del 16.20 (feb-jun)", "desde el 16.20")
POCOS_CASOS = 5
POCOS_DATOS = "pocos datos"      # una sola muerte previa no dice qué daño te mata
TIPOS = ("fisico", "magico", "verdadero")
# Un objeto da escudo si el texto de Data Dragon dice que lo otorga. Quedan fuera "poder de curaciones y escudos",
# "Rompeescudos" (Colmillo de Serpiente) o "Golpe de Escudo de Luz" (Cielo Desgarrado).
ESCUDO_PROPIO = re.compile(r"(obtienes|otorga) un escudo|en un escudo|\d+ de escudo")
# Escudos de un solo tipo: "escudo mágico", "escudo contra daño mágico", "escudo que protege contra 0 de daño físico"
ESCUDO_DE_TIPO = re.compile(r"escudo (?:que protege )?(?:contra )?(?:\S+ de )?(?:daño )?(mágico|físico)")
ETIQUETA = {"fisico": "físico", "magico": "mágico", "verdadero": "verdadero", "ambos": "físico y mágico",
            "general": "general", "mezclado": "mezclado"}


def _mmss(ms: int) -> str:
    s = ms // 1000
    return f"{s // 60}:{s % 60:02d}"


def _periodo(partida: dict) -> str:
    mayor, menor = partida["info"]["gameVersion"].split(".")[:2]
    return PERIODOS[0] if (int(mayor), int(menor)) < PARCHE_CORTE else PERIODOS[1]


# ---------- objetos ----------

def _defensas(obj: dict) -> list[str]:
    s = obj["stats_base"]
    salida = []
    if s.get("Armadura_plana"):
        salida.append("armadura")
    if s.get("Resist_Magica_plana"):
        salida.append("resistencia mágica")
    if s.get("Vida_maxima_plana"):
        salida.append("vida")
    texto = (obj["metadata"].get("descripcion_legible") or "").lower()
    if ESCUDO_PROPIO.search(texto):
        de_tipo = ESCUDO_DE_TIPO.search(texto)
        salida.append(f"escudo {de_tipo.group(1)}" if de_tipo else "escudo")
    return salida


def _clase_por_defensas(defensas: list[str]) -> str | None:
    armadura = "armadura" in defensas or "escudo físico" in defensas
    rm = "resistencia mágica" in defensas or "escudo mágico" in defensas
    if armadura and rm:
        return "ambos"
    if armadura:
        return "fisico"
    if rm:
        return "magico"
    return "general" if defensas else None


def clase_objeto(obj: dict | None) -> str | None:
    """Contra qué defiende: fisico, magico, ambos o general (solo vida o escudo). None si no es defensivo completo.
    Las botas cuentan solo con armadura o resistencia mágica."""
    if not obj:
        return None
    defensas, meta = _defensas(obj), obj["metadata"]
    if meta.get("botas"):
        return _clase_por_defensas([d for d in defensas if d in ("armadura", "resistencia mágica")])
    if not meta.get("final") or (meta.get("precio") or 0) < PRECIO_MINIMO:
        return None
    return _clase_por_defensas(defensas)


def clase_componente(obj: dict | None) -> str | None:
    """Como clase_objeto, para lo que todavía se mejora en otro objeto. Solo mira estadísticas: da igual el precio."""
    if not obj or obj["metadata"].get("final") or obj["metadata"].get("botas"):
        return None
    return _clase_por_defensas([d for d in _defensas(obj) if not d.startswith("escudo")])


def compras(eventos: list[dict], pid: int) -> list[dict]:
    """Compras en orden, aplicando ventas y deshacer. ITEM_UNDO: afterId 0 deshace una compra; beforeId 0, una venta."""
    historial = []
    for e in sorted((x for x in eventos if x.get("participantId") == pid), key=lambda x: x["timestamp"]):
        tipo = e.get("type")
        if tipo == "ITEM_PURCHASED":
            historial.append({"t": e["timestamp"], "id": e["itemId"], "vendido": None, "deshecho": False})
        elif tipo == "ITEM_SOLD":
            for h in reversed(historial):
                if h["id"] == e["itemId"] and not h["deshecho"] and h["vendido"] is None:
                    h["vendido"] = e["timestamp"]
                    break
        elif tipo == "ITEM_UNDO" and e.get("afterId") == 0:
            for h in reversed(historial):
                if h["id"] == e.get("beforeId") and not h["deshecho"] and h["vendido"] is None:
                    h["deshecho"] = True
                    break
        elif tipo == "ITEM_UNDO" and e.get("beforeId") == 0:
            for h in reversed(historial):
                if h["id"] == e.get("afterId") and h["vendido"] is not None:
                    h["vendido"] = None
                    break
    return [h for h in historial if not h["deshecho"]]


# ---------- muertes ----------

def _vida_maxima(timeline: dict, pid: int, t: int) -> int | None:
    frames = [f for f in timeline["info"]["frames"] if f["timestamp"] <= t]
    if not frames or "participantFrames" not in frames[-1]:
        return None
    return frames[-1]["participantFrames"].get(str(pid), {}).get("championStats", {}).get("healthMax")


def muertes(partida: dict, timeline: dict, yo: dict) -> list[dict]:
    """Tus muertes en orden. Torres, súbditos, monstruos y aliados cuentan en el daño, no como enemigos."""
    pid = yo["participantId"]
    gente = {p["participantId"]: p for p in partida["info"]["participants"]}
    eventos = [e for f in timeline["info"]["frames"] for e in f["events"]]
    salida = []
    for e in sorted((x for x in eventos if x.get("type") == "CHAMPION_KILL" and x.get("victimId") == pid),
                    key=lambda x: x["timestamp"]):
        total, por_enemigo, golpes = [0, 0, 0], defaultdict(lambda: [0, 0, 0]), defaultdict(Counter)
        for d in e.get("victimDamageReceived") or []:
            valores = (d.get("physicalDamage", 0), d.get("magicDamage", 0), d.get("trueDamage", 0))
            for i, v in enumerate(valores):
                total[i] += v
            quien = gente.get(d.get("participantId"))
            if quien and quien["teamId"] != yo["teamId"]:
                for i, v in enumerate(valores):
                    por_enemigo[quien["championName"]][i] += v
                if d.get("spellName"):
                    golpes[quien["championName"]][d["spellName"]] += sum(valores)
        vida = _vida_maxima(timeline, pid, e["timestamp"])
        salida.append({"t": e["timestamp"],
                       "asesino": gente.get(e.get("killerId"), {}).get("championName", SIN_CAMPEON),
                       "mas_dano": max(por_enemigo, key=lambda k: sum(por_enemigo[k])) if por_enemigo else None,
                       "dano": total, "por_enemigo": dict(por_enemigo), "golpes": dict(golpes),
                       "parcial": bool(vida and sum(total) < VIDA_PARCIAL * vida)})
    return salida


def perfil(lista: list[dict]) -> dict:
    """Daño y % por tipo. Los % no se redondean aquí: los umbrales miran el valor exacto."""
    totales = [sum(m["dano"][i] for m in lista) for i in range(3)]
    suma = sum(totales)
    return {"n": len(lista), "total": suma, "dano": dict(zip(TIPOS, totales)),
            "pct": {t: (100 * v / suma if suma else 0) for t, v in zip(TIPOS, totales)}}


def cumple_perfil(perfil_regla: str | None, p: dict) -> bool:
    """fisico o magico: llega a la mayoría. mezclado: físico y mágico llegan cada uno al umbral parcial.
    Pueden cumplirse dos a la vez: un 56/39 es físico y también mezclado."""
    if perfil_regla == "mezclado":
        return p["pct"]["fisico"] >= UMBRAL_PARCIAL and p["pct"]["magico"] >= UMBRAL_PARCIAL
    return perfil_regla in ("fisico", "magico") and p["pct"][perfil_regla] >= UMBRAL_SI


def amenazas(lista: list[dict]) -> dict[str, list[int]]:
    """Daño [físico, mágico, verdadero] de cada enemigo en estas muertes, de mayor a menor."""
    suma = defaultdict(lambda: [0, 0, 0])
    for m in lista:
        for nombre, v in m["por_enemigo"].items():
            for i in range(3):
                suma[nombre][i] += v[i]
    return dict(sorted(suma.items(), key=lambda kv: -sum(kv[1])))


# ---------- coincidencia ----------

def coincide_tipo(clase: str, p: dict) -> str:
    """El tipo del defensivo contra el perfil de las muertes anteriores a comprarlo."""
    if not p["total"]:
        return "sin muertes previas"
    if p["n"] == 1:
        return POCOS_DATOS
    if clase == "general":
        return "general"
    pct = p["pct"]["fisico"] + p["pct"]["magico"] if clase == "ambos" else p["pct"][clase]
    return "sí" if pct >= UMBRAL_SI else "parcial" if pct >= UMBRAL_PARCIAL else "no"


def _campeones_regla(s: dict) -> tuple[set[str], set[str]]:
    aplica = s.get("aplica") or {}
    return ({c.lower() for c in aplica.get("campeones_1", [])}, {c.lower() for c in aplica.get("campeones_2", [])})


def coincide_reglas(objeto: str, amenaza: str | None, enemigos: list[str], p: dict, situaciones: list[dict],
                    ya_tenia: tuple = ()) -> dict:
    """Qué dicen las reglas actuales (campo "aplica") de comprar este objeto. La amenaza nombrada manda, salvo con
    una sola muerte previa: entonces solo cuenta si el rival está en la partida, que no depende de tus muertes.
    ya_tenia: objetos en tu inventario al comprar; comprar otro cuando ya tienes el indicado no es desacuerdo."""
    s = next((x for x in situaciones if x["objeto"] == objeto), None)
    if s is None:
        return {"estado": "sin regla", "detalle": ""}
    if not s.get("aplica"):
        return {"estado": "no evaluable", "detalle": ""}
    uno, dos = _campeones_regla(s)
    clave = amenaza.lower() if amenaza and p["n"] != 1 else None

    def otros(indice):
        return [x["objeto"] for x in situaciones if x["objeto"] != objeto and clave in _campeones_regla(x)[indice]]

    if clave in uno:
        return {"estado": "1ª opción", "detalle": f"contra {amenaza}"}
    if clave in dos:
        primera = otros(0)
        cuales = ", ".join(x + (" (ya la tenías)" if x in ya_tenia else "") for x in primera)
        return {"estado": "2ª opción", "detalle": f"contra {amenaza}" + (f": 1ª {cuales}" if primera else "")}
    presentes = [e for e in enemigos if e.lower() in uno | dos]
    if presentes:
        return {"estado": "por rival presente", "detalle": ", ".join(presentes)}
    if clave is not None:
        elegidos = otros(0) or otros(1)
        tenidos = [x for x in elegidos if x in ya_tenia]
        if tenidos:
            return {"estado": "ya tenía el indicado", "detalle": f"contra {amenaza}: {', '.join(tenidos)}"}
        if elegidos:
            return {"estado": "otro objeto", "detalle": f"contra {amenaza}: {', '.join(elegidos)}"}
    if not p["total"]:
        return {"estado": "sin muertes previas", "detalle": ""}
    if p["n"] == 1:
        return {"estado": POCOS_DATOS, "detalle": "una sola muerte antes de comprar"}
    if cumple_perfil(s["aplica"].get("perfil"), p):
        return {"estado": "por perfil", "detalle": ETIQUETA[s["aplica"]["perfil"]]}
    return {"estado": "sin coincidencia", "detalle": "ni el rival ni el perfil están en su regla"}


def _sirve(compra_: dict, tipo: str) -> bool:
    """Contra daño verdadero, ni armadura ni resistencia mágica lo reducen: cuenta lo que dé vida o escudo, aunque
    también dé alguna de ellas (Randuin). Un escudo de un solo tipo no cuenta (Fauces, Blindadas de Avance)."""
    if tipo == "verdadero":
        return bool({"vida", "escudo"} & set(compra_["defensas"]))
    return compra_["clase"] in ("general", "ambos", tipo)


def retraso(lista: list[dict], defensivos: list[dict], fin_ms: int, componentes: tuple = ()) -> dict | None:
    """Del primer enemigo que fue quien más daño hizo en 2 muertes: cuánto tardó un defensivo que sirva contra él.
    Su tipo de daño sale de las muertes hasta esa 2ª, no de lo que hizo después. "componente": la primera compra útil
    tras esa muerte, sea componente o defensivo completo (a veces se compra el objeto entero de una vez)."""
    cuenta = Counter()
    for m in lista:
        if not m["mas_dano"]:
            continue
        cuenta[m["mas_dano"]] += 1
        if cuenta[m["mas_dano"]] == 2:
            enemigo, t2 = m["mas_dano"], m["t"]
            break
    else:
        return None
    dano = amenazas([x for x in lista if x["t"] <= t2])[enemigo]
    tipo = TIPOS[dano.index(max(dano))]
    utiles = [d for d in defensivos if _sirve(d, tipo)]
    base = {"enemigo": enemigo, "t2": t2, "tipo": tipo, "objeto": None, "minutos": None, "componente": None}
    ya = [d for d in utiles if d["t"] <= t2 and (d["vendido"] is None or d["vendido"] > t2)]
    if ya:
        return {**base, "estado": "ya lo tenía", "objeto": ya[0]["nombre"]}
    respuestas = sorted((x for x in [*componentes, *utiles] if x["t"] > t2 and _sirve(x, tipo)),
                        key=lambda x: x["t"])
    if respuestas:
        base["componente"] = {"objeto": respuestas[0]["nombre"], "minutos": (respuestas[0]["t"] - t2) / 60_000}
    despues = [d for d in utiles if d["t"] > t2]
    if despues:
        return {**base, "estado": "comprado", "objeto": despues[0]["nombre"], "minutos": (despues[0]["t"] - t2) / 60_000}
    return {**base, "estado": "nunca", "minutos": (fin_ms - t2) / 60_000}


# ---------- partida ----------

def _oro_contra(timeline: dict, pid: int, otro: int, t: int) -> int | None:
    frames = [f for f in timeline["info"]["frames"] if f["timestamp"] <= t and "participantFrames" in f]
    if not frames:
        return None
    pf = frames[-1]["participantFrames"]
    if str(pid) not in pf or str(otro) not in pf:
        return None
    return pf[str(otro)]["totalGold"] - pf[str(pid)]["totalGold"]


def _a_medio_armar(yo: dict, historial: list[dict], objetos: dict) -> list[dict]:
    """Componentes defensivos caros que seguían en el inventario al terminar (p. ej. rumbo a Fauces)."""
    salida = []
    for i in range(6):
        id_ = yo.get(f"item{i}")
        obj = objetos.get(str(id_))
        if not obj or obj["metadata"].get("final") or obj["metadata"].get("botas"):
            continue
        if (obj["metadata"].get("precio") or 0) < PRECIO_MINIMO or not _defensas(obj):
            continue
        t = max((h["t"] for h in historial if h["id"] == id_), default=None)
        if t is not None:
            salida.append({"nombre": obj["metadata"]["nombre"], "t": t})
    return sorted(salida, key=lambda x: x["t"])


def analizar(partida: dict, timeline: dict, yo: dict, objetos: dict, situaciones: list[dict],
             campeones: dict | None = None) -> dict:
    """objetos: el dict "objetos" de objetos_latest.json. situaciones: las de reglas/kindred_objetos.json."""
    pid, info = yo["participantId"], partida["info"]
    dur = info["gameDuration"] * 1000
    gente = {p["championName"]: p["participantId"] for p in info["participants"]}
    enemigos = [p["championName"] for p in info["participants"] if p["teamId"] != yo["teamId"]]
    eventos = [e for f in timeline["info"]["frames"] for e in f["events"]]
    historial = compras(eventos, pid)
    lista = muertes(partida, timeline, yo)

    defensivos = []
    for h in historial:          # en orden de compra: los anteriores son lo que ya tenías
        obj = objetos.get(str(h["id"]))
        clase = clase_objeto(obj)
        if not clase:
            continue
        nombre, fin = obj["metadata"]["nombre"], h["vendido"] or dur
        antes = [m for m in lista if m["t"] < h["t"]]
        despues = [m for m in lista if h["t"] <= m["t"] < fin]
        p_antes = perfil(antes)
        amenaza_antes = next(iter(amenazas(antes)), None)
        ya_tenia = tuple(d["nombre"] for d in defensivos if d["vendido"] is None or d["vendido"] > h["t"])
        hay_despues = fin - h["t"] >= MIN_DESPUES_MS
        defensivos.append({
            "id": h["id"], "nombre": nombre, "t": h["t"], "vendido": h["vendido"], "clase": clase,
            "defensas": _defensas(obj), "perfil_antes": p_antes, "amenaza_antes": amenaza_antes,
            "tipo": coincide_tipo(clase, p_antes),
            "regla": coincide_reglas(nombre, amenaza_antes, enemigos, p_antes, situaciones, ya_tenia),
            "antes": {"n": len(antes), "ini": 0, "fin": h["t"],
                      "tasa": len(antes) / (h["t"] / DECENA_MS) if h["t"] else None},
            "despues": {"n": len(despues), "ini": h["t"], "fin": fin,
                        "tasa": len(despues) / ((fin - h["t"]) / DECENA_MS) if hay_despues else None},
            "contra_amenaza": {"mas_dano": sum(1 for m in despues if m["mas_dano"] == amenaza_antes),
                               "ultimo_golpe": sum(1 for m in despues if m["asesino"] == amenaza_antes)}
                              if amenaza_antes else None})

    componentes = [{"t": h["t"], "nombre": objetos[str(h["id"])]["metadata"]["nombre"],
                    "clase": clase_componente(objetos[str(h["id"])]),
                    "defensas": [x for x in _defensas(objetos[str(h["id"])]) if not x.startswith("escudo")]}
                   for h in historial if clase_componente(objetos.get(str(h["id"])))]
    todas = amenazas(lista)
    amenaza = None
    if todas:
        nombre = next(iter(todas))
        golpes = Counter()
        for m in lista:
            golpes.update(m["golpes"].get(nombre, {}))
        compra = defensivos[0]["t"] if defensivos else None
        amenaza = {"nombre": nombre, "dano": todas[nombre],
                   "tipos": datos_campeones.tipos(campeones, nombre) if campeones else [],
                   "golpe": golpes.most_common(1)[0][0] if golpes else None,
                   "oro": {"primera": _oro_contra(timeline, pid, gente[nombre], lista[0]["t"]),
                           "compra": _oro_contra(timeline, pid, gente[nombre], compra) if compra is not None else None,
                           "final": _oro_contra(timeline, pid, gente[nombre], dur)}}
    return {"match_id": partida["metadata"]["matchId"], "resultado": "victoria" if yo["win"] else "derrota",
            "periodo": _periodo(partida), "dur": dur, "muertes": lista, "perfil": perfil(lista), "amenaza": amenaza,
            "enemigos_dano": todas, "defensivos": defensivos, "a_medio_armar": _a_medio_armar(yo, historial, objetos),
            "retraso": retraso(lista, defensivos, dur, tuple(componentes))}


# ---------- base y resumen ----------

def tabla_base(analisis: list[dict]) -> dict:
    """Por periodo y tramo de 5 min: [muertes, decenas de minuto jugadas]."""
    tabla = defaultdict(lambda: defaultdict(lambda: [0, 0.0]))
    for r in analisis:
        t = tabla[r["periodo"]]
        for ini in range(0, r["dur"], TRAMO_MS):
            t[ini][1] += (min(ini + TRAMO_MS, r["dur"]) - ini) / DECENA_MS
        for m in r["muertes"]:
            t[m["t"] // TRAMO_MS * TRAMO_MS][0] += 1
    return tabla


def base_en(tabla: dict, periodo: str, ini: int, fin: int) -> float | None:
    """Muertes cada 10 min del periodo en esos minutos: la tasa de cada tramo, según cuánto de él cubre [ini, fin]."""
    suma, peso = 0.0, 0.0
    for inicio, (muertes_, decenas) in tabla.get(periodo, {}).items():
        cubierto = min(fin, inicio + TRAMO_MS) - max(ini, inicio)
        if cubierto > 0 and decenas:
            suma += muertes_ / decenas * cubierto
            peso += cubierto
    return suma / peso if peso else None


def resumen(analisis: list[dict], tabla: dict) -> dict:
    salida = {}
    for periodo in PERIODOS:
        xs = [r for r in analisis if r["periodo"] == periodo]
        if not xs:
            continue
        por_objeto = defaultdict(list)
        for r in xs:
            for d in r["defensivos"]:
                por_objeto[d["nombre"]].append(d)
        filas = []
        for nombre, ds in sorted(por_objeto.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            fila = {"objeto": nombre, "veces": len(ds), "minuto": median(d["t"] for d in ds) / 60_000,
                    "tipo": Counter(d["tipo"] for d in ds), "regla": Counter(d["regla"]["estado"] for d in ds)}
            for clave in ("antes", "despues"):
                tramos = [d[clave] for d in ds if d[clave]["tasa"] is not None]
                tiempo = sum(x["fin"] - x["ini"] for x in tramos)
                fila[clave] = sum(x["n"] for x in tramos) / (tiempo / DECENA_MS) if tiempo else None
                con_base = [(base_en(tabla, periodo, x["ini"], x["fin"]), x["fin"] - x["ini"]) for x in tramos]
                con_base = [(b, w) for b, w in con_base if b is not None]
                fila[f"base_{clave}"] = (sum(b * w for b, w in con_base) / sum(w for _, w in con_base)
                                         if con_base else None)
            filas.append(fila)
        retrasos = [r["retraso"] for r in xs if r["retraso"]]
        minutos = [x["minutos"] for x in retrasos if x["estado"] == "comprado"]
        componente = [x["componente"]["minutos"] for x in retrasos if x["componente"]]
        muertes_ = [m for r in xs for m in r["muertes"]]
        salida[periodo] = {
            "partidas": len(xs), "con_defensivo": sum(1 for r in xs if r["defensivos"]), "muertes": len(muertes_),
            "parciales": sum(1 for m in muertes_ if m["parcial"]), "perfil": perfil(muertes_), "filas": filas,
            "retraso": {"partidas": len(retrasos), "mediana": median(minutos) if minutos else None,
                        "comprado": len(minutos), "ya": sum(1 for x in retrasos if x["estado"] == "ya lo tenía"),
                        "nunca": sum(1 for x in retrasos if x["estado"] == "nunca"),
                        "componente_partidas": len(componente),
                        "componente_mediana": median(componente) if componente else None,
                        "sin_respuesta": sum(1 for x in retrasos if x["estado"] == "nunca" and not x["componente"])}}
    return salida


# ---------- texto ----------

def _perfil_texto(p: dict) -> str:
    return "   ".join(f"{ETIQUETA[t]} {round(p['pct'][t])}%" for t in TIPOS)


def _tasa(x: float | None) -> str:
    return "-" if x is None else f"{x:.2f}"


def _oro_texto(x: int | None) -> str:
    return "?" if x is None else f"{x:+d}"


def texto_partida(r: dict, tabla: dict) -> list[str]:
    lineas = [f"PERFIL DE MIS MUERTES ({len(r['muertes'])})   {_perfil_texto(r['perfil'])}"]
    if not r["muertes"]:
        lineas = ["No moriste en esta partida."]
    for d in r["defensivos"]:
        despues = [m for m in r["muertes"] if d["despues"]["ini"] <= m["t"] < d["despues"]["fin"]]
        lineas += [f"  antes de {d['nombre']} ({d['antes']['n']}): {_perfil_texto(d['perfil_antes'])}",
                   f"  después de {d['nombre']} ({len(despues)}): {_perfil_texto(perfil(despues))}"]
    if r["muertes"]:
        lineas += ["", f"{'min':>6}  {'te mató':<16}{'más daño':<16}físico / mágico / verdadero"]
        for m in r["muertes"]:
            extra = []
            if m["asesino"] != m["mas_dano"] and m["asesino"] in m["por_enemigo"]:
                extra.append(f"{m['asesino']}: {sum(m['por_enemigo'][m['asesino']])}")
            if m["parcial"]:
                extra.append("desglose parcial")
            nota = f"   ({'; '.join(extra)})" if extra else ""
            f_, ma, v = m["dano"]
            lineas.append(f"{_mmss(m['t']):>6}  {m['asesino']:<16}{m['mas_dano'] or '-':<16}{f_:>6} / {ma:>6} / {v:>6}{nota}")
    a = r["amenaza"]
    if a:
        tipos = f" ({', '.join(a['tipos'])})" if a["tipos"] else ""
        golpe = f"; golpe principal: {a['golpe']}" if a["golpe"] else ""
        oro = a["oro"]
        compra = f", {_oro_texto(oro['compra'])} en la compra" if oro["compra"] is not None else ""
        lineas += ["", f"AMENAZA PRINCIPAL  {a['nombre']}{tipos}: {sum(a['dano'])} de daño en mis muertes",
                   f"  físico {a['dano'][0]}, mágico {a['dano'][1]}, verdadero {a['dano'][2]}{golpe}",
                   f"  oro contra mí: {_oro_texto(oro['primera'])} en la 1ª muerte{compra}, "
                   f"{_oro_texto(oro['final'])} al final"]
        siguientes = [f"{n} {sum(v)}" for n, v in r["enemigos_dano"].items() if n != a["nombre"]][:2]
        if siguientes:
            lineas.append(f"  siguientes: {', '.join(siguientes)}")
    lineas.append("")
    if not r["defensivos"]:
        lineas.append("DEFENSIVOS  ninguno completo")
    for d in r["defensivos"]:
        vendido = f", vendido {_mmss(d['vendido'])}" if d["vendido"] else ""
        regla = d["regla"]
        detalle = f" ({regla['detalle']})" if regla["detalle"] else ""
        lineas += [f"DEFENSIVO  {d['nombre']}, {_mmss(d['t'])} ({', '.join(d['defensas'])}){vendido}"]
        por_tipo = d["tipo"]
        if d["perfil_antes"]["total"] and d["clase"] != "general":
            por_tipo += f" ({round(d['perfil_antes']['pct']['fisico'])}% físico, " \
                        f"{round(d['perfil_antes']['pct']['magico'])}% mágico antes de comprar)"
        lineas += [f"  por tipo: {por_tipo}",
                   f"  según reglas actuales: {regla['estado']}{detalle}"]
        ant, des = d["antes"], d["despues"]
        lineas.append(f"  muertes/10 min: antes {_tasa(ant['tasa'])} "
                      f"(base {_tasa(base_en(tabla, r['periodo'], ant['ini'], ant['fin']))}), después {_tasa(des['tasa'])} "
                      f"(base {_tasa(base_en(tabla, r['periodo'], des['ini'], des['fin']))})")
        if d["contra_amenaza"]:
            c = d["contra_amenaza"]
            lineas.append(f"  contra {d['amenaza_antes']} después: más daño en {c['mas_dano']}, "
                          f"último golpe en {c['ultimo_golpe']}")
    for x in r["a_medio_armar"]:
        lineas.append(f"A MEDIO ARMAR  {x['nombre']}, {_mmss(x['t'])}")
    q = r["retraso"]
    if q:
        inicio = f"RETRASO  2ª muerte contra {q['enemigo']} en {_mmss(q['t2'])} (daño sobre todo {ETIQUETA[q['tipo']]}): "
        if q["estado"] == "comprado":
            lineas.append(f"{inicio}{q['minutos']:.1f} min hasta {q['objeto']}")
        elif q["estado"] == "ya lo tenía":
            lineas.append(f"{inicio}ya tenía {q['objeto']}")
        else:
            lineas.append(f"{inicio}ningún defensivo que sirva (quedaban {q['minutos']:.1f} min)")
        if q["componente"]:
            lineas.append(f"  primera compra útil: {q['componente']['minutos']:.1f} min, {q['componente']['objeto']}")
        elif q["estado"] == "nunca":
            lineas.append("  primera compra útil: ninguna, ni un componente")
    lineas += ["", "Base = muertes cada 10 min de ese periodo en los mismos minutos; compara, no prueba causa. "
                   "Daño ya reducido por tu armadura y resistencia."]
    return lineas


def texto_resumen(res: dict) -> list[str]:
    lineas = []
    for periodo, x in res.items():
        lineas += [f"=== {periodo}: {x['partidas']} partidas, {x['muertes']} muertes, "
                   f"{x['con_defensivo']} partidas con defensivo",
                   f"Perfil de mis muertes: {_perfil_texto(x['perfil'])}"
                   + (f"  ({x['parciales']} con desglose parcial)" if x["parciales"] else ""), ""]
        lineas.append(f"{'objeto':<30}{'veces':>6}{'min':>6}{'antes (base)':>15}{'después (base)':>16}"
                      "  por tipo | según reglas actuales")
        for f in x["filas"]:
            marca = "*" if f["veces"] < POCOS_CASOS else ""
            tipo = ", ".join(f"{k} {n}" for k, n in f["tipo"].most_common())
            regla = ", ".join(f"{k} {n}" for k, n in f["regla"].most_common())
            lineas.append(f"{f['objeto'] + marca:<30}{f['veces']:>6}{f['minuto']:>6.1f}"
                          f"{_tasa(f['antes']) + ' (' + _tasa(f['base_antes']) + ')':>15}"
                          f"{_tasa(f['despues']) + ' (' + _tasa(f['base_despues']) + ')':>16}  {tipo} | {regla}")
        q = x["retraso"]
        mediana = "-" if q["mediana"] is None else f"{q['mediana']:.1f} min"
        comp = "-" if q["componente_mediana"] is None else f"{q['componente_mediana']:.1f} min"
        lineas += ["", f"Retraso, en {q['partidas']} partidas con un enemigo en 2 muertes: mediana {mediana} "
                       f"({q['comprado']} partidas); ya lo tenía {q['ya']}; nunca {q['nunca']}.",
                   f"Primera compra útil, aunque sea un componente: mediana {comp} ({q['componente_partidas']} partidas); "
                   f"ni un componente: {q['sin_respuesta']}.", ""]
    lineas += [f"* Menos de {POCOS_CASOS} compras: es anécdota, no cambies una regla por esto.",
               "Base = muertes cada 10 min de ese periodo en los mismos minutos; compara, no prueba causa.",
               "No mezcles periodos: las partidas de febrero a junio son de otra época."]
    return lineas
