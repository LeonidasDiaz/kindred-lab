"""Partidas SINTÉTICAS con eventos de match-v5; no usa red."""
import unittest

from kindred_lab import defensivo


def obj(nombre, final=True, botas=False, precio=3000, desc="", componentes=(), **stats):
    return {"metadata": {"nombre": nombre, "final": final, "botas": botas, "precio": precio,
                         "descripcion_legible": desc, "componentes": list(componentes)}, "stats_base": stats}


OBJETOS = {
    "10": obj("Danza", componentes=["23", "22"], Armadura_plana=50),
    "11": obj("Randuin", Armadura_plana=75, Vida_maxima_plana=350),
    "12": obj("Fauces", Resist_Magica_plana=40, desc="Otorga un escudo mágico"),
    "13": obj("Sterak", Vida_maxima_plana=400, desc="Un escudo al bajar de vida"),
    "14": obj("Punteras", final=False, botas=True, Armadura_plana=25),
    "15": obj("Berserker", final=False, botas=True),
    "16": obj("Matakrakens"),
    "17": obj("Sorbechizos", final=False, precio=1300, Resist_Magica_plana=25),
    "18": obj("Escudo de Doran", precio=450, Vida_maxima_plana=110),
    "19": obj("Mixto", Armadura_plana=30, Resist_Magica_plana=30),
    "20": obj("Tela", final=False, precio=300, Armadura_plana=15),
    "21": obj("Cristal", final=False, precio=400, Vida_maxima_plana=150),
    "22": obj("Espada", final=False, precio=350, desc="un escudo", AD_plano=10),
    "23": obj("Cota", final=False, precio=800, componentes=["20", "20"], Armadura_plana=30),
}
SITUACIONES = [
    {"objeto": "Randuin", "aplica": {"campeones_1": ["Sett", "Jhin"]}},
    {"objeto": "Danza", "aplica": {"campeones_1": ["Zed"], "campeones_2": ["Sett"], "perfil": "fisico"}},
    {"objeto": "Fauces", "aplica": {"perfil": "magico"}},
    {"objeto": "Sterak", "aplica": {"perfil": "mezclado"}},
    {"objeto": "Cimitarra", "aplica": {"campeones_1": ["Teemo"]}},
    {"objeto": "Placa", "aplica": {}},
]
CAMPEONES = {"campeones": {"Sett": {"nombre": "Sett", "tipos": ["Fighter", "Tank"]}}}


def golpe(pid, f=0, m=0, v=0, spell="", tipo="OTHER"):
    return {"participantId": pid, "physicalDamage": f, "magicDamage": m, "trueDamage": v, "spellName": spell,
            "type": tipo, "name": "campo poco fiable", "basic": False, "spellSlot": 0}


def muerte(minuto, asesino, *golpes):
    return {"type": "CHAMPION_KILL", "timestamp": minuto * 60_000, "victimId": 1, "killerId": asesino,
            "victimDamageReceived": list(golpes)}


def compra(minuto, item):
    return {"type": "ITEM_PURCHASED", "timestamp": minuto * 60_000, "participantId": 1, "itemId": item}


def frames(eventos, minutos=31):
    salida = [{"timestamp": m * 60_000, "events": [],
               "participantFrames": {str(p): {"totalGold": (1000 + 100 * m if p == 1 else 1000 + 200 * m),
                                              "championStats": {"healthMax": 1000}} for p in range(1, 11)}}
              for m in range(minutos)]
    salida[0]["events"] = eventos
    return {"info": {"frames": salida}}


def partida(version="16.21.1.1", duracion=1800):
    nombres = {6: "Sett", 7: "Syndra", 8: "Jhin", 9: "Zed", 10: "Teemo"}
    gente = [{"participantId": i, "teamId": 100 if i <= 5 else 200, "win": False,
              "championName": "Kindred" if i == 1 else nombres.get(i, f"Aliado{i}")} for i in range(1, 11)]
    return {"metadata": {"matchId": "LA1_1"}, "info": {"gameVersion": version, "gameDuration": duracion,
                                                       "participants": gente}}


class TestClases(unittest.TestCase):
    def test_clase_objeto(self):
        c = lambda i: defensivo.clase_objeto(OBJETOS[i])
        self.assertEqual((c("10"), c("11"), c("12"), c("13"), c("19")), ("fisico", "fisico", "magico", "general", "ambos"))
        self.assertEqual(c("14"), "fisico")                 # botas con armadura, aunque se mejoren
        self.assertIsNone(c("15"))                          # botas sin defensa
        self.assertIsNone(c("16"))                          # objeto de daño
        self.assertIsNone(c("17"))                          # a medio armar
        self.assertIsNone(c("18"))                          # barato: no es defensivo completo
        self.assertIsNone(defensivo.clase_objeto(None))

    def test_clase_componente(self):
        c = lambda i: defensivo.clase_componente(OBJETOS[i])
        self.assertEqual(c("17"), "magico")                 # a medio armar
        self.assertEqual(c("20"), "fisico")                 # barato también: es lo que alcanza
        self.assertEqual(c("21"), "general")                # solo vida
        self.assertIsNone(c("22"))                          # componente de daño, aunque su texto hable de escudo
        self.assertIsNone(c("10"))                          # objeto final
        self.assertIsNone(c("14"))                          # las botas ya cuentan como defensivo
        self.assertIsNone(defensivo.clase_componente(None))

    def test_escudos_de_un_solo_tipo(self):
        for texto in ("obtienes un escudo mágico .", "obtienes un escudo contra daño mágico durante 3 seg",
                      "obtienes un escudo que protege contra 0 de daño mágico durante 5 seg."):
            self.assertEqual(defensivo._defensas(obj("X", desc=texto)), ["escudo mágico"], texto)
            self.assertEqual(defensivo.clase_objeto(obj("X", desc=texto)), "magico", texto)
        texto = "obtienes un escudo que protege contra 0 de daño físico durante 5 seg."
        self.assertEqual(defensivo._defensas(obj("X", desc=texto)), ["escudo físico"])
        self.assertEqual(defensivo.clase_objeto(obj("X", desc=texto)), "fisico")
        # Daño mágico en otra frase: el escudo no es solo mágico
        texto = "Tras recibir daño mágico obtienes un escudo durante 3 seg."
        self.assertEqual(defensivo._defensas(obj("X", desc=texto)), ["escudo"])

    def test_solo_es_escudo_si_te_lo_otorga(self):
        for texto in ("obtienes un escudo que decae", "te otorga un escudo durante 3 seg.",
                      "Otorga un escudo antihechizos que bloquea", "te otorgará 0 de escudo durante 3 seg.",
                      "de 290 a 360 de escudo que decae", "Convierte el exceso de curación en un escudo ."):
            self.assertEqual(defensivo._defensas(obj("X", desc=texto.lower())), ["escudo"], texto)
        for texto in ("8% de poder de curaciones y escudos", "Rompeescudos reduce el escudo que obtenga en un 0%",
                      "Golpe de Escudo de Luz", "Al curar u otorgar escudo a un aliado",
                      "Las curaciones y los escudos que tengas aumentarán", "Curación y Poder de Escudo",
                      "hayas otorgado una curación o un escudo"):
            self.assertEqual(defensivo._defensas(obj("X", desc=texto)), [], texto)
            self.assertIsNone(defensivo.clase_objeto(obj("X", desc=texto)), texto)

    def test_arbol_a_cualquier_profundidad(self):
        self.assertEqual(defensivo.arbol(OBJETOS, 10), {"23", "22", "20"})
        self.assertEqual(defensivo.arbol(OBJETOS, 20), set())
        self.assertEqual(defensivo.arbol(OBJETOS, 999), set())

    def test_compras_con_deshacer_y_vender(self):
        ev = [compra(1, 10), {"type": "ITEM_UNDO", "timestamp": 61_000, "participantId": 1, "beforeId": 10, "afterId": 0},
              compra(2, 11), {"type": "ITEM_SOLD", "timestamp": 180_000, "participantId": 1, "itemId": 11},
              compra(4, 12), {"type": "ITEM_SOLD", "timestamp": 300_000, "participantId": 1, "itemId": 12},
              {"type": "ITEM_UNDO", "timestamp": 301_000, "participantId": 1, "beforeId": 0, "afterId": 12},
              {"type": "ITEM_PURCHASED", "timestamp": 1, "participantId": 2, "itemId": 13}]
        h = defensivo.compras(ev, 1)
        self.assertEqual([(x["id"], x["vendido"]) for x in h], [(11, 180_000), (12, None)])


class TestMuertes(unittest.TestCase):
    def test_desglose_atacantes_y_parcial(self):
        ev = [muerte(5, 6, golpe(6, f=600, v=300, spell="settw"), golpe(7, m=200), golpe(2, f=50),
                     golpe(0, f=100, tipo="TOWER")),
              muerte(9, 0, golpe(0, f=100, tipo="MONSTER"))]
        m = defensivo.muertes(partida(), frames(ev), partida()["info"]["participants"][0])
        self.assertEqual(m[0]["dano"], [750, 200, 300])           # torre y aliado cuentan en el perfil
        self.assertEqual(m[0]["por_enemigo"], {"Sett": [600, 0, 300], "Syndra": [0, 200, 0]})   # como enemigos, no
        self.assertEqual((m[0]["asesino"], m[0]["mas_dano"], m[0]["parcial"]), ("Sett", "Sett", False))
        self.assertEqual(m[1]["asesino"], defensivo.SIN_CAMPEON)
        self.assertIsNone(m[1]["mas_dano"])
        self.assertTrue(m[1]["parcial"])                          # 100 de 1000 de vida

    def test_perfil(self):
        lista = [{"dano": [50, 30, 20]}]
        p = defensivo.perfil(lista)
        self.assertEqual(p["pct"], {"fisico": 50, "magico": 30, "verdadero": 20})
    def test_cumple_perfil(self):
        def cumple(regla, f, m, v):
            return defensivo.cumple_perfil(regla, defensivo.perfil([{"dano": [f, m, v]}]))

        self.assertTrue(cumple("fisico", 56, 39, 5))
        self.assertTrue(cumple("mezclado", 56, 39, 5))           # los dos a la vez
        self.assertTrue(cumple("magico", 40, 55, 5))
        self.assertTrue(cumple("mezclado", 35, 35, 30))
        self.assertFalse(cumple("mezclado", 65, 34, 1))
        self.assertFalse(cumple("fisico", 40, 20, 40))           # mucho verdadero: no llega
        self.assertFalse(cumple("magico", 40, 20, 40))
        self.assertFalse(cumple(None, 100, 0, 0))                # regla sin perfil
        self.assertEqual(defensivo.perfil([])["total"], 0)


class TestCoincidencia(unittest.TestCase):
    def p(self, f, m, v):
        return defensivo.perfil([{"dano": [f, m, v]}, {"dano": [0, 0, 0]}])     # 2 muertes: ya hay datos

    def test_por_tipo_con_umbrales(self):
        self.assertEqual(defensivo.coincide_tipo("fisico", self.p(50, 50, 0)), "sí")
        self.assertEqual(defensivo.coincide_tipo("fisico", self.p(35, 65, 0)), "parcial")
        self.assertEqual(defensivo.coincide_tipo("fisico", self.p(34, 66, 0)), "no")
        self.assertEqual(defensivo.coincide_tipo("magico", self.p(20, 20, 60)), "no")   # el verdadero no cuenta a favor
        self.assertEqual(defensivo.coincide_tipo("ambos", self.p(25, 25, 50)), "sí")
        self.assertEqual(defensivo.coincide_tipo("general", self.p(1, 0, 0)), "general")
        self.assertEqual(defensivo.coincide_tipo("fisico", defensivo.perfil([])), "sin muertes previas")

    def regla(self, objeto, amenaza, enemigos=(), p=None):
        return defensivo.coincide_reglas(objeto, amenaza, list(enemigos), p or self.p(1, 0, 0), SITUACIONES)

    def test_reglas_opciones(self):
        self.assertEqual(self.regla("Randuin", "Sett")["estado"], "1ª opción")
        self.assertEqual(self.regla("Randuin", "SETT")["estado"], "1ª opción")     # sin distinguir mayúsculas
        r = self.regla("Danza", "Sett")
        self.assertEqual((r["estado"], r["detalle"]), ("2ª opción", "contra Sett: 1ª Randuin"))

    def test_una_sola_muerte_previa_son_pocos_datos(self):
        una = defensivo.perfil([{"dano": [58, 42, 0]}])
        self.assertEqual(defensivo.coincide_tipo("fisico", una), "pocos datos")
        self.assertEqual(defensivo.coincide_tipo("general", una), "pocos datos")
        self.assertEqual(self.regla("Sterak", "Syndra", p=una)["estado"], "pocos datos")
        self.assertEqual(self.regla("Randuin", "Sett", ["Sett"], p=una)["estado"], "por rival presente")
        self.assertEqual(self.regla("Fauces", "Sett", ["Sett"], p=una)["estado"], "pocos datos")   # sin "otro objeto"

    def test_lo_que_ya_tenia_no_es_desacuerdo(self):
        r = defensivo.coincide_reglas("Fauces", "Sett", [], self.p(1, 0, 0), SITUACIONES, ("Randuin",))
        self.assertEqual((r["estado"], r["detalle"]), ("ya tenía el indicado", "contra Sett: Randuin"))
        r = defensivo.coincide_reglas("Danza", "Sett", [], self.p(1, 0, 0), SITUACIONES, ("Randuin",))
        self.assertEqual((r["estado"], r["detalle"]), ("2ª opción", "contra Sett: 1ª Randuin (ya la tenías)"))

    def test_reglas_otros_casos(self):
        self.assertEqual(self.regla("Cimitarra", "Sett", ["Teemo", "Sett"])["estado"], "por rival presente")
        self.assertEqual(self.regla("Fauces", "Sett")["estado"], "otro objeto")
        self.assertEqual(self.regla("Fauces", "Syndra", p=self.p(10, 90, 0))["estado"], "por perfil")
        self.assertEqual(self.regla("Fauces", "Syndra", p=self.p(40, 55, 5))["estado"], "por perfil")     # también mezclado
        self.assertEqual(self.regla("Fauces", "Syndra", p=self.p(90, 10, 0))["estado"], "sin coincidencia")
        self.assertEqual(self.regla("Sterak", "Syndra", p=self.p(56, 39, 5))["estado"], "por perfil")
        self.assertEqual(self.regla("Sterak", "Syndra", p=self.p(78, 20, 2))["estado"], "sin coincidencia")
        self.assertEqual(self.regla("Placa", "Sett")["estado"], "no evaluable")
        self.assertEqual(self.regla("Punteras", "Sett")["estado"], "sin regla")
        self.assertEqual(self.regla("Fauces", None, p=defensivo.perfil([]))["estado"], "sin muertes previas")


class TestRetraso(unittest.TestCase):
    def m(self, minuto, nombre, dano):
        return {"t": minuto * 60_000, "mas_dano": nombre, "por_enemigo": {nombre: dano}, "dano": dano}

    def d(self, minuto, clase, nombre="X", vendido=None, defensas=None, arbol=(), botas=False):
        defensas = defensas or {"fisico": ["armadura"], "magico": ["resistencia mágica"], "general": ["vida"]}[clase]
        return {"t": minuto * 60_000, "clase": clase, "nombre": nombre, "vendido": vendido, "defensas": defensas,
                "arbol": set(arbol), "botas": botas}

    def c(self, minuto, clase, nombre, id_="20"):
        d = self.d(minuto, clase, nombre)
        del d["arbol"], d["botas"], d["vendido"]        # un componente no es un defensivo completo
        return {**d, "id": id_}

    def test_sin_dos_muertes_contra_el_mismo(self):
        self.assertIsNone(defensivo.retraso([self.m(5, "A", [1, 0, 0]), self.m(6, "B", [1, 0, 0])], [], 1_800_000))

    def test_comprado_salta_los_que_no_sirven(self):
        lista = [self.m(5, "A", [9, 0, 0]), self.m(10, "A", [9, 0, 0])]
        r = defensivo.retraso(lista, [self.d(12, "magico", "RM"), self.d(16, "fisico", "Armadura")], 1_800_000)
        self.assertEqual((r["enemigo"], r["estado"], r["objeto"], r["minutos"]), ("A", "comprado", "Armadura", 6.0))

    def test_ya_lo_tenia_salvo_si_lo_vendio(self):
        lista = [self.m(5, "A", [9, 0, 0]), self.m(10, "A", [9, 0, 0])]
        self.assertEqual(defensivo.retraso(lista, [self.d(3, "fisico")], 1_800_000)["estado"], "ya lo tenía")
        r = defensivo.retraso(lista, [self.d(3, "fisico", vendido=480_000)], 1_800_000)
        self.assertEqual((r["estado"], r["minutos"]), ("nunca", 20.0))

    def test_primer_componente_util(self):
        lista = [self.m(5, "A", [9, 0, 0]), self.m(10, "A", [9, 0, 0])]
        comps = (self.c(4, "fisico", "Antes"), self.c(11, "magico", "No sirve"), self.c(12, "fisico", "Tela"))
        r = defensivo.retraso(lista, [self.d(16, "fisico", "Danza", arbol=["20"])], 1_800_000, comps)
        self.assertEqual(r["componente"], {"objeto": "Tela", "minutos": 2.0, "estado": "parte del objeto",
                                           "termina": "Danza", "botas": False})
        self.assertEqual((r["objeto"], r["minutos"]), ("Danza", 6.0))

    def test_objeto_entero_cuenta_como_primera_compra(self):
        lista = [self.m(5, "A", [9, 0, 0]), self.m(10, "A", [9, 0, 0])]
        r = defensivo.retraso(lista, [self.d(16, "fisico", "Danza")], 1_800_000)
        self.assertEqual(r["componente"], {"objeto": "Danza", "minutos": 6.0, "estado": "objeto entero",
                                           "termina": "Danza", "botas": False})

    def test_destino_de_la_primera_compra(self):
        lista = [self.m(5, "A", [9, 0, 0]), self.m(10, "A", [9, 0, 0])]

        def destino(*defensivos):
            c = defensivo.retraso(lista, list(defensivos), 1_800_000, (self.c(12, "fisico", "Tela"),))["componente"]
            return (c["estado"], c["termina"], c["botas"])

        self.assertEqual(destino(self.d(16, "magico", "Fauces", arbol=["1033"])), ("otro objeto", None, False))
        self.assertEqual(destino(self.d(16, "fisico", "Punteras", arbol=["20"], botas=True)),
                         ("parte del objeto", "Punteras", True))
        # El objeto que ya estaba terminado antes del componente no es su destino
        self.assertEqual(destino(self.d(11, "magico", "Fauces", arbol=["20"])), ("sin terminar", None, False))

    def test_componente_sin_completar_el_objeto(self):
        lista = [self.m(5, "A", [9, 0, 0]), self.m(10, "A", [9, 0, 0])]
        r = defensivo.retraso(lista, [], 1_800_000, (self.c(13, "fisico", "Tela"),))
        self.assertEqual((r["estado"], r["componente"]), ("nunca", {"objeto": "Tela", "minutos": 3.0, "estado": "sin terminar",
                                                                    "termina": None, "botas": False}))
        self.assertIsNone(defensivo.retraso(lista, [], 1_800_000)["componente"])

    def test_ya_lo_tenia_no_busca_componente(self):
        lista = [self.m(5, "A", [9, 0, 0]), self.m(10, "A", [9, 0, 0])]
        r = defensivo.retraso(lista, [self.d(3, "fisico")], 1_800_000, (self.c(13, "fisico", "Tela"),))
        self.assertIsNone(r["componente"])

    def test_contra_verdadero_cuenta_vida_o_escudo(self):
        lista = [self.m(5, "A", [1, 0, 9]), self.m(10, "A", [1, 0, 9])]

        def primero(*compras_):
            return defensivo.retraso(lista, list(compras_), 1_800_000)["objeto"]

        armadura, rm = self.d(12, "fisico", "Armadura"), self.d(12, "magico", "RM")
        self.assertIsNone(primero(armadura, rm))
        self.assertEqual(primero(armadura, self.d(14, "general", "Vida")), "Vida")
        self.assertEqual(primero(armadura, self.d(14, "general", "Arcoescudo", defensas=["escudo"])), "Arcoescudo")
        self.assertEqual(primero(armadura, self.d(14, "fisico", "Randuin", defensas=["armadura", "vida"])), "Randuin")
        fauces = self.d(14, "magico", "Fauces", defensas=["resistencia mágica", "escudo mágico"])
        self.assertIsNone(primero(armadura, fauces))
        blindadas = self.d(14, "fisico", "Blindadas", defensas=["armadura", "escudo físico"])
        self.assertIsNone(primero(armadura, blindadas))
        rukerno = self.d(14, "magico", "Rukerno", defensas=["resistencia mágica", "vida", "escudo mágico"])
        self.assertEqual(primero(armadura, rukerno), "Rukerno")      # cuenta por su vida

    def test_contra_fisico_sigue_mirando_la_clase(self):
        lista = [self.m(5, "A", [9, 0, 0]), self.m(10, "A", [9, 0, 0])]
        r = defensivo.retraso(lista, [self.d(12, "magico", "RM", defensas=["resistencia mágica", "escudo"]),
                                      self.d(14, "general", "Vida")], 1_800_000)
        self.assertEqual(r["objeto"], "Vida")

    def test_el_tipo_no_mira_lo_que_pasa_despues(self):
        lista = [self.m(5, "A", [9, 0, 0]), self.m(10, "A", [9, 0, 0]), self.m(20, "A", [0, 0, 999])]
        self.assertEqual(defensivo.retraso(lista, [], 1_800_000)["tipo"], "fisico")


class TestAnalizar(unittest.TestCase):
    def setUp(self):
        self.ev = [compra(1, 16), compra(20, 10), compra(22, 15),
                   muerte(5, 6, golpe(6, f=800, v=200, spell="settq")),
                   muerte(10, 6, golpe(6, f=300, v=900, spell="settw"), golpe(7, m=10)),
                   muerte(25, 6, golpe(6, f=64), golpe(7, m=1000, spell="syndrar"))]
        self.p = partida()
        self.yo = dict(self.p["info"]["participants"][0], item0=10, item1=17)
        self.ev.append(compra(27, 17))
        self.r = defensivo.analizar(self.p, frames(self.ev), self.yo, OBJETOS, SITUACIONES, CAMPEONES)

    def test_perfil_y_amenaza(self):
        self.assertEqual(self.r["perfil"]["dano"], {"fisico": 1164, "magico": 1010, "verdadero": 1100})
        a = self.r["amenaza"]
        self.assertEqual((a["nombre"], a["dano"], a["tipos"], a["golpe"]), ("Sett", [1164, 0, 1100], ["Fighter", "Tank"], "settw"))
        self.assertEqual(a["oro"], {"primera": 500, "compra": 2000, "final": 3000})

    def test_coincidencia_solo_con_muertes_anteriores(self):
        d = self.r["defensivos"][0]
        self.assertEqual((d["nombre"], d["t"], d["clase"]), ("Danza", 1_200_000, "fisico"))
        self.assertEqual(d["perfil_antes"]["dano"], {"fisico": 1100, "magico": 10, "verdadero": 1100})   # sin la de los 25
        self.assertEqual(d["tipo"], "parcial")
        self.assertEqual(d["regla"]["estado"], "2ª opción")
        self.assertEqual(d["amenaza_antes"], "Sett")

    def test_efecto_y_amenaza_despues(self):
        d = self.r["defensivos"][0]
        self.assertEqual((d["antes"]["n"], d["antes"]["tasa"]), (2, 1.0))
        self.assertEqual((d["despues"]["n"], d["despues"]["tasa"]), (1, 1.0))
        self.assertEqual(d["contra_amenaza"], {"mas_dano": 0, "ultimo_golpe": 1})      # Sett remata, Syndra hizo el daño

    def test_retraso_y_a_medio_armar(self):
        self.assertEqual((self.r["retraso"]["estado"], self.r["retraso"]["minutos"]), ("comprado", 10.0))
        self.assertEqual(self.r["a_medio_armar"], [{"nombre": "Sorbechizos", "t": 27 * 60_000}])

    def test_poco_tiempo_despues_no_da_tasa(self):
        r = defensivo.analizar(self.p, frames([compra(29, 10)]), self.yo, OBJETOS, SITUACIONES)
        self.assertIsNone(r["defensivos"][0]["despues"]["tasa"])

    def test_vendido_corta_el_efecto(self):
        ev = [compra(10, 10), {"type": "ITEM_SOLD", "timestamp": 15 * 60_000, "participantId": 1, "itemId": 10},
              muerte(20, 6, golpe(6, f=2000))]
        r = defensivo.analizar(self.p, frames(ev), self.yo, OBJETOS, SITUACIONES)
        self.assertEqual((r["defensivos"][0]["despues"]["fin"], r["defensivos"][0]["despues"]["n"]), (15 * 60_000, 0))

    def test_lo_indicado_ya_comprado_o_vendido(self):
        muertes_ = [muerte(5, 6, golpe(6, f=2000)), muerte(8, 6, golpe(6, f=2000))]
        r = defensivo.analizar(self.p, frames(muertes_ + [compra(10, 11), compra(15, 12)]), self.yo, OBJETOS, SITUACIONES)
        self.assertEqual(r["defensivos"][1]["regla"]["estado"], "ya tenía el indicado")
        vendido = [compra(10, 11), {"type": "ITEM_SOLD", "timestamp": 12 * 60_000, "participantId": 1, "itemId": 11}, compra(15, 12)]
        r = defensivo.analizar(self.p, frames(muertes_ + vendido), self.yo, OBJETOS, SITUACIONES)
        self.assertEqual(r["defensivos"][1]["regla"]["estado"], "otro objeto")

    def test_componente_y_objeto_que_lo_contiene(self):
        ev = [muerte(5, 6, golpe(6, f=2000)), muerte(8, 6, golpe(6, f=2000)), compra(10, 20), compra(15, 10)]
        r = defensivo.analizar(self.p, frames(ev), self.yo, OBJETOS, SITUACIONES)
        c = r["retraso"]["componente"]
        self.assertEqual((c["objeto"], c["estado"], c["termina"], c["minutos"]), ("Tela", "parte del objeto", "Danza", 2.0))
        self.assertIn("primera compra útil: 2.0 min, Tela (parte de Danza)",
                      "\n".join(defensivo.texto_partida(r, defensivo.tabla_base([r]))))

    def test_partida_sin_muertes_ni_defensivos(self):
        r = defensivo.analizar(self.p, frames([]), dict(self.yo, item1=0), OBJETOS, SITUACIONES)
        self.assertIsNone(r["amenaza"])
        self.assertIsNone(r["retraso"])
        self.assertIn("No moriste en esta partida.", defensivo.texto_partida(r, {}))

    def test_texto_de_partida(self):
        texto = "\n".join(defensivo.texto_partida(self.r, defensivo.tabla_base([self.r])))
        self.assertIn("AMENAZA PRINCIPAL  Sett (Fighter, Tank): 2264 de daño", texto)
        self.assertIn("según reglas actuales: 2ª opción (contra Sett: 1ª Randuin)", texto)
        self.assertIn("(Sett: 64)", texto)
        self.assertIn("10.0 min hasta Danza", texto)
        self.assertIn("A MEDIO ARMAR  Sorbechizos", texto)
        self.assertNotIn("victoria", texto)


class TestBaseYResumen(unittest.TestCase):
    def r(self, periodo=defensivo.PERIODOS[1], dur=600_000, tiempos=()):
        return {"periodo": periodo, "dur": dur, "muertes": [{"t": t} for t in tiempos]}

    def test_base_pondera_tramos(self):
        tabla = defensivo.tabla_base([self.r(tiempos=[60_000, 400_000, 500_000])])
        self.assertEqual(defensivo.base_en(tabla, defensivo.PERIODOS[1], 0, 300_000), 2.0)       # 1 en 5 min
        self.assertEqual(defensivo.base_en(tabla, defensivo.PERIODOS[1], 300_000, 600_000), 4.0)  # 2 en 5 min
        self.assertEqual(defensivo.base_en(tabla, defensivo.PERIODOS[1], 150_000, 450_000), 3.0)  # mitad y mitad
        self.assertIsNone(defensivo.base_en(tabla, defensivo.PERIODOS[0], 0, 300_000))
        self.assertIsNone(defensivo.base_en(tabla, defensivo.PERIODOS[1], 900_000, 1_000_000))

    def test_tramo_incompleto_cuenta_solo_lo_jugado(self):
        tabla = defensivo.tabla_base([self.r(dur=450_000, tiempos=[400_000])])
        self.assertEqual(defensivo.base_en(tabla, defensivo.PERIODOS[1], 300_000, 450_000), 4.0)   # 1 en 2.5 min

    def test_periodos_por_parche(self):
        self.assertEqual(defensivo._periodo(partida("16.11.1.1")), defensivo.PERIODOS[0])
        self.assertEqual(defensivo._periodo(partida("16.20.1.1")), defensivo.PERIODOS[1])
        self.assertEqual(defensivo._periodo(partida("17.1.1.1")), defensivo.PERIODOS[1])

    def test_resumen_separa_periodos_y_no_da_victorias(self):
        ev = [compra(10, 10), muerte(5, 6, golpe(6, f=1000)), muerte(8, 6, golpe(6, f=1000)), muerte(20, 7, golpe(7, m=1000))]
        yo = partida()["info"]["participants"][0]
        nueva = defensivo.analizar(partida("16.21.1.1"), frames(ev), yo, OBJETOS, SITUACIONES)
        vieja = defensivo.analizar(partida("16.5.1.1"), frames(ev), yo, OBJETOS, SITUACIONES)
        tabla = defensivo.tabla_base([nueva, vieja])
        res = defensivo.resumen([nueva, vieja], tabla)
        self.assertEqual(list(res), list(defensivo.PERIODOS))
        x = res[defensivo.PERIODOS[1]]
        self.assertEqual((x["partidas"], x["muertes"], x["con_defensivo"]), (1, 3, 1))
        f = x["filas"][0]
        self.assertEqual((f["objeto"], f["veces"], f["minuto"], f["antes"]), ("Danza", 1, 10.0, 2.0))
        self.assertEqual(f["despues"], 0.5)
        self.assertEqual((f["base_antes"], f["base_despues"]), (2.0, 0.5))
        self.assertEqual(x["retraso"], {"partidas": 1, "mediana": 2.0, "comprado": 1, "ya": 0, "nunca": 0,
                                        "componente_partidas": 1, "componente_mediana": 2.0, "sin_respuesta": 0,
                                        "destinos": {"objeto entero": 1}, "en_botas": 0})
        texto = "\n".join(defensivo.texto_resumen(res))
        self.assertIn("Danza*", texto)
        self.assertNotIn("victoria", texto.lower())
