"""Objetos SINTÉTICOS con la forma del item.json de Data Dragon; no usan red."""
import json
import tempfile
import unittest
from pathlib import Path

from kindred_lab import config, objetos


def item(desc, comprable=True, precio=3000):
    return {"name": "X", "description": desc, "maps": {"11": comprable}, "gold": {"total": precio, "purchasable": True}}


DESC_DANZA = ("<mainText><stats><attention>60</attention> de Daño de Ataque<br><attention>50</attention> de Armadura"
              "<br><attention>15</attention> de Aceleración de Habilidad</stats><br><br><passive>Ignorar Dolor</passive>"
              "<br>Un porcentaje del daño recibido se distribuye.</mainText>")
OFICIAL_DANZA = ("60 de Daño de Ataque 50 de Armadura 15 de Aceleración de Habilidad Ignorar Dolor "
                 "Un porcentaje del daño recibido se distribuye.")


CLAVE_MELEE = "calc.MeleeItemCalcValue.0.mNumber"


def juego_danza(melee=0.3):
    """Entrada SINTÉTICA con la forma de items.cdtb.bin.json."""
    return {"itemID": 6333, "price": 275, "mFlatArmorMod": 50.0,
            "mDataValues": [{"mName": "Duracion", "mValue": 3.0, "__type": "ItemDataValue"},
                            {"mName": "SinValor", "__type": "ItemDataValue"}],
            "DataValuesModeOverride": {"ARAM": {"DataValues": [{"mName": "Duracion", "mValue": 9.0}]}},
            "mEffectAmount": [0.0, 8.0],
            "mItemCalculations": {"MeleeItemCalcValue": {
                "mFormulaParts": [{"mNumber": melee + 1e-8, "__type": "NumberCalculationPart"}],
                "mDisplayAsPercent": True, "DamageType": 1, "{72c5c2a8}": 1,
                "mExpandedTooltipCalculationDisplay": 5, "__type": "GameCalculation"}},
            "__type": "ItemData"}


class TestValoresJuego(unittest.TestCase):
    def setUp(self):
        self.juego = {
            "Items/6333": juego_danza(),
            "Items/226333": juego_danza(melee=0.35),                      # variante de Arena: otro id
            "Items/6333/Spells/6333Active": {"__type": "SpellObject", "mSpell": {
                "cooldownTime": [20.0, 20.0], "mEffectAmount": [{"value": [0.0, 5.0]}], "castRange": [900.0]}},
            "Items/6333/Spells/226333Active": {"__type": "SpellObject", "mSpell": {"cooldownTime": [99.0]}},
            "Items/6333/Particles/6333_Vfx": {"__type": "VfxSystemDefinitionData", "lifetime": 0.5},
        }
        self.v = objetos.valores_juego(self.juego, "6333", objetos.indice_hechizos(self.juego))

    def test_valores_con_nombre_y_sin_ruido_de_coma_flotante(self):
        self.assertEqual(self.v["valor.Duracion"], 3)                     # configuración normal, no la de ARAM
        self.assertEqual(self.v["valor.SinValor"], 0)
        self.assertEqual(self.v[CLAVE_MELEE], 0.3)

    def test_efectos_y_hechizos_sin_ceros(self):
        self.assertEqual(self.v["efecto.1"], 8)
        self.assertNotIn("efecto.0", self.v)
        self.assertEqual(self.v["hechizo.6333Active.enfriamiento"], 20)     # los niveles iguales se juntan
        self.assertEqual(self.v["hechizo.6333Active.efecto.0.value.1"], 5)

    def test_deja_fuera_lo_que_no_sirve(self):
        claves = " ".join(self.v)
        for fuera in ("ARAM", "castRange", "Vfx", "lifetime", "price", "mFlatArmorMod",
                      "DamageType", "Display", "72c5c2a8", "226333Active"):
            self.assertNotIn(fuera, claves)

    def test_campo_con_hash_no_avisa_al_recibir_nombre(self):
        def juego(calc):
            return {"Items/1": {"mItemCalculations": {"Dano": {**calc, "mFormulaParts": [{"mNumber": 45.0}]}}}}
        antes = objetos.valores_juego(juego({"{72c5c2a8}": 1}), "1", {})
        ahora = objetos.valores_juego(juego({"DamageType": 1}), "1", {})
        self.assertEqual(objetos.diferencias_valores(antes, ahora), {})
        self.assertEqual(ahora, {"calc.Dano.0.mNumber": 45})

    def test_campo_numerico_nuevo_si_avisa(self):
        juego = {"Items/1": {"mItemCalculations": {"Dano": {"mFormulaParts": [{"mCampoNuevo": 7.0}]}}}}
        self.assertEqual(objetos.valores_juego(juego, "1", {}), {"calc.Dano.0.mCampoNuevo": 7})

    def test_otros_ids_y_objeto_ausente(self):
        indice = objetos.indice_hechizos(self.juego)
        self.assertEqual(objetos.valores_juego(self.juego, "226333", indice)[CLAVE_MELEE], 0.35)
        self.assertIsNone(objetos.valores_juego(self.juego, "999", indice))

    def test_diferencias(self):
        self.assertEqual(objetos.diferencias_valores({"a": 1, "b": 2}, {"a": 1, "b": 3, "c": 4}),
                         {"b": {"antes": 2, "ahora": 3}, "c": {"antes": None, "ahora": 4}})


class TestDataDragon(unittest.TestCase):
    def test_texto_oficial(self):
        self.assertEqual(objetos.texto_oficial(DESC_DANZA), OFICIAL_DANZA)

    def test_stats_del_bloque(self):
        self.assertEqual(objetos.stats_desde_descripcion(DESC_DANZA),
                         {"AD_plano": 60, "Armadura_plana": 50, "Aceleracion_de_habilidad_plana": 15})

    def test_porcentajes_como_fraccion(self):
        desc = ("<stats><attention>25%</attention> de Velocidad de Ataque<br><attention>4%</attention> de Velocidad de "
                "Movimiento<br><attention>20</attention> de Velocidad de Movimiento</stats>")
        self.assertEqual(objetos.stats_desde_descripcion(desc),
                         {"Vel_Ataque": 0.25, "Vel_Movimiento_Porcentual": 0.04, "Vel_Movimiento_plana": 20})

    def test_sin_bloque(self):
        self.assertEqual(objetos.stats_desde_descripcion("<mainText>Nada</mainText>"), {})

    def test_etiqueta_desconocida_es_error(self):
        with self.assertRaises(ValueError):
            objetos.stats_desde_descripcion("<stats><attention>5</attention> de Estadística Nueva</stats>")

    def test_linea_sin_formato_es_error(self):
        with self.assertRaises(ValueError):
            objetos.stats_desde_descripcion("<stats>algo raro</stats>")

    def test_es_comprable(self):
        self.assertTrue(objetos.es_comprable(item("")))
        self.assertFalse(objetos.es_comprable(item("", comprable=False)))
        self.assertFalse(objetos.es_comprable({**item(""), "hideFromAll": True}))


class TestNombres(unittest.TestCase):
    def test_claves_y_valores_a_cualquier_profundidad(self):
        original = {"Vel_Ataque_Porcentual": 0.1,
                    "a": [{"estadistica_modificada": "Vel_Movimiento_Plana"}],
                    "nota": "Vel_Movimiento_Plana en texto libre no cambia"}
        self.assertEqual(objetos.unificar_nombres(original),
                         {"Vel_Ataque": 0.1,
                          "a": [{"estadistica_modificada": "Vel_Movimiento_plana"}],
                          "nota": "Vel_Movimiento_Plana en texto libre no cambia"})

    def test_no_toca_estadisticas_distintas(self):
        self.assertEqual(objetos.unificar_nombres({"estadistica_origen": "AD_total"}),
                         {"estadistica_origen": "AD_total"})


class TestMigrar(unittest.TestCase):
    def setUp(self):
        self.manual = {"objetos": {
            "1": {"metadata": {"nombre": "Danza", "precio": 3300,
                               "descripcion_legible": OFICIAL_DANZA.replace("Un porcentaje", "(10%/30%)")},
                  "stats_base": {"AD": 60, "Armadura": 40, "Aceleracion_de_habilidad_plana": 15},
                  "mecanicas": {"pasiva": {"estadistica_modificada": "Prob_Critico_Porcentual"}},
                  "restricciones_tienda": {"limite": 1}},
            "2": {"metadata": {"nombre": "Igual", "precio": 500, "descripcion_legible": "5 de Armadura",
                               "comprable_en_tienda": False},
                  "stats_base": {"Armadura_plana": 5, "nota": "una nota"}, "mecanicas": {}},
            "3": {"metadata": {"nombre": "Sin DD", "precio": 1, "descripcion_legible": "x"},
                  "stats_base": {}, "mecanicas": {}},
        }}
        self.dd = {"1": item(DESC_DANZA), "2": item("<stats><attention>5</attention> de Armadura</stats>")}
        self.capa, self.informe = objetos.migrar(self.manual, self.dd, "16.15.1")

    def test_conserva_mecanicas_con_nombres_unificados(self):
        o = self.capa["objetos"]["1"]
        self.assertEqual(o["parche_verificado"], "16.15.1")
        self.assertEqual(o["mecanicas"], {"pasiva": {"estadistica_modificada": "Prob_Critico"}})

    def test_descripciones(self):
        o = self.capa["objetos"]["1"]
        self.assertEqual(o["descripcion_verificada"], OFICIAL_DANZA)
        self.assertIn("(10%/30%)", o["descripcion_manual"])
        self.assertNotIn("descripcion_manual", self.capa["objetos"]["2"])
        self.assertEqual(self.informe["descripciones_manuales"], [{"id": "1", "nombre": "Danza"}])

    def test_discrepancias_con_data_dragon(self):
        self.assertEqual(self.informe["discrepancias"], [
            {"id": "1", "nombre": "Danza", "stats": {"Armadura_plana": {"manual": 40, "data_dragon": 50}}}])

    def test_campos_manuales_de_metadata(self):
        self.assertEqual(self.capa["objetos"]["1"]["metadata_manual"], {"restricciones_tienda": {"limite": 1}})
        self.assertEqual(self.capa["objetos"]["2"]["metadata_manual"],
                         {"comprable_en_tienda": False, "nota_stats": "una nota"})

    def test_sin_data_dragon_se_conserva(self):
        self.assertIn("3", self.capa["objetos"])
        self.assertEqual(self.informe["sin_data_dragon"], [{"id": "3", "nombre": "Sin DD"}])

    def test_descripcion_vacia_no_borra_estadisticas(self):
        manual = {"objetos": {"9": {"metadata": {"nombre": "Mapa", "precio": 400, "descripcion_legible": "30 de Vida"},
                                    "stats_base": {"Vida_maxima_plana": 30}, "mecanicas": {}}}}
        capa, informe = objetos.migrar(manual, {"9": item("")}, "16.15.1")
        self.assertEqual(informe["discrepancias"], [])
        self.assertEqual(informe["sin_data_dragon"], [{"id": "9", "nombre": "Mapa"}])
        self.assertNotIn("descripcion_verificada", capa["objetos"]["9"])

    def test_informe(self):
        self.assertEqual(self.informe["renombres"], {"AD": 1, "Armadura": 1, "Prob_Critico_Porcentual": 1})
        md = objetos.informe_markdown(self.informe)
        self.assertIn("| 1 | Danza | Armadura_plana | 40 | 50 |", md)
        self.assertIn("| `AD` | `AD_plano` | 1 |", md)


class TestGenerar(unittest.TestCase):
    def setUp(self):
        self.capa = {"objetos": {
            "1": {"nombre": "Danza", "parche_verificado": "16.15.1", "descripcion_verificada": OFICIAL_DANZA,
                  "descripcion_manual": "con (10%/30%)", "mecanicas": {"pasiva": {"x": 1}}},
            "2": {"nombre": "Ya no se compra", "parche_verificado": "16.15.1",
                  "descripcion_verificada": "viejo", "mecanicas": {"pasiva": {"x": 1}},
                  "metadata_manual": {"nota_desarrollador": "eliminado"}},
            "3": {"nombre": "Fuera de Data Dragon", "parche_verificado": "16.15.1", "mecanicas": {"pasiva": {"x": 1}}},
            "4": {"nombre": "Mapa", "parche_verificado": "16.15.1", "mecanicas": {}},
        }}
        self.ref = {"objetos": {
            "3": {"metadata": {"nombre": "Fuera de Data Dragon", "precio": 900, "descripcion_legible": "manual 3"},
                  "stats_base": {"AD": 10, "nota": "n"}, "mecanicas": {}},
            "4": {"metadata": {"nombre": "Mapa", "precio": 400, "descripcion_legible": "30 de Vida"},
                  "stats_base": {"Vida_maxima_plana": 30}, "mecanicas": {}},
        }}
        self.dd = {"1": {**item(DESC_DANZA, precio=3300), "name": "Danza "},
                   "2": item("<stats><attention>5</attention> de Armadura</stats>Nuevo texto", comprable=False),
                   "4": item(""),
                   "5": {**item("<stats><attention>7</attention> de Letalidad</stats>"), "name": "Nuevo"},
                   "6": {**item("<stats><attention>1</attention> de Armadura</stats>", comprable=False), "name": "Otro"}}
        self.d = objetos.generar(self.dd, self.capa, self.ref, "16.22.1")["objetos"]

    def test_metadata_y_stats_de_data_dragon(self):
        o = self.d["1"]
        self.assertEqual((o["metadata"]["nombre"], o["metadata"]["precio"]), ("Danza", 3300))
        self.assertEqual(o["metadata"]["descripcion_legible"], OFICIAL_DANZA)
        self.assertEqual(o["stats_base"]["AD_plano"], 60)

    def test_final_y_botas(self):
        self.dd["1"]["into"] = ["5"]
        self.dd["5"]["tags"] = ["Boots"]
        d = objetos.generar(self.dd, self.capa, self.ref, "16.22.1")["objetos"]
        self.assertEqual((d["1"]["metadata"]["final"], d["1"]["metadata"]["botas"]), (False, False))
        self.assertEqual((d["5"]["metadata"]["final"], d["5"]["metadata"]["botas"]), (True, True))
        self.assertFalse(d["3"]["metadata"]["final"])              # sin Data Dragon no se sabe

    def test_conserva_capa_manual(self):
        o = self.d["1"]
        self.assertEqual(o["mecanicas"], {"pasiva": {"x": 1}})
        self.assertEqual(o["parche_verificado"], "16.15.1")
        self.assertEqual(o["metadata"]["descripcion_manual"], "con (10%/30%)")

    def test_alcance_comprables_mas_capa(self):
        self.assertEqual(set(self.d), {"1", "2", "3", "4", "5"})    # el 6 no se compra ni tiene capa

    def test_disponible(self):
        self.assertTrue(self.d["1"]["metadata"]["disponible"])
        self.assertFalse(self.d["2"]["metadata"]["disponible"])
        self.assertEqual(self.d["2"]["metadata"]["nota_desarrollador"], "eliminado")

    def test_sin_data_dragon_usa_la_referencia(self):
        o = self.d["3"]
        self.assertFalse(o["metadata"]["disponible"])
        self.assertEqual(o["stats_base"], {"AD_plano": 10})
        self.assertEqual((o["metadata"]["precio"], o["metadata"]["descripcion_legible"]), (900, "manual 3"))
        self.assertEqual(self.d["4"]["stats_base"], {"Vida_maxima_plana": 30})     # descripción vacía

    def test_avisa_solo_si_cambia_la_descripcion_con_mecanicas(self):
        self.assertFalse(self.d["1"]["revisar"])
        self.assertTrue(self.d["2"]["revisar"])
        self.assertFalse(self.d["3"]["revisar"])      # sin datos nuevos no hay con qué comparar
        self.assertFalse(self.d["5"]["revisar"])      # sin mecánicas no hay nada que revisar

    def test_objeto_nuevo_sin_capa(self):
        o = self.d["5"]
        self.assertEqual((o["mecanicas"], o["parche_verificado"]), ({}, None))


class TestActualizarYVerificar(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.raw, self.out, self.capa = base / "raw", base / "out", base / "capa.json"
        self.capa.write_text(json.dumps({"objetos": {"1": {
            "nombre": "Danza", "parche_verificado": "16.15.1", "descripcion_verificada": OFICIAL_DANZA,
            "mecanicas": {"pasiva": {"x": 1}}}}}), encoding="utf-8")
        self._dd("16.15.1", DESC_DANZA, 3300)
        self._dd("16.22.1", DESC_DANZA.replace("<attention>60</attention>", "<attention>65</attention>"), 3400)

    def _dd(self, version, desc, precio):
        ruta = self.raw / version / "es_MX" / objetos.ARCHIVO_DDRAGON
        ruta.parent.mkdir(parents=True)
        ruta.write_text(json.dumps({"data": {"1": {**item(desc, precio=precio), "name": "Danza"}}}), encoding="utf-8")

    def _actualizar(self, version, melee=0.3):
        return objetos.actualizar(version=version, raw_dir=self.raw, out_dir=self.out, capa_ruta=self.capa,
                                  referencia_ruta=self.out / "no_existe.json",
                                  cargar_juego=lambda v: {"Items/1": juego_danza(melee)})

    def test_valor_oculto_avisa_aunque_la_descripcion_siga_igual(self):
        self._dd("16.23.1", DESC_DANZA, 3300)
        objetos.actualizar(version="16.15.1", raw_dir=self.raw, out_dir=self.out, capa_ruta=self.capa,
                           referencia_ruta=self.out / "no_existe.json",
                           cargar_juego=lambda v: {"Items/1": juego_danza(0.3)})
        self.assertEqual(objetos.fijar_base_valores("16.15.1", self.out, self.capa), 1)
        res = self._actualizar("16.23.1", melee=0.25)
        self.assertEqual(res["avisos"], [])                       # la descripción oficial no cambió
        self.assertEqual(res["avisos_valores"], [{
            "id": "1", "nombre": "Danza", "parche_verificado": "16.15.1", "descripcion_igual": True,
            "cambios": {CLAVE_MELEE: {"antes": 0.3, "ahora": 0.25}}}])
        self.assertEqual(res["comparacion"]["valores"], {"1": {CLAVE_MELEE: {"antes": 0.3, "ahora": 0.25}}})
        reporte = res["reporte"].read_text(encoding="utf-8")
        self.assertIn("Valores del juego por revisar (1)", reporte)
        self.assertIn(f"{CLAVE_MELEE}: 0.3 -> 0.25", reporte)

    def test_el_aviso_de_valores_se_repite_hasta_verificar(self):
        self._dd("16.23.1", DESC_DANZA, 3300)
        self._actualizar("16.15.1")
        objetos.fijar_base_valores("16.15.1", self.out, self.capa)
        self.assertEqual(len(self._actualizar("16.23.1", melee=0.25)["avisos_valores"]), 1)
        self.assertEqual(len(self._actualizar("16.23.1", melee=0.25)["avisos_valores"]), 1)
        objetos.verificar("1", out_dir=self.out, capa_ruta=self.capa)
        self.assertEqual(objetos.cargar_capa(self.capa)["objetos"]["1"]["valores_verificados"][CLAVE_MELEE], 0.25)
        self.assertFalse(objetos.cargar("latest", self.out)["objetos"]["1"]["valores_cambiados"])
        self.assertEqual(self._actualizar("16.23.1", melee=0.25)["avisos_valores"], [])

    def test_base_valores_no_sobrescribe(self):
        self._actualizar("16.15.1", melee=0.3)
        self.assertEqual(objetos.fijar_base_valores("16.15.1", self.out, self.capa), 1)
        self._actualizar("16.15.1", melee=0.5)
        self.assertEqual(objetos.fijar_base_valores("16.15.1", self.out, self.capa), 0)
        self.assertEqual(objetos.cargar_capa(self.capa)["objetos"]["1"]["valores_verificados"][CLAVE_MELEE], 0.3)

    def test_sin_archivos_del_juego_sigue_y_lo_dice(self):
        def falla(_):
            raise OSError("sin red")
        self._actualizar("16.15.1")
        objetos.fijar_base_valores("16.15.1", self.out, self.capa)
        res = objetos.actualizar(version="16.22.1", raw_dir=self.raw, out_dir=self.out, capa_ruta=self.capa,
                                 referencia_ruta=self.out / "no_existe.json", cargar_juego=falla)
        self.assertEqual(res["error_juego"], "sin red")
        self.assertEqual(res["avisos_valores"], [])               # sin datos no es "desaparecieron los valores"
        self.assertEqual(res["comparacion"]["valores"], {})
        self.assertIsNone(res["datos"]["objetos"]["1"]["valores_juego"])

    def test_compara_avisa_y_no_toca_la_capa(self):
        antes = self.capa.read_text(encoding="utf-8")
        self.assertIsNone(self._actualizar("16.15.1")["comparacion"])
        res = self._actualizar("16.22.1")
        self.assertEqual(res["comparacion"]["stats"], {"1": {"AD_plano": {"antes": 60, "ahora": 65}}})
        self.assertEqual(res["comparacion"]["precio"], {"1": {"antes": 3300, "ahora": 3400}})
        self.assertEqual([a["id"] for a in res["avisos"]], ["1"])
        self.assertEqual(self.capa.read_text(encoding="utf-8"), antes)
        self.assertEqual(res["datos"]["objetos"]["1"]["parche_verificado"], "16.15.1")
        reporte = res["reporte"].read_text(encoding="utf-8")
        self.assertIn("Mecánicas por revisar (1)", reporte)
        self.assertIn("AD_plano: 60 -> 65", reporte)

    def test_verificar_quita_el_aviso(self):
        self._actualizar("16.15.1")
        self._actualizar("16.22.1")
        r = objetos.verificar("1", out_dir=self.out, capa_ruta=self.capa)
        self.assertEqual(r, {"nombre": "Danza", "version": "16.22.1"})
        c = objetos.cargar_capa(self.capa)["objetos"]["1"]
        self.assertEqual(c["parche_verificado"], "16.22.1")
        self.assertIn("65 de Daño", c["descripcion_verificada"])
        self.assertFalse(objetos.cargar("latest", self.out)["objetos"]["1"]["revisar"])
        self.assertEqual(self._actualizar("16.22.1")["avisos"], [])

    def test_verificar_id_desconocido(self):
        self._actualizar("16.15.1")
        with self.assertRaises(KeyError):
            objetos.verificar("999", out_dir=self.out, capa_ruta=self.capa)


class TestCapaReal(unittest.TestCase):
    """reglas/objetos_mecanicas.json: la capa manual que se usa de verdad."""

    def test_sin_nombres_repetidos(self):
        capa = json.loads(Path(config.OBJETOS_MECANICAS).read_text(encoding="utf-8"))
        self.assertEqual(objetos.unificar_nombres(capa["objetos"]), capa["objetos"])

    def test_cada_objeto_tiene_parche_verificado_y_mecanicas(self):
        capa = json.loads(Path(config.OBJETOS_MECANICAS).read_text(encoding="utf-8"))
        for id_, o in capa["objetos"].items():
            self.assertIn("parche_verificado", o, id_)
            self.assertIn("mecanicas", o, id_)


if __name__ == "__main__":
    unittest.main()
