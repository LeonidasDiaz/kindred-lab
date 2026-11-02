"""Pruebas con una partida SINTÉTICA (inventada, con la forma de match-v5); no usan red."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from kindred_lab import cdragon, partidas, runas

FIX = Path(__file__).parent / "fixtures"


def sel(id_, v1=0, v2=0, v3=0):
    return {"perk": id_, "var1": v1, "var2": v2, "var3": v3}


class TestPartidas(unittest.TestCase):
    def setUp(self):
        crudo = json.loads((FIX / "runesReforged_16.20.1.json").read_text(encoding="utf-8"))
        self.datos = runas.normalizar(crudo, "16.20.1", "es_MX")
        ids = {r["clave"]: r["id"] for r in self.datos["runas"].values()}
        yo = {"puuid": "yo", "participantId": 1, "summoner1Id": 11, "summoner2Id": 6, "teamId": 100, "championName": "Kindred", "win": True,
              "kills": 11, "deaths": 7, "assists": 20, "physicalDamageTaken": 30000, "magicDamageTaken": 10000,
              "perks": {"styles": [
                  {"description": "primaryStyle", "style": 8000, "selections": [
                      sel(ids["PressTheAttack"], 5557, 0, 0), sel(ids["Triumph"], 1532, 620, 0), sel(ids["LegendAlacrity"], 10, 40, 0),
                      sel(ids["LastStand"], 1891, 0, 0)]},
                  {"description": "subStyle", "style": 8400, "selections": [
                      sel(ids["BonePlating"], 778, 0, 0), sel(ids["Unflinching"], 102000, 0, 0)]}]}}
        enem = [{"puuid": f"e{i}", "participantId": 6 + i, "teamId": 200, "championName": n, "win": False,
                 "kills": 0, "deaths": 0, "assists": 0, "perks": {"styles": []}}
                for i, n in enumerate(["Kayn", "Zac", "Lux", "Brand", "Leblanc"])]
        self.partida = {"metadata": {"matchId": "LA1_1"},
                        "info": {"gameVersion": "16.21.1.123", "gameDuration": 1993,
                                 "gameStartTimestamp": 1_792_000_000_000, "participants": [yo] + enem}}
        self.timeline = {"info": {"frames": [{"events": [
            {"type": "CHAMPION_KILL", "victimId": 1, "timestamp": 300_000},
            {"type": "CHAMPION_KILL", "victimId": 1, "timestamp": 700_000},
            {"type": "CHAMPION_KILL", "victimId": 6, "timestamp": 100_000}]}]}}
        self.valores = {"runas": {"LastStand": {"var": "var1", "div": 1},
                                  "Unflinching": {"var": "var1", "div": 1000, "unidad": "s"}}}

    def test_fila(self):
        f = partidas.fila_desde_partida(self.partida, "yo", self.datos, self.valores, self.timeline)
        self.assertEqual((f["resultado"], f["kda"], f["duracion_min"], f["parche"]), ("victoria", "11/7/20", "33.2", "16.21"))
        self.assertEqual(f["enemigos"], "Kayn|Zac|Lux|Brand|Leblanc")
        self.assertEqual((f["piedra_angular"], f["fila_3"], f["secundaria"]), ("PressTheAttack", "LastStand", "Resolve"))
        self.assertEqual((f["secundaria_1"], f["secundaria_2"]), ("BonePlating", "Unflinching"))
        self.assertEqual(f["muertes_antes_min10"], 1)
        self.assertEqual(f["dano_que_me_mata"], "AD")
        self.assertEqual((f["valor_fila_3"], f["valor_secundaria_2"], f["valor_piedra_angular"]), ("1891", "102s", ""))

    def test_secundaria_se_ordena_por_fila(self):
        sec = self.partida["info"]["participants"][0]["perks"]["styles"][1]
        sec["selections"].reverse()                  # elegida al revés: Inquebrantable primero
        f = partidas.fila_desde_partida(self.partida, "yo", self.datos, self.valores, self.timeline)
        self.assertEqual((f["secundaria_1"], f["secundaria_2"]), ("BonePlating", "Unflinching"))
        self.assertEqual(f["valor_secundaria_2"], "102s")

    def test_hechizos(self):
        f = partidas.fila_desde_partida(self.partida, "yo", self.datos, self.valores, self.timeline)
        self.assertEqual(f["hechizos"], "Fantasma+Castigo")
        vieja = dict(f, hechizos="", match_id="LA1_1")
        self.assertEqual(partidas.completar_hechizos([vieja], "yo", lambda mid: self.partida), 1)
        self.assertEqual(vieja["hechizos"], "Fantasma+Castigo")
        r = {(x["campo"], x["runa"]): x for x in partidas.resumen([f])}
        self.assertEqual(r[("hechizos", "Fantasma+Castigo")]["partidas"], 1)
        self.assertIsNone(r[("hechizos", "Fantasma+Castigo")]["valor_medio"])

    def test_calibrar(self):
        r = partidas.calibrar(self.partida, "yo", self.datos,
                              {"PressTheAttack": 5557, "LastStand": 1891, "Unflinching": 102, "Triumph": 9999})
        self.assertEqual(r["PressTheAttack"], {"var": "var1", "div": 1})
        self.assertEqual(r["LastStand"], {"var": "var1", "div": 1})
        self.assertEqual(r["Unflinching"], {"var": "var1", "div": 1000})
        self.assertNotIn("Triumph", r)           # sin valor distinto de 0 que coincida

    def test_agregar_migra_encabezado_y_no_duplica(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "p.csv"
            vieja = [c for c in partidas.COLUMNAS if c != "match_id"]
            with ruta.open("w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh); w.writerow(vieja); w.writerow(["2026-10-18"] + [""] * (len(vieja) - 1))
            f = partidas.fila_desde_partida(self.partida, "yo", self.datos, self.valores, self.timeline)
            self.assertEqual(partidas.agregar([f], ruta), 1)
            self.assertEqual(partidas.agregar([f], ruta), 0)
            filas = partidas.leer_registro(ruta)
            self.assertEqual(len(filas), 2)
            self.assertEqual(filas[0]["fecha"], "2026-10-18")

    def test_resumen(self):
        f = partidas.fila_desde_partida(self.partida, "yo", self.datos, self.valores, self.timeline)
        r = {(x["campo"], x["runa"]): x for x in partidas.resumen([f, dict(f, resultado="derrota")])}
        x = r[("fila_3", "LastStand")]
        self.assertEqual((x["partidas"], x["victorias"], x["valor_medio"]), (2, 1, 1891))

    def test_resumen_ignora_partidas_cortas(self):
        f = partidas.fila_desde_partida(self.partida, "yo", self.datos, self.valores, self.timeline)
        corta = dict(f, duracion_min="15.3", valor_fila_3="200")
        r = {(x["campo"], x["runa"]): x for x in partidas.resumen([f, corta])}
        self.assertEqual(r[("fila_3", "LastStand")]["partidas"], 1)
        r = {(x["campo"], x["runa"]): x for x in partidas.resumen([f, corta], duracion_minima=0)}
        self.assertEqual(r[("fila_3", "LastStand")]["partidas"], 2)


class TestCDragon(unittest.TestCase):
    """El fixture copia el formato de perks.json de Community Dragon (es_mx); no usa red."""

    def setUp(self):
        TestPartidas.setUp(self)
        perks = json.loads((FIX / "cdragon_perks_es_mx.json").read_text(encoding="utf-8"))
        self.estad = cdragon.estadisticas(perks)

    def test_estadisticas(self):
        self.assertEqual(self.estad[8005][0], {"etiqueta": "Total de daño", "vars": ["var1"], "tiempo": False, "porcentaje": False})
        self.assertTrue(self.estad[9104][0]["tiempo"])
        self.assertEqual(self.estad[8008][0]["vars"], ["var1", "var2"])   # solo la primera línea
        self.assertEqual(self.estad[8135][0]["vars"], ["var2"])
        self.assertNotIn(8000, self.estad)

    def test_fila_sin_calibrar(self):
        f = partidas.fila_desde_partida(self.partida, "yo", self.datos, None, self.timeline, self.estad)
        self.assertEqual(f["valor_piedra_angular"], "5557")
        self.assertEqual((f["valor_fila_1"], f["valor_fila_2"], f["valor_fila_3"]), ("1532", "10:40", "1891"))
        self.assertEqual(f["valor_secundaria_1"], "778")
        self.assertIn("Triumph: Total de vida restaurada 1532; Total de oro adicional otorgado 620",
                      f["estadisticas_runas"])

    def test_calibrado_manda_sobre_cdragon(self):
        f = partidas.fila_desde_partida(self.partida, "yo", self.datos, self.valores, self.timeline, self.estad)
        self.assertEqual(f["valor_secundaria_2"], "102s")

    def test_resumen_tiempos(self):
        f = partidas.fila_desde_partida(self.partida, "yo", self.datos, None, self.timeline, self.estad)
        g = dict(f, valor_fila_2="11:20")
        r = {(x["campo"], x["runa"]): x for x in partidas.resumen([f, g])}
        self.assertEqual(r[("fila_2", "LegendAlacrity")]["valor_medio"], "11:00")
        self.assertIsNone(r[("fila_2", "LegendAlacrity")]["por_minuto"])

    def test_porcentaje_sin_por_minuto(self):
        self.assertTrue(self.estad[8429][0]["porcentaje"])
        self.assertEqual(cdragon.formatear({"var1": 54}, self.estad[8429][0]), "54%")
        f = partidas.fila_desde_partida(self.partida, "yo", self.datos, None, self.timeline, self.estad)
        a, b = dict(f, valor_secundaria_1="54%"), dict(f, valor_secundaria_1="62%")
        r = {(x["campo"], x["runa"]): x for x in partidas.resumen([a, b])}
        x = r[("secundaria_1", "BonePlating")]
        self.assertEqual((x["valor_medio"], x["por_minuto"]), ("58%", None))

    def test_anotar_y_excluir(self):
        f = partidas.fila_desde_partida(self.partida, "yo", self.datos, self.valores, self.timeline)
        vieja = dict(f, match_id="LA1_5")
        filas = [vieja, f]                       # f es LA1_1; la más reciente es LA1_5
        r = partidas.anotar(filas, "ultima", alcance="no", nota="Ivern mid robó la jungla", excluir=True)
        self.assertIs(r, vieja)
        self.assertEqual(r["alcance_temprano"], "no")
        self.assertTrue(r["notas"].endswith("Ivern mid robó la jungla; excluir"))
        res = {(x["campo"], x["runa"]): x for x in partidas.resumen(filas)}
        self.assertEqual(res[("fila_3", "LastStand")]["partidas"], 1)
        partidas.anotar(filas, "LA1_5", excluir=False)
        self.assertFalse(partidas.es_excluida(vieja))
        with self.assertRaises(KeyError):
            partidas.anotar(filas, "LA1_999")

    def test_resumen_por_minuto(self):
        f = partidas.fila_desde_partida(self.partida, "yo", self.datos, None, self.timeline, self.estad)
        larga = dict(f, duracion_min="40.0", valor_fila_3="4000")   # 100/min
        corta = dict(f, duracion_min="25.0", valor_fila_3="2000")   # 80/min
        r = {(x["campo"], x["runa"]): x for x in partidas.resumen([larga, corta])}
        self.assertEqual(r[("fila_3", "LastStand")]["por_minuto"], 90.0)


class TestRegistroEjemplo(unittest.TestCase):
    """ejemplos/partidas_ejemplo.csv (inventado) sirve para probar 'partidas resumen' sin clave de Riot."""
    EJEMPLO = Path(__file__).parents[1] / "ejemplos" / "partidas_ejemplo.csv"

    def test_columnas_y_sin_match_id_reales(self):
        with self.EJEMPLO.open(encoding="utf-8", newline="") as f:
            lector = csv.DictReader(f)
            self.assertEqual(lector.fieldnames, partidas.COLUMNAS)
            ids = [fila["match_id"] for fila in lector]
        self.assertTrue(ids and all(i.startswith("EJEMPLO_") for i in ids))

    def test_resumen_con_registro(self):
        import contextlib, io
        from kindred_lab.__main__ import main
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            codigo = main(["partidas", "resumen", "--registro", str(self.EJEMPLO)])
        self.assertEqual(codigo, 0)
        self.assertIn("AbsoluteFocus", salida.getvalue())
        self.assertIn("Se ignoran 1 partidas marcadas con 'excluir'", salida.getvalue())


class TestSecretos(unittest.TestCase):
    def test_lee_archivo_y_el_entorno_manda(self):
        import os
        from kindred_lab import config, riot
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "s.json"
            ruta.write_text('{"riot_api_key": "RGAPI-real", "riot_id": "Yo#LAN"}', encoding="utf-8")
            viejo, viejo_env = config.SECRETOS, os.environ.pop("RIOT_API_KEY", None)
            config.SECRETOS = ruta
            try:
                self.assertEqual(riot.clave_api(), "RGAPI-real")
                os.environ["RIOT_API_KEY"] = "RGAPI-env"
                self.assertEqual(riot.clave_api(), "RGAPI-env")
                os.environ.pop("RIOT_API_KEY")
                ruta.write_text('{"riot_api_key": "RGAPI-xxxxxxxx"}', encoding="utf-8")
                with self.assertRaises(ValueError):     # sigue el valor de ejemplo
                    riot.clave_api()
            finally:
                config.SECRETOS = viejo
                if viejo_env is not None:
                    os.environ["RIOT_API_KEY"] = viejo_env


if __name__ == "__main__":
    unittest.main()
