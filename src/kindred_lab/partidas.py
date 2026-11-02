"""Partidas: de la respuesta de la API de Riot a una fila de registro/partidas.csv.

Se llena solo: resultado, duración, KDA, enemigos, runas elegidas, muertes antes del minuto 10,
qué daño recibiste más (AD/AP) y los valores de cada runa. Qué var1/var2/var3 es cada valor sale de
Community Dragon (cdragon.py); `calibrar` solo hace falta si alguna runa no trae ese texto.
Sigue siendo manual lo subjetivo: alcance_temprano y las notas.
"""
import csv
import json
from datetime import datetime
from pathlib import Path

from . import cdragon, config

COLUMNAS = ["fecha", "parche", "resultado", "duracion_min", "kda", "enemigos", "alcance_temprano",
            "dano_que_me_mata", "piedra_angular", "fila_1", "fila_2", "fila_3", "secundaria",
            "secundaria_1", "secundaria_2", "hechizos", "muertes_antes_min10", "valor_piedra_angular",
            "valor_fila_1", "valor_fila_2", "valor_fila_3", "valor_secundaria_1", "valor_secundaria_2",
            "estadisticas_runas", "notas", "match_id"]


# ---------- valores de runas ----------

def cargar_valores(ruta: Path | None = None) -> dict:
    ruta = ruta or config.VALORES_RUNAS
    if not ruta.exists():
        return {"runas": {}}
    return json.loads(ruta.read_text(encoding="utf-8"))


def guardar_valores(datos: dict, ruta: Path | None = None) -> None:
    (ruta or config.VALORES_RUNAS).write_text(
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _valor(sel: dict, clave: str, valores: dict, estad: dict) -> str:
    """Valor principal de la runa: el calibrado a mano manda; si no, el de Community Dragon."""
    cfg = valores.get("runas", {}).get(clave)
    if cfg:
        v = sel.get(cfg["var"], 0) / cfg.get("div", 1)
        return f"{round(v):d}{cfg.get('unidad', '')}"
    stats = estad.get(sel["perk"])
    return cdragon.formatear(sel, stats[0]) if stats else ""


# ---------- partida -> fila ----------

HECHIZOS = {1: "Purificar", 3: "Extenuación", 4: "Destello", 6: "Fantasma", 7: "Curación", 11: "Castigo",
            12: "Teleportar", 13: "Claridad", 14: "Prender", 21: "Barrera", 32: "Marca"}


def hechizos(participante: dict) -> str:
    """'Destello+Castigo', 'Fantasma+Castigo'... (Castigo siempre al final)."""
    nombres = [HECHIZOS.get(participante.get(k), str(participante.get(k)))
               for k in ("summoner1Id", "summoner2Id") if participante.get(k) is not None]
    return "+".join(sorted(nombres, key=lambda n: (n == "Castigo", n)))


def completar_hechizos(filas: list[dict], puuid: str, cargar_partida) -> int:
    """Rellena la columna hechizos de filas viejas con las partidas en caché. Devuelve cuántas completó."""
    n = 0
    for f in filas:
        if f["match_id"] and not f["hechizos"]:
            try:
                f["hechizos"] = hechizos(_participante(cargar_partida(f["match_id"]), puuid))
                n += 1
            except (OSError, KeyError, ValueError):
                pass
    return n


def _participante(partida: dict, puuid: str) -> dict:
    for p in partida["info"]["participants"]:
        if p["puuid"] == puuid:
            return p
    raise KeyError(f"El puuid no participó en {partida['metadata']['matchId']}")


def _clave_arbol(datos_runas: dict, id_arbol: int) -> str:
    for clave, a in datos_runas["arboles"].items():
        if a["id"] == id_arbol:
            return clave
    return str(id_arbol)


def _fila_runa(datos_runas: dict, perk: int) -> int:
    r = datos_runas["runas"].get(str(perk))
    return r["fila"] if r else 99


def _clave_runa(datos_runas: dict, perk: int) -> str:
    r = datos_runas["runas"].get(str(perk))
    return r["clave"] if r else str(perk)


def muertes_antes(timeline: dict | None, participant_id: int, minuto: int = 10) -> int | str:
    if not timeline:
        return ""
    limite = minuto * 60_000
    return sum(1 for f in timeline["info"]["frames"] for e in f["events"]
               if e["type"] == "CHAMPION_KILL" and e["victimId"] == participant_id and e["timestamp"] < limite)


def fila_desde_partida(partida: dict, puuid: str, datos_runas: dict, valores: dict | None = None,
                       timeline: dict | None = None, estad: dict | None = None) -> dict:
    valores = valores or {"runas": {}}
    estad = estad or {}
    info = partida["info"]
    p = _participante(partida, puuid)
    estilos = {s["description"]: s for s in p["perks"]["styles"]}
    prim, sec = estilos["primaryStyle"], estilos["subStyle"]
    pp = [_clave_runa(datos_runas, s["perk"]) for s in prim["selections"]]
    # La API da la secundaria en el orden en que la elegiste; se ordena por fila para que
    # secundaria_1 sea siempre la de la fila más alta (p. ej. Coraza Ósea antes que Inquebrantable).
    sec_sel = sorted(sec["selections"], key=lambda s: _fila_runa(datos_runas, s["perk"]))
    ss = [_clave_runa(datos_runas, s["perk"]) for s in sec_sel]

    fisico, magico = p.get("physicalDamageTaken", 0), p.get("magicDamageTaken", 0)
    total = fisico + magico
    nota_dano = ""
    dano = ""
    if total:
        dano = "AD" if fisico >= magico else "AP"
        nota_dano = f"recibido: {round(100 * fisico / total)}% AD / {round(100 * magico / total)}% AP"

    # hora local de tu PC (no UTC), para que una partida de las 8 pm no salga con fecha de mañana
    fecha = datetime.fromtimestamp(info["gameStartTimestamp"] / 1000).strftime("%Y-%m-%d")
    resultado = "remake" if p.get("gameEndedInEarlySurrender") else ("victoria" if p["win"] else "derrota")
    enemigos = [x["championName"] for x in info["participants"] if x["teamId"] != p["teamId"]]

    return {
        "fecha": fecha,
        "parche": ".".join(info["gameVersion"].split(".")[:2]),
        "resultado": resultado,
        "duracion_min": f"{info['gameDuration'] / 60:.1f}",
        "kda": f"{p['kills']}/{p['deaths']}/{p['assists']}",
        "enemigos": "|".join(enemigos),
        "alcance_temprano": "",
        "dano_que_me_mata": dano,
        "piedra_angular": pp[0], "fila_1": pp[1], "fila_2": pp[2], "fila_3": pp[3],
        "secundaria": _clave_arbol(datos_runas, sec["style"]),
        "secundaria_1": ss[0], "secundaria_2": ss[1],
        "hechizos": hechizos(p),
        "muertes_antes_min10": muertes_antes(timeline, p["participantId"]),
        "valor_piedra_angular": _valor(prim["selections"][0], pp[0], valores, estad),
        "valor_fila_1": _valor(prim["selections"][1], pp[1], valores, estad),
        "valor_fila_2": _valor(prim["selections"][2], pp[2], valores, estad),
        "valor_fila_3": _valor(prim["selections"][3], pp[3], valores, estad),
        "valor_secundaria_1": _valor(sec_sel[0], ss[0], valores, estad),
        "valor_secundaria_2": _valor(sec_sel[1], ss[1], valores, estad),
        "estadisticas_runas": " | ".join(
            f"{k}: {cdragon.todas(s, estad[s['perk']])}"
            for k, s in zip(pp + ss, prim["selections"] + sec_sel) if s["perk"] in estad),
        "notas": nota_dano,
        "match_id": partida["metadata"]["matchId"],
    }


# ---------- calibración ----------

def _selecciones(partida: dict, puuid: str, datos_runas: dict) -> dict:
    p = _participante(partida, puuid)
    return {_clave_runa(datos_runas, s["perk"]): s
            for st in p["perks"]["styles"] for s in st["selections"]}


def calibrar(partida: dict, puuid: str, datos_runas: dict, esperados: dict[str, float]) -> dict:
    """Busca, para cada runa, qué var (y qué divisor) reproduce el número que viste en pantalla.

    Devuelve {clave: {"var","div","unidad"?}} solo de las que encontró; el resto no se toca.
    """
    sels = _selecciones(partida, puuid, datos_runas)
    encontradas = {}
    for clave, objetivo in esperados.items():
        sel = sels.get(clave)
        if not sel:
            continue
        tol = 1.0 if objetivo >= 10 else 0.5
        for var in ("var1", "var2", "var3"):
            for div in (1, 10, 100, 1000):
                if abs(sel.get(var, 0) / div - objetivo) <= tol and sel.get(var, 0) != 0:
                    encontradas[clave] = {"var": var, "div": div}
                    break
            if clave in encontradas:
                break
    return encontradas


# ---------- registro CSV ----------

def leer_registro(ruta: Path | None = None) -> list[dict]:
    ruta = ruta or config.REGISTRO_CSV
    if not ruta.exists():
        return []
    with ruta.open(encoding="utf-8-sig", newline="") as f:
        return [{c: (fila.get(c) or "") for c in COLUMNAS} for fila in csv.DictReader(f)]


def escribir_registro(filas: list[dict], ruta: Path | None = None) -> None:
    ruta = ruta or config.REGISTRO_CSV
    with ruta.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(filas)


def agregar(nuevas: list[dict], ruta: Path | None = None) -> int:
    """Añade filas al CSV sin duplicar match_id; migra el encabezado viejo (sin match_id). Devuelve cuántas añadió."""
    filas = leer_registro(ruta)
    vistos = {f["match_id"] for f in filas if f["match_id"]}
    nuevas = [n for n in nuevas if n["match_id"] not in vistos]
    escribir_registro(filas + nuevas, ruta)
    return len(nuevas)


# ---------- anotaciones manuales ----------

MARCA_EXCLUIR = "excluir"


def es_excluida(fila: dict) -> bool:
    return MARCA_EXCLUIR in fila.get("notas", "").lower()


def _numero_partida(match_id: str) -> int:
    n = match_id.rpartition("_")[2]
    return int(n) if n.isdigit() else -1


def anotar(filas: list[dict], match_id: str, alcance: str | None = None, nota: str | None = None,
           excluir: bool | None = None) -> dict:
    """Modifica (en la lista) la fila de match_id ('ultima' = la partida más reciente) y la devuelve."""
    con_id = [f for f in filas if f["match_id"]]
    if not con_id:
        raise KeyError("El registro no tiene partidas importadas.")
    if match_id == "ultima":
        fila = max(con_id, key=lambda f: _numero_partida(f["match_id"]))
    else:
        coinciden = [f for f in con_id if f["match_id"] == match_id]
        if not coinciden:
            raise KeyError(f"No hay ninguna partida {match_id} en el registro.")
        fila = coinciden[0]
    if alcance is not None:
        fila["alcance_temprano"] = alcance
    partes = [x.strip() for x in fila["notas"].split(";") if x.strip()]
    if nota:
        partes.append(nota.strip())
    if excluir is True and not es_excluida(fila):
        partes.append(MARCA_EXCLUIR)
    elif excluir is False:
        partes = [x for x in partes if x.lower() != MARCA_EXCLUIR]
    fila["notas"] = "; ".join(partes)
    return fila


# ---------- resumen ----------

def _numero(txt: str) -> float | None:
    """'3545' -> 3545; '102s' -> 102; '10:40' -> 640 (segundos)."""
    if ":" in txt:
        m, _, s = txt.partition(":")
        return float(m) * 60 + float(s) if m.strip().isdigit() and s.strip().isdigit() else None
    t = "".join(c for c in txt if c.isdigit() or c == ".")
    return float(t) if t else None


def es_corta(fila: dict, duracion_minima: float) -> bool:
    d = _numero(fila["duracion_min"])
    return d is not None and d < duracion_minima


def resumen(filas: list[dict], minimo: int = 1, duracion_minima: float = 20) -> list[dict]:
    """Agrupa por piedra angular / fila 3 / secundaria y calcula partidas, victorias y valor medio por runa.

    Ignora remakes, partidas de menos de `duracion_minima` minutos (rendiciones tempranas: las runas
    casi no influyeron) y las marcadas con "excluir" en notas (p. ej. un compañero que sabotea).
    """
    grupos: dict[tuple, list[dict]] = {}
    for f in filas:
        if f["resultado"] not in ("victoria", "derrota") or es_corta(f, duracion_minima) or es_excluida(f):
            continue
        for campo, valor in (("piedra_angular", "valor_piedra_angular"), ("fila_1", "valor_fila_1"),
                             ("fila_2", "valor_fila_2"), ("fila_3", "valor_fila_3"),
                             ("secundaria_1", "valor_secundaria_1"), ("secundaria_2", "valor_secundaria_2"),
                             ("hechizos", "hechizos")):
            if f[campo]:
                grupos.setdefault((campo, f[campo]), []).append((f, valor))
    salida = []
    for (campo, clave), items in sorted(grupos.items()):
        if len(items) < minimo:
            continue
        valores = [v for f, col in items if (v := _numero(f[col])) is not None]
        medio = round(sum(valores) / len(valores)) if valores else None
        es_tiempo = any(":" in f[col] for f, col in items)
        es_pct = any("%" in f[col] for f, col in items)
        por_min = None
        if medio is not None and es_tiempo:
            medio = f"{medio // 60}:{medio % 60:02d}"          # tiempos (Leyenda) en m:ss; por minuto no aplica
        elif medio is not None and es_pct:
            medio = f"{medio}%"                                # porcentajes (Acondicionamiento): sin por minuto
        else:
            # promedio de (valor / duración) de cada partida: compara partidas largas y cortas por igual
            tasas = [v / d for f, col in items
                     if (v := _numero(f[col])) is not None and (d := _numero(f["duracion_min"]))]
            por_min = round(sum(tasas) / len(tasas), 1) if tasas else None
        salida.append({"campo": campo, "runa": clave, "partidas": len(items),
                       "victorias": sum(1 for f, _ in items if f["resultado"] == "victoria"),
                       "valor_medio": medio, "por_minuto": por_min})
    return salida
