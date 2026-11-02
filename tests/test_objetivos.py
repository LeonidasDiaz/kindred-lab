"""Partida SINTÉTICA con eventos de objetivos de match-v5; no usa red."""
import unittest

from kindred_lab import objetivos


class TestObjetivos(unittest.TestCase):
    def setUp(self):
        parts = [{"participantId": i, "teamId": 100 if i <= 5 else 200, "win": True} for i in range(1, 11)]
        self.partida = {"metadata": {"matchId": "LA1_1"}, "info": {"participants": parts}}
        self.yo = parts[0]
        ev = [
            {"type": "ELITE_MONSTER_KILL", "timestamp": 300_000, "monsterType": "DRAGON", "killerTeamId": 200, "killerId": 6},
            {"type": "ELITE_MONSTER_KILL", "timestamp": 400_000, "monsterType": "HORDE", "killerId": 2},
            {"type": "TURRET_PLATE_DESTROYED", "timestamp": 500_000, "teamId": 200},
            {"type": "BUILDING_KILL", "timestamp": 900_000, "buildingType": "TOWER_BUILDING", "teamId": 100},
            {"type": "ELITE_MONSTER_KILL", "timestamp": 1_000_000, "monsterType": "DRAGON", "killerTeamId": 100, "killerId": 1},
            {"type": "ELITE_MONSTER_KILL", "timestamp": 1_500_000, "monsterType": "BARON_NASHOR", "killerTeamId": 100, "killerId": 3},
            {"type": "BUILDING_KILL", "timestamp": 1_600_000, "buildingType": "TOWER_BUILDING", "teamId": 200},
            {"type": "CHAMPION_KILL", "timestamp": 100_000, "victimId": 1},
        ]
        self.timeline = {"info": {"frames": [{"timestamp": 0, "events": ev}]}}

    def test_contar(self):
        r = objetivos.contar(self.partida, self.timeline, self.yo)
        self.assertEqual(r["dragones"], (1, 1))
        self.assertEqual(r["larvas"], (1, 0))            # equipo por killerId si falta killerTeamId
        self.assertEqual(r["placas"], (1, 0))             # placa del enemigo (teamId 200) = nuestra
        self.assertEqual(r["torres"], (1, 1))
        self.assertEqual(r["baron"], (1, 0))
        self.assertEqual(r["primer_dragon"], ("ellos", 5))
        self.assertEqual(r["primer_baron"], ("nosotros", 25))

    def test_hasta_minuto(self):
        r = objetivos.contar(self.partida, self.timeline, self.yo, minuto=10)
        self.assertEqual((r["dragones"], r["baron"], r["torres"]), ((0, 1), (0, 0), (0, 0)))

    def test_totales(self):
        r = objetivos.contar(self.partida, self.timeline, self.yo)
        p = dict(r, resultado="derrota", baron=(0, 1), primer_baron=("ellos", 22))
        t = objetivos.totales([r, p])
        self.assertEqual(t["victoria"]["baron"], 1)
        self.assertEqual(t["derrota"]["baron"], -1)
        self.assertEqual(t["primer_baron"], {"nosotros": (1, 1), "ellos": (1, 0)})


if __name__ == "__main__":
    unittest.main()
