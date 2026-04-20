from fastapi import FastAPI, HTTPException
from scraper.standings import scrape_standings
from scraper.lnfa2.standings import scrape_lnfa2
from services.firebase_uploader import upload_lnfa1, upload_lnfa2
from services.firebase_reader_lnfa1 import (
    get_lnfa1_standings,
    get_lnfa1_games,
    get_lnfa1_top_players,
)
from services.firebase_reader_lnfa2 import (
    get_lnfa2_standings,
    get_lnfa2_standings_by_region,
    get_lnfa2_games,
    get_lnfa2_top_players,
)

app = FastAPI(title="LNFA Scraper 🚀")


@app.get("/")
def root():
    return {"message": "LNFA API running 🚀"}


# =========================
# LNFA 1 — SCRAPING
# =========================

@app.get("/scrape/lnfa1/standings")
def scrape_lnfa1_standings():
    try:
        data = scrape_standings()
        stats = upload_lnfa1(data)
        return {
            "message": "LNFA1 scraping completed and uploaded to Firebase ✅",
            "uploaded": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# LNFA 2 — SCRAPING
# =========================

@app.get("/scrape/lnfa2/standings")
def scrape_lnfa2_standings():
    try:
        data = scrape_lnfa2()
        stats = upload_lnfa2(data)
        return {
            "message": "LNFA2 scraping completed and uploaded to Firebase ✅",
            "uploaded": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# LNFA 1 — LECTURA BBDD
# =========================

@app.get("/lnfa1/standings")
def lnfa1_standings():
    """East y West ordenados por VIC → DIF → P.F"""
    try:
        return get_lnfa1_standings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/lnfa1/games")
def lnfa1_games():
    """Partidos agrupados por jornada"""
    try:
        return get_lnfa1_games()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/lnfa1/players/top10")
def lnfa1_top_players():
    """Top 10 jugadores por puntos"""
    try:
        return get_lnfa1_top_players()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# LNFA 2 — LECTURA BBDD
# =========================

@app.get("/lnfa2/standings")
def lnfa2_standings():
    """Todas las regiones (cataluña, levante, madrid, norte, sur) ordenadas por VIC → DIF → P.F"""
    try:
        return get_lnfa2_standings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/lnfa2/standings/{region}")
def lnfa2_standings_region(region: str):
    """
    Standings de una región concreta.
    Regiones válidas: cataluña, levante, madrid, norte, sur
    """
    try:
        return get_lnfa2_standings_by_region(region)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/lnfa2/games")
def lnfa2_games():
    """Partidos agrupados por jornada"""
    try:
        return get_lnfa2_games()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/lnfa2/players/top10")
def lnfa2_top_players():
    """Top 10 jugadores por puntos"""
    try:
        return get_lnfa2_top_players()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
