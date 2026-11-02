"""Runas: normalización, guardado por parche, comparación y búsqueda.

Formato normalizado (data/processed/runas/runas_<version>.json):
{
  "version": "16.20.1",
  "idioma": "es_MX",
  "arboles": {"Precision": {"id": 8000, "nombre": "Precisión"}, ...},
  "runas": {
    "8005": {"id": 8005, "clave": "PressTheAttack", "nombre": "Estrategia Ofensiva",
             "arbol": "Precision", "fila": 0, "corta": "...", "larga": "..."},
    ...
  }
}
"fila" 0 = piedras angulares; 1-3 = filas menores (en Valor/Dominación la secundaria usa estas).
"""
import json
import re
import unicodedata
from pathlib import Path

from . import config, ddragon

ARCHIVO_DDRAGON = "runesReforged.json"


# ---------- normalización ----------

def limpiar_texto(txt: str | None) -> str:
    """Quita etiquetas HTML de Data Dragon y espacios sobrantes."""
    txt = re.sub(r"<br\s*/?>", " ", txt or "")
    txt = re.sub(r"<[^>]+>", "", txt)
    return re.sub(r"\s+", " ", txt).strip()


def normalizar(crudo: list, version: str, idioma: str) -> dict:
    arboles, runas = {}, {}
    for arbol in crudo:
        arboles[arbol["key"]] = {"id": arbol["id"], "nombre": arbol["name"]}
        for fila, slot in enumerate(arbol["slots"]):
            for r in slot["runes"]:
                runas[str(r["id"])] = {
                    "id": r["id"],
                    "clave": r["key"],
                    "nombre": r["name"],
                    "arbol": arbol["key"],
                    "fila": fila,
                    "corta": limpiar_texto(r.get("shortDesc")),
                    "larga": limpiar_texto(r.get("longDesc")),
                }
    return {"version": version, "idioma": idioma, "arboles": arboles, "runas": runas}


# ---------- disco ----------

def ruta_procesada(version: str, out_dir: Path | None = None) -> Path:
    return (out_dir or config.RUNAS_DIR) / f"runas_{version}.json"


def guardar(datos: dict, out_dir: Path | None = None) -> Path:
    out = out_dir or config.RUNAS_DIR
    out.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(datos, ensure_ascii=False, indent=2)
    destino = ruta_procesada(datos["version"], out)
    destino.write_text(texto, encoding="utf-8")
    # runas_latest.json solo apunta a la versión más nueva guardada, aunque descargues una vieja.
    if datos["version"] == versiones_procesadas(out)[-1]:
        (out / "runas_latest.json").write_text(texto, encoding="utf-8")
    return destino


def cargar(version: str = "latest", out_dir: Path | None = None) -> dict:
    out = out_dir or config.RUNAS_DIR
    ruta = out / ("runas_latest.json" if version == "latest" else f"runas_{version}.json")
    if not ruta.exists():
        raise FileNotFoundError(f"No existe {ruta}. Ejecuta primero: python -m kindred_lab runas actualizar")
    return json.loads(ruta.read_text(encoding="utf-8"))


def versiones_procesadas(out_dir: Path | None = None) -> list[str]:
    out = out_dir or config.RUNAS_DIR
    if not out.exists():
        return []
    vs = [p.stem.removeprefix("runas_") for p in out.glob("runas_*.json") if p.stem != "runas_latest"]
    return sorted(vs, key=ddragon.clave_version)


# ---------- comparación ----------

def comparar(anterior: dict, nuevo: dict) -> dict:
    """Devuelve las runas nuevas, quitadas y cambiadas (con el campo que cambió)."""
    a, n = anterior["runas"], nuevo["runas"]
    cambiadas = []
    for rid in sorted(set(a) & set(n), key=int):
        campos = [k for k in ("nombre", "arbol", "fila", "larga") if a[rid][k] != n[rid][k]]
        if campos:
            cambiadas.append({"id": rid, "campos": campos, "antes": a[rid], "ahora": n[rid]})
    return {
        "desde": anterior["version"],
        "hasta": nuevo["version"],
        "nuevas": [n[r] for r in sorted(set(n) - set(a), key=int)],
        "quitadas": [a[r] for r in sorted(set(a) - set(n), key=int)],
        "cambiadas": cambiadas,
    }


def hay_cambios(c: dict) -> bool:
    return bool(c["nuevas"] or c["quitadas"] or c["cambiadas"])


def reporte_markdown(c: dict, arboles: dict) -> str:
    nombre_arbol = lambda k: arboles.get(k, {}).get("nombre", k)
    lineas = [f"# Cambios de runas: {c['desde']} → {c['hasta']}", ""]
    if not hay_cambios(c):
        return "\n".join(lineas + ["Sin cambios."]) + "\n"
    if c["nuevas"]:
        lineas += ["## Nuevas", ""] + [f"- **{r['nombre']}** ({nombre_arbol(r['arbol'])}, fila {r['fila']}): {r['larga']}" for r in c["nuevas"]] + [""]
    if c["quitadas"]:
        lineas += ["## Quitadas", ""] + [f"- **{r['nombre']}** ({nombre_arbol(r['arbol'])})" for r in c["quitadas"]] + [""]
    if c["cambiadas"]:
        lineas += ["## Cambiadas", ""]
        for x in c["cambiadas"]:
            lineas.append(f"### {x['ahora']['nombre']} ({nombre_arbol(x['ahora']['arbol'])})")
            lineas.append(f"Cambió: {', '.join(x['campos'])}")
            for campo in x["campos"]:
                lineas += [f"- antes ({campo}): {x['antes'][campo]}", f"- ahora ({campo}): {x['ahora'][campo]}"]
            lineas.append("")
    return "\n".join(lineas)


# ---------- búsqueda ----------

def _sin_acentos(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(ch) != "Mn")


def buscar(datos: dict, texto: str) -> list[dict]:
    """Busca por nombre o clave, sin importar mayúsculas ni acentos."""
    q = _sin_acentos(texto)
    return [r for r in datos["runas"].values()
            if q in _sin_acentos(r["nombre"]) or q in _sin_acentos(r["clave"])]


def arbol_por_filas(datos: dict, arbol: str) -> list[list[dict]]:
    """Runas de un árbol agrupadas por fila. 'arbol' acepta clave (Precision) o nombre (Precisión)."""
    q = _sin_acentos(arbol)
    clave = next((k for k, v in datos["arboles"].items()
                  if _sin_acentos(k) == q or _sin_acentos(v["nombre"]) == q), None)
    if clave is None:
        raise KeyError(f"Árbol '{arbol}' no encontrado. Opciones: {', '.join(datos['arboles'])}")
    filas: dict[int, list] = {}
    for r in datos["runas"].values():
        if r["arbol"] == clave:
            filas.setdefault(r["fila"], []).append(r)
    return [sorted(filas[f], key=lambda r: r["id"]) for f in sorted(filas)]


# ---------- flujo completo ----------

def actualizar(version: str | None = None, idioma: str = config.IDIOMA,
               archivo_local: Path | None = None,
               raw_dir: Path | None = None, out_dir: Path | None = None) -> dict:
    """Descarga (o lee) las runas, las guarda normalizadas y las compara con el parche anterior.

    Devuelve {"version", "ruta", "comparacion" (o None), "reporte" (ruta o None)}.
    """
    if archivo_local is not None:
        if not version:
            raise ValueError("Con un archivo local hay que indicar la versión.")
        crudo = json.loads(Path(archivo_local).read_text(encoding="utf-8"))
    else:
        version = version or ddragon.ultima_version()
        crudo = ddragon.descargar(version, idioma, ARCHIVO_DDRAGON, raw_dir=raw_dir)

    nuevo = normalizar(crudo, version, idioma)
    previas = [v for v in versiones_procesadas(out_dir) if ddragon.clave_version(v) < ddragon.clave_version(version)]
    ruta = guardar(nuevo, out_dir)

    comparacion, ruta_reporte = None, None
    if previas:
        anterior = cargar(previas[-1], out_dir)
        comparacion = comparar(anterior, nuevo)
        ruta_reporte = (out_dir or config.RUNAS_DIR) / f"cambios_{anterior['version']}_a_{version}.md"
        ruta_reporte.write_text(reporte_markdown(comparacion, nuevo["arboles"]), encoding="utf-8")
    return {"version": version, "ruta": ruta, "comparacion": comparacion, "reporte": ruta_reporte}
