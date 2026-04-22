import firebase_admin
from firebase_admin import credentials, firestore
import re

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

REGIONS = ["cataluña", "levante", "madrid", "norte", "sur"]


def _safe_int(value) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def _sort_standings(teams: list) -> list:
    """Ordena equipos: VIC desc → DIF desc → P.F desc"""
    return sorted(
        teams,
        key=lambda t: (
            -_safe_int(t.get("VIC", 0)),
            -_safe_int(t.get("DIF", 0)),
            -_safe_int(t.get("P.F", 0)),
        )
    )


def _natural_round_key(round_str: str) -> tuple:
    numbers = re.findall(r'\d+', round_str)
    return (int(numbers[0]),) if numbers else (9999,)


def _get_last_updated() -> str:
    meta_doc = db.collection("lnfa2").document("meta").get()
    return meta_doc.to_dict().get("last_updated", "") if meta_doc.exists else ""


# ------------------------------------------------------------------
# STANDINGS — todas las regiones
# ------------------------------------------------------------------

def get_lnfa2_standings() -> dict:
    base = db.collection("lnfa2").document("standings")

    standings = {}
    for region in REGIONS:
        docs = base.collection(region).stream()
        teams = [doc.to_dict() for doc in docs]
        standings[region] = _sort_standings(teams)

    return {
        "last_updated": _get_last_updated(),
        "standings": standings,
    }


# ------------------------------------------------------------------
# STANDINGS — una región concreta
# ------------------------------------------------------------------

def get_lnfa2_standings_by_region(region: str) -> dict:
    region = region.lower()
    if region not in REGIONS:
        raise ValueError(f"Región '{region}' no válida. Opciones: {REGIONS}")

    docs = db.collection("lnfa2").document("standings").collection(region).stream()
    teams = [doc.to_dict() for doc in docs]

    return {
        "last_updated": _get_last_updated(),
        "region": region,
        "standings": _sort_standings(teams),
    }


# ------------------------------------------------------------------
# GAMES agrupados por jornada
# ------------------------------------------------------------------

def get_lnfa2_games() -> dict:
    games_docs = db.collection("lnfa2").document("games").collection("list").stream()
    games = [doc.to_dict() for doc in games_docs]

    rounds: dict[str, list] = {}
    for game in games:
        round_key = game.get("round", "Sin jornada")
        rounds.setdefault(round_key, []).append(game)

    for round_key in rounds:
        rounds[round_key] = sorted(rounds[round_key], key=lambda g: g.get("date", ""))

    sorted_rounds = dict(sorted(rounds.items(), key=lambda item: _natural_round_key(item[0])))

    return {
        "last_updated": _get_last_updated(),
        "total_games": len(games),
        "rounds": sorted_rounds,
    }


# ------------------------------------------------------------------
# TOP 10 JUGADORES
# ------------------------------------------------------------------

def get_lnfa2_top_players() -> dict:
    players_docs = db.collection("lnfa2").document("players").collection("list").stream()
    players = [doc.to_dict() for doc in players_docs]

    # Ordenar por pts (entero) descendente
    sorted_players = sorted(players, key=lambda p: -_safe_int(p.get("pts", 0)))

    return {
        "last_updated": _get_last_updated(),
        "total_players": len(players),
        "top10": sorted_players[:10],
    }


# ------------------------------------------------------------------
# DETALLE DE EQUIPO
# ------------------------------------------------------------------

def get_lnfa2_team_detail(team_name: str) -> dict:
    """
    Devuelve las stats de un equipo (buscándolo en las 5 regiones)
    + top 5 jugadores de ese equipo.
    """
    base = db.collection("lnfa2").document("standings")

    team_data = None
    region = None

    for reg in REGIONS:
        docs = base.collection(reg).stream()
        for doc in docs:
            t = doc.to_dict()
            if t.get("Equipo", "").lower() == team_name.lower():
                team_data = t
                region = reg
                break
        if team_data:
            break

    if not team_data:
        raise ValueError(f"Equipo '{team_name}' no encontrado en LNFA2")

    # Top 5 jugadores del equipo
    players_docs = db.collection("lnfa2").document("players").collection("list").stream()
    team_players = [
        doc.to_dict()
        for doc in players_docs
        if doc.to_dict().get("team", "").lower() == team_name.lower()
    ]

    sorted_team_players = sorted(team_players, key=lambda p: -_safe_int(p.get("pts", 0)))

    return {
        "last_updated": _get_last_updated(),
        "team": team_data,
        "region": region,
        "top_players": sorted_team_players[:5],
        "total_team_players": len(team_players),
    }
