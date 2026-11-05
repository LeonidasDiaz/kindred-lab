# kindred-lab: uso y comandos

Datos de League of Legends para decidir las runas de Kindred (y, más adelante, los objetos)
sin depender de páginas de builds. Solo usa la librería estándar de Python (3.10+).

Reglas y hallazgos de juego (runas, objetos, primeros minutos): [hallazgos.md](hallazgos.md).

## Estructura

```
kindred-lab/
├── src/kindred_lab/
│   ├── config.py      rutas y valores por defecto (idioma es_MX, carpetas, región de Riot)
│   ├── ddragon.py     cliente de Data Dragon (runas por parche) con caché en disco
│   ├── runas.py       normalizar, guardar por parche, comparar, buscar
│   ├── reglas.py      cargar y validar las reglas de runas de Kindred
│   ├── objetos.py     objetos por parche: Data Dragon más la capa manual de mecánicas
│   ├── campeones.py   tipos de campeón de Data Dragon, guardados para no descargar en los análisis
│   ├── riot.py        cliente de la API de Riot (match-v5) con caché en disco
│   ├── cdragon.py     qué var1/var2/var3 es cada número de runa (Community Dragon)
│   ├── partidas.py    partida de Riot -> fila del registro, calibración, resumen
│   ├── temprano.py    extra: muertes y oro en los primeros minutos (no afecta las runas)
│   ├── objetivos.py   extra: dragones, Barón, torres y placas por partida
│   ├── jungla.py      extra: visión, muertes caras y dónde mueres
│   ├── momentos.py    extra: en qué tramo de 5 minutos se tuerce la partida
│   ├── defensivo.py   extra: auditoría de tus defensivos
│   └── __main__.py    línea de comandos
├── data/
│   ├── raw/ddragon/<version>/<idioma>/   runesReforged.json tal cual (se regenera)
│   ├── raw/riot/                         partidas y timelines tal cual, una vez por partida
│   ├── raw/cdragon/                      perks.json de Community Dragon
│   ├── processed/runas/                  runas_<version>.json, runas_latest.json, cambios_X_a_Y.md
│   ├── processed/objetos/                objetos_<version>.json, objetos_latest.json, cambios_X_a_Y.md
│   └── processed/campeones/              campeones_latest.json (tipos de Data Dragon)
├── README.md / README.en.md  presentación del proyecto (español / inglés)
├── docs/uso.md              este manual: todos los comandos
├── docs/hallazgos.md        reglas y hallazgos de juego (runas, objetos, primeros minutos)
├── docs/hoja_de_ruta.md     funciones futuras y su estado
├── docs/migracion_objetos.md  qué cambió al migrar el archivo manual de objetos
├── reglas/
│   ├── kindred_runas.json   las 3 preguntas para elegir runas (editable a mano)
│   ├── valores_runas.json   valores de runa calibrados a mano (manda sobre Community Dragon)
│   ├── kindred_objetos.json objetos defensivos por situación (editable a mano; `objetos defensivo` usa su campo `aplica`)
│   └── objetos_mecanicas.json  capa manual de mecánicas de objetos, con su parche verificado
├── referencia/objetos_16.15.1_manual.json  archivo manual original de objetos, sin cambios
├── referencia/kindred_2026_manual.json     datos de Kindred hechos a mano, sin cambios
├── registro/partidas.csv    tu registro de partidas (lo llena `partidas importar`)
├── registro/partidas_respaldo.csv  respaldo viejo (oct. 2026); sus anotaciones ya están en partidas.csv
├── ejemplos/partidas_ejemplo.csv   14 partidas inventadas para probar `partidas resumen --registro` sin clave
├── rutina.ps1               después de cada partida: importar, anotar la última, resumen, tus muertes y tus defensivos
├── publicar.ps1             copia la parte pública a ..\kindred-lab-publico (no se publica él mismo)
├── secretos.json            tu clave de Riot y tu Riot ID (lo creas tú; en .gitignore)
├── secretos.ejemplo.json    plantilla de lo anterior
├── tests/                   pruebas sin red, con fixtures
├── .github/workflows/       GitHub Actions: pruebas en cada push
└── LICENSE                  MIT
```

`data/raw/` se puede borrar: todo se vuelve a descargar. No borres `registro/`, `reglas/` ni `secretos.json`.

## Instalación

```powershell
cd kindred-lab
python -m pip install -e .        # opcional; sin esto: $env:PYTHONPATH="src"  (PowerShell)
```

Sin instalar, antepón `PYTHONPATH=src` (Linux/Mac), `set PYTHONPATH=src` (cmd) o
`$env:PYTHONPATH="src"` (PowerShell) a los comandos.

## Runas (Data Dragon)

```powershell
python -m kindred_lab runas actualizar              # descarga el último parche y lo compara con el anterior
python -m kindred_lab runas actualizar --version 16.20.1
python -m kindred_lab runas versiones               # parches guardados
python -m kindred_lab runas comparar 16.19.1 16.20.1
python -m kindred_lab runas buscar "ultima batalla" # sin importar acentos
python -m kindred_lab runas arbol Precision         # o "precisión", "valor", "dominación"...
python -m kindred_lab reglas validar                # ¿las reglas apuntan a runas que existen?
```

## Objetos (Data Dragon más capa manual)

```powershell
python -m kindred_lab objetos actualizar              # genera el último parche y lo compara con el anterior
python -m kindred_lab objetos actualizar --version 16.22.1
python -m kindred_lab objetos verificar 6333          # ya revisé las mecánicas de ese objeto en el último parche
```

- **Data Dragon** llena `metadata` y `stats_base` en cada parche. Las estadísticas se leen del bloque `<stats>` de
  la descripción, porque su campo `stats` no trae aceleración, letalidad, tenacidad y otras; una etiqueta
  desconocida es un error para que no se pierda en silencio.
- **`reglas/objetos_mecanicas.json`** es la capa manual: mecánicas, `parche_verificado`, la descripción oficial con
  la que se verificó y tus descripciones con datos agregados. `objetos actualizar` nunca la modifica. Las mecánicas
  se escriben ahí con los nombres únicos de `ALIAS_STATS` (en `objetos.py`).
- **Aviso:** si cambia la descripción oficial de un objeto con mecánicas, sale en pantalla y en
  `cambios_X_a_Y.md`, y se repite hasta que lo revises y corras `objetos verificar <id>`. **Sin aviso no significa
  vigente:** la descripción de Danza de la Muerte dice "un porcentaje", sin el número. Por eso cada mecánica conserva
  su `parche_verificado`.
- **Valores del juego:** `objetos actualizar` también guarda en `valores_juego` los números de los archivos del juego
  (`items.cdtb.bin.json` de Community Dragon, unos 15 MB por parche, en `data/raw/cdragon/`): solo el id de la Grieta y
  su configuración normal, sin variantes de Arena ni de otros modos. Si un número de un objeto con mecánicas ya no es
  el verificado (`valores_verificados` en la capa manual), **avisa aunque la descripción oficial siga igual**, y se
  repite hasta `objetos verificar <id>`. Si esos archivos no se pueden bajar, sigue sin ellos y lo dice. Los nombres
  no siguen un formato común: esto solo detecta cambios, no llena las mecánicas. `objetos base-valores` fijó una sola
  vez la base de 16.15.1 y no sobrescribe. No cubre la lógica de las pasivas, que no está en esos archivos.
- **`disponible`** se calcula en cada parche (se compra en la Grieta). Los objetos con capa manual que ya no se
  compran se conservan con `disponible: false`.
- Si Data Dragon no trae el objeto o su descripción está vacía (Filo de la Tormenta 3097, Mapamundi 3865), se usan
  los datos de `referencia/objetos_16.15.1_manual.json`, el original sin cambios.
- `objetos migrar` creó la capa una sola vez y se niega a sobrescribirla. Qué cambió: [migracion_objetos.md](migracion_objetos.md).

## Tus partidas (API de Riot)

**Preparación (una vez):**

1. Genera una clave en https://developer.riotgames.com (la de desarrollo caduca cada 24 h).
2. Copia `secretos.ejemplo.json` como `secretos.json` y llénalo:
   ```json
   { "riot_api_key": "RGAPI-...", "riot_id": "Nombre#TAG" }
   ```
   Alternativas (mandan sobre el archivo): variables `RIOT_API_KEY` y `RIOT_ID`, o `--riot-id "Nombre#TAG"`.
   Cuando la clave caduque, solo cambias esa línea del archivo.

**Importar:**

```powershell
python -m kindred_lab partidas importar --cantidad 10
```

- Por defecto trae Solo/Dúo (`--cola 420`) y solo Kindred (`--campeon Kindred`; `--campeon ""` para todos).
  LAN se consulta por la región `americas`. `--cantidad` cuenta partidas de la cola antes de filtrar por campeón.
- No duplica partidas (usa `match_id`) y migra un CSV viejo sin esa columna.
- Se llenan solos: fecha (tu hora local), parche (`16.21`), resultado, duración, KDA, enemigos, runas,
  hechizos de invocador (p. ej. `Fantasma+Castigo`; las partidas viejas se completan solas desde la caché), muertes antes del minuto 10, daño que más recibiste (AD/AP en `dano_que_me_mata`; físico, mágico y verdadero en `notas`) y los valores
  de cada runa (`valor_*`, más `estadisticas_runas` con todos sus números).
- Siguen siendo manuales `alcance_temprano` y tus notas.
- La API da las runas secundarias en el orden en que las elegiste; se guardan ordenadas por fila.

**Valores de runa.** Riot guarda los números de cada runa en `var1/var2/var3` sin decir cuál es cuál.
El importador baja de Community Dragon el texto de fin de partida de cada runa
(p. ej. `Total de daño: @eogvar1@`) y lo usa solo. Si alguna runa sale rara (por ejemplo, Cadencia Letal
mezcla tiempo y daño, y Acondicionamiento muestra dos estadísticas), calíbrala a mano con los números
que ves en la pantalla de fin de partida:

```powershell
python -m kindred_lab partidas calibrar LA1_1234567890 LethalTempo=320
```

Guarda en `reglas/valores_runas.json` lo que coincida y, a partir de ahí, ese valor manda sobre Community Dragon.
El `match_id` está en la última columna de `registro/partidas.csv`. Después de calibrar, para recalcular partidas
ya importadas deja el CSV solo con su encabezado y vuelve a correr `importar` (las partidas están en caché).

**Anotar (sin abrir el CSV):**

```powershell
python -m kindred_lab partidas anotar ultima --alcance no --nota "Ivern mid robó la jungla" --excluir
python -m kindred_lab partidas anotar LA1_1234567890 --alcance si
python -m kindred_lab partidas anotar ultima --incluir      # quita la marca de excluir
```

`ultima` es la partida más reciente del registro. `--excluir` añade la palabra `excluir` a las notas y el
resumen ignora esa partida (para partidas donde un compañero sabotea, abandonos, etc.). Después de anotar,
**no vacíes el CSV para reimportar**: perderías las anotaciones. `importar` ya agrega solo las partidas nuevas.

**Resumen:**

```powershell
python -m kindred_lab partidas resumen                        # ignora partidas de menos de 20 min
python -m kindred_lab partidas resumen --duracion-minima 25
python -m kindred_lab partidas resumen --duracion-minima 0    # cuenta todas
python -m kindred_lab partidas resumen --minimo 5             # solo runas con 5+ partidas
python -m kindred_lab partidas resumen --registro ejemplos/partidas_ejemplo.csv   # datos inventados, sin clave
```

Muestra, por runa: partidas, victorias, valor medio y valor por minuto (para comparar partidas largas y
cortas). Las rendiciones tempranas y las partidas marcadas con `excluir` se ignoran. Con pocas partidas esto es
anécdota: no cambies una regla por 3 partidas.

Los tiempos se muestran en m:ss y no tienen "por minuto":
- **Leyenda: Celeridad**: minuto en que completaste las acumulaciones.
- **Concentración Absoluta** y **Caminata Sobre Agua** (Brujería): *tiempo total activo* según Community Dragon,
  es decir, cuánto tiempo tuviste el efecto: más del 70% de vida (Concentración Absoluta) o estar en el río
  (Caminata Sobre Agua). Para comparar partidas de distinta duración, divídelo entre la duración: p. ej. 18:30
  en una partida de 28.7 min = 64% del tiempo con más del 70% de vida.

## Extra: los primeros minutos (no afecta las runas)

```powershell
python -m kindred_lab temprano               # antes del minuto 10
python -m kindred_lab temprano --minuto 15
python -m kindred_lab temprano --todas       # incluye las partidas marcadas con 'excluir'
```

Lee las partidas que `importar` ya guardó en `data/raw/riot/` (no descarga nada ni toca el CSV).
Por partida: muertes de tu equipo antes del minuto N, en cuántas participó el jungla enemigo, tus muertes,
tu participación en las bajas de tu equipo y la diferencia de oro de equipo en ese minuto. Al final, totales:
si el jungla enemigo está en la mayoría de las muertes, contraemboscar es tu mayor mejora; si no, son
peleas de carril que no dependen de ti. Te identifica por el `riot_id` de `secretos.json` (sin distinguir
mayúsculas ni espacios, como Riot), sin red.

## Extra: objetivos

```powershell
python -m kindred_lab objetivos              # toda la partida
python -m kindred_lab objetivos --minuto 20  # solo hasta el minuto 20
```

Por partida: dragones, larvas del vacío, heraldo, Barón, torres y placas (tu equipo-enemigo) y quién tomó el
primer Barón. Al final, la diferencia media en victorias y derrotas, y cuánto ganas según quién toma el primer
dragón y el primer Barón. Lee las mismas timelines guardadas; no descarga nada.

## Extra: lo que depende de ti como jungla

```powershell
python -m kindred_lab jungla
python -m kindred_lab jungla --ultima    # solo tu última partida, muerte por muerte
```

Por partida: puntuación de visión por minuto, balizas de control, centinelas destruidos, **centinelas tuyos en
los 90 s previos a cada dragón o Barón**, tus muertes, **muertes caras** (en los 90 s previos a un dragón o Barón
del enemigo) y **dónde moriste** (tu jungla, jungla enemiga, río, carril; zonas aproximadas). Al final, la
comparación entre victorias y derrotas.

Con `--ultima`, en vez de la tabla, la partida más reciente del registro (aunque esté marcada con `excluir`):
cada una de tus muertes en orden, con minuto, zona, campeón que te mató (`(sin campeón)` si fue torre, súbditos o
monstruo) y si fue cara (y con qué objetivo enemigo).

## Extra: auditoría de tus defensivos

```powershell
python -m kindred_lab objetos defensivo                        # resumen, separado por periodo
python -m kindred_lab objetos defensivo --ultima               # tu última partida, muerte por muerte
python -m kindred_lab objetos defensivo --partida LA1_...      # una partida concreta
```

Lee las mismas timelines guardadas; no descarga nada. No calcula % de victorias por objeto.

- **Perfil de tus muertes:** % físico, mágico y verdadero, solo del daño en tus muertes (`victimDamageReceived`).
  Torres, súbditos, monstruos y aliados cuentan aquí, pero no como enemigos. Una muerte cuyo desglose suma menos de
  la mitad de tu vida máxima se marca como "desglose parcial".
- **Amenaza principal:** quién metió más daño en tus muertes, su tipo de Data Dragon (informativo: Jhin sale como
  `Marksman, Mage`) y su oro menos el tuyo en la 1ª muerte, en la compra y al final.
- **Defensivo:** objeto completo con armadura, resistencia mágica, vida o un escudo que te otorga según su descripción, más las botas con
  armadura o resistencia mágica. Se clasifica con los datos del último parche, también en partidas viejas.
- **Coincidencia por tipo:** con las muertes **anteriores** a la compra. 50% o más del daño correspondiente es "sí",
  de 35 a 49% "parcial" y menos "no". Los objetos de solo vida o escudo salen como "general". Con una sola muerte
  previa sale "pocos datos": no dice qué daño te mata.
- **Según reglas actuales:** con el campo `aplica` de `reglas/kindred_objetos.json`. Son las reglas de hoy, no las
  que existían cuando jugaste. Estados: `1ª opción` y `2ª opción` (la amenaza está en la regla del objeto),
  `por rival presente` (otro enemigo de la partida está en ella), `otro objeto` (la amenaza está en la regla de otro), `ya tenía el indicado` (ese otro ya estaba en tu inventario),
  `por perfil`, `pocos datos`, `sin coincidencia`, `sin regla` y `no evaluable` (`aplica` vacío). El perfil es
  `mezclado` si físico y mágico llegan cada uno al 35%. Con una sola muerte previa, la amenaza y el perfil no cuentan;
  el rival presente sí, porque no depende de tus muertes.
- **Retraso:** del primer enemigo que fue quien más daño hizo en 2 de tus muertes, minutos entre esa 2ª muerte y el
  primer defensivo cuyo tipo sirva contra él, según su daño hasta ese momento. Contra daño sobre todo verdadero cuenta lo
  que dé vida o escudo, aunque también dé armadura o resistencia mágica; los escudos de un solo tipo (Fauces, Blindadas de Avance) no cuentan. "Ya lo tenía" y "nunca" se cuentan aparte. Además mide la **primera compra útil** tras esa
  muerte, aunque sea un componente barato con armadura, resistencia mágica o vida: sirve para probar la regla de
  comprar un componente en la siguiente vuelta a base.
- **Efecto:** muertes cada 10 min antes y después, junto a la **base**: la tasa de ese periodo en los mismos minutos.
  Hace falta porque tus muertes suben con los minutos en cualquier partida. Compara, no prueba causa. También cuenta
  las muertes posteriores contra quien era la amenaza al comprar, por más daño y por último golpe.

El resumen separa las partidas antes y desde el parche 16.20, y marca con `*` los objetos con menos de 5 compras.
El daño viene ya reducido por tu armadura y resistencia: comprar armadura baja por sí solo el % físico posterior, y
por eso la coincidencia nunca mira lo que pasó después de comprar.

## Extra: en qué momento se tuerce la partida

```powershell
python -m kindred_lab momentos
```

Parte cada partida en tramos de 5 minutos (0-5 ... 30-35) y compara victorias y derrotas en cada tramo:
tus muertes, tus muertes en tu jungla, tus participaciones en bajas, cuánto oro ganó o perdió tu equipo en
ese tramo y la diferencia de oro al final del tramo. Al final, en qué tramo cada derrota quedó atrás en oro
para ya no recuperarse. Sirve para buscar la causa antes del Barón o del 4º dragón, que suelen ser la consecuencia.

## Publicar (repositorio público)

Este repositorio es privado: guarda tu registro de partidas. La versión pública vive en otra carpeta con su
propio historial, y se actualiza con:

```powershell
.\publicar.ps1                                   # destino: ..\kindred-lab-publico
.\publicar.ps1 -Mensaje "Publicación: jungla --ultima"
```

- Copia solo una lista blanca (código, pruebas, ejemplos, reglas, `referencia/`, `data/processed/runas/` y `objetos/`, documentación, README,
  licencia y workflow). Nunca copia `registro/`, `secretos.json`, `data/raw/`, `CLAUDE.md` ni `publicar.ps1`.
- Es un espejo: lo que sale de la lista blanca desaparece del público en la siguiente publicación.
- Quita los match_id reales entre paréntesis (p. ej. en `hallazgos.md`).
- Antes del commit busca tu clave, tu Riot ID (sin espacios ni mayúsculas), match_id reales, tus correos privados
  (todos los de autor del historial privado menos el `noreply`, aunque cambies tu `user.email`) y
  cualquier `RGAPI-` con forma de clave; si encuentra algo, no publica y solo dice en qué archivo.
- Corre las pruebas y `reglas validar` en la copia pública.
- Hace commit como `Leonidas Diaz <99288021+LeonidasDiaz@users.noreply.github.com>`. **Nunca hace push**: eso
  lo haces tú con `git -C ..\kindred-lab-publico push`.

## Flujo recomendado

1. Después de cada parche: `runas actualizar` y `objetos actualizar` → si hay cambios, revisa los `cambios_X_a_Y.md`;
   luego `reglas validar` (si una regla apunta a una runa que ya no existe, sugiere la parecida).
2. Después de jugar: `partidas importar`, completa `alcance_temprano` si usas tus 3 preguntas, y `partidas resumen`.
   Todo eso lo hace `.\rutina.ps1`:

   ```powershell
   .\rutina.ps1
   ```

   Importa (`--cantidad 10`), te pregunta si en la selección decidiste que alguien te alcanzaba (si/no) y una nota
   opcional, los guarda con `partidas anotar ultima`, muestra `partidas resumen`, luego `jungla --ultima` (tus
   muertes de la partida que acabas de jugar) y `objetos defensivo --ultima` (tus defensivos en ella). Si la importación falla
   (p. ej. clave caducada) se detiene; si no entró ninguna partida nueva, no anota nada (`ultima` sería la anterior);
   si entraron varias, anota solo la más reciente y te avisa. Al final, si `registro/partidas.csv` cambió, hace
   commit solo de ese archivo con el mensaje `Partida <match_id>: <resultado>` (una por cada partida nueva; si solo
   cambiaron anotaciones, `Registro: anotaciones`). Si git falla, avisa y no se detiene. Si Windows no deja correr scripts:
   `powershell -ExecutionPolicy Bypass -File .\rutina.ps1`.

## Pruebas

```powershell
$env:PYTHONPATH="src"; python -m unittest discover -s tests -v
```

GitHub Actions (`.github/workflows/pruebas.yml`) las corre en cada push, en Ubuntu y Windows con Python 3.10 y
3.13, junto con `reglas validar`. Las pruebas no usan red: las partidas y los datos de Community Dragon de `tests/` son sintéticos,
con el formato de las respuestas reales.
