# Kindred: reglas y hallazgos

Lo que hemos aprendido con tus partidas y con `kindred-lab`. Datos al 29/10/2026: 97 partidas de Solo/Dúo
con Kindred (febrero a octubre de 2026; 93 sin remakes ni excluidas, 86 de más de 20 minutos), parche 16.21
(los datos de objetos vienen del parche 16.15.1, confirma en la tienda). Las secciones con fecha anterior
usan menos partidas: son **tendencias**, no reglas definitivas.

**En una línea:** pierdes cuando mueres en tu jungla entre el minuto 10 y el 30 y cuando el enemigo se lleva
el Barón o el 4º dragón. Las runas mueven el resultado mucho menos que eso.

---

## 1. Rutina después de cada partida

```powershell
python -m kindred_lab partidas importar --cantidad 10
python -m kindred_lab partidas anotar ultima --alcance si      # o no; --excluir si fue una partida rara
python -m kindred_lab partidas resumen
python -m kindred_lab temprano --minuto 5
python -m kindred_lab momentos          # cada ~10 partidas: en qué tramo se tuercen tus derrotas
```

- Atajo: `.\rutina.ps1` hace las tres primeras (importa, te pregunta `alcance` y una nota opcional, y muestra
  el resumen), después muestra tus muertes de esa partida (`jungla --ultima`: minuto, zona, quién te mató y si
  fue cara) y al final hace commit de `registro/partidas.csv`. Si la importación falla o no hay partida nueva,
  no anota nada.
- Primero `importar`, después `anotar`: si no, `ultima` apunta a la partida anterior.
- `--alcance` es lo que **decidiste en la selección**, no lo que pasó (eso ya lo guarda `muertes_antes_min10`).
- No vacíes el CSV para reimportar: perderías tus anotaciones.
- Cada parche nuevo: `runas actualizar` y `reglas validar`.

Detalle de todos los comandos en [uso.md](uso.md).

---

## 2. Reglas de runas

**Fijas:** Precisión + Triunfo + Leyenda: Celeridad.

**Pregunta 1: ¿alguien te puede alcanzar sin fallar en los primeros 5 minutos?**

| ¿Te alcanzan sin fallar? | Secundaria | Fila 3 de Precisión |
|---|---|---|
| Sí: alguien te alcanza sin fallar | **Valor**: Coraza Ósea (AD) o Acondicionamiento (AP) + Inquebrantable | **La Última Batalla** |
| No: nadie | **Daño**: Dominación (Impacto Súbito + Cazador de Tesoros), o Brujería mientras dura la prueba | **Corte** |

**Valor solo si alguien te alcanza sin fallar:** una habilidad que no se puede esquivar, como la W de Pantheon, el R
de Jarvan o la W de Ryze. Si nadie te alcanza así, ve a daño (Brujería mientras dura la prueba; Dominación contra
mucho poke), aunque el jungla enemigo sea de presión temprana. Valor "por si acaso" te quita las partidas donde el
daño rinde. Ejemplo: el 30/10, contra Viego, Lux y Seraphine, elegiste Valor sin que nadie te
alcanzara sin fallar.

**Pregunta 2 (solo con Valor): ¿qué daño te mata temprano?** AD → Coraza Ósea. AP → Acondicionamiento.
Acondicionamiento no actúa hasta el minuto 12; si el peligro temprano es AD (p. ej. Lee Sin), Coraza Ósea.

**Pregunta 3: ¿cómo serán las peleas?** Estrategia Ofensiva por defecto; Cadencia Letal solo en peleas
largas contra tanques.

**Excepciones (hipótesis, probar al menos 5 partidas):**
- Daño verdadero importante (Maestro Yi, Vayne, Fiora, Camille): **Crecimiento Excesivo** en lugar de
  Inquebrantable. La vida sirve contra daño verdadero y agranda el escudo de Sterak.
- Asesinos con poco control: Crecimiento Excesivo también puede rendir más que Inquebrantable.
- Equipo casi todo de tanques sin burst: Corte aun con Valor.

**Fragmento de defensa (hipótesis):**
- Valor (te alcanzan temprano): **vida plana (65)**.
- Dominación (nadie te alcanza): **vida escalable (10 a 180 según nivel)**; supera a la plana hacia el nivel 7 y
  también agranda el escudo de Sterak. Confirma los valores en el cliente.
- Mucho control que no sea levantamiento ni supresión: **tenacidad 15%**. Las fuentes de tenacidad se multiplican
  (Mercurio + fragmento = 40.5%, no 45%) y no reducen levantamientos, supresión ni estasis.

**Mecánicas que aprendimos:**
- Coraza Ósea y Acondicionamiento están en la misma fila: no se combinan. Revitalizar, Inquebrantable y
  Crecimiento Excesivo también comparten fila.
- Revitalizar infla sus números: su "curación adicional" (≈10% de tu curación total) incluye la curación de tu
  definitiva sobre aliados **y enemigos**. No mide tu supervivencia.
- Recuerdos Macabros: hasta 18 recuerdos = 108 de aceleración de baratija (52% menos enfriamiento). El
  enfriamiento base depende del **nivel promedio de todos los campeones**: con 18 recuerdos y todos en nivel 18,
  centinela cada ~43 s y lente cada ~48 s.
- Velocidad de ataque máxima: 3.0. Cadencia Letal no la supera.
- Las dos secundarias tienen que ser de **filas distintas**. En Brujería, Caminata Sobre Agua y Tormenta
  Creciente están las dos en la fila 3: no se combinan.
- **Impacto Súbito** (daño verdadero 4 s después de un desplazamiento): tu Q lo activa en cada pelea.
- **Cazador de Tesoros** con 5 acumulaciones ≈ 450 de oro ≈ 13 de AD, repartido a mitad de partida. Ayuda poco.

### Lo que dicen tus datos (86 partidas de más de 20 min, 29/10)

| Secundaria | Partidas | Victorias |
|---|---|---|
| Dominación | 51 | 30 (59%) |
| Valor | 28 | 12 (43%) |
| Inspiración | 6 | 2 (33%) |

| Runa | Partidas | Victorias |
|---|---|---|
| Impacto Súbito | 30 | 19 (63%) |
| Golpe Bajo | 11 | 5 (45%) |
| Cazador de Tesoros | 43 | 25 (58%) |
| Cadencia Letal | 16 | 10 (62%) |
| Estrategia Ofensiva | 69 | 34 (49%) |
| Corte | 58 | 31 (53%) |
| La Última Batalla | 22 | 11 (50%) |

**Cuidado al leerlo: se mezclan épocas.** El 59% de Dominación viene casi todo de marzo (20 de 28, una buena racha).
En el mismo mes la diferencia casi desaparece: **octubre, Valor 13 de 29 (45%) y Dominación 6 de 11 (55%)**, y en
octubre Dominación solo va en partidas donde nadie te alcanza. **No hay evidencia de que una secundaria gane más que
la otra.** Se queda la regla de la Pregunta 1, con Impacto Súbito en lugar de Recuerdos Macabros (la visión no
separa tus victorias de tus derrotas; ver sección 5).

Brujería (Caminata Sobre Agua + Concentración Absoluta) no aparece en ninguna partida de Solo/Dúo importada.

### Datos anteriores (16 partidas con runas, 23/10)

| Runa | Partidas | Victorias | Valor medio | Por minuto |
|---|---|---|---|---|
| Estrategia Ofensiva | 15 | 9 | 3,716 de daño | 109 |
| La Última Batalla | 13 | 7 | 2,497 de daño | 73 |
| Corte | 2 | 2 | 2,332 de daño | 67 |
| Golpe de Gracia | 1 | 0 | 536 de daño | 20 |
| Cadencia Letal | 1 | 0 | 320 de daño | 12 |
| Triunfo | 16 | 9 | 1,358 de curación | 41 |
| Coraza Ósea | 11 | 6 | 1,027 bloqueados | 30 |
| Inquebrantable | 11 | 5 | 88 s con resistencias | – |
| Crecimiento Excesivo | 2 | 2 | 172 de vida | – |

- Estrategia Ofensiva es tu runa más fuerte. Golpe de Gracia y Cadencia Letal rindieron muy poco.
- La Última Batalla rinde más en derrotas (pasas más tiempo con poca vida); por eso su número no la compara
  justamente con Corte, que viene de otro tipo de partida.
- Inquebrantable rinde contra mucho control (≈108 s vs Rengar, Akali, Nautilus) y poco contra asesinos de burst
  (≈61 s vs Zed, Talon, Pantheon).
- Con Dominación, todas tus runas dependen de derribos: si la partida sale mal desde el inicio, no te queda nada.
  Valor es un seguro; Dominación, una apuesta.

---

## 3. Objetos defensivos

Lista completa y editable en [`reglas/kindred_objetos.json`](../reglas/kindred_objetos.json).

| Contra | Objeto | Estado |
|---|---|---|
| Sobre todo críticos (Caitlyn, Jhin); su pasiva no hace nada contra habilidades | Presagio de Randuin | probado |
| Luchadores que se pegan (Darius, Mundo, Garen, Sett, Aatrox) | Randuin; segunda opción, Danza de la Muerte (por AD, armadura y curación con derribos) | Danza: hipótesis |
| Daño mágico repartido o un combo AP | Fauces de Malmortius | probado |
| Una habilidad que abre el combo: asesinos AD (Zed, Talon, Pantheon, Kha'Zix, Qiyana), atadura, marca | Filo de la Noche | probado |
| Supresión (Malzahar, Warwick, Urgot) o ceguera (Teemo) | Cimitarra Mercurial | probado |
| Mago AP muy fedeado | Rukerno Kaénico | hipótesis |
| AP con control, solo si vas atrás y sin otra RM | Al Filo de la Cordura | dudoso (3 partidas: quita daño frente al Rey Arruinado; el 02/11 sobró RM y faltó armadura). Las 3 son anteriores al arreglo del parche 26.22 ("Wit's End: Fixed failing to maintain 4 stacks", notas oficiales): no miden el objeto arreglado |
| Daño mezclado o mucho control | Guantelete de Sterak | hipótesis |
| Equipo casi todo AD, o asesinos AD que te matan de golpe | Danza de la Muerte | hipótesis: hay que probarla |
| 2+ asesinos AD con poco control | Placa Hexperimental | hipótesis (neutral en 1 partida) |
| Peleas en grupo donde aprovechan tu reaparición | Ángel Guardián | hipótesis |

**Reglas de decisión:**
- **La selección decide runas y primer defensivo; el marcador, los siguientes.** Lo que lees del equipo enemigo en
  la selección elige tus runas y tu primer objeto defensivo. Los siguientes se deciden por quién te está pegando
  (marcador), porque el campeón engaña: el 02/11 el equipo parecía "de AP" (Lissandra, Fiddlesticks, Lux) y
  recibiste 74% de daño AD.
- **Defensivo contra AD:**
  - Críticos → **Randuin**. Su pasiva no hace nada contra habilidades.
  - Luchadores que se pegan (Darius, Mundo, Garen, Sett, Aatrox) → **Randuin**; segunda opción, **Danza de la Muerte**
    (por AD, armadura y curación con derribos).
  - Asesinos AD con habilidades (Zed, Talon, Pantheon, Kha'Zix, Qiyana) → **Filo de la Noche** si una habilidad
    abre el combo; **Danza de la Muerte** si te matan de golpe.
  - Danza sigue en hipótesis: hay que probarla.
- **Fauces o Cordura:** ¿te matan de un combo? → Fauces. ¿Te controlan y te bajan poco a poco? → Cordura.
  ¿Ya llevas Sterak? → Cordura (Fauces y Sterak son Salvavidas, no se combinan).
- **Objetos sin daño** solo cuando su efecto no lo da ningún objeto con daño: Randuin (críticos y ralentización)
  y Rukerno (mago fedeado). Contra asesinos de letalidad, Randuin rinde poco.
- **Contra asesinos que te atrapan solo**, Ángel Guardián solo alarga tu muerte: mejor evitar la atrapada
  (visión, Filo de la Noche) o aguantar el combo (vida).
- **Si un mismo enemigo te mata 2 o 3 veces,** el siguiente objeto es contra él y en las peleas te colocas lejos de él.
- **Vuelve a preguntar "¿quién me mata?" en cada vuelta a base.** Si un enemigo se dispara (Katarina con
  cargas de Mejai, Viego con sus bajas), tu siguiente defensivo responde a esa persona. Rukerno Kaénico no es
  Salvavidas: se combina con Sterak (Fauces no).
- **Recordatorio Mortal en lugar de Lord Dominik** contra quien se cura mucho (Briar, Mundo, Maestro Yi, Sylas, Zac).
- **Filo del Infinito:** su salto llega con el crítico acumulado (25% + 25% con Dominik). Si vas adelante,
  cómpralo en 3º o 4º; si vas parejo o atrás, defensivo en 3º. Contra AP, Cordura en 3º te da las dos cosas.
- Con Matakrakens, Rey Arruinado, Cordura, Leyenda y botas de velocidad sigues bajo el límite de 3.0
  (≈2.5 con tu Q y 10 marcas).

---

### Hechizos de invocador
- **Contra asesinos (Zed, Talon, Fizz, Katarina, Naafiri): Destello.** Confirmado por tu experiencia: con Fantasma
  contra Talon y Fizz moriste 2 veces antes del minuto 5.
- **Fantasma: en prueba** contra peleadores cuerpo a cuerpo que te persiguen (Udyr, Darius, Briar, Illaoi).
  3 partidas, 2 victorias; la única en su caso ideal (vs Wukong, Illaoi, Yone) fue derrota. Faltan más partidas.
- La columna `hechizos` del registro se llena sola; `partidas resumen` compara las combinaciones.

---

## 4. Los primeros minutos

Datos de `temprano` (17 partidas):

| Minuto | Adelante o igual en oro | Atrás |
|---|---|---|
| 5 | ganaste 7 de 8 | ganaste 3 de 9 |
| 10 | ganaste 7 de 8 | ganaste 3 de 9 |
| 15 | ganaste 7 de 8 | ganaste 3 de 9 |

**Tus partidas se deciden muy temprano.** Antes del minuto 5:

| | Participación en bajas de tu equipo | Daño a campeones |
|---|---|---|
| Victorias | 50% | 776 |
| Derrotas | 9% | 341 |

Al minuto 15 la participación se iguala (47% y 45%): en las derrotas llegas a las peleas, pero tarde.

**Otros datos:**
- Tu equipo muere ~6 veces antes del minuto 10; tú, menos de 1. Juegas seguro: tienes margen para arriesgar más.
- El jungla enemigo está en ~43% de esas muertes; el resto son peleas de carril que no dependen de ti.
- Dos patrones de derrota: **poca presencia** (Rengar, Briar, Fiddlesticks: poco daño y pocas bajas) y
  **peleaste y no convertiste** (Briar del 23/10: 2,207 de daño y 1 de 10 bajas).

### Plan para los primeros 5 minutos
1. Antes de empezar, elige el carril al que llegarás a los ~3:15: aliado con control y rival que va a empujar.
2. Termina tu primera vuelta cerca de ese carril, no del otro lado del mapa.
3. Si empieza una pelea entre el minuto 2 y el 4 cerca de tu camino (sobre todo bot), ve.
4. Cangrejo a los 3:30 solo si tus carriles cercanos pueden ayudarte.
5. Invadir y farmear lejos, después del minuto 5.

### Según el jungla enemigo (hipótesis)
- **Jungla que escala con farmeo** (Cho'Gath, Karthus, Shyvana, Maestro Yi): róbale campamentos cuando muera o
  esté lejos. Retrasa sus objetos (y las cargas de Cho'Gath) y ahí salen tus marcas de monstruos.
  vs Cho'Gath (27/10): robándole la jungla nunca fue un problema (victoria).
- **Jungla de presión temprana** (Lee Sin, Rengar, Briar, Wukong, Viego, Graves: 8 de 15 muertes de tu equipo antes del min 15 el 27/10): síguelo y contraemboscalo; robarle
  no lo frena.
- **Partidas de Dominación** (nadie te alcanza): farmear tranquilo y escalar también funciona. En 3 de tus 4
  victorias con Dominación no participaste en ninguna baja antes del minuto 5. La regla de "ve a las peleas
  tempranas" aplica sobre todo a las partidas de Valor.

### Hábitos
- **Después de cada campamento, mira el minimapa:** ¿dónde está su jungla? Si no lo sabes, centinela en su entrada.
  Si está cerca de un carril tuyo, contraemboscada; si está lejos, roba sus campamentos del otro lado.
- **Marcador de bajas:** 2 o más bajas antes del minuto 5 = partida de peleas; farmea hacia ellas.
- **Emboscadas:** avisa con ping antes de llegar. Si un carril falla dos veces, cambia de carril.
- **Si ganas el duelo de jungla**, convierte la ventaja en objetivos (dragón, heraldo, torre), no en más farmeo.
- **Invasión a nivel 1 (mid + jungla):** no pelees el 2 contra 1; empieza por el otro lado o toma su jungla.
- **Mismo lado de inicio:** eres la contraemboscada natural; pelea el cangrejo solo con ventaja.
- **Compañero que sabotea** (p. ej. un mid que te roba la jungla): silencia, juega con los carriles que siguen
  jugando, reporta al final y marca la partida con `--excluir`.

---

## 5. Objetivos: el Barón y el 4º dragón deciden tus partidas largas

Datos de `objetivos` (93 partidas, 29/10):

| Quién lo consigue | Partidas | Victorias |
|---|---|---|
| Primer Barón: tu equipo | 44 | **36 (82%)** |
| Primer Barón: el enemigo | 33 | **4 (12%)** |
| 4 o más dragones: tu equipo | 12 | **10 (83%)** |
| 4 o más dragones: el enemigo | 22 | **2 (9%)** |
| Primer dragón: tu equipo | 34 | 21 (62%) |
| Primer dragón: el enemigo | 59 | 29 (49%) |

- El primer Barón y el 4º dragón son lo que más separa tus victorias de tus derrotas. Que el primer Barón enemigo
  caiga antes o después del minuto 25 no cambia nada: lo que importa es no dejarlo pasar.
- **El primer dragón casi no importa**: el enemigo se lo lleva en 2 de cada 3 partidas y aun así ganas la mitad.
  No arriesgues una pelea por él. **El 4º sí**: pelea ese con todo (R, centinelas, sin morir antes).
- Larvas y heraldo casi no cambian nada. Torres y placas son más consecuencia que causa.
- Ojo: el Barón y el 4º dragón suelen ser la **consecuencia** de una partida que ya iba torcida. Dónde se tuerce
  está en la sección 6.

**Plan para el Barón (tú tienes el Castigo):**
1. Visión y lente en el río del Barón hacia el minuto 19-21.
2. No mueras justo antes: una muerte de la jungla ahí le regala el Barón al enemigo.
3. Si vas adelante, tómalo en cuanto aparezca, con visión y tu equipo cerca.
4. Si ellos lo intentan: dentro de tu definitiva el Barón no baja del 10% (y al terminar se cura), así que puedes
   negárselo y robarlo con Castigo cuando termine. Calcula el momento.

### Lo que depende de ti: muertes, no visión (`jungla`, 93 partidas, 29/10)

| | Victorias (50) | Derrotas (43) |
|---|---|---|
| Visión por minuto | 1.47 | 1.34 |
| Balizas de control | 3.0 | 3.1 |
| Centinelas tuyos antes de cada objetivo | 0.68 | 0.60 |
| Muertes por partida | 4.7 | **7.7** |
| **Muertes caras** (90 s antes de un dragón o Barón enemigo) | **0.5** | **1.5** |
| **Muertes en tu propia jungla, por partida** | **0.8** | **2.2** |

- La visión es casi igual; la diferencia está en **cuándo y dónde mueres**. En octubre compras 6-9 balizas por
  partida y en marzo 0-3, y marzo fue tu mejor mes (71%): más balizas no dieron más victorias.
- Casi la mitad de tus muertes de más en las derrotas son **en tu propia jungla**. En la jungla enemiga mueres
  igual en victorias y derrotas: el problema no es invadir, es que te encuentran farmeando.
- **Regla:** en el minuto y medio antes de un dragón o Barón, tu vida vale ese objetivo. Nada de arbustos sin
  visión, farmear solo del otro lado o perseguir bajas.
- **Cuando vas atrás**, farmea del lado de tus carriles y torres, con centinela en la entrada de tu jungla. Si no
  ves a su jungla y a su mid, no entres a los campamentos lejanos.
- Pon 1-2 centinelas antes de cada objetivo (hoy pones medio).

---

## 6. Cuándo se tuerce la partida (`momentos`, 93 partidas, 29/10)

Promedio por partida en cada tramo de 5 minutos (victorias | derrotas):

| Tramo | Tus muertes | En tu jungla | Bajas en que participas | Oro que gana o pierde tu equipo |
|---|---|---|---|---|
| 0-5 | 0.56 \| 0.42 | 0.16 \| 0.19 | 1.2 \| 1.1 | +176 \| −323 |
| 5-10 | 0.78 \| 0.84 | 0.14 \| 0.26 | 1.7 \| 1.4 | +570 \| −479 |
| 10-15 | 0.64 \| **1.14** | 0.10 \| 0.21 | 2.8 \| 2.0 | +1,412 \| −995 |
| **15-20** | 0.85 \| **1.36** | 0.10 \| **0.40** | **3.6 \| 2.0** | **+2,228 \| −1,692** |
| 20-25 | 0.74 \| 1.27 | 0.12 \| 0.39 | 3.2 \| 1.9 | +1,413 \| −1,159 |
| 25-30 | 0.82 \| **1.64** | 0.07 \| **0.58** | 3.8 \| 2.3 | +1,690 \| −2,335 |

**Dos momentos:**
1. **Minuto 5: empieza la mitad de tus derrotas.** En 21 de 43 tu equipo ya iba atrás en oro al minuto 5 y no
   volvió a ir adelante. No son tus muertes (en ese tramo mueres *menos* en derrotas): son carriles y el jungla
   enemigo. Ir atrás al minuto 5 no es perder (remontas varias), pero marca el tipo de partida.
2. **Minutos 10 a 20: la diferencia se hace grande, y ahí sí depende de ti.** Es el tramo con más oro en juego.
   En las derrotas mueres más, **4 veces más en tu jungla**, y participas en casi la mitad de bajas: entras a
   farmear solo, te encuentran, y tu equipo pelea sin ti.

Solo 3 derrotas fueron partidas que nunca fueron atrás en oro antes del minuto 35 (tiradas al final): no es el problema.

**Regla: si al minuto 10 tu equipo va atrás, no farmees solo en tu jungla.** Farmea pegado a un carril con
prioridad o júntate con tu equipo antes de cada objetivo. Mejor perder un campamento que perder una muerte.
Antes de cada campamento, minimapa: si faltan 2 o más enemigos y tus carriles cercanos están empujados hacia tu
torre, ese lado no es seguro.

No se sabe si mueres en tu jungla porque vas atrás (te invaden más) o si vas atrás porque mueres ahí; seguramente
las dos. La respuesta práctica es la misma.

---

## 7. Cómo controlar la partida

Reglas para llevar tú la partida, con las cifras de las secciones 4 a 6.

- **Elige antes del minuto 3 a qué carril vas a ayudar:** el que tiene control o el que puede cargar. Si no te
  sigue dos veces, cambia de carril. Antes del minuto 5 participas en el 50% de las bajas de tu equipo en tus
  victorias y en el 9% en tus derrotas.
- **Una baja sin objetivo es media baja:** después de cada baja, toma algo (placas, cangrejo, dragón, su jungla).
  El objetivo es lo que gana: con el primer Barón ganas el 82% de tus partidas.
- **Minuto 10 a 20: estar con el equipo.** Si vas adelante, invade con visión y asfixia su jungla; si vas atrás,
  júntate con tu carril más fuerte. Es el tramo con más oro en juego (del 15 al 20: +2,228 en victorias, −1,692 en
  derrotas) y donde en las derrotas mueres 4 veces más en tu jungla (0.40 contra 0.10) y participas en menos bajas
  (2.0 contra 3.6).
- **Si avisaste y el carril no escuchó, no vayas a morir con él:** cambia esa baja por un objetivo del otro lado
  del mapa. Mueres 7.7 veces por partida en tus derrotas y 4.7 en tus victorias.
- **Objetivos: avisa con un minuto de anticipación** ("drake 1 min"), pon visión y llega primero. El 1º dragón no
  vale una pelea arriesgada (el enemigo se lo lleva en 59 de 93 partidas y aun así ganas el 49%); el 4º y el Barón
  sí (con el 4º dragón ganas el 83% y sin él el 9%; con el primer Barón el 82% y sin él el 12%). Hoy pones medio
  centinela antes de cada objetivo y tus muertes caras son 1.5 por partida en derrotas contra 0.5 en victorias.
- **Tu R decide peleas por objetivos:** dentro nadie baja del 10%, ni tu equipo ni el Barón.

---

## 8. Pendiente

- **Pausado mientras dura la prueba de Brujería:** probar Dominación con Impacto Súbito + Cazador de Tesoros y Corte
  en partidas donde nadie te alcanza (~5 partidas). Se retoma al terminar la de Brujería, para comparar las dos en el
  mismo tipo de partida.
- Probar la regla del minuto 10: en ~10 partidas, revisar en `momentos` si bajaron tus muertes en tu jungla del
  minuto 10 al 30 en las derrotas.
- Probar las hipótesis de objetos: Sterak, Danza de la Muerte, Rukerno, Cordura (contra Sylas).
- En ~5 partidas, revisar `temprano --minuto 5`: ¿subió tu participación en las derrotas?
- Si sube y sigues perdiendo: agregar oro por carril al minuto 10 y tu jungla contra la suya (campamentos, nivel).
- Probar Brujería (Concentración Absoluta + Caminata Sobre Agua) en 8 a 10 partidas seguidas donde nadie te alcanza
  sin fallar, en lugar de Dominación. Resto de runas: Estrategia Ofensiva, Triunfo, Leyenda: Celeridad, Corte, y vida
  escalable de fragmento. Contra equipos que te pegan de lejos (poke), Dominación, porque Concentración Absoluta se
  apaga por debajo del 70% de vida. Comparar contra Dominación de octubre (6 de 11) con `partidas resumen`, y revisar
  en `momentos` y `jungla` que no suban las muertes en tu jungla ni las muertes caras.
- Después de terminar la prueba de Brujería, probar en Dominación: **Golpe Bajo** en lugar de Impacto Súbito cuando
  **tu** equipo tiene mucho control (varios entre Leona, Nautilus, Malphite, Amumu, Sejuani...). Golpe Bajo se activa
  con el control de cualquiera, también con la ralentización de tu E; Impacto Súbito solo con tu Q. Comparar su daño
  por partida con la media de Impacto Súbito (1,089).
- Después de terminar la prueba de Brujería, probar en Dominación: **Cazador Definitivo** en lugar de Cazador de
  Tesoros (hasta 31 de aceleración en la R con 5 acumulaciones).
