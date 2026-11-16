"""Paginación de ids de partidas con una API falsa; no usa red ni clave."""
import unittest
import urllib.parse
from unittest import mock

from kindred_lab import riot


class ApiFalsa:
    """Historial de la cola, de la más reciente a la más vieja; registra cada página pedida."""

    def __init__(self, n):
        self.historial = [f"LA1_{1000 - i}" for i in range(n)]
        self.paginas = []

    def __call__(self, url):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        inicio, cuantos = int(q["start"][0]), int(q["count"][0])
        self.paginas.append((inicio, cuantos))
        return self.historial[inicio:inicio + cuantos]


class TestIdsNuevas(unittest.TestCase):
    def pedir(self, api, conocidos, maximo=100):
        with mock.patch.object(riot, "_get", api):
            return riot.ids_nuevas("puuid", set(conocidos), maximo, pagina=20)

    def test_se_detiene_en_la_primera_registrada(self):
        api = ApiFalsa(300)
        ids, motivo = self.pedir(api, {"LA1_975", "LA1_900"})
        self.assertEqual((len(ids), ids[0], ids[-1], motivo), (25, "LA1_1000", "LA1_976", "conocida"))
        self.assertEqual(api.paginas, [(0, 20), (20, 20)])       # no pide más de lo necesario

    def test_mas_de_10_partidas_nuevas_no_se_pierden(self):
        ids, motivo = self.pedir(ApiFalsa(300), {"LA1_950"})
        self.assertEqual((len(ids), motivo), (50, "conocida"))

    def test_limite_sin_encontrar_ninguna(self):
        api = ApiFalsa(300)
        ids, motivo = self.pedir(api, {"LA1_1"}, maximo=50)
        self.assertEqual((len(ids), motivo), (50, "limite"))
        self.assertEqual(api.paginas, [(0, 20), (20, 20), (40, 10)])

    def test_historial_agotado(self):
        ids, motivo = self.pedir(ApiFalsa(30), set())
        self.assertEqual((len(ids), motivo), (30, "fin"))

    def test_completo_rellena_huecos_detras_de_las_registradas(self):
        api = ApiFalsa(100)
        conocidos = {f"LA1_{n}" for n in range(1000, 900, -1)} - {"LA1_990", "LA1_930"}     # dos huecos
        with mock.patch.object(riot, "_get", api):
            ids, motivo = riot.ids_nuevas("puuid", conocidos, 80, pagina=20, completo=True)
        self.assertEqual((ids, motivo), (["LA1_990", "LA1_930"], "limite"))
        self.assertEqual(api.paginas, [(0, 20), (20, 20), (40, 20), (60, 20)])

    def test_completo_hasta_el_fin_del_historial(self):
        with mock.patch.object(riot, "_get", ApiFalsa(30)):
            ids, motivo = riot.ids_nuevas("puuid", {"LA1_1000"}, 100, pagina=20, completo=True)
        self.assertEqual((len(ids), ids[0], motivo), (29, "LA1_999", "fin"))

    def test_id_repetido_entre_paginas_cuenta_una_vez(self):
        api = ApiFalsa(60)

        def con_desfase(url):           # terminó una partida entre la 1ª y la 2ª página: todo se corre un lugar
            lote = api(url)
            return ([api.historial[19]] + lote[:-1]) if lote and lote[0] == api.historial[20] else lote

        with mock.patch.object(riot, "_get", con_desfase):
            ids, _ = riot.ids_nuevas("puuid", set(), 40, pagina=20)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 39)

    def test_la_mas_reciente_ya_registrada(self):
        ids, motivo = self.pedir(ApiFalsa(30), {"LA1_1000"})
        self.assertEqual((ids, motivo), ([], "conocida"))


class TestCache(unittest.TestCase):
    def setUp(self):
        import tempfile
        from pathlib import Path
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.dir = Path(d.name)

    def test_guarda_y_reusa_sin_volver_a_pedir(self):
        api = mock.Mock(return_value={"metadata": {"matchId": "LA1_1"}})
        with mock.patch.object(riot, "_get", api):
            self.assertEqual(riot.partida("LA1_1", raw_dir=self.dir), {"metadata": {"matchId": "LA1_1"}})
            self.assertEqual(riot.partida("LA1_1", raw_dir=self.dir), {"metadata": {"matchId": "LA1_1"}})
        self.assertEqual(api.call_count, 1)
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()), ["LA1_1.json"])

    def test_corte_a_media_escritura_no_deja_cache(self):
        api = mock.Mock(return_value={"info": {"frames": [1, 2, 3]}})
        with mock.patch.object(riot, "_get", api), \
                mock.patch.object(riot.os, "fsync", side_effect=OSError("se fue la luz")):
            with self.assertRaises(OSError):
                riot.timeline("LA1_1", raw_dir=self.dir)
        self.assertEqual(list(self.dir.iterdir()), [])            # ni JSON truncado ni .tmp
        with mock.patch.object(riot, "_get", api):
            self.assertEqual(riot.timeline("LA1_1", raw_dir=self.dir), {"info": {"frames": [1, 2, 3]}})
        self.assertEqual(api.call_count, 2)                       # se vuelve a pedir: no había caché a medias


if __name__ == "__main__":
    unittest.main()
