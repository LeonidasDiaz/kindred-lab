"""Pruebas sin red: usan los fixtures de tests/fixtures y carpetas temporales."""
import json
import tempfile
import unittest
from pathlib import Path

from kindred_lab import ddragon, runas

FIX = Path(__file__).parent / "fixtures"
V1, V2 = "16.19.1", "16.20.1"


def cargar_fixture(v):
    return json.loads((FIX / f"runesReforged_{v}.json").read_text(encoding="utf-8"))


class TestNormalizar(unittest.TestCase):
    def setUp(self):
        self.d = runas.normalizar(cargar_fixture(V1), V1, "es_MX")

    def test_quita_html(self):
        larga = self.d["runas"]["8005"]["larga"]
        self.assertNotIn("<", larga)
        self.assertIn("Tras 3 ataques", larga)

    def test_filas_y_arbol(self):
        self.assertEqual(self.d["runas"]["8005"]["fila"], 0)        # piedra angular
        self.assertEqual(self.d["runas"]["8299"]["fila"], 3)
        self.assertEqual(self.d["runas"]["8299"]["arbol"], "Precision")
        self.assertEqual(self.d["arboles"]["Resolve"]["nombre"], "Valor")


class TestComparar(unittest.TestCase):
    def test_detecta_nueva_quitada_cambiada(self):
        a = runas.normalizar(cargar_fixture(V1), V1, "es_MX")
        b = runas.normalizar(cargar_fixture(V2), V2, "es_MX")
        c = runas.comparar(a, b)
        self.assertEqual([r["nombre"] for r in c["nuevas"]], ["Revitalizar"])
        self.assertEqual([r["nombre"] for r in c["quitadas"]], ["Demolición"])
        self.assertEqual([x["ahora"]["nombre"] for x in c["cambiadas"]], ["Estrategia Ofensiva"])
        self.assertEqual(c["cambiadas"][0]["campos"], ["larga"])

    def test_sin_cambios(self):
        a = runas.normalizar(cargar_fixture(V1), V1, "es_MX")
        self.assertFalse(runas.hay_cambios(runas.comparar(a, a)))


class TestBusqueda(unittest.TestCase):
    def setUp(self):
        self.d = runas.normalizar(cargar_fixture(V1), V1, "es_MX")

    def test_sin_acentos_ni_mayusculas(self):
        self.assertEqual([r["id"] for r in runas.buscar(self.d, "ULTIMA batalla")], [8299])
        self.assertEqual([r["id"] for r in runas.buscar(self.d, "coraza osea")], [8473])

    def test_arbol_por_nombre_en_espanol(self):
        filas = runas.arbol_por_filas(self.d, "precisión")
        self.assertEqual(len(filas), 4)
        self.assertEqual([r["nombre"] for r in filas[3]], ["Golpe de Gracia", "La Última Batalla"])


class TestFlujoCompleto(unittest.TestCase):
    def test_actualizar_dos_parches(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            r1 = runas.actualizar(V1, archivo_local=FIX / f"runesReforged_{V1}.json", out_dir=out)
            self.assertIsNone(r1["comparacion"])
            r2 = runas.actualizar(V2, archivo_local=FIX / f"runesReforged_{V2}.json", out_dir=out)
            self.assertTrue(runas.hay_cambios(r2["comparacion"]))
            self.assertTrue(r2["reporte"].exists())
            self.assertIn("Revitalizar", r2["reporte"].read_text(encoding="utf-8"))
            self.assertEqual(runas.cargar("latest", out)["version"], V2)
            self.assertEqual(runas.versiones_procesadas(out), [V1, V2])

    def test_actualizar_version_vieja_no_se_compara_con_nueva(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            runas.actualizar(V2, archivo_local=FIX / f"runesReforged_{V2}.json", out_dir=out)
            r = runas.actualizar(V1, archivo_local=FIX / f"runesReforged_{V1}.json", out_dir=out)
            self.assertIsNone(r["comparacion"])
            self.assertEqual(runas.cargar("latest", out)["version"], V2)   # latest no retrocede


class TestVersiones(unittest.TestCase):
    def test_orden_numerico(self):
        vs = sorted(["16.9.1", "16.20.1", "16.10.1"], key=ddragon.clave_version)
        self.assertEqual(vs, ["16.9.1", "16.10.1", "16.20.1"])


if __name__ == "__main__":
    unittest.main()
