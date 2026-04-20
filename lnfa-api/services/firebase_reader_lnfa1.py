import firebase_admin
from firebase_admin import credentials, firestore
import re

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()


def _safe_int(value) -> int:
    """Convierte un valor a int de forma segura, devuelve 0 si falla."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def _sort_standings(teams: list) -> list:
    """
    Ordena equipos por:
      1. VIC  (victorias)        → descendente
      2. DIF  (diferencia pts)   → descendente
      3. P.F  (puntos a favor)   → descendente
    """
    return sorted(
        teams,
        key=lambda t: (
            -_safe_int(t.get("VIC", 0)),
            -_safe_int(t.get("DIF", 0)),
            -_safe_int(t.get("P.F", 0)),
        )
    )


def _natural_round_key(round_str: str) -> tuple:
    """Ordena jornadas numéricamente: Jornada 2 antes de Jornada 10."""
    numbers = re.findall(r'\d+', round_str)
    return (int(numbers[0]),) if numbers else (9999,)


def _get_last_updated() -> str:
    meta_doc = db.collection("lnfa1").document("meta").get()
    return meta_doc.to_dict().get("last_updated", "") if meta_doc.exists else ""


# ------------------------------------------------------------------
# STANDINGS
# ------------------------------------------------------------------

def get_lnfa1_standings() -> dict:
    """
    Lee East y West desde Firestore y los devuelve ordenados.
    Orden: VIC desc → DIF desc → P.F desc
    """
    base = db.collection("lnfa1")

    east = [doc.to_dict() for doc in base.document("standings").collection("east").stream()]
    west = [doc.to_dict() for doc in base.document("standings").collection("west").stream()]

    return {
        "last_updated": _get_last_updated(),
        "east": _sort_standings(east),
        "west": _sort_standings(west),
    }


# ------------------------------------------------------------------
# GAMES agrupados por jornada
# ------------------------------------------------------------------

def get_lnfa1_games() -> dict:
    """
    Lee los partidos desde Firestore agrupados por jornada,
    ordenados numéricamente. Dentro de cada jornada, por fecha.
    """
    games_docs = db.collection("lnfa1").document("games").collection("list").stream()
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

def get_lnfa1_top_players() -> dict:
    """
    Lee los jugadores desde Firestore y devuelve el top 10
    ordenado por 'pts' (puntos totales) de forma descendente.
    """
    players_docs = db.collection("lnfa1").document("players").collection("list").stream()
    players = [doc.to_dict() for doc in players_docs]

    sorted_players = sorted(players, key=lambda p: -_safe_int(p.get("pts", 0)))

    return {
        "last_updated": _get_last_updated(),
        "total_players": len(players),
        "top10": sorted_players[:10],
    }
