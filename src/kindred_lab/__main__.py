"""Línea de comandos.

  python -m kindred_lab runas actualizar [--version 16.20.1] [--idioma es_MX] [--archivo runesReforged.json]
  python -m kindred_lab runas comparar 16.19.1 16.20.1
  python -m kindred_lab runas buscar "ultima batalla"
  python -m kindred_lab runas arbol Precision
  python -m kindred_lab runas versiones
  python -m kindred_lab reglas validar
  python -m kindred_lab partidas importar --riot-id "Nombre#TAG" [--cantidad 10]
  python -m kindred_lab partidas calibrar <match_id> --riot-id "Nombre#TAG" PressTheAttack=3545 ...
  python -m kindred_lab partidas resumen
  python -m kindred_lab temprano [--minuto 10]      (extra: primeros minutos, no afecta las runas)
  python -m kindred_lab objetivos [--minuto 20]     (extra: dragones, Barón, torres... por partida)
  python -m kindred_lab jungla [--ultima]           (extra: visión, muertes caras y dónde mueres)
  python -m kindred_lab momentos                    (extra: en qué tramo de 5 min se tuerce la partida)
"""
import argparse
import os
import sys
from pathlib import Path

from . import cdragon, config, partidas, riot, runas


def _imprimir_runa(r: dict, arboles: dict) -> None:
    arbol = arboles.get(r["arbol"], {}).get("nombre", r["arbol"])
    fila = "piedra angular" if r["fila"] == 0 else f"fila {r['fila']}"
    print(f"{r['nombre']}  [{arbol}, {fila}, id {r['id']}]")
    print(f"  {r['larga'] or r['corta']}\n")


def cmd_actualizar(a) -> int:
    res = runas.actualizar(version=a.version, idioma=a.idioma,
                           archivo_local=Path(a.archivo) if a.archivo else None)
    print(f"Parche {res['version']}: guardado en {res['ruta']}")
    c = res["comparacion"]
    if c is None:
        print("Primer parche guardado: no hay nada con qué comparar todavía.")
    elif not runas.hay_cambios(c):
        print(f"Sin cambios respecto a {c['desde']}.")
    else:
        print(f"Cambios respecto a {c['desde']}: {len(c['nuevas'])} nuevas, "
              f"{len(c['quitadas'])} quitadas, {len(c['cambiadas'])} cambiadas.")
        print(f"Reporte: {res['reporte']}")
    return 0


def cmd_comparar(a) -> int:
    viejo, nuevo = runas.cargar(a.desde), runas.cargar(a.hasta)
    print(runas.reporte_markdown(runas.comparar(viejo, nuevo), nuevo["arboles"]))
    return 0


def cmd_buscar(a) -> int:
    datos = runas.cargar(a.version)
    encontradas = runas.buscar(datos, a.texto)
    if not encontradas:
        print(f"Nada coincide con '{a.texto}'.")
        return 1
    for r in encontradas:
        _imprimir_runa(r, datos["arboles"])
    return 0


def cmd_arbol(a) -> int:
    datos = runas.cargar(a.version)
    for fila in runas.arbol_por_filas(datos, a.arbol):
        n = fila[0]["fila"]
        print(f"--- {'Piedras angulares' if n == 0 else f'Fila {n}'} ---")
        for r in fila:
            _imprimir_runa(r, datos["arboles"])
    return 0


def cmd_versiones(_a) -> int:
    vs = runas.versiones_procesadas()
    print("\n".join(vs) if vs else "Todavía no has guardado ningún parche.")
    return 0


def cmd_validar_reglas(a) -> int:
    from . import reglas
    datos = runas.cargar(a.version)
    problemas = reglas.validar(reglas.cargar(), datos)
    if not problemas:
        print(f"Reglas válidas para el parche {datos['version']}.")
        return 0
    print("\n".join(problemas))
    return 1


def _riot_id(a) -> str:
    rid = a.riot_id or os.environ.get("RIOT_ID") or riot.secretos().get("riot_id", "")
    if not rid or rid.startswith("TuNombre"):
        raise ValueError("Falta tu Riot ID: ponlo en secretos.json (riot_id), en la variable RIOT_ID "
                         "o con --riot-id \"Nombre#TAG\".")
    return rid


def cmd_importar(a) -> int:
    datos_runas = runas.cargar()
    valores = partidas.cargar_valores()
    try:
        estad = cdragon.estadisticas(cdragon.descargar())
    except OSError as e:
        estad = {}
        print(f"Aviso: no se pudo bajar perks.json de Community Dragon ({e}); solo se usan valores calibrados.")
    pu = riot.puuid(_riot_id(a), a.region)
    ids = riot.ids_partidas(pu, a.cantidad, a.cola, a.region)
    filas, otras = [], 0
    for mid in ids:
        p = riot.partida(mid, region=a.region)
        mia = partidas._participante(p, pu)
        if a.campeon and mia["championName"] != a.campeon:
            otras += 1
            continue
        filas.append(partidas.fila_desde_partida(p, pu, datos_runas, valores,
                                                 riot.timeline(mid, region=a.region), estad))
    nuevas = partidas.agregar(filas)
    registro = partidas.leer_registro()
    completadas = partidas.completar_hechizos(registro, pu, lambda mid: riot.partida(mid, region=a.region))
    if completadas:
        partidas.escribir_registro(registro)
        print(f"Hechizos de invocador completados en {completadas} partidas anteriores.")
    print(f"{len(ids)} partidas revisadas: {len(filas)} de {a.campeon or 'cualquier campeón'}, "
          f"{otras} de otros campeones omitidas, {nuevas} nuevas añadidas a {config.REGISTRO_CSV.name}.")
    return 0


def cmd_calibrar(a) -> int:
    esperados = {}
    for par in a.valores:
        clave, _, num = par.partition("=")
        esperados[clave] = float(num)
    pu = riot.puuid(_riot_id(a), a.region)
    p = riot.partida(a.match_id, region=a.region)
    hallado = partidas.calibrar(p, pu, runas.cargar(), esperados)
    for clave in esperados:
        print(f"{clave}: " + (f"{hallado[clave]['var']} / {hallado[clave]['div']}" if clave in hallado else "sin coincidencia"))
    if hallado:
        val = partidas.cargar_valores()
        val["runas"].update(hallado)
        partidas.guardar_valores(val)
        print(f"Guardado en {config.VALORES_RUNAS}")
    return 0 if hallado else 1


def cmd_anotar(a) -> int:
    registro = partidas.leer_registro()
    excluir = True if a.excluir else (False if a.incluir else None)
    f = partidas.anotar(registro, a.match_id, a.alcance, a.nota, excluir)
    partidas.escribir_registro(registro)
    print(f"{f['match_id']} ({f['fecha']}, {f['resultado']}, {f['kda']})")
    print(f"  alcance_temprano: {f['alcance_temprano'] or '(vacío)'}")
    print(f"  notas: {f['notas'] or '(vacío)'}")
    return 0


def cmd_resumen(a) -> int:
    registro = partidas.leer_registro(Path(a.registro) if a.registro else None)
    cortas = sum(1 for f in registro if partidas.es_corta(f, a.duracion_minima))
    excluidas = sum(1 for f in registro if partidas.es_excluida(f) and not partidas.es_corta(f, a.duracion_minima))
    filas = partidas.resumen(registro, a.minimo, a.duracion_minima)
    if cortas:
        print(f"Se ignoran {cortas} partidas de menos de {a.duracion_minima:g} min.")
    if excluidas:
        print(f"Se ignoran {excluidas} partidas marcadas con 'excluir'.")
    if cortas or excluidas:
        print()
    if not filas:
        print("No hay partidas con resultado en el registro.")
        return 1
    print(f"{'campo':<16}{'runa':<22}{'partidas':>9}{'victorias':>10}{'valor medio':>13}{'por minuto':>12}")
    for f in filas:
        vm = "" if f["valor_medio"] is None else f["valor_medio"]
        pm = "" if f["por_minuto"] is None else f["por_minuto"]
        print(f"{f['campo']:<16}{f['runa']:<22}{f['partidas']:>9}{f['victorias']:>10}{vm!s:>13}{pm!s:>12}")
    print("\nCon pocas partidas, esto es anécdota: no cambies una regla por 3 partidas.")
    return 0


def cmd_temprano(a) -> int:
    from . import temprano
    rid = _riot_id(a)
    pu = None
    filas = []
    for f in partidas.leer_registro():
        if not f["match_id"] or f["resultado"] not in ("victoria", "derrota"):
            continue
        if partidas.es_excluida(f) and not a.todas:
            continue
        cache = temprano.cargar_cache(f["match_id"])
        if not cache:
            continue
        partida_, timeline_ = cache
        try:
            yo = temprano.buscar_yo(partida_, riot_id=rid, puuid=pu)
        except KeyError:
            pu = pu or riot.puuid(rid, a.region)        # respaldo: una llamada a la API
            yo = temprano.buscar_yo(partida_, puuid=pu)
        r = temprano.analizar(partida_, timeline_, yo, a.minuto)
        r["fecha"] = f["fecha"]
        filas.append(r)
    if not filas:
        print("No hay partidas importadas con timeline en data/raw/riot/.")
        return 1

    filas.sort(key=lambda r: (r["fecha"], r["match_id"]))
    m = a.minuto
    print(f"{'fecha':<11}{'resultado':<10}{'jungla rival':<14}{'muertes eq.':>12}{'con su jg':>10}"
          f"{'mías':>6}{'bajas eq.':>10}{'participé':>10}{f'oro min {m}':>12}"
          f"{'daño a camp.':>13}")
    for r in filas:
        oro = "" if r["dif_oro"] is None else f"{r['dif_oro']:+d}"
        dano = "" if r["dano_campeones"] is None else r["dano_campeones"]
        print(f"{r['fecha']:<11}{r['resultado']:<10}{r['jungla_enemigo']:<14}{r['muertes_equipo']:>12}"
              f"{r['con_jungla_enemigo']:>10}{r['mias']:>6}{r['bajas_equipo']:>10}"
              f"{r['mis_participaciones']:>10}{oro:>12}{dano!s:>13}")

    t = temprano.totales(filas)
    print(f"\nAntes del minuto {m}, en {t['partidas']} partidas:")
    print(f"- Tu equipo muere {t['muertes_equipo_media']} veces por partida; tú, {t['mias_media']}.")
    print(f"- El jungla enemigo participó en el {t['pct_con_jungla']}% de esas muertes "
          f"(el resto: peleas de carril sin él).")
    print(f"- Participaste en el {t['pct_participacion']}% de las bajas de tu equipo.")
    if t["dif_oro_media"] is not None:
        print(f"- Oro de equipo en el minuto {m}: {t['dif_oro_media']:+d} de media. "
              f"Atrás en {t['atras']} partidas (ganaste {t['victorias_atras']}), "
              f"adelante o igual en {t['adelante']} (ganaste {t['victorias_adelante']}).")
    print(f"\nVictorias contra derrotas (antes del minuto {m}):")
    print(f"{'':<12}{'partidas':>9}{'participé':>11}{'daño a camp.':>14}")
    for res, v in t["por_resultado"].items():
        part = "" if v["participacion"] is None else f"{v['participacion']}%"
        dano = "" if v["dano"] is None else round(v["dano"])
        print(f"{res:<12}{v['partidas']:>9}{part:>11}{dano!s:>14}")
    print("\nDaño alto con pocas bajas = emboscaste y no salió; daño bajo con pocas bajas = no fuiste.")
    return 0


def _partidas_en_cache(a, solo_ultima: bool = False):
    """(fila del registro, partida, timeline, yo) de cada partida válida con caché.
    Con solo_ultima, solo la más reciente del registro, aunque esté marcada con 'excluir'."""
    from . import temprano
    rid = _riot_id(a)
    pu = None
    filas = [f for f in partidas.leer_registro() if f["match_id"] and f["resultado"] in ("victoria", "derrota")]
    if solo_ultima:
        filas = [max(filas, key=lambda f: partidas._numero_partida(f["match_id"]))] if filas else []
    for f in filas:
        if partidas.es_excluida(f) and not (a.todas or solo_ultima):
            continue
        cache = temprano.cargar_cache(f["match_id"])
        if not cache:
            continue
        partida_, timeline_ = cache
        try:
            yo = temprano.buscar_yo(partida_, riot_id=rid, puuid=pu)
        except KeyError:
            pu = pu or riot.puuid(rid, a.region)
            yo = temprano.buscar_yo(partida_, puuid=pu)
        yield f, partida_, timeline_, yo


def cmd_objetivos(a) -> int:
    from . import objetivos
    filas = []
    for f, partida_, timeline_, yo in _partidas_en_cache(a):
        r = objetivos.contar(partida_, timeline_, yo, a.minuto)
        r["fecha"], r["duracion"] = f["fecha"], f["duracion_min"]
        filas.append(r)
    if not filas:
        print("No hay partidas importadas con timeline en data/raw/riot/.")
        return 1
    filas.sort(key=lambda r: (r["fecha"], r["match_id"]))
    hasta = f"hasta el minuto {a.minuto}" if a.minuto else "en toda la partida"
    print(f"Objetivos {hasta} (tu equipo-enemigo):\n")
    print(f"{'fecha':<11}{'resultado':<10}{'min':>5}{'dragones':>10}{'larvas':>8}{'heraldo':>9}"
          f"{'barón':>7}{'torres':>8}{'placas':>8}{'1er barón':>12}")

    def par(x):
        return f"{x[0]}-{x[1]}"

    for r in filas:
        pb = f"{r['primer_baron'][0][:3]} {r['primer_baron'][1]}'" if r["primer_baron"] else "-"
        print(f"{r['fecha']:<11}{r['resultado']:<10}{r['duracion']:>5}{par(r['dragones']):>10}"
              f"{par(r['larvas']):>8}{par(r['heraldo']):>9}{par(r['baron']):>7}{par(r['torres']):>8}"
              f"{par(r['placas']):>8}{pb:>12}")

    t = objetivos.totales(filas)
    print(f"\nDiferencia media (tu equipo menos el enemigo):")
    print(f"{'':<12}{'partidas':>9}{'dragones':>10}{'larvas':>8}{'heraldo':>9}{'barón':>7}{'torres':>8}{'placas':>8}")
    for res in ("victoria", "derrota"):
        v = t[res]
        print(f"{res:<12}{v['partidas']:>9}" + "".join(
            f"{'' if v[c] is None else f'{v[c]:+}':>{w}}"
            for c, w in (("dragones", 10), ("larvas", 8), ("heraldo", 9), ("baron", 7), ("torres", 8), ("placas", 8))))
    for obj, nombre in (("primer_dragon", "Primer dragón"), ("primer_baron", "Primer Barón")):
        n_nos, g_nos = t[obj]["nosotros"]
        n_ell, g_ell = t[obj]["ellos"]
        print(f"{nombre}: tu equipo en {n_nos} partidas (ganaste {g_nos}); el enemigo en {n_ell} (ganaste {g_ell}).")
    return 0


def _jungla_ultima(a) -> int:
    from . import jungla
    ultima = next(_partidas_en_cache(a, solo_ultima=True), None)
    if ultima is None:
        print("La partida más reciente del registro no tiene timeline en data/raw/riot/.")
        return 1
    f, partida_, timeline_, yo = ultima
    print(f"Última partida: {f['match_id']} ({f['fecha']}, {f['resultado']}, {f['kda']}, {f['duracion_min']} min)")
    lista = jungla.muertes(partida_, timeline_, yo)
    if not lista:
        print("No moriste en esta partida.")
        return 0
    nombres = {"DRAGON": "dragón", "BARON_NASHOR": "Barón"}
    print(f"{'minuto':>7}  {'zona':<16}{'te mató':<20}cara")
    for m in lista:
        cara = f"sí ({nombres.get(m['cara'], m['cara'])} enemigo)" if m["cara"] else ""
        print(f"{m['minuto']:>7}  {m['zona']:<16}{m['asesino']:<20}{cara}")
    print("\n'cara' = en los 90 s previos a un dragón o Barón que tomó el enemigo. "
          f"'{jungla.SIN_CAMPEON}' = torre, súbditos o monstruo.")
    return 0


def cmd_jungla(a) -> int:
    from . import jungla
    if a.ultima:
        return _jungla_ultima(a)
    filas = []
    for f, partida_, timeline_, yo in _partidas_en_cache(a):
        try:
            dur = float(f["duracion_min"])
        except ValueError:
            dur = None
        r = jungla.analizar(partida_, timeline_, yo, dur)
        r["fecha"] = f["fecha"]
        filas.append(r)
    if not filas:
        print("No hay partidas importadas con timeline en data/raw/riot/.")
        return 1
    filas.sort(key=lambda r: (r["fecha"], r["match_id"]))

    def v(x):
        return "" if x is None else x

    print(f"{'fecha':<11}{'resultado':<10}{'visión/min':>11}{'balizas':>8}{'destruidos':>11}"
          f"{'cent. antes obj.':>17}{'muertes':>8}{'caras':>6}  dónde moriste")
    for r in filas:
        donde = ", ".join(f"{z} {n}" for z, n in r["donde"].items() if n)
        cent = f"{r['centinelas_antes']}/{r['objetivos']} obj."
        print(f"{r['fecha']:<11}{r['resultado']:<10}{v(r['vision_min'])!s:>11}{v(r['balizas'])!s:>8}"
              f"{v(r['destruidos'])!s:>11}{cent:>17}{r['muertes']:>8}{r['muertes_caras']:>6}  {donde}")

    t = jungla.totales(filas)
    print("\nVictorias contra derrotas (promedio por partida):")
    print(f"{'':<12}{'partidas':>9}{'visión/min':>11}{'balizas':>8}{'destruidos':>11}"
          f"{'cent./objetivo':>15}{'muertes':>8}{'caras':>7}")
    for res in ("victoria", "derrota"):
        x = t[res]
        print(f"{res:<12}{x['partidas']:>9}{v(x['vision_min'])!s:>11}{v(x['balizas'])!s:>8}{v(x['destruidos'])!s:>11}"
              f"{v(x['centinelas_por_objetivo'])!s:>15}{v(x['muertes'])!s:>8}{v(x['muertes_caras'])!s:>7}")
    print("\nDónde moriste (total):")
    for res in ("victoria", "derrota"):
        d = t[res]["donde"]
        tot = sum(d.values()) or 1
        print(f"  {res}: " + ", ".join(f"{z} {n} ({round(100 * n / tot)}%)" for z, n in d.items()))
    print("\n'cent. antes obj.' = centinelas tuyos en los 90 s previos a cada dragón o Barón (de cualquier equipo).")
    print("'caras' = tus muertes en los 90 s previos a un dragón o Barón que tomó el enemigo.")
    return 0


def cmd_momentos(a) -> int:
    from . import momentos
    filas = [momentos.analizar(p_, t_, yo) for _, p_, t_, yo in _partidas_en_cache(a)]
    if not filas:
        print("No hay partidas importadas con timeline en data/raw/riot/.")
        return 1
    t = momentos.totales(filas)

    def v(x):
        return "-" if x is None else x

    print("Por tramo de 5 minutos, promedio por partida (victorias | derrotas):\n")
    print(f"{'tramo':<8}{'partidas':>12}{'tus muertes':>15}{'en tu jungla':>16}{'participas':>15}"
          f"{'oro ganado en el tramo':>26}{'oro al final':>18}")
    for ini, fin in momentos.TRAMOS:
        x = t[f"{ini}-{fin}"]
        g, d = x["victoria"], x["derrota"]
        if not g["partidas"] and not d["partidas"]:
            continue
        def par(campo):
            a_, b_ = g[campo], d[campo]
            if campo in ("cambio_oro", "oro_fin"):
                a_, b_ = (None if x is None else round(x) for x in (a_, b_))
            return f"{v(a_)!s:>6} | {v(b_)!s:<6}"
        print(f"{f'{ini}-{fin}':<8}{g['partidas']:>5} | {d['partidas']:<4}{par('muertes'):>15}{par('en_mi_jungla'):>16}"
              f"{par('participaciones'):>15}{par('cambio_oro'):>26}{par('oro_fin'):>18}")
    print("\nTramo en el que cada derrota quedó atrás en oro para ya no recuperarse:")
    print("  " + ", ".join(f"{k}: {n}" for k, n in t["volteo_derrotas"].items() if n)
          + f"; nunca atrás hasta el minuto 35: {t['derrotas_sin_volteo']}")
    print("\n'oro ganado en el tramo' = cuánto creció (o bajó) la diferencia de oro de tu equipo en esos 5 minutos.")
    print("'participas' = bajas de tu equipo en las que mataste o asististe.")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="kindred_lab")
    sub = p.add_subparsers(dest="grupo", required=True)
    r = sub.add_parser("runas", help="Datos de runas").add_subparsers(dest="cmd", required=True)

    s = r.add_parser("actualizar", help="Descarga el parche y lo compara con el anterior")
    s.add_argument("--version", help="Por defecto, la última publicada")
    s.add_argument("--idioma", default=config.IDIOMA)
    s.add_argument("--archivo", help="runesReforged.json local (sin red)")
    s.set_defaults(fn=cmd_actualizar)

    s = r.add_parser("comparar", help="Reporte de cambios entre dos parches guardados")
    s.add_argument("desde"); s.add_argument("hasta")
    s.set_defaults(fn=cmd_comparar)

    s = r.add_parser("buscar", help="Busca runas por nombre (sin importar acentos)")
    s.add_argument("texto"); s.add_argument("--version", default="latest")
    s.set_defaults(fn=cmd_buscar)

    s = r.add_parser("arbol", help="Muestra un árbol completo por filas")
    s.add_argument("arbol", help="Precision, Domination, Resolve, Sorcery, Inspiration (o su nombre en español)")
    s.add_argument("--version", default="latest")
    s.set_defaults(fn=cmd_arbol)

    s = r.add_parser("versiones", help="Parches que ya tienes guardados")
    s.set_defaults(fn=cmd_versiones)

    g = sub.add_parser("reglas", help="Reglas de runas de Kindred").add_subparsers(dest="cmd", required=True)
    s = g.add_parser("validar", help="Comprueba que las runas de las reglas existan en el parche")
    s.add_argument("--version", default="latest")
    s.set_defaults(fn=cmd_validar_reglas)

    g = sub.add_parser("partidas", help="Importar y resumir tus partidas").add_subparsers(dest="cmd", required=True)
    s = g.add_parser("importar", help="Baja tus últimas partidas de la API de Riot y las añade al registro")
    s.add_argument("--riot-id", help="Nombre#TAG (o variable RIOT_ID)")
    s.add_argument("--cantidad", type=int, default=10)
    s.add_argument("--cola", type=int, default=config.COLA_SOLO_DUO)
    s.add_argument("--campeon", default=config.CAMPEON, help="Solo este campeón ('' para todos)")
    s.add_argument("--region", default=config.RIOT_REGION)
    s.set_defaults(fn=cmd_importar)

    s = g.add_parser("calibrar", help="Aprende qué campo de la API es cada valor de runa, con una captura")
    s.add_argument("match_id"); s.add_argument("valores", nargs="+", help="Clave=número visto en pantalla")
    s.add_argument("--riot-id"); s.add_argument("--region", default=config.RIOT_REGION)
    s.set_defaults(fn=cmd_calibrar)

    s = g.add_parser("anotar", help="Llena alcance_temprano y notas sin abrir el CSV")
    s.add_argument("match_id", help="LA1_... o 'ultima' para la partida más reciente")
    s.add_argument("--alcance", choices=["si", "no"], help="Lo que decidiste en la selección: ¿alguien me puede alcanzar sin fallar "
                        "en los primeros 5 minutos? (no lo que pasó)")
    s.add_argument("--nota", help="Texto que se añade a notas")
    x = s.add_mutually_exclusive_group()
    x.add_argument("--excluir", action="store_true", help="El resumen ignora esta partida")
    x.add_argument("--incluir", action="store_true", help="Quita la marca de excluir")
    s.set_defaults(fn=cmd_anotar)

    s = g.add_parser("resumen", help="Partidas, victorias y valor medio por runa")
    s.add_argument("--minimo", type=int, default=1)
    s.add_argument("--duracion-minima", type=float, default=20,
                   help="Ignora partidas más cortas (rendiciones tempranas). 0 = no ignorar ninguna")
    s.add_argument("--registro", help="Otro CSV en vez de registro/partidas.csv "
                                      "(p. ej. ejemplos/partidas_ejemplo.csv, sin clave de Riot)")
    s.set_defaults(fn=cmd_resumen)

    s = sub.add_parser("jungla", help="Extra: visión, centinelas antes de objetivos, muertes caras y dónde mueres")
    s.add_argument("--ultima", action="store_true",
                   help="Solo la última partida: cada muerte con minuto, zona, quién te mató y si fue cara")
    s.add_argument("--todas", action="store_true", help="Incluye las partidas marcadas con 'excluir'")
    s.add_argument("--riot-id"); s.add_argument("--region", default=config.RIOT_REGION)
    s.set_defaults(fn=cmd_jungla)

    s = sub.add_parser("momentos", help="Extra: en qué tramo de 5 minutos se tuerce la partida")
    s.add_argument("--todas", action="store_true", help="Incluye las partidas marcadas con 'excluir'")
    s.add_argument("--riot-id"); s.add_argument("--region", default=config.RIOT_REGION)
    s.set_defaults(fn=cmd_momentos)

    s = sub.add_parser("objetivos", help="Extra: dragones, larvas, heraldo, Barón, torres y placas por partida")
    s.add_argument("--minuto", type=int, default=None, help="Contar solo hasta este minuto (por defecto, toda la partida)")
    s.add_argument("--todas", action="store_true", help="Incluye las partidas marcadas con 'excluir'")
    s.add_argument("--riot-id"); s.add_argument("--region", default=config.RIOT_REGION)
    s.set_defaults(fn=cmd_objetivos)

    s = sub.add_parser("temprano", help="Extra: muertes y oro de tu equipo en los primeros minutos")
    s.add_argument("--minuto", type=int, default=10)
    s.add_argument("--todas", action="store_true", help="Incluye las partidas marcadas con 'excluir'")
    s.add_argument("--riot-id"); s.add_argument("--region", default=config.RIOT_REGION)
    s.set_defaults(fn=cmd_temprano)

    a = p.parse_args(argv)
    try:
        return a.fn(a)
    except (FileNotFoundError, KeyError, ValueError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
