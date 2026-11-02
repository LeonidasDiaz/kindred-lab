"""Rutas y valores por defecto del proyecto. Todo lo que dependa del disco sale de aquí."""
from pathlib import Path

# Raíz del proyecto: dos niveles arriba de src/kindred_lab/
RAIZ = Path(__file__).resolve().parents[2]

DATA = RAIZ / "data"
RAW = DATA / "raw" / "ddragon"           # respuestas de Data Dragon tal cual, por versión
PROCESADO = DATA / "processed"
RUNAS_DIR = PROCESADO / "runas"          # runas normalizadas y reportes de cambios

DDRAGON_BASE = "https://ddragon.leagueoflegends.com"
IDIOMA = "es_MX"
TIMEOUT_S = 30

# --- Riot API (partidas) ---
RIOT_RAW = DATA / "raw" / "riot"               # partidas y timelines tal cual, una vez por partida
REGISTRO_CSV = RAIZ / "registro" / "partidas.csv"
VALORES_RUNAS = RAIZ / "reglas" / "valores_runas.json"   # qué var1/var2/var3 es cada valor de runa
RIOT_REGION = "americas"                       # LAN (la1) se consulta por la región "americas"
COLA_SOLO_DUO = 420
CAMPEON = "Kindred"
SECRETOS = RAIZ / "secretos.json"            # clave de Riot y Riot ID; está en .gitignore

# --- Community Dragon: textos de estadísticas de fin de partida de cada runa ---
CDRAGON_RAW = DATA / "raw" / "cdragon"
CDRAGON_PERKS = "https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/{idioma}/v1/perks.json"
