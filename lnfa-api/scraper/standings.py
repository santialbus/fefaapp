import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL = "https://www.fefa.es/lnfa-2025-2026/"

COLUMNS_TO_KEEP = [
    "Pos", "Equipo", "%V", "VIC", "EMP", "DER",
    "P.F", "P.C", "DIF", "DEF", "ATA"
]

# Palabras clave que indican una fila de cookies / basura
COOKIE_JUNK = {"HTTP", "HTTPS", "CookieConsent", "NOMBRE DE LA COOKIE", "_ga", "_gat", "_gid"}


def get_soup():
    response = requests.get(URL, verify=False)
    response.raise_for_status()
    return BeautifulSoup(response.text, "lxml")


def parse_standings_table(table):
    rows = table.find_all("tr")
    headers = []
    data = []

    for i, row in enumerate(rows):
        cols = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]

        if i == 0:
            headers = cols
            continue

        if not cols or not cols[0].isdigit():
            continue

        row_dict = dict(zip(headers, cols))
        filtered = {k: row_dict.get(k, "") for k in COLUMNS_TO_KEEP}
        data.append(filtered)

    return data


def parse_players_table(table):
    """
    Parsea la tabla de jugadores usando los headers reales de la web.
    Estructura esperada: JUGADOR/A | Equipo | Posición | PTS
    Filtra filas de cookies y basura.
    """
    rows = table.find_all("tr")
    players = []
    headers = []

    for i, row in enumerate(rows):
        cols = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]

        if not cols:
            continue

        # Primera fila con contenido = headers
        if i == 0:
            headers = cols
            continue

        # Debe tener el mismo número de columnas que los headers
        if len(cols) != len(headers):
            continue

        # Filtrar filas de cookies y basura
        if any(cols[0].startswith(junk) or cols[0] == junk for junk in COOKIE_JUNK):
            continue

        # Filtrar filas donde PTS no sea un número (más basura)
        pts_value = cols[3] if len(cols) > 3 else ""
        if not pts_value.isdigit():
            continue

        players.append({
            "name": cols[0],
            "team": cols[1],
            "position": cols[2],
            "pts": int(pts_value),
        })

    return players


def scrape_standings():
    soup = get_soup()
    tables = soup.find_all("table")

    east = []
    west = []
    games = []
    players = []

    # 🏈 STANDINGS (primeras 2 tablas)
    for idx, table in enumerate(tables):
        parsed = parse_standings_table(table)

        if idx == 0:
            east = parsed
        elif idx == 1:
            west = parsed

    # 📅 PARTIDOS
    for row in soup.find_all("tr"):
        cols = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]

        if len(cols) == 6 and "-" in cols[2]:
            games.append({
                "date": cols[0],
                "home": cols[1],
                "result": cols[2],
                "away": cols[3],
                "round": cols[5],
            })

    # 🧑 JUGADORES — buscar la tabla que tenga el header correcto
    for table in tables:
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if "JUGADOR/A" in headers:
            players = parse_players_table(table)
            break

    return {
        "east": east,
        "west": west,
        "games": games,
        "players": players
    }
