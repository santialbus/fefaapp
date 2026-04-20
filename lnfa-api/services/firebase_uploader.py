import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Inicializar Firebase solo una vez
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()


def _upload_collection(col_ref, items: list):
    """Sube una lista de dicts a una colección, borrando primero los docs existentes."""
    # Borrar documentos existentes (para que no queden datos viejos)
    existing = col_ref.stream()
    for doc in existing:
        doc.reference.delete()

    for item in items:
        col_ref.add(item)


def upload_lnfa1(data: dict):
    """
    Sube los datos de LNFA1 a Firestore.

    Estructura en Firestore:
        lnfa1/
            meta          → { last_updated }
            standings/
                east/     → colección de equipos
                west/     → colección de equipos
            games/        → colección de partidos
            players/      → colección de jugadores
    """
    base = db.collection("lnfa1")

    # Meta
    base.document("meta").set({"last_updated": datetime.utcnow().isoformat()})

    # Standings - East
    east_ref = base.document("standings").collection("east")
    _upload_collection(east_ref, data.get("east", []))

    # Standings - West
    west_ref = base.document("standings").collection("west")
    _upload_collection(west_ref, data.get("west", []))

    # Games
    games_ref = base.document("games").collection("list")
    _upload_collection(games_ref, data.get("games", []))

    # Players
    players_ref = base.document("players").collection("list")
    _upload_collection(players_ref, data.get("players", []))

    return {
        "east": len(data.get("east", [])),
        "west": len(data.get("west", [])),
        "games": len(data.get("games", [])),
        "players": len(data.get("players", [])),
    }


def upload_lnfa2(data: dict):
    """
    Sube los datos de LNFA2 a Firestore.

    Estructura en Firestore:
        lnfa2/
            meta              → { last_updated }
            standings/
                cataluña/     → colección de equipos
                levante/      → colección de equipos
                madrid/       → colección de equipos
                norte/        → colección de equipos
                sur/          → colección de equipos
            games/            → colección de partidos
            players/          → colección de jugadores
    """
    base = db.collection("lnfa2")

    # Meta
    base.document("meta").set({"last_updated": datetime.utcnow().isoformat()})

    # Standings por región
    region_counts = {}
    for region_name, teams in data.get("regions", {}).items():
        region_ref = base.document("standings").collection(region_name)
        _upload_collection(region_ref, teams)
        region_counts[region_name] = len(teams)

    # Games
    games_ref = base.document("games").collection("list")
    _upload_collection(games_ref, data.get("games", []))

    # Players
    players_ref = base.document("players").collection("list")
    _upload_collection(players_ref, data.get("players", []))

    return {
        "regions": region_counts,
        "games": len(data.get("games", [])),
        "players": len(data.get("players", [])),
    }
