# Kindred: reglas y hallazgos

Lo que hemos aprendido con tus partidas y con `kindred-lab`. Datos al 29/10/2026: 97 partidas de Solo/Dúo
con Kindred (febrero a octubre de 2026; 93 sin remakes ni excluidas, 86 de más de 20 minutos), parche 16.21
(los datos de objetos son del parche 16.22.1, confirma en la tienda). Las secciones con fecha anterior
usan menos partidas: son **tendencias**, no reglas definitivas.

Las secciones 4 a 7 se recalcularon con la revisión del 15/11, con el mismo corte del
29/10: hoy el registro da **95 partidas válidas (52 victorias, 43 derrotas)**. La sección 2 sigue con las cifras
del 29/10. Las cifras marcadas "calculado aparte" todavía no las muestra ningún comando (ver la
[hoja de ruta](hoja_de_ruta.md)).

**En una línea:** en tus derrotas mueres más en tu jungla entre el minuto 10 y el 30 (1.4 muertes por partida
contra 0.4 en victorias; en toda la partida, 2.2 contra 0.8). El Barón y el 4º dragón van con
las partidas que ya ibas ganando o perdiendo: el oro al minuto 20 predice casi lo mismo. Con estas partidas no se ha medido
una diferencia por las runas: el margen es de unos ±23 puntos.

---

## 1. Rutina después de cada partida

```powershell
python -m kindred_lab partidas importar
python -m kindred_lab partidas anotar ultima --alcance si      # o no; --excluir si fue una partida rara
python -m kindred_lab partidas resumen
python -m kindred_lab temprano --minuto 5
python -m kindred_lab momentos          # cada ~10 partidas: en qué tramo se tuercen tus derrotas
```

- Atajo: `.\rutina.ps1` hace las tres primeras (importa, te pregunta `alcance` y la lección de la partida, y muestra
  el resumen), después muestra tus muertes de esa partida (`jungla --ultima`: minuto, zona, quién te mató y si
  fue cara), luego tus defensivos (`objetos defensivo --ultima`) y al final hace commit de `registro/partidas.csv`. Si la importación falla o no hay partida nueva,
  no anota nada.
- Primero `importar`, después `anotar`: si no, `ultima` apunta a la partida anterior.
- `--alcance` es lo que **decidiste en la selección**, no lo que pasó (eso ya lo guarda `muertes_antes_min10`).
- En la nota de la rutina, escribe una sola lección por partida, por ejemplo "Fauces bien, Syndra me mataba" o "llegué
  tarde al componente".
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

Con estas partidas no se ha medido una diferencia entre runas: 59% contra 45% tiene un margen de unos ±23 puntos.
Estas tablas mezclan filtros y se rehacen con uno solo después de la prueba de Brujería (ver la hoja de ruta).

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

- Estrategia Ofensiva es tu runa más fuerte (15 partidas). Golpe de Gracia y Cadencia Letal rindieron muy poco en
  esta tabla, pero es 1 partida de cada una; con más partidas, Cadencia Letal ganó 10 de 16 (tabla de arriba).
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
| Sobre todo críticos (Caitlyn, Jhin); su pasiva no hace nada contra habilidades | Presagio de Randuin | hipótesis (1 partida a favor) |
| Luchadores que se pegan (Darius, Mundo, Garen, Sett, Aatrox) | Randuin; segunda opción, Danza de la Muerte (por AD, armadura y curación con derribos) | Danza: hipótesis |
| Daño mágico repartido o un combo AP | Fauces de Malmortius | hipótesis (1 partida a favor); la misma que Filo de la Noche |
| Una habilidad que abre el combo: asesinos AD (Zed, Talon, Pantheon, Kha'Zix, Qiyana), atadura, marca | Filo de la Noche | hipótesis (1 partida a favor), junto con Fauces |
| Supresión (Malzahar, Warwick, Urgot) o ceguera (Teemo) | Cimitarra Mercurial | probado en 2 partidas, más tu regla de siempre contra Malzahar y Teemo |
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
- **Compro tarde el defensivo, o no lo compro (`objetos defensivo`, 100 partidas, 05/11).** Cuando un enemigo fue quien más daño hizo en 2 de mis muertes, en cerca de la mitad de las partidas nunca compré un defensivo completo útil contra él: 26 de 44 antes del 16.20 y 18 de 38 desde entonces. Cuando lo compré, tardé una mediana de 7.0 min (14 partidas) y 11.6 min (16 partidas) desde esa 2ª muerte. Algunos "nunca" pueden ser partidas que terminaron pronto.
- **Regla nueva (hipótesis):** tras la 2ª muerte contra el mismo enemigo, en la siguiente vuelta a base compro un componente defensivo contra él, aunque no me alcance para el objeto completo. Punto de partida para probarla, primera compra útil aunque sea un
  componente: mediana de 5.4 min (15 de 44 partidas) antes del 16.20 y 8.3 min (21 de 38) desde entonces; sin ni un
  componente, 25 y 13 partidas. De esas compras desde el 16.20, 13 de 21 eran parte del defensivo que terminé, 3 fueron el
  objeto entero y 5 quedaron sin terminar. Antes del 16.20 no son comparables: 11 de
  15 acababan en botas (desde el 16.20, 1 de 21).
  El componente tiene que ser contra el tipo de daño que te mata, y contra daño verdadero solo sirve la vida (Cristal de
  Rubí, Cinturón de Gigante), no la armadura ni la RM. Ejemplo: 03/11, el Sello de Acero contra Sett, que hizo 57% de
  daño verdadero en mis muertes. Al comprarlo, Sett llevaba 89% físico; el daño verdadero llegó después: el Sello fue
  razonable con lo que se sabía en ese momento. Contra campeones que se sabe desde la selección que hacen daño
  verdadero (como Sett), conviene sumar vida.
  **Cómo se mete en la build:** Matakrakens, luego el componente defensivo (solo si el mismo enemigo ya hizo más daño en 2 de mis muertes),
  luego Rey Arruinado, y al final termino el defensivo de ese componente. El componente tiene que formar parte del objeto
  que voy a terminar. En jungla, una capa de RM temprana solo cuando un enemigo AP concreto me gana directamente (jungla
  AP que invade o mid que rota), no porque su equipo tenga mucho AP.
- **El último golpe engaña (1 partida, 03/11; `objetos defensivo`).** Sett me dio el último golpe en 6 de 8 muertes, pero fue quien más daño hizo solo en 4: en dos de las otras puso 64 y 342. Ir por Fauces no fue error: Syndra fue quien más daño hizo en mis 2 muertes anteriores, con más de 1000 mágico cada una.
- **Daño verdadero (1 partida, 03/11).** Sett hizo 57% de daño verdadero en mis muertes (`settw`): contra eso, la armadura no sirve; solo vida y colocación.
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
- **Contra asesinos (Zed, Talon, Fizz, Katarina, Naafiri): Destello** (hipótesis, 1 partida): con Fantasma contra
  Talon y Fizz moriste 2 veces antes del minuto 5.
- **Fantasma: en prueba** contra peleadores cuerpo a cuerpo que te persiguen (Udyr, Darius, Briar, Illaoi).
  3 partidas, 2 victorias; la única en su caso ideal (vs Wukong, Illaoi, Yone) fue derrota. Faltan más partidas.
- La columna `hechizos` del registro se llena sola; `partidas resumen` compara las combinaciones.

---

## 4. Los primeros minutos

Datos de `temprano` (95 partidas al 29/10: 52 victorias y 43 derrotas):

| Minuto | Adelante o igual en oro | Atrás |
|---|---|---|
| 5 | ganaste 29 de 45 (64%) | ganaste 23 de 50 (46%) |
| 10 | ganaste 39 de 54 (72%) | ganaste 13 de 41 (32%) |
| 15 | ganaste 40 de 53 (75%) | ganaste 12 de 42 (29%) |

**Los primeros 5 minutos no separan tus victorias de tus derrotas.** Antes del minuto 5:

| | Participación en bajas de tu equipo | Daño a campeones |
|---|---|---|
| Victorias | 44% | 769 |
| Derrotas | 45% | 753 |

Al minuto 15 sigue igual (43% y 45%). El oro al minuto 5 pesa poco (ganas el 64% yendo adelante y el 46% yendo
atrás); al minuto 10 la diferencia ya es grande (72% contra 32%). La versión anterior de esta sección ("tus partidas
se deciden muy temprano", con 50% contra 9% de participación) salía de 17 partidas y no se sostiene con 95.

**Otros datos:**
- Tu equipo muere 6.5 veces antes del minuto 10; tú, 1.3.
- El jungla enemigo está en el 43% de esas muertes; el resto son peleas de carril que no dependen de ti.
- Dos ejemplos de derrota, no medidos en las 95 partidas: **poca presencia** (Rengar, Briar, Fiddlesticks: poco daño
  y pocas bajas) y **peleaste y no convertiste** (Briar del 23/10: 2,207 de daño y 1 de 10 bajas).

### Plan para los primeros 5 minutos
Es un plan de juego, no sale de los datos: participar temprano no separó tus victorias de tus derrotas.
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
- **Partidas de Dominación** (nadie te alcanza): farmear tranquilo y escalar también funciona. En 11 de tus 35
  victorias con Dominación no participaste en ninguna baja antes del minuto 5.

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

## 5. Objetivos: el Barón y el 4º dragón van con las partidas que ya ibas ganando

Datos de `objetivos` (95 partidas, 29/10):

| Quién lo consigue | Partidas | Victorias |
|---|---|---|
| Primer Barón: tu equipo | 45 | 37 (82%) |
| Primer Barón: el enemigo | 33 | 4 (12%) |
| 4 o más dragones: tu equipo | 12 | 10 (83%) |
| 4 o más dragones: el enemigo | 22 | 2 (9%) |
| Primer dragón: tu equipo | 35 | 22 (63%) |
| Primer dragón: el enemigo | 60 | 30 (50%) |

**Es una asociación, no una causa.** El oro de tu equipo al minuto 20, antes de que aparezca el Barón, predice casi
lo mismo: yendo adelante ganas 40 de 49 (82%) y yendo atrás, 7 de 40 (18%). Dentro de cada grupo el primer Barón
sí agrega algo (calculado aparte; 89 partidas con dato al minuto 20):

| Oro al minuto 20 | Primer Barón tuyo | Primer Barón enemigo |
|---|---|---|
| Adelante | ganaste 31 de 33 | ganaste 3 de 9 |
| Atrás | ganaste 6 de 12 | ganaste 1 de 24 |

Son grupos de 9 a 33 partidas: una tendencia. Yendo atrás, con el primer Barón tuyo ganaste 6 de 12 (y en 6 de tus
7 remontadas el primer Barón fue tuyo), pero no se sabe si las causa.

- **El 4º dragón:** la tabla de 4 o más dragones la calculé aparte (`objetivos` no la da). Yendo atrás al minuto 20,
  tu equipo llegó a 4 dragones en 1 sola partida y el enemigo en 18 (ganaste 1). No hay datos para decir que pelear
  el 4º con todo cuando vas atrás cambie el resultado.
- **El primer dragón casi no se asocia con el resultado:** el enemigo se lo lleva en 60 de 95 partidas y aun así
  ganas la mitad. No arriesgues una pelea por él.
- Larvas y heraldo casi no cambian nada. Torres y placas son más consecuencia que causa.
- Dónde se tuerce la partida está en la sección 6.

**Plan para el Barón (tú tienes el Castigo):**
1. Visión y lente en el río del Barón hacia el minuto 19-21.
2. No mueras justo antes: una muerte de la jungla ahí le regala el Barón al enemigo.
3. Si vas adelante, tómalo en cuanto aparezca, con visión y tu equipo cerca.
4. Si ellos lo intentan: dentro de tu definitiva el Barón no baja del 10% (y al terminar se cura), así que puedes
   negárselo y robarlo con Castigo cuando termine. Calcula el momento.

### Muertes y visión en victorias y derrotas (`jungla`, 95 partidas, 29/10)

| | Victorias (52) | Derrotas (43) |
|---|---|---|
| Visión por minuto | 1.46 | 1.34 |
| Balizas de control | 3.0 | 3.1 |
| Centinelas tuyos antes de cada objetivo | 0.67 | 0.60 |
| Muertes por partida | 4.6 | **7.7** |
| **Muertes en tu propia jungla, por partida** | **0.8** | **2.2** |

**Morir antes de un objetivo** (calculado aparte). Si mueres en los 90 s antes de un dragón o Barón, el enemigo se
lo lleva mucho más a menudo:

| | Moriste en los 90 s previos | No moriste |
|---|---|---|
| Todas | el enemigo lo tomó 93 de 137 veces (68%) | 174 de 376 (46%) |
| Victorias | 26 de 61 (43%) | 57 de 206 (28%) |
| Derrotas | 67 de 76 (88%) | 117 de 170 (69%) |

La diferencia se mantiene dentro de victorias y dentro de derrotas. La cifra anterior ("muertes caras": 0.5 por
partida en victorias contra 1.5 en derrotas, la que todavía muestra `jungla`) medía sobre todo exposición: solo
cuenta las muertes antes de un objetivo que tomó el enemigo, y en las derrotas el enemigo toma muchos más.
Sigue siendo una asociación: también puedes morir ahí porque el enemigo ya estaba peleando por el objetivo.

- La visión es casi igual; la diferencia está en **cuándo y dónde mueres**. Dentro de octubre (44 partidas)
  compras 5.0 balizas por partida en victorias y 4.6 en derrotas (mediana 4.5, de 1 a 9): más balizas no separan
  tus victorias de tus derrotas. No compares con marzo, que es otra época.
- Casi la mitad de tus muertes de más en las derrotas son **en tu propia jungla**, en marzo (0.9 por partida en
  victorias contra 3.1 en derrotas) y en octubre (0.7 contra 1.7). En la jungla enemiga mueres igual en victorias y
  derrotas.
- **Pero no está medido que te encuentren farmeando solo:** el análisis sabe dónde mueres, no cómo. De tus 62
  muertes en tu jungla del minuto 10 al 30 en derrotas, 41 fueron en una pelea (otra baja a menos de 3,000 unidades
  y ±20 s) y 21 aisladas, de ellas solo 8 con un único atacante (en victorias: 14 en pelea y 5 aisladas, de 19).
  Es una aproximación mía, calculada aparte; `jungla` todavía no lo distingue. La mayoría son peleas en tu lado del
  mapa.
- **Regla:** en el minuto y medio antes de un dragón o Barón, tu vida vale ese objetivo: si mueres ahí, el enemigo
  se lo lleva el 68% de las veces, contra el 46% si sigues vivo. Nada de arbustos sin visión, farmear solo del otro
  lado o perseguir bajas.
- **Cuando vas atrás**, farmea del lado de tus carriles y torres, con centinela en la entrada de tu jungla. Si no
  ves a su jungla y a su mid, no entres a los campamentos lejanos.
- Pon 1-2 centinelas antes de cada objetivo (hoy pones medio).

---

## 6. Cuándo se tuerce la partida (`momentos`, 95 partidas, 29/10)

Promedio por partida en cada tramo de 5 minutos (victorias | derrotas):

| Tramo | Tus muertes | En tu jungla | Bajas en que participas | Oro que gana o pierde tu equipo |
|---|---|---|---|---|
| 0-5 | 0.54 \| 0.42 | 0.15 \| 0.19 | 1.2 \| 1.1 | +188 \| −323 |
| 5-10 | 0.75 \| 0.84 | 0.13 \| 0.26 | 1.8 \| 1.4 | +599 \| −479 |
| 10-15 | 0.65 \| **1.14** | 0.12 \| 0.21 | 2.9 \| 2.0 | +1,451 \| −995 |
| **15-20** | 0.84 \| **1.36** | 0.10 \| **0.40** | **3.7 \| 2.0** | **+2,301 \| −1,692** |
| 20-25 | 0.80 \| 1.27 | 0.11 \| 0.39 | 3.3 \| 1.9 | +1,367 \| −1,159 |
| 25-30 | 0.80 \| **1.64** | 0.07 \| **0.58** | 3.8 \| 2.3 | +1,765 \| −2,335 |

La columna "Bajas en que participas" cuenta bajas, no el porcentaje de las de tu equipo (ver el punto 2 abajo).

**Desde cuándo una partida queda de un lado** (calculado aparte). El tramo desde el que tu equipo fue atrás (en
derrotas) o adelante (en victorias) por más de 1,000 de oro en todos los cortes siguientes:

| Desde el tramo | Derrotas: atrás por más de 1,000 | Victorias: adelante por más de 1,000 |
|---|---|---|
| 0-5 | 5 | 5 |
| 5-10 | 11 | 13 |
| 10-15 | 5 | 9 |
| 15-20 | 3 | 9 |
| 20-25 | 7 | 2 |
| 25-30 | 4 | 1 |
| 30-35 | 2 | 3 |
| Nunca (parejas o con vuelcos) | 6 | 10 |

**Dos momentos:**
1. **El minuto 5 no decide.** En 68 de 95 partidas el oro al minuto 5 está dentro de ±1,000, y solo 5 derrotas (y
   5 victorias) ya iban más de 1,000 atrás (o adelante) desde ahí. Al minuto 15 ya estaban de un lado 21 de 43
   derrotas y 27 de 52 victorias. La versión anterior ("el minuto 5 empieza
   la mitad de tus derrotas", 21 de 43) contaba sin umbral: una derrota que fue atrás todo el juego "empieza" en el
   primer corte por construcción, y la misma cuenta en victorias da 19 de 52. `momentos` todavía muestra esa
   cuenta sin umbral.
2. **Minutos 10 a 20: la diferencia se hace grande.** Es uno de los dos tramos con más oro en juego (el otro, del
   25 al 30).
   En las derrotas mueres más en tu jungla (del 15 al 20: 17 muertes en 42 derrotas contra 5 en 49 victorias, 0.40
   contra 0.10 por partida). La mayoría de esas muertes son en peleas, no aisladas (sección 5). También participas
   en menos bajas (2.0 contra 3.7 por partida), pero eso es exposición: en las derrotas tu equipo consigue menos
   bajas. Como parte de las bajas de tu equipo participas igual: 47% en derrotas y 49% en victorias del 15 al 20,
   y en ningún tramo la diferencia pasa de 5 puntos (calculado aparte).

**Las derrotas se deciden tanto temprano como tarde.** 21 de 43 ya iban más de 1,000 atrás para siempre al minuto
15, pero 19 no quedaron de un lado antes del minuto 20: 13 quedaron atrás después del 20 y 6 nunca (parejas o con
vuelcos). Las 3 restantes, del 15 al 20.

**Regla (hipótesis): si al minuto 10 tu equipo va atrás, no farmees solo en tu jungla.** Farmea pegado a un carril
con prioridad o júntate con tu equipo antes de cada objetivo. Mejor perder un campamento que perder una muerte.
Antes de cada campamento, minimapa: si faltan 2 o más enemigos y tus carriles cercanos están empujados hacia tu
torre, ese lado no es seguro.

Los datos no respaldan todavía la condición "si vas atrás al minuto 10": en las derrotas mueres en tu jungla del
minuto 10 al 20 casi igual yendo atrás al minuto 10 (0.56 por partida, 27 derrotas) que adelante (0.60, 15
derrotas). Tampoco se sabe si mueres en tu jungla porque vas atrás o si vas atrás porque mueres ahí.

---

## 7. Cómo controlar la partida

Reglas para llevar tú la partida, con las cifras de las secciones 4 a 6.

- **Elige antes del minuto 3 a qué carril vas a ayudar:** el que tiene control o el que puede cargar. Si no te
  sigue dos veces, cambia de carril. Es un hábito, no una cifra: antes del minuto 5 participas igual en victorias y
  derrotas (44% y 45% de las bajas de tu equipo).
- **Una baja sin objetivo es media baja:** después de cada baja, toma algo (placas, cangrejo, dragón, su jungla).
  Con el primer Barón ganas el 82% de tus partidas, pero yendo adelante en oro al minuto 20 también (82%): el Barón
  suele cerrar lo que ya ibas ganando.
- **Minuto 10 a 20: estar con el equipo** (hipótesis sin respaldo en los datos: participas igual en victorias y
  derrotas, 49% y 47% de las bajas de tu equipo del 15 al 20). Si vas adelante, invade con visión y asfixia su
  jungla; si vas atrás, júntate con tu carril más fuerte. Del 15 al 20 hay mucho oro en juego (+2,301 en victorias,
  −1,692 en derrotas) y en las derrotas mueres más en tu jungla (17 muertes en 42 derrotas contra 5 en 49
  victorias), la mayoría en peleas.
- **Si avisaste y el carril no escuchó, no vayas a morir con él:** cambia esa baja por un objetivo del otro lado
  del mapa. Mueres 7.7 veces por partida en tus derrotas y 4.6 en tus victorias.
- **Objetivos: avisa con un minuto de anticipación** ("drake 1 min"), pon visión y llega primero. El 1º dragón no
  vale una pelea arriesgada (el enemigo se lo lleva en 60 de 95 partidas y aun así ganas el 50%). El 4º dragón y el
  Barón van con el resultado (83% y 82% cuando son tuyos), pero sobre todo porque llegan en partidas que ya ibas
  ganando. Hoy pones medio
  centinela antes de cada objetivo, y si mueres en los 90 s previos el enemigo se lleva el objetivo el 68% de las
  veces (46% si sigues vivo).
- **Tu R decide peleas por objetivos:** dentro nadie baja del 10%, ni tu equipo ni el Barón.

---

## 8. Pendiente

Solo pruebas de juego. Las funciones por programar están en la [hoja de ruta](hoja_de_ruta.md).

- **Pausado mientras dura la prueba de Brujería:** probar Dominación con Impacto Súbito + Cazador de Tesoros y Corte
  en partidas donde nadie te alcanza (~5 partidas). Se retoma al terminar la de Brujería, para comparar las dos en el
  mismo tipo de partida.
- Probar la regla del minuto 10: en ~10 partidas, revisar en `momentos` si bajaron tus muertes en tu jungla del
  minuto 10 al 30 en las derrotas.
- Probar las hipótesis de objetos: Sterak, Danza de la Muerte, Rukerno, Cordura (contra Sylas).
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
