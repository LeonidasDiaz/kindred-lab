"""Objetos: estadísticas de Data Dragon más una capa manual de mecánicas.

- reglas/objetos_mecanicas.json es la capa manual: mecánicas, parche en que se verificaron y la descripción
  oficial con la que se verificaron. No se regenera.
- metadata y stats_base salen de Data Dragon. Su campo "stats" solo trae 12 tipos (sin aceleración, letalidad,
  tenacidad...), así que las estadísticas se leen del bloque <stats> de la descripción.
- Los valores detallados salen de los archivos del juego (Community Dragon). Sus nombres no siguen un formato común:
  se guardan tal cual, solo para avisar si cambia un número. No llenan las mecánicas.
"""
import html
import json
import re
from pathlib import Path

from . import cdragon, config, ddragon

ARCHIVO_DDRAGON = "item.json"

# Nombres repetidos -> el nombre único (la forma más usada de cada grupo)
ALIAS_STATS = {
    "AD": "AD_plano",
    "Armadura": "Armadura_plana",
    "Vida": "Vida_maxima_plana",
    "mana_maximo_plano": "Mana_maximo_plano",
    "Robo_Vida": "Robo_Vida_Porcentual",
    "Omnivampirismo_porcentual": "Omnivampirismo_Porcentual",
    "Regen_Vida_Basica_Porcentual": "Regen_Vida_Básica_Porcentual",
    "Vel_Movimiento_Plana": "Vel_Movimiento_plana",
    "Vel_Ataque_Porcentual": "Vel_Ataque",
    "Prob_Critico_Porcentual": "Prob_Critico",
    "Aceleracion_Habilidad_Definitiva": "Aceleracion_Habilidad_Definitiva_plana",
}

# (etiqueta en el bloque <stats>, ¿es porcentaje?) -> nombre de la estadística. Los porcentajes se guardan como fracción.
ETIQUETAS = {
    ("Vida", False): "Vida_maxima_plana",
    ("Maná", False): "Mana_maximo_plano",
    ("Daño de Ataque", False): "AD_plano",
    ("Poder de Habilidad", False): "AP_plano",
    ("Armadura", False): "Armadura_plana",
    ("Resistencia Mágica", False): "Resist_Magica_plana",
    ("Aceleración de Habilidad", False): "Aceleracion_de_habilidad_plana",
    ("Letalidad", False): "Letalidad_plana",
    ("Penetración de Magia", False): "Penetracion_Magica_Plana",
    ("Penetración de Magia", True): "Penetracion_Magica_Porcentual",
    ("Penetración de Armadura", True): "Penetracion_Fisica_Porcentual",
    ("Velocidad de Ataque", True): "Vel_Ataque",
    ("Velocidad de Movimiento", False): "Vel_Movimiento_plana",
    ("Velocidad de Movimiento", True): "Vel_Movimiento_Porcentual",
    ("Probabilidad de Golpe Crítico", True): "Prob_Critico",
    ("Daño de Golpe Crítico", True): "Daño_Crit_Porcentual",
    ("Regen. de Vida Básica", True): "Regen_Vida_Básica_Porcentual",
    ("Regen. de Maná Básica", True): "Regen_Mana_Básica_Porcentual",
    ("Robo de Vida", True): "Robo_Vida_Porcentual",
    ("Omnivampirismo", True): "Omnivampirismo_Porcentual",
    ("Tenacidad", True): "Tenacidad_Porcentual",
    ("poder de curaciones y escudos", True): "Poder_Curaciones_Escudos_Porcentual",
    ("oro cada 10 seg", False): "Generacion_Oro_Plana_10s",
    ("fuerza adaptable", False): "Fuerza_Adaptable_plana",
}

_LINEA_STAT = re.compile(r"<attention>\s*([\d.]+)(%?)\s*</attention>\s*(?:de\s+)?(.+)")


# ---------- lectura de Data Dragon ----------

def texto_oficial(descripcion: str) -> str:
    """Descripción de Data Dragon sin etiquetas: es lo que se compara para avisar de cambios."""
    sin_etiquetas = re.sub(r"<[^>]+>", " ", html.unescape(descripcion or ""))
    return re.sub(r"\s+", " ", sin_etiquetas).strip()


def stats_desde_descripcion(descripcion: str) -> dict:
    """Estadísticas del bloque <stats>. Una línea o etiqueta desconocida es un error, no se ignora."""
    bloque = re.search(r"<stats>(.*?)</stats>", descripcion or "", re.S)
    if not bloque:
        return {}
    stats = {}
    for linea in re.split(r"<br\s*/?>", bloque.group(1)):
        linea = linea.strip()
        if not linea:
            continue
        m = _LINEA_STAT.fullmatch(linea)
        if not m:
            raise ValueError(f"Línea de estadística que no se entiende: {linea!r}")
        numero, pct, etiqueta = float(m.group(1)), bool(m.group(2)), m.group(3).strip()
        clave = ETIQUETAS.get((etiqueta, pct))
        if clave is None:
            raise ValueError(f"Etiqueta de estadística desconocida: {etiqueta!r} (porcentaje: {pct})")
        valor = round(numero / 100, 4) if pct else numero
        stats[clave] = int(valor) if float(valor).is_integer() else valor
    return stats


def tiene_descripcion(item: dict | None) -> bool:
    """Sin descripción (p. ej. Mapamundi) Data Dragon no dice nada: no significa que no tenga estadísticas."""
    return bool(item and (item.get("description") or "").strip())


def es_comprable(item: dict) -> bool:
    """Se compra en la Grieta del Invocador."""
    return bool(item.get("maps", {}).get("11") and item.get("gold", {}).get("purchasable")
                and not item.get("hideFromAll"))


# ---------- capa manual ----------

def unificar_nombres(nodo):
    """Aplica ALIAS_STATS a claves y valores exactos, a cualquier profundidad. No toca el texto libre."""
    if isinstance(nodo, dict):
        return {ALIAS_STATS.get(k, k): unificar_nombres(v) for k, v in nodo.items()}
    if isinstance(nodo, list):
        return [unificar_nombres(x) for x in nodo]
    if isinstance(nodo, str):
        return ALIAS_STATS.get(nodo, nodo)
    return nodo


def cargar_capa(ruta: Path | None = None) -> dict:
    ruta = ruta or config.OBJETOS_MECANICAS
    if not ruta.exists():
        raise FileNotFoundError(f"No existe {ruta}. Ejecuta primero: python -m kindred_lab objetos migrar")
    return json.loads(ruta.read_text(encoding="utf-8"))


def guardar_capa(capa: dict, ruta: Path | None = None) -> Path:
    ruta = ruta or config.OBJETOS_MECANICAS
    ruta.write_text(json.dumps(capa, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


# ---------- migración del archivo manual ----------

def migrar(manual: dict, dd_items: dict, version: str) -> tuple[dict, dict]:
    """Del archivo manual (metadata, stats_base, mecanicas) a la capa manual más un informe.

    `dd_items` es el "data" del item.json del mismo parche. Data Dragon manda en las estadísticas.
    """
    capa = {"descripcion": "Capa manual de objetos: mecánicas verificadas a mano. metadata y stats_base salen de "
                           "Data Dragon. 'parche_verificado' solo cambia con 'objetos verificar'.",
            "objetos": {}}
    informe = {"version": version, "total": 0, "con_mecanicas": 0, "renombres": {}, "discrepancias": [],
               "descripciones_manuales": [], "sin_data_dragon": []}

    def contar_alias(nodo):
        if isinstance(nodo, dict):
            for k, v in nodo.items():
                if k in ALIAS_STATS:
                    informe["renombres"][k] = informe["renombres"].get(k, 0) + 1
                contar_alias(v)
        elif isinstance(nodo, list):
            for x in nodo:
                contar_alias(x)
        elif isinstance(nodo, str) and nodo in ALIAS_STATS:
            informe["renombres"][nodo] = informe["renombres"].get(nodo, 0) + 1

    for id_, obj in manual["objetos"].items():
        meta = obj["metadata"]
        stats_manual = dict(obj["stats_base"])
        nota = stats_manual.pop("nota", None)
        contar_alias(stats_manual)
        contar_alias(obj["mecanicas"])
        stats_manual = unificar_nombres(stats_manual)

        extra = {k: v for k, v in meta.items() if k not in ("nombre", "precio", "descripcion_legible")}
        if "restricciones_tienda" in obj:
            extra["restricciones_tienda"] = obj["restricciones_tienda"]
        if nota:
            extra["nota_stats"] = nota

        entrada = {"nombre": meta["nombre"], "parche_verificado": version}
        item = dd_items.get(id_)
        if not tiene_descripcion(item):
            informe["sin_data_dragon"].append({"id": id_, "nombre": meta["nombre"]})
        else:
            oficial = texto_oficial(item["description"])
            entrada["descripcion_verificada"] = oficial
            if meta["descripcion_legible"] != oficial:
                entrada["descripcion_manual"] = meta["descripcion_legible"]
                informe["descripciones_manuales"].append({"id": id_, "nombre": meta["nombre"]})
            stats_dd = stats_desde_descripcion(item["description"])
            diferentes = {k: {"manual": stats_manual.get(k), "data_dragon": stats_dd.get(k)}
                          for k in sorted(set(stats_manual) | set(stats_dd)) if stats_manual.get(k) != stats_dd.get(k)}
            if diferentes:
                informe["discrepancias"].append({"id": id_, "nombre": meta["nombre"], "stats": diferentes})
        if extra:
            entrada["metadata_manual"] = extra
        entrada["mecanicas"] = unificar_nombres(obj["mecanicas"])

        capa["objetos"][id_] = entrada
        informe["total"] += 1
        informe["con_mecanicas"] += bool(obj["mecanicas"])
    return capa, informe


def informe_markdown(informe: dict) -> str:
    def v(x):
        return "–" if x is None else x

    lineas = [f"# Migración del archivo manual de objetos (parche {informe['version']})", "",
              "De `referencia/objetos_16.15.1_manual.json` (original sin cambios) a `reglas/objetos_mecanicas.json`.", "",
              f"- Objetos: {informe['total']}, {informe['con_mecanicas']} con mecánicas.",
              f"- Descripciones editadas a mano, conservadas como `descripcion_manual`: "
              f"{len(informe['descripciones_manuales'])}.",
              "- Todas las mecánicas quedan con `parche_verificado` = el del archivo manual.", "",
              f"## Objetos que no coinciden con Data Dragon {informe['version']} ({len(informe['discrepancias'])})", "",
              "Manda Data Dragon: el valor del archivo manual se queda solo en `referencia/`.", "",
              "| id | Objeto | Estadística | Manual | Data Dragon |", "|---|---|---|---|---|"]
    for d in informe["discrepancias"]:
        for stat, par in d["stats"].items():
            lineas.append(f"| {d['id']} | {d['nombre']} | {stat} | {v(par['manual'])} | {v(par['data_dragon'])} |")
    lineas += ["", "## Nombres unificados", "", "| Antes | Ahora | Usos |", "|---|---|---|"]
    for viejo, usos in sorted(informe["renombres"].items()):
        lineas.append(f"| `{viejo}` | `{ALIAS_STATS[viejo]}` | {usos} |")
    if informe["sin_data_dragon"]:
        lineas += ["", f"## Sin descripción en Data Dragon {informe['version']}", "",
                   "Data Dragon no dice nada de estos objetos: se conserva el valor manual de `referencia/`.", ""]
        lineas += [f"- {x['id']} {x['nombre']}" for x in informe["sin_data_dragon"]]
    return "\n".join(lineas) + "\n"


# ---------- valores de los archivos del juego ----------

# Campos numéricos que describen cómo se muestra un cálculo, no un valor del objeto
_CAMPOS_SIN_VALOR = {"__type", "DamageType", "epicness", "mPrecision", "mExpandedTooltipCalculationDisplay",
                     "mSimpleTooltipCalculationDisplay"}


def _numero(x: float):
    redondeado = round(x, 4)         # los archivos guardan 0.30000001192...
    return int(redondeado) if float(redondeado).is_integer() else redondeado


def _aplanar(nodo, prefijo: str, salida: dict, sin_ceros: bool = False) -> None:
    """Solo números: {"calc.Daño.0.mNumber": 45}. Las claves son genéricas, sin mapa por objeto.

    Lista negra y no blanca: un campo numérico nuevo de Riot debe avisar, no perderse en silencio.
    """
    if isinstance(nodo, bool):
        return
    if isinstance(nodo, (int, float)):
        if nodo or not sin_ceros:
            salida[prefijo] = _numero(nodo)
    elif isinstance(nodo, dict):
        for k, v in nodo.items():
            # Un número bajo una clave {hash} es un campo sin nombre: al recibirlo daría un falso aviso
            if k not in _CAMPOS_SIN_VALOR and not (k.startswith("{") and isinstance(v, (int, float))):
                _aplanar(v, f"{prefijo}.{k}", salida, sin_ceros)
    elif isinstance(nodo, list):
        if len(nodo) > 1 and all(isinstance(v, (int, float)) and v == nodo[0] for v in nodo):
            return _aplanar(nodo[0], prefijo, salida, sin_ceros)       # los 7 niveles valen lo mismo
        for i, v in enumerate(nodo):
            _aplanar(v, f"{prefijo}.{i}", salida, sin_ceros)


def indice_hechizos(juego: dict) -> dict[str, list[str]]:
    """id de objeto -> sus entradas 'Items/<id>/Spells/...'. Los efectos visuales se quedan fuera."""
    indice: dict[str, list[str]] = {}
    for clave, valor in juego.items():
        partes = clave.split("/")
        if len(partes) > 2 and partes[0] == "Items" and valor.get("__type") == "SpellObject":
            indice.setdefault(partes[1], []).append(clave)
    return indice


def valores_juego(juego: dict, id_: str, hechizos: dict[str, list[str]]) -> dict | None:
    """Valores detallados de un objeto en items.cdtb.bin.json. None si el archivo no lo trae.

    Solo la entrada de ese id (las variantes de Arena y otros modos tienen otro id) y su configuración
    normal: DataValuesModeOverride, que cambia valores en ARAM y otros modos, se ignora.
    """
    entrada = juego.get(f"Items/{id_}")
    if entrada is None:
        return None
    salida = {}
    for v in entrada.get("mDataValues", []):
        if "mName" in v:
            salida[f"valor.{v['mName']}"] = _numero(v.get("mValue", 0))
    calculos = {}
    _aplanar(entrada.get("mItemCalculations", {}), "calc", calculos)
    salida.update({k.replace(".mFormulaParts.", "."): v for k, v in calculos.items()})
    _aplanar(entrada.get("mEffectAmount", []), "efecto", salida, sin_ceros=True)
    for clave in hechizos.get(id_, []):
        hechizo = juego[clave].get("mSpell", {})
        nombre = clave.rsplit("/", 1)[1]
        if nombre[0].isdigit() and not nombre.startswith(id_):
            continue                       # hechizo de una variante colgado de este id (p. ej. 223152Active, de Arena)
        _aplanar(hechizo.get("cooldownTime", []), f"hechizo.{nombre}.enfriamiento", salida, sin_ceros=True)
        _aplanar(hechizo.get("mEffectAmount", []), f"hechizo.{nombre}.efecto", salida, sin_ceros=True)
    return salida


def diferencias_valores(antes: dict, ahora: dict) -> dict:
    return {k: {"antes": antes.get(k), "ahora": ahora.get(k)}
            for k in sorted(set(antes) | set(ahora)) if antes.get(k) != ahora.get(k)}


# ---------- objetos por parche ----------

def generar(dd_items: dict, capa: dict, referencia: dict, version: str, idioma: str = config.IDIOMA,
            juego: dict | None = None) -> dict:
    """Une Data Dragon, los archivos del juego y la capa manual: los comprables en la Grieta más todo lo que
    tenga capa manual.

    "disponible" se calcula en cada parche. "revisar" avisa de que la descripción oficial ya no es la verificada y
    "valores_cambiados", de que un número de los archivos del juego ya no es el verificado. Que no avisen no prueba
    que la mecánica siga vigente: la lógica de cada pasiva no está en esos archivos.
    """
    manuales = capa["objetos"]
    ids = {i for i, item in dd_items.items() if es_comprable(item)} | set(manuales)
    hechizos = indice_hechizos(juego) if juego else {}
    salida = {}
    for id_ in sorted(ids, key=lambda x: (len(x), x)):
        item, c = dd_items.get(id_), manuales.get(id_, {})
        ref = referencia.get("objetos", {}).get(id_)
        ref_meta = ref["metadata"] if ref else {}
        if tiene_descripcion(item):
            oficial = texto_oficial(item["description"])
            stats = stats_desde_descripcion(item["description"])
        elif ref:                  # Data Dragon no dice nada: se conserva lo último que se supo a mano
            oficial = ref_meta["descripcion_legible"]
            stats = {k: v for k, v in unificar_nombres(ref["stats_base"]).items() if k != "nota"}
        else:
            oficial, stats = "", {}
        nombre = (item or {}).get("name", "").strip() or c.get("nombre") or ref_meta.get("nombre", "")
        metadata = {"nombre": nombre, "precio": item["gold"]["total"] if item else ref_meta.get("precio"),
                    "descripcion_legible": oficial, "disponible": bool(item and es_comprable(item)),
                    "final": bool(item and not item.get("into")),        # no se mejora en otro objeto
                    "botas": "Boots" in (item or {}).get("tags", []),
                    "componentes": (item or {}).get("from", [])}         # ids directos; pueden repetirse
        if "descripcion_manual" in c:
            metadata["descripcion_manual"] = c["descripcion_manual"]
        metadata.update(c.get("metadata_manual", {}))
        mecanicas = c.get("mecanicas", {})
        valores = valores_juego(juego, id_, hechizos) if juego else None
        base = c.get("valores_verificados")
        salida[id_] = {"metadata": metadata, "stats_base": stats, "mecanicas": mecanicas,
                       "parche_verificado": c.get("parche_verificado"),
                       "revisar": bool(mecanicas and tiene_descripcion(item)
                                       and oficial != c.get("descripcion_verificada")),
                       "valores_juego": valores,
                       "valores_cambiados": (diferencias_valores(base, valores)
                                             if mecanicas and base is not None and valores is not None else {})}
    return {"version": version, "idioma": idioma, "objetos": salida}


def ruta_procesada(version: str, out_dir: Path | None = None) -> Path:
    return (out_dir or config.OBJETOS_DIR) / f"objetos_{version}.json"


def versiones_procesadas(out_dir: Path | None = None) -> list[str]:
    out = out_dir or config.OBJETOS_DIR
    if not out.exists():
        return []
    vs = [p.stem.removeprefix("objetos_") for p in out.glob("objetos_*.json") if p.stem != "objetos_latest"]
    return sorted(vs, key=ddragon.clave_version)


def guardar(datos: dict, out_dir: Path | None = None) -> Path:
    out = out_dir or config.OBJETOS_DIR
    out.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(datos, ensure_ascii=False, indent=2)
    destino = ruta_procesada(datos["version"], out)
    destino.write_text(texto, encoding="utf-8")
    # objetos_latest.json solo apunta a la versión más nueva guardada, aunque generes una vieja.
    if datos["version"] == versiones_procesadas(out)[-1]:
        (out / "objetos_latest.json").write_text(texto, encoding="utf-8")
    return destino


def cargar(version: str = "latest", out_dir: Path | None = None) -> dict:
    out = out_dir or config.OBJETOS_DIR
    ruta = out / ("objetos_latest.json" if version == "latest" else f"objetos_{version}.json")
    if not ruta.exists():
        raise FileNotFoundError(f"No existe {ruta}. Ejecuta primero: python -m kindred_lab objetos actualizar")
    return json.loads(ruta.read_text(encoding="utf-8"))


# ---------- comparación y avisos ----------

def comparar(anterior: dict, nuevo: dict) -> dict:
    a, n = anterior["objetos"], nuevo["objetos"]
    comunes = sorted(set(a) & set(n), key=lambda x: (len(x), x))
    stats = {}
    for i in comunes:
        cambios = {k: {"antes": a[i]["stats_base"].get(k), "ahora": n[i]["stats_base"].get(k)}
                   for k in sorted(set(a[i]["stats_base"]) | set(n[i]["stats_base"]))
                   if a[i]["stats_base"].get(k) != n[i]["stats_base"].get(k)}
        if cambios:
            stats[i] = cambios
    return {"desde": anterior["version"], "hasta": nuevo["version"],
            "nuevos": sorted(set(n) - set(a), key=lambda x: (len(x), x)),
            "quitados": sorted(set(a) - set(n), key=lambda x: (len(x), x)),
            "stats": stats,
            "valores": {i: d for i in comunes
                        if a[i].get("valores_juego") is not None and n[i].get("valores_juego") is not None
                        and (d := diferencias_valores(a[i]["valores_juego"], n[i]["valores_juego"]))},
            "precio": {i: {"antes": a[i]["metadata"]["precio"], "ahora": n[i]["metadata"]["precio"]}
                       for i in comunes if a[i]["metadata"]["precio"] != n[i]["metadata"]["precio"]},
            "disponible": {i: n[i]["metadata"]["disponible"] for i in comunes
                           if a[i]["metadata"]["disponible"] != n[i]["metadata"]["disponible"]}}


def por_revisar(datos: dict, capa: dict) -> list[dict]:
    """Objetos con mecánicas cuya descripción oficial cambió desde que se verificaron."""
    return [{"id": i, "nombre": o["metadata"]["nombre"], "parche_verificado": o["parche_verificado"],
             "verificada": capa["objetos"].get(i, {}).get("descripcion_verificada"),
             "actual": o["metadata"]["descripcion_legible"]}
            for i, o in datos["objetos"].items() if o["revisar"]]


def por_revisar_valores(datos: dict) -> list[dict]:
    """Objetos con mecánicas con algún valor del juego distinto del verificado, aunque la descripción siga igual."""
    return [{"id": i, "nombre": o["metadata"]["nombre"], "parche_verificado": o["parche_verificado"],
             "descripcion_igual": not o["revisar"], "cambios": o["valores_cambiados"]}
            for i, o in datos["objetos"].items() if o["valores_cambiados"]]


def detalle_cambios(cambios: dict) -> str:
    return ", ".join(f"{k}: {v['antes']} -> {v['ahora']}" for k, v in cambios.items())


def reporte_markdown(c: dict, datos: dict, avisos: list[dict], avisos_valores: list[dict] | None = None) -> str:
    objs = datos["objetos"]
    avisos_valores = avisos_valores or []

    def nombre(i):
        return f"{objs[i]['metadata']['nombre']} ({i})" if i in objs else i

    lineas = [f"# Objetos: cambios de {c['desde']} a {c['hasta']}", "",
              f"## Mecánicas por revisar ({len(avisos)})", "",
              "La descripción oficial ya no es la que se verificó. Después de revisar: `objetos verificar <id>`.", ""]
    for a in avisos:
        lineas += [f"### {a['nombre']} ({a['id']}), verificada en {a['parche_verificado']}", "",
                   f"- Verificada: {a['verificada']}", f"- Actual: {a['actual']}", ""]
    lineas += [f"## Valores del juego por revisar ({len(avisos_valores)})", "",
               "Objetos con mecánicas con algún valor distinto del verificado. Después de revisar: "
               "`objetos verificar <id>`.", ""]
    for a in avisos_valores:
        igual = "; descripción oficial igual" if a["descripcion_igual"] else ""
        lineas.append(f"- {a['nombre']} ({a['id']}), verificada en {a['parche_verificado']}{igual}: "
                      f"{detalle_cambios(a['cambios'])}")
    lineas += ["", f"## Estadísticas ({len(c['stats'])})", ""]
    for i, cambios in c["stats"].items():
        lineas.append(f"- {nombre(i)}: {detalle_cambios(cambios)}")
    lineas += ["", f"## Valores del juego de {c['desde']} a {c['hasta']} ({len(c['valores'])})", ""]
    lineas += [f"- {nombre(i)}: {detalle_cambios(d)}" for i, d in c["valores"].items()]
    lineas += ["", f"## Precio ({len(c['precio'])})", ""]
    lineas += [f"- {nombre(i)}: {v['antes']} -> {v['ahora']}" for i, v in c["precio"].items()]
    lineas += ["", f"## Disponibilidad ({len(c['disponible'])})", ""]
    lineas += [f"- {nombre(i)}: {'ya se compra' if v else 'ya no se compra'}" for i, v in c["disponible"].items()]
    lineas += ["", f"## Objetos nuevos ({len(c['nuevos'])})", ""]
    lineas += [f"- {nombre(i)}" for i in c["nuevos"]]
    lineas += ["", f"## Objetos quitados ({len(c['quitados'])})", ""]
    lineas += [f"- {i}" for i in c["quitados"]]
    return "\n".join(lineas) + "\n"


# ---------- flujo completo ----------

def _referencia(ruta: Path | None = None) -> dict:
    ruta = ruta or config.OBJETOS_REFERENCIA
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}


def actualizar(version: str | None = None, idioma: str = config.IDIOMA, raw_dir: Path | None = None,
               out_dir: Path | None = None, capa_ruta: Path | None = None, referencia_ruta: Path | None = None,
               cargar_juego=None) -> dict:
    """Genera los objetos del parche y los compara con el anterior guardado. No toca la capa manual.

    Si los archivos del juego no se pueden bajar, sigue sin ellos y lo dice en "error_juego".
    """
    version = version or ddragon.ultima_version()
    dd = ddragon.descargar(version, idioma, ARCHIVO_DDRAGON, raw_dir=raw_dir)["data"]
    capa = cargar_capa(capa_ruta)
    juego, error_juego = None, None
    try:
        juego = (cargar_juego or cdragon.descargar_items)(version)
    except OSError as e:
        error_juego = str(e)
    datos = generar(dd, capa, _referencia(referencia_ruta), version, idioma, juego)
    previas = [v for v in versiones_procesadas(out_dir) if ddragon.clave_version(v) < ddragon.clave_version(version)]
    ruta = guardar(datos, out_dir)
    avisos, avisos_valores = por_revisar(datos, capa), por_revisar_valores(datos)
    comparacion, ruta_reporte = None, None
    if previas:
        comparacion = comparar(cargar(previas[-1], out_dir), datos)
        ruta_reporte = (out_dir or config.OBJETOS_DIR) / f"cambios_{previas[-1]}_a_{version}.md"
        ruta_reporte.write_text(reporte_markdown(comparacion, datos, avisos, avisos_valores), encoding="utf-8")
    return {"version": version, "ruta": ruta, "datos": datos, "avisos": avisos, "avisos_valores": avisos_valores,
            "error_juego": error_juego, "comparacion": comparacion, "reporte": ruta_reporte}


def fijar_base_valores(version: str, out_dir: Path | None = None, capa_ruta: Path | None = None) -> int:
    """Una sola vez: da a las mecánicas verificadas en `version` los valores del juego de ese parche como base.

    No sobrescribe: lo que ya tiene base la conserva. Devuelve cuántos objetos recibieron base.
    """
    capa = cargar_capa(capa_ruta)
    objetos = cargar(version, out_dir)["objetos"]
    fijados = 0
    for id_, entrada in capa["objetos"].items():
        valores = objetos.get(id_, {}).get("valores_juego")
        if (entrada["mecanicas"] and entrada.get("parche_verificado") == version
                and "valores_verificados" not in entrada and valores is not None):
            entrada["valores_verificados"] = valores
            fijados += 1
    guardar_capa(capa, capa_ruta)
    return fijados


def verificar(id_: str, version: str = "latest", out_dir: Path | None = None, capa_ruta: Path | None = None) -> dict:
    """Marca una mecánica como revisada: guarda el parche y la descripción oficial de ese parche."""
    capa = cargar_capa(capa_ruta)
    if id_ not in capa["objetos"]:
        raise KeyError(f"El objeto {id_} no está en {config.OBJETOS_MECANICAS.name}.")
    datos = cargar(version, out_dir)
    if id_ not in datos["objetos"]:
        raise KeyError(f"El objeto {id_} no está en los datos del parche {datos['version']}.")
    objeto = datos["objetos"][id_]
    entrada = capa["objetos"][id_]
    entrada["parche_verificado"] = datos["version"]
    entrada["descripcion_verificada"] = objeto["metadata"]["descripcion_legible"]
    if objeto.get("valores_juego") is not None:
        entrada["valores_verificados"] = objeto["valores_juego"]
    guardar_capa(capa, capa_ruta)
    objeto["parche_verificado"], objeto["revisar"], objeto["valores_cambiados"] = datos["version"], False, {}
    guardar(datos, out_dir)
    return {"nombre": entrada["nombre"], "version": datos["version"]}
