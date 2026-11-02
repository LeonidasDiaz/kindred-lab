"""Partida SINTÉTICA con frames de match-v5; no usa red."""
import unittest

from kindred_lab import momentos


def frame(ms, oro_azul, oro_rojo, eventos=()):
    pf = {str(i): {"totalGold": oro_azul if i <= 5 else oro_rojo} for i in range(1, 11)}
    return {"timestamp": ms, "participantFrames": pf, "events": list(eventos)}


class TestMomentos(unittest.TestCase):
    def setUp(self):
        parts = [{"participantId": i, "teamId": 100 if i <= 5 else 200, "win": False} for i in range(1, 11)]
        self.partida = {"metadata": {"matchId": "LA1_1"}, "info": {"participants": parts}}
        self.yo = parts[0]
        muerte = {"type": "CHAMPION_KILL", "timestamp": 420_000, "victimId": 1, "killerId": 6,
                  "position": {"x": 4500, "y": 7600}}               # tu jungla (lado azul)
        baja = {"type": "CHAMPION_KILL", "timestamp": 200_000, "victimId": 7, "killerId": 2,
                "assistingParticipantIds": [1]}
        frames = [frame(m * 60_000, 500 + 100 * m, 500 + 100 * m) for m in range(0, 5)]
        frames += [frame(5 * 60_000, 1000, 1000)]                     # 0 de diferencia al 5
        frames += [frame(m * 60_000, 1000 + 100 * m, 1100 + 100 * m) for m in range(6, 11)]  # -100 por jugador = -500 de equipo al 10
        frames += [frame(m * 60_000, 2000, 2200) for m in range(11, 13)]
        frames[3]["events"].append(baja)
        frames[7]["events"].append(muerte)
        self.timeline = {"info": {"frames": frames}}

    def test_analizar(self):
        r = momentos.analizar(self.partida, self.timeline, self.yo)
        t = {x["tramo"]: x for x in r["tramos"]}
        self.assertEqual(list(t), ["0-5", "5-10", "10-15"])          # la partida dura 12 min
        self.assertEqual((t["0-5"]["participaciones"], t["0-5"]["cambio_oro"]), (1, 0))
        self.assertEqual((t["5-10"]["muertes"], t["5-10"]["en_mi_jungla"]), (1, 1))
        self.assertEqual(t["5-10"]["cambio_oro"], -500)
        self.assertIsNone(t["10-15"]["oro_fin"])                      # no llegó al minuto 15

    def test_totales(self):
        r = momentos.analizar(self.partida, self.timeline, self.yo)
        tot = momentos.totales([r])
        self.assertEqual(tot["5-10"]["derrota"]["muertes"], 1)
        self.assertEqual(tot["volteo_derrotas"]["5-10"], 1)
        self.assertEqual(tot["0-5"]["victoria"]["partidas"], 0)


if __name__ == "__main__":
    unittest.main()
