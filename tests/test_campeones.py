"""Datos SINTÉTICOS con la forma de champion.json de Data Dragon; no usa red."""
import json
import tempfile
import unittest
from pathlib import Path

from kindred_lab import campeones, ddragon


def dd(version):
    return {"version": version, "data": {"Fiddlesticks": {"name": "Fiddlesticks", "tags": ["Mage", "Support"]},
                                         "Jhin": {"name": "Jhin", "tags": ["Marksman", "Mage"]}}}


class TestCampeones(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raw, self.out = Path(self.tmp.name) / "raw", Path(self.tmp.name) / "out"

    def poner_en_cache(self, version):
        ruta = ddragon.ruta_cache(version, "es_MX", campeones.ARCHIVO_DDRAGON, self.raw)
        ruta.parent.mkdir(parents=True)
        ruta.write_text(json.dumps(dd(version)), encoding="utf-8")

    def test_generar_y_tipos_sin_distinguir_mayusculas(self):
        datos = campeones.generar(dd("16.22.1")["data"], "16.22.1")
        self.assertEqual(datos["campeones"]["Jhin"], {"nombre": "Jhin", "tipos": ["Marksman", "Mage"]})
        self.assertEqual(campeones.tipos(datos, "FiddleSticks"), ["Mage", "Support"])
        self.assertEqual(campeones.tipos(datos, "NoExiste"), [])

    def test_actualizar_no_reemplaza_un_parche_mas_nuevo(self):
        self.poner_en_cache("16.22.1")
        self.poner_en_cache("16.9.1")
        campeones.actualizar("16.22.1", raw_dir=self.raw, out_dir=self.out)
        campeones.actualizar("16.9.1", raw_dir=self.raw, out_dir=self.out)
        self.assertEqual(campeones.cargar(self.out)["version"], "16.22.1")

    def test_cargar_sin_archivo_dice_que_correr(self):
        with self.assertRaisesRegex(FileNotFoundError, "objetos actualizar"):
            campeones.cargar(self.out)
