import json
import unittest
from pathlib import Path

from kindred_lab import reglas, runas

FIX = Path(__file__).parent / "fixtures"


class TestReglas(unittest.TestCase):
    def setUp(self):
        crudo = json.loads((FIX / "runesReforged_16.19.1.json").read_text(encoding="utf-8"))
        self.datos = runas.normalizar(crudo, "16.19.1", "es_MX")

    def test_regla_valida(self):
        r = {"fijas": {"arbol_principal": "Precision", "fila_1": "Triumph"},
             "preguntas": [{"si": {"secundaria": "Resolve", "incluye": ["Unflinching"]},
                            "opciones": {"x": {"fila_3": "LastStand"}}}]}
        self.assertEqual(reglas.validar(r, self.datos), [])

    def test_detecta_runa_y_arbol_inexistentes(self):
        r = {"fijas": {"arbol_principal": "Precision"},
             "preguntas": [{"no": {"secundaria": "Domination", "incluye": ["LethalTempoX"]}}]}
        problemas = reglas.validar(r, self.datos)
        self.assertEqual(len(problemas), 2)
        self.assertIn("LethalTempoX", problemas[0])
        self.assertIn("LethalTempo", problemas[0])    # sugiere la parecida
        self.assertIn("Domination", problemas[1])

    def test_reglas_de_objetos(self):
        objs = {"version": "16.22.1", "objetos": {"1": {"metadata": {"nombre": "Danza"}}}}
        camps = {"campeones": {"DrMundo": {}, "Sett": {}}}
        bien = {"situaciones": [{"objeto": "Danza", "aplica": {"campeones_2": ["Sett", "drmundo"], "perfil": "fisico"}}]}
        self.assertEqual(reglas.validar_objetos(bien, objs, camps), [])
        mal = {"situaciones": [{"objeto": "Danza", "aplica": {"campeones_1": ["Mundo"], "perfil": "AD"}},
                               {"objeto": "Otro"}]}
        problemas = reglas.validar_objetos(mal, objs, camps)
        self.assertEqual(len(problemas), 4)
        self.assertIn("AD", problemas[0])
        self.assertIn("Mundo", problemas[1])
        self.assertIn("Otro", problemas[2])
        self.assertIn("aplica", problemas[3])

    def test_archivo_de_reglas_del_proyecto_se_puede_leer(self):
        r = reglas.cargar()
        self.assertIn("PressTheAttack", reglas.claves_usadas(r))
        self.assertIn("Overgrowth", reglas.claves_usadas(r))     # también revisa las excepciones
        self.assertEqual(reglas.claves_arbol_usadas(r), {"Precision", "Resolve", "Domination"})


if __name__ == "__main__":
    unittest.main()
