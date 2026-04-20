import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL = "https://www.fefa.es/lnfa-2-2025-2026/"

COLUMNS_TO_KEEP = [
    "Pos", "Equipo", "%V", "VIC", "EMP", "DER",
    "P.F", "P.C", "DIF", "DEF", "ATA"
]

REGIONS = ["cataluña", "levante", "madrid", "norte", "sur"]

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
    Parsea la tabla de jugadores de LNFA2.
    Estructura esperada: JUGADOR/A | Equipo | PTS
    Filtra filas de cookies y basura.
    """
    rows = table.find_all("tr")
    players = []
    headers = []

    for i, row in enumerate(rows):
        cols = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]

        if not cols:
            continue

        if i == 0:
            headers = cols
            continue

        if len(cols) != len(headers):
            continue

        # Filtrar basura de cookies
        if any(cols[0].startswith(junk) or cols[0] == junk for junk in COOKIE_JUNK):
            continue

        # PTS debe ser número
        pts_value = cols[2] if len(cols) > 2 else ""
        if not pts_value.isdigit():
            continue

        players.append({
            "name": cols[0],
            "team": cols[1],
            "pts": int(pts_value),
        })

    return players


def classify_region(team_name: str):
    name = team_name.lower()

    if "catal" in name:
        return "cataluña"
    if "valencia" in name or "levante" in name or "alicante" in name:
        return "levante"
    if "madrid" in name:
        return "madrid"
    if "galicia" in name or "asturias" in name or "cantabria" in name or "euskal" in name or "norte" in name:
        return "norte"
    if "andaluc" in name or "sevilla" in name or "sur" in name:
        return "sur"

    return None


def scrape_lnfa2():
    soup = get_soup()
    tables = soup.find_all("table")

    regions = {r: [] for r in REGIONS}
    games = []
    players = []

    # 🏈 STANDINGS por región
    for idx, table in enumerate(tables):
        if idx >= len(REGIONS):
            break
        regions[REGIONS[idx]] = parse_standings_table(table)

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

    # 🧑 JUGADORES — tabla con header JUGADOR/A
    for table in tables:
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if "JUGADOR/A" in headers:
            players = parse_players_table(table)
            break

    return {
        "regions": regions,
        "games": games,
        "players": players
    }
