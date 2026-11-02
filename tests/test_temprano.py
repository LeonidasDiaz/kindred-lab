"""Partida SINTÉTICA con la forma de match-v5 y su timeline; no usa red."""
import unittest

from kindred_lab import temprano


def jugador(pid, equipo, campeon, pos, win, nombre="X", tag="LAN"):
    return {"participantId": pid, "teamId": equipo, "championName": campeon, "teamPosition": pos,
            "win": win, "puuid": f"p{pid}", "riotIdGameName": nombre, "riotIdTagline": tag}


class TestTemprano(unittest.TestCase):
    def setUp(self):
        aliados = [jugador(1, 100, "Kindred", "JUNGLE", False, "Cazador Eterno", "LAN")] + \
                  [jugador(i, 100, f"A{i}", "TOP", False) for i in range(2, 6)]
        enemigos = [jugador(6, 200, "Briar", "JUNGLE", True)] + \
                   [jugador(i, 200, f"E{i}", "MIDDLE", True) for i in range(7, 11)]
        self.partida = {"metadata": {"matchId": "LA1_9"}, "info": {"participants": aliados + enemigos}}
        ev = [
            {"type": "CHAMPION_KILL", "timestamp": 200_000, "victimId": 2, "killerId": 6, "assistingParticipantIds": []},
            {"type": "CHAMPION_KILL", "timestamp": 300_000, "victimId": 3, "killerId": 7, "assistingParticipantIds": [6]},
            {"type": "CHAMPION_KILL", "timestamp": 400_000, "victimId": 4, "killerId": 8, "assistingParticipantIds": []},
            {"type": "CHAMPION_KILL", "timestamp": 450_000, "victimId": 1, "killerId": 9, "assistingParticipantIds": []},
            {"type": "CHAMPION_KILL", "timestamp": 500_000, "victimId": 6, "killerId": 1, "assistingParticipantIds": [2]},
            {"type": "CHAMPION_KILL", "timestamp": 550_000, "victimId": 7, "killerId": 5, "assistingParticipantIds": []},
            {"type": "CHAMPION_KILL", "timestamp": 700_000, "victimId": 2, "killerId": 6, "assistingParticipantIds": []},
            {"type": "WARD_PLACED", "timestamp": 100_000},
        ]
        def pf(pos, dano):
            d = {str(i): {"totalGold": 3000 if i <= 5 else 3200} for i in range(1, 11)}
            d["1"].update(position=pos, damageStats={"totalDamageDoneToChampions": dano})
            return d
        posiciones = [(7000, 3000), (7400, 7300), (1000, 9000), (13500, 6000), (9000, 4500)]  # jungla, mid, top, bot, jungla
        frames = [{"timestamp": 0, "events": ev[:2], "participantFrames": pf({"x": 500, "y": 500}, 0)}]
        for n, (x, y) in enumerate(posiciones, start=1):
            frames.append({"timestamp": n * 60_000, "events": [], "participantFrames": pf({"x": x, "y": y}, n * 100)})
        frames.append({"timestamp": 600_000, "events": ev[2:], "participantFrames": pf({"x": 500, "y": 500}, 1234)})
        self.timeline = {"info": {"frames": frames}}

    def test_buscar_yo_por_riot_id(self):
        yo = temprano.buscar_yo(self.partida, riot_id="cazador eterno#lan")
        self.assertEqual(yo["championName"], "Kindred")
        with self.assertRaises(KeyError):
            temprano.buscar_yo(self.partida, riot_id="Otro#LAN")

    def test_buscar_yo_sin_espacios(self):
        # Riot no distingue espacios: "CazadorEterno" en secretos.json encuentra a "Cazador Eterno"
        yo = temprano.buscar_yo(self.partida, riot_id="CazadorEterno#LAN")
        self.assertEqual(yo["championName"], "Kindred")

    def test_analizar(self):
        yo = temprano.buscar_yo(self.partida, riot_id="Cazador Eterno#LAN")
        r = temprano.analizar(self.partida, self.timeline, yo)
        self.assertEqual(r["jungla_enemigo"], "Briar")
        self.assertEqual(r["muertes_equipo"], 4)          # la del min 11:40 no cuenta
        self.assertEqual(r["con_jungla_enemigo"], 2)      # como asesino y como asistencia
        self.assertEqual(r["mias"], 1)
        self.assertEqual((r["bajas_equipo"], r["mis_participaciones"]), (2, 1))
        self.assertEqual(r["dif_oro"], 5 * 3000 - 5 * 3200)

    def test_dano_a_campeones(self):
        yo = temprano.buscar_yo(self.partida, riot_id="Cazador Eterno#LAN")
        r = temprano.analizar(self.partida, self.timeline, yo)
        self.assertEqual(r["dano_campeones"], 1234)        # el del frame del minuto 10
        self.assertNotIn("min_carril", r)

    def test_jungla_por_castigo(self):
        for p in self.partida["info"]["participants"]:
            p.pop("teamPosition")
        self.partida["info"]["participants"][7]["summoner2Id"] = 11
        self.assertEqual(temprano.jungla_enemigo(self.partida, 100)["championName"], "E8")

    def test_totales(self):
        yo = temprano.buscar_yo(self.partida, riot_id="Cazador Eterno#LAN")
        r = temprano.analizar(self.partida, self.timeline, yo)
        t = temprano.totales([r, dict(r, resultado="victoria", dif_oro=500)])
        self.assertEqual((t["pct_con_jungla"], t["pct_participacion"]), (50, 50))
        self.assertEqual((t["atras"], t["victorias_atras"], t["adelante"], t["victorias_adelante"]), (1, 0, 1, 1))
        self.assertEqual(t["por_resultado"]["victoria"]["dano"], 1234)
        self.assertEqual(t["por_resultado"]["derrota"]["participacion"], 50)


if __name__ == "__main__":
    unittest.main()
