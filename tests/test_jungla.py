"""Partida SINTÉTICA con eventos de match-v5; no usa red."""
import unittest

from kindred_lab import jungla


class TestJungla(unittest.TestCase):
    def setUp(self):
        parts = [{"participantId": i, "teamId": 100 if i <= 5 else 200, "win": False, "championName": f"Campeon{i}"}
                 for i in range(1, 11)]
        parts[0].update(visionScore=60, visionWardsBoughtInGame=4, wardsKilled=7)
        self.partida = {"metadata": {"matchId": "LA1_1"}, "info": {"participants": parts}}
        self.yo = parts[0]
        ev = [
            {"type": "WARD_PLACED", "timestamp": 1_250_000, "creatorId": 1, "wardType": "YELLOW_TRINKET"},
            {"type": "WARD_PLACED", "timestamp": 1_280_000, "creatorId": 1, "wardType": "CONTROL_WARD"},
            {"type": "WARD_PLACED", "timestamp": 1_280_000, "creatorId": 2, "wardType": "CONTROL_WARD"},
            {"type": "WARD_PLACED", "timestamp": 1_290_000, "creatorId": 1, "wardType": "UNDEFINED"},
            # muerte cara: 60 s antes del Barón enemigo, en el río
            {"type": "CHAMPION_KILL", "timestamp": 1_260_000, "victimId": 1, "killerId": 7,
             "position": {"x": 5000, "y": 10000}},
            # muerte normal, en la jungla enemiga (lado rojo, fuera de carriles y río)
            {"type": "CHAMPION_KILL", "timestamp": 600_000, "victimId": 1, "killerId": 8,
             "position": {"x": 10500, "y": 7000}},
            {"type": "ELITE_MONSTER_KILL", "timestamp": 1_320_000, "monsterType": "BARON_NASHOR", "killerTeamId": 200},
            {"type": "ELITE_MONSTER_KILL", "timestamp": 300_000, "monsterType": "DRAGON", "killerTeamId": 100},
        ]
        self.timeline = {"info": {"frames": [{"timestamp": 0, "events": ev}]}}

    def test_zonas(self):
        self.assertEqual(jungla.zona(300, 300, 100), "base")
        self.assertEqual(jungla.zona(7400, 7300, 100), "carril")
        self.assertEqual(jungla.zona(5000, 10000, 100), "río")
        self.assertEqual(jungla.zona(10500, 7000, 100), "jungla enemiga")
        self.assertEqual(jungla.zona(10500, 7000, 200), "tu jungla")
        self.assertEqual(jungla.zona(4500, 7600, 100), "tu jungla")

    def test_analizar(self):
        r = jungla.analizar(self.partida, self.timeline, self.yo, 30.0)
        self.assertEqual(r["vision_min"], 2.0)
        self.assertEqual((r["balizas"], r["destruidos"]), (4, 7))
        self.assertEqual((r["objetivos"], r["centinelas_antes"]), (2, 2))   # 2 propios antes del Barón; UNDEFINED no cuenta
        self.assertEqual((r["muertes"], r["muertes_caras"]), (2, 1))
        self.assertEqual(r["donde"]["río"], 1)
        self.assertEqual(r["donde"]["jungla enemiga"], 1)

    def test_muertes(self):
        lista = jungla.muertes(self.partida, self.timeline, self.yo)
        self.assertEqual(lista, [
            {"minuto": "10:00", "zona": "jungla enemiga", "asesino": "Campeon8", "cara": None},
            {"minuto": "21:00", "zona": "río", "asesino": "Campeon7", "cara": "BARON_NASHOR"},
        ])

    def test_muertes_sin_campeon(self):
        # killerId 0 = torre, súbditos o monstruo; sin posición, zona desconocida
        self.timeline["info"]["frames"][0]["events"].append(
            {"type": "CHAMPION_KILL", "timestamp": 95_500, "victimId": 1, "killerId": 0})
        primera = jungla.muertes(self.partida, self.timeline, self.yo)[0]
        self.assertEqual(primera["minuto"], "1:35")
        self.assertEqual(primera["zona"], "?")
        self.assertEqual(primera["asesino"], jungla.SIN_CAMPEON)
        self.assertIsNone(primera["cara"])

    def test_totales(self):
        r = jungla.analizar(self.partida, self.timeline, self.yo, 30.0)
        t = jungla.totales([r])
        self.assertEqual(t["derrota"]["centinelas_por_objetivo"], 1.0)
        self.assertEqual(t["derrota"]["muertes_caras"], 1)
        self.assertEqual(t["victoria"]["partidas"], 0)


if __name__ == "__main__":
    unittest.main()
