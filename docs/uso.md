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
│   ├── riot.py        cliente de la API de Riot (match-v5) con caché en disco
│   ├── cdragon.py     qué var1/var2/var3 es cada número de runa (Community Dragon)
│   ├── partidas.py    partida de Riot -> fila del registro, calibración, resumen
│   ├── temprano.py    extra: muertes y oro en los primeros minutos (no afecta las runas)
│   ├── objetivos.py   extra: dragones, Barón, torres y placas por partida
│   ├── jungla.py      extra: visión, muertes caras y dónde mueres
│   ├── momentos.py    extra: en qué tramo de 5 minutos se tuerce la partida
│   └── __main__.py    línea de comandos
├── data/
│   ├── raw/ddragon/<version>/<idioma>/   runesReforged.json tal cual (se regenera)
│   ├── raw/riot/                         partidas y timelines tal cual, una vez por partida
│   ├── raw/cdragon/                      perks.json de Community Dragon
│   └── processed/runas/                  runas_<version>.json, runas_latest.json, cambios_X_a_Y.md
├── README.md / README.en.md  presentación del proyecto (español / inglés)
├── docs/uso.md              este manual: todos los comandos
├── docs/hallazgos.md        reglas y hallazgos de juego (runas, objetos, primeros minutos)
├── reglas/
│   ├── kindred_runas.json   las 3 preguntas para elegir runas (editable a mano)
│   ├── valores_runas.json   valores de runa calibrados a mano (manda sobre Community Dragon)
│   └── kindred_objetos.json objetos defensivos por situación (solo consulta, editable a mano)
├── registro/partidas.csv    tu registro de partidas (lo llena `partidas importar`)
├── registro/partidas_respaldo.csv  respaldo viejo (oct. 2026); sus anotaciones ya están en partidas.csv
├── ejemplos/partidas_ejemplo.csv   14 partidas inventadas para probar `partidas resumen --registro` sin clave
├── rutina.ps1               después de cada partida: importar, anotar la última, resumen y tus muertes
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
  hechizos de invocador (p. ej. `Fantasma+Castigo`; las partidas viejas se completan solas desde la caché), muertes antes del minuto 10, daño que más recibiste (AD/AP, en `dano_que_me_mata` y `notas`) y los valores
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

- Copia solo una lista blanca (código, pruebas, ejemplos, reglas, `data/processed/runas/`, documentación, README,
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

1. Después de cada parche: `runas actualizar` → si hay cambios, revisa `data/processed/runas/cambios_X_a_Y.md`;
   luego `reglas validar` (si una regla apunta a una runa que ya no existe, sugiere la parecida).
2. Después de jugar: `partidas importar`, completa `alcance_temprano` si usas tus 3 preguntas, y `partidas resumen`.
   Todo eso lo hace `.\rutina.ps1`:

   ```powershell
   .\rutina.ps1
   ```

   Importa (`--cantidad 10`), te pregunta si en la selección decidiste que alguien te alcanzaba (si/no) y una nota
   opcional, los guarda con `partidas anotar ultima`, muestra `partidas resumen` y luego `jungla --ultima` (tus
   muertes de la partida que acabas de jugar). Si la importación falla
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
