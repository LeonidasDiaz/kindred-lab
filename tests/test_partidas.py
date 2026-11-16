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

    def test_nota_de_dano_cuenta_el_verdadero(self):
        self.partida["info"]["participants"][0]["trueDamageTaken"] = 10000
        f = partidas.fila_desde_partida(self.partida, "yo", self.datos, self.valores, self.timeline)
        self.assertEqual(f["notas_auto"], "recibido: 60% físico / 20% mágico / 20% verdadero")
        self.assertEqual(f["notas"], "")                       # las notas son solo tuyas
        self.assertEqual(f["dano_que_me_mata"], "AD")        # esta columna sigue comparando físico contra mágico

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

    def test_agregar_no_duplica_y_conserva_anotaciones(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "p.csv"
            vieja = dict(partidas.fila_desde_partida(self.partida, "yo", self.datos, self.valores, self.timeline),
                         match_id="LA1_5", alcance_temprano="si", notas="Ivern mid robó la jungla")
            partidas.escribir_registro([vieja], ruta)
            f = partidas.fila_desde_partida(self.partida, "yo", self.datos, self.valores, self.timeline)
            self.assertEqual(partidas.agregar([f], ruta), 1)
            self.assertEqual(partidas.agregar([f], ruta), 0)
            filas = partidas.leer_registro(ruta)
            self.assertEqual([x["match_id"] for x in filas], ["LA1_5", "LA1_1"])
            self.assertEqual((filas[0]["alcance_temprano"], filas[0]["notas"]), ("si", "Ivern mid robó la jungla"))

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
        self.assertTrue(r["notas"].endswith("Ivern mid robó la jungla"))
        self.assertEqual(r["excluir"], "si")
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


class TestRegistroDanado(unittest.TestCase):
    """Los casos de la revisión del 15/11: un CSV dañado no debe vaciar ni cambiar el registro."""

    def setUp(self):
        TestPartidas.setUp(self)
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.ruta = Path(self.dir.name) / "p.csv"
        self.f = partidas.fila_desde_partida(self.partida, "yo", self.datos, self.valores, self.timeline)

    def escribir(self, encabezado, *filas, delimiter=","):
        with self.ruta.open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, delimiter=delimiter)
            w.writerow(encabezado)
            w.writerows(filas)
        return self.ruta.read_bytes()

    def fila(self, **cambios):
        return [dict(self.f, **cambios)[c] for c in partidas.COLUMNAS]

    def aborta_sin_tocar(self, antes, texto):
        with self.assertRaisesRegex(partidas.RegistroInvalido, texto):
            partidas.agregar([dict(self.f, match_id="LA1_9")], self.ruta)
        self.assertEqual(self.ruta.read_bytes(), antes)

    def test_guardado_con_punto_y_coma(self):
        antes = self.escribir(partidas.COLUMNAS, self.fila(), delimiter=";")
        self.aborta_sin_tocar(antes, "encabezado")

    def test_encabezado_viejo_sin_match_id(self):
        antes = self.escribir([c for c in partidas.COLUMNAS if c != "match_id"], self.fila()[:-1])
        self.aborta_sin_tocar(antes, "faltan match_id")

    def test_coma_sin_comillas_en_una_nota(self):
        fila = self.fila(notas="Fauces bien", match_id="LA1_2")
        i = partidas.COLUMNAS.index("notas")
        antes = self.escribir(partidas.COLUMNAS, fila[:i] + ["Fauces bien", "Syndra me mataba"] + fila[i + 1:])
        self.aborta_sin_tocar(antes, "más campos")

    def test_match_id_invalido_o_repetido(self):
        antes = self.escribir(partidas.COLUMNAS, self.fila(match_id="Syndra me mataba"))
        self.aborta_sin_tocar(antes, "match_id inválido")
        antes = self.escribir(partidas.COLUMNAS, self.fila(match_id="LA1_2"), self.fila(match_id="LA1_2"))
        self.aborta_sin_tocar(antes, "repetido")

    def test_valores_manuales_inesperados(self):
        for columna, valor in (("excluir", "sí"), ("excluir", "x"), ("excluir", "1"), ("alcance_temprano", "quizá"),
                               ("alcance_temprano", "Sí")):
            antes = self.escribir(partidas.COLUMNAS, self.fila(match_id="LA1_2", **{columna: valor}))
            self.aborta_sin_tocar(antes, f"{columna} = {valor!r}")

    def test_valores_manuales_validos(self):
        self.escribir(partidas.COLUMNAS, self.fila(match_id="LA1_2", excluir="si", alcance_temprano="no"),
                      self.fila(match_id="LA1_3", excluir="", alcance_temprano="si"),
                      self.fila(match_id="LA1_4", excluir=" si ", alcance_temprano=""))
        self.assertEqual([partidas.es_excluida(f) for f in partidas.leer_registro(self.ruta)], [True, False, True])

    def test_archivo_vacio(self):
        self.ruta.write_bytes(b"")
        self.aborta_sin_tocar(b"", "encabezado")

    def test_conserva_columnas_agregadas_a_mano(self):
        self.escribir(partidas.COLUMNAS + ["rival_jungla"], self.fila(match_id="LA1_2") + ["Kayn"])
        self.assertEqual(partidas.agregar([self.f], self.ruta), 1)
        filas = partidas.leer_registro(self.ruta)
        self.assertEqual([x["rival_jungla"] for x in filas], ["Kayn", ""])
        with self.ruta.open(encoding="utf-8", newline="") as fh:
            self.assertEqual(next(csv.reader(fh))[-1], "rival_jungla")

    def test_escritura_atomica_con_respaldo(self):
        partidas.escribir_registro([dict(self.f, match_id="LA1_2", notas="primera")], self.ruta)
        self.assertFalse(self.ruta.with_name("p.csv.bak").exists())          # no había nada que respaldar
        antes = self.ruta.read_bytes()
        partidas.escribir_registro([dict(self.f, match_id="LA1_2", notas="segunda")], self.ruta)
        self.assertEqual(self.ruta.with_name("p.csv.bak").read_bytes(), antes)
        self.assertEqual(partidas.leer_registro(self.ruta)[0]["notas"], "segunda")
        self.assertEqual(sorted(p.name for p in Path(self.dir.name).iterdir()), ["p.csv", "p.csv.bak"])

    def test_error_al_escribir_no_toca_el_registro(self):
        partidas.escribir_registro([dict(self.f, match_id="LA1_2")], self.ruta)
        antes = self.ruta.read_bytes()

        from unittest import mock
        nuevas = [dict(self.f, match_id=f"LA1_{i}") for i in range(2, 60)]
        with mock.patch.object(partidas.os, "fsync", side_effect=OSError("disco lleno")):   # temporal ya escrito
            with self.assertRaises(OSError):
                partidas.escribir_registro(nuevas, self.ruta)
        self.assertEqual(self.ruta.read_bytes(), antes)
        self.assertFalse(self.ruta.with_name("p.csv.tmp").exists())

    def test_no_escribe_filas_que_luego_no_se_podrian_leer(self):
        partidas.escribir_registro([dict(self.f, match_id="LA1_2")], self.ruta)
        antes = self.ruta.read_bytes()
        with self.assertRaises(partidas.RegistroInvalido):
            partidas.escribir_registro([dict(self.f, match_id="LA1_2"), dict(self.f, match_id="LA1_2")], self.ruta)
        self.assertEqual(self.ruta.read_bytes(), antes)

    def test_excluir_ya_no_es_una_subcadena_de_la_nota(self):
        partidas.escribir_registro([dict(self.f, match_id="LA1_2", notas="no excluir, fue partida normal")], self.ruta)
        fila = partidas.leer_registro(self.ruta)[0]
        self.assertFalse(partidas.es_excluida(fila))
        partidas.anotar([fila], "LA1_2", excluir=True)
        self.assertEqual((fila["excluir"], fila["notas"]), ("si", "no excluir, fue partida normal"))
        partidas.anotar([fila], "LA1_2", excluir=False)
        self.assertEqual((fila["excluir"], fila["notas"]), ("", "no excluir, fue partida normal"))

    def test_registro_viejo_migra_excluir_desde_las_notas(self):
        vieja = [c for c in partidas.COLUMNAS if c not in ("excluir", "notas_auto")]
        filas = [dict(self.f, match_id="LA1_2", notas="recibido: 70% AD / 30% AP; Ivern robó; excluir"),
                 dict(self.f, match_id="LA1_3", notas="recibido: 70% AD / 30% AP; no excluir, fue normal"),
                 dict(self.f, match_id="LA1_4", notas="excluir: mid AFK")]
        antes = self.escribir(vieja, *[[f[c] for c in vieja] for f in filas])
        a, b, c = partidas.leer_registro(self.ruta)
        self.assertEqual((a["excluir"], a["notas_auto"], a["notas"]), ("si", "recibido: 70% AD / 30% AP", "Ivern robó"))
        self.assertEqual((b["excluir"], b["notas"]), ("", "no excluir, fue normal"))
        self.assertEqual((c["excluir"], c["notas_auto"], c["notas"]), ("", "", "excluir: mid AFK"))   # solo el exacto
        self.assertEqual(self.ruta.read_bytes(), antes)                             # leer no reescribe
        partidas.agregar([], self.ruta)
        with self.ruta.open(encoding="utf-8", newline="") as fh:
            self.assertEqual(next(csv.reader(fh)), partidas.COLUMNAS)

    def test_registro_con_excluir_pero_sin_notas_auto(self):
        vieja = [c for c in partidas.COLUMNAS if c != "notas_auto"]
        self.escribir(vieja, [dict(self.f, match_id="LA1_2", notas="recibido: 1% AD / 99% AP; lección", excluir="si")[c]
                              for c in vieja])
        fila = partidas.leer_registro(self.ruta)[0]
        self.assertEqual((fila["notas_auto"], fila["notas"], fila["excluir"]), ("recibido: 1% AD / 99% AP", "lección", "si"))

    def test_recalcular_solo_toca_lo_automatico(self):
        vieja = dict(self.f, match_id="LA1_2", kda="0/0/0", notas_auto="recibido: 70% AD / 30% AP",
                     alcance_temprano="si", notas="Fauces bien, Syndra me mataba", excluir="si", rival_jungla="Kayn")
        sin_cache = dict(self.f, match_id="LA1_3", kda="9/9/9", notas="mía")
        filas = [vieja, sin_cache]
        nueva = dict(self.f, match_id="LA1_2", alcance_temprano="", notas="", excluir="")
        r = partidas.recalcular(filas, lambda mid: nueva if mid == "LA1_2" else None)
        self.assertEqual(vieja["kda"], "11/7/20")
        self.assertEqual(vieja["notas_auto"], "recibido: 75% físico / 25% mágico / 0% verdadero")
        self.assertEqual((vieja["alcance_temprano"], vieja["notas"], vieja["excluir"], vieja["rival_jungla"]),
                         ("si", "Fauces bien, Syndra me mataba", "si", "Kayn"))
        self.assertEqual(vieja["muertes_antes_min10"], "1")              # se guarda como texto, como al leer
        self.assertEqual(sin_cache["kda"], "9/9/9")
        self.assertEqual(r["sin_cache"], ["LA1_3"])
        self.assertIn(("LA1_2", "kda", "0/0/0", "11/7/20"), r["cambios"])
        self.assertFalse(any(c in ("alcance_temprano", "notas", "excluir", "match_id") for _, c, _, _ in r["cambios"]))

    def test_recalcular_sin_cambios_no_cambia_nada(self):
        fila = {c: str(v) for c, v in dict(self.f, match_id="LA1_2").items()}
        r = partidas.recalcular([fila], lambda mid: dict(self.f, match_id=mid))
        self.assertEqual(r["cambios"], [])

    def test_nunca_deja_menos_partidas(self):
        filas = [dict(self.f, match_id=f"LA1_{i}", notas=f"nota {i}") for i in range(2, 9)]
        partidas.escribir_registro(filas, self.ruta)
        antes = self.ruta.read_bytes()
        for pocas in ([], filas[:3], [dict(self.f, match_id="LA1_99")]):
            with self.assertRaisesRegex(partidas.RegistroInvalido, "se perderían"):
                partidas.escribir_registro(pocas, self.ruta)
            self.assertEqual(self.ruta.read_bytes(), antes)

    def test_quitar_partidas_a_proposito(self):
        filas = [dict(self.f, match_id=f"LA1_{i}") for i in range(2, 5)]
        partidas.escribir_registro(filas, self.ruta)
        with self.assertRaises(partidas.RegistroInvalido):          # quitar una no autoriza quitar otra
            partidas.escribir_registro(filas[:1], self.ruta, quitar=frozenset({"LA1_3"}))
        partidas.escribir_registro(filas[:2], self.ruta, quitar=frozenset({"LA1_4"}))
        self.assertEqual([f["match_id"] for f in partidas.leer_registro(self.ruta)], ["LA1_2", "LA1_3"])

    def test_ida_y_vuelta_de_notas_dificiles(self):
        notas = ['dijo "gg", y se fue', "línea 1\nlínea 2", "retorno\rsuelto", "  espacios  ", "Kayn 🐺; Ekko"]
        filas = [dict(self.f, match_id=f"LA1_{i}", notas=n) for i, n in enumerate(notas, start=2)]
        partidas.escribir_registro(filas, self.ruta)
        self.assertEqual([f["notas"] for f in partidas.leer_registro(self.ruta)], notas)

    def test_orden_de_columnas_distinto_se_acepta(self):
        self.escribir(list(reversed(partidas.COLUMNAS)), list(reversed(self.fila(match_id="LA1_2"))))
        self.assertEqual(partidas.leer_registro(self.ruta)[0]["match_id"], "LA1_2")


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
