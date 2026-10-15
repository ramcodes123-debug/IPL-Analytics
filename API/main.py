
from functools import lru_cache

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from SRC.data_loader import load_data
from SRC.preprocessing import prepare_deliveries, prepare_matches
from SRC.player_analytics import (
    get_batting_stats,
    get_bowling_stats,
    get_player_season_stats,
    get_player_of_match_awards,
)
from SRC.team_analytics import (
    get_team_stats,
    get_head_to_head,
    get_team_season_stats,
    get_team_top_batters,
    get_team_top_bowlers,
)
from SRC.match_analytics import get_match_scorecard
from SRC.venue_analytics import (
    get_venue_stats,
    get_venue_season_stats,
)


app = FastAPI(
    title="IPL Analytics API",
    description=(
        "API for exploring IPL batting, bowling, teams, matches, "
        "head-to-head records, and venues."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def get_data():
    """Load and prepare the processed IPL datasets once."""
    deliveries, matches = load_data()

    deliveries = prepare_deliveries(deliveries)
    matches = prepare_matches(matches)

    return deliveries, matches


def json_safe(value):
    """Convert pandas and NumPy values into JSON-compatible values."""
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]

    if isinstance(value, pd.DataFrame):
        return json_safe(value.to_dict(orient="records"))

    if isinstance(value, pd.Series):
        return json_safe(value.to_dict())

    if isinstance(value, np.ndarray):
        return json_safe(value.tolist())

    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)

    if isinstance(value, (np.bool_,)):
        return bool(value)

    if value is pd.NA or value is pd.NaT:
        return None

    if isinstance(value, float) and not np.isfinite(value):
        return None

    if pd.isna(value) if not isinstance(value, (list, dict, tuple)) else False:
        return None

    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()

    return value


def records(df):
    """Return a DataFrame as JSON-safe records."""
    return json_safe(df.reset_index(drop=True).to_dict(orient="records"))


@app.get("/", tags=["General"])
def root():
    return {
        "message": "Welcome to the IPL Analytics API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["General"])
def health():
    try:
        deliveries, matches = get_data()
        return {
            "status": "healthy",
            "delivery_rows": len(deliveries),
            "match_rows": len(matches),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not load IPL datasets: {exc}",
        )


@app.get("/summary", tags=["General"])
def dataset_summary():
    deliveries, matches = get_data()

    seasons = sorted(
        int(s)
        for s in deliveries["season"].dropna().unique()
    )

    return {
        "delivery_rows": len(deliveries),
        "match_rows": len(matches),
        "distinct_matches": int(matches["match_id"].nunique()),
        "seasons": seasons,
        "venues": int(deliveries["venue"].nunique()),
    }


@app.get("/players", tags=["Players"])
def list_players(
    search: str = Query(default="", description="Optional player-name search"),
    limit: int = Query(default=100, ge=1, le=500),
):
    deliveries, _ = get_data()

    players = sorted(
        set(deliveries["striker"].dropna().astype(str))
        | set(deliveries["bowler"].dropna().astype(str))
    )

    if search:
        players = [
            p for p in players
            if search.casefold() in p.casefold()
        ]

    return {"count": len(players), "players": players[:limit]}


@app.get("/players/{player}/batting", tags=["Players"])
def player_batting(player: str):
    deliveries, _ = get_data()

    result = get_batting_stats(deliveries, player=player)

    if result.empty:
        raise HTTPException(status_code=404, detail="Player not found")

    return records(result)


@app.get("/players/{player}/bowling", tags=["Players"])
def player_bowling(player: str):
    deliveries, _ = get_data()

    result = get_bowling_stats(deliveries, player=player)

    if result.empty:
        raise HTTPException(status_code=404, detail="Player not found")

    return records(result)


@app.get("/players/{player}/seasons", tags=["Players"])
def player_seasons(player: str):
    deliveries, _ = get_data()

    if not (deliveries["striker"] == player).any():
        raise HTTPException(status_code=404, detail="Player not found")

    return records(get_player_season_stats(deliveries, player))


@app.get("/players/{player}/awards", tags=["Players"])
def player_awards(player: str):
    _, matches = get_data()

    if "player_of_match" not in matches.columns:
        return {"player": player, "awards": 0}

    awards = get_player_of_match_awards(matches, player)

    return {"player": player, "awards": awards}


@app.get("/teams", tags=["Teams"])
def list_teams():
    _, matches = get_data()

    teams = sorted(
        set(matches["team_1"].dropna().astype(str))
        | set(matches["team_2"].dropna().astype(str))
    )

    return {"count": len(teams), "teams": teams}


@app.get("/teams/{team}/summary", tags=["Teams"])
def team_summary(team: str):
    _, matches = get_data()

    valid_teams = set(matches["team_1"].dropna()) | set(
        matches["team_2"].dropna()
    )

    if team not in valid_teams:
        raise HTTPException(status_code=404, detail="Team not found")

    return json_safe(get_team_stats(matches, team))


@app.get("/teams/{team}/seasons", tags=["Teams"])
def team_seasons(team: str):
    _, matches = get_data()

    valid_teams = set(matches["team_1"].dropna()) | set(
        matches["team_2"].dropna()
    )

    if team not in valid_teams:
        raise HTTPException(status_code=404, detail="Team not found")

    return records(get_team_season_stats(matches, team))


@app.get("/teams/{team}/top-batters", tags=["Teams"])
def team_top_batters(
    team: str,
    limit: int = Query(default=10, ge=1, le=100),
):
    deliveries, _ = get_data()

    if not (deliveries["batting_team"] == team).any():
        raise HTTPException(status_code=404, detail="Team not found")

    return records(get_team_top_batters(deliveries, team, limit))


@app.get("/teams/{team}/top-bowlers", tags=["Teams"])
def team_top_bowlers(
    team: str,
    limit: int = Query(default=10, ge=1, le=100),
):
    deliveries, _ = get_data()

    if not (deliveries["bowling_team"] == team).any():
        raise HTTPException(status_code=404, detail="Team not found")

    return records(get_team_top_bowlers(deliveries, team, limit))


@app.get("/head-to-head", tags=["Teams"])
def head_to_head(team_1: str, team_2: str):
    _, matches = get_data()

    if team_1 == team_2:
        raise HTTPException(
            status_code=400,
            detail="Choose two different teams",
        )

    result = get_head_to_head(matches, team_1, team_2)

    if result["matches"] == 0:
        raise HTTPException(
            status_code=404,
            detail="No head-to-head matches found for these teams",
        )

    return json_safe(result)


@app.get("/venues", tags=["Venues"])
def list_venues():
    deliveries, _ = get_data()

    venues = sorted(
        deliveries["venue"].dropna().astype(str).unique().tolist()
    )

    return {"count": len(venues), "venues": venues}


@app.get("/venues/{venue}/stats", tags=["Venues"])
def venue_stats(venue: str):
    deliveries, matches = get_data()

    if not (deliveries["venue"] == venue).any():
        raise HTTPException(status_code=404, detail="Venue not found")

    result = get_venue_stats(deliveries, matches, venue)

    return json_safe(result)


@app.get("/venues/{venue}/seasons", tags=["Venues"])
def venue_seasons(venue: str):
    deliveries, matches = get_data()

    if not (deliveries["venue"] == venue).any():
        raise HTTPException(status_code=404, detail="Venue not found")

    result = get_venue_season_stats(deliveries, matches, venue)

    return json_safe(result)


@app.get("/matches", tags=["Matches"])
def list_matches(
    season: int | None = None,
    team: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
):
    _, matches = get_data()
    df = matches.copy()

    if season is not None:
        df = df[pd.to_numeric(df["season"], errors="coerce") == season]

    if team:
        df = df[
            (df["team_1"] == team)
            | (df["team_2"] == team)
        ]

    if "date" in df.columns:
        df = df.sort_values("date", ascending=False)

    return {
        "count": len(df),
        "matches": records(df.head(limit)),
    }


@app.get("/matches/{match_id}/scorecard", tags=["Matches"])
def match_scorecard(match_id: int):
    deliveries, matches = get_data()

    match_rows = matches[matches["match_id"] == match_id]

    if match_rows.empty:
        raise HTTPException(status_code=404, detail="Match not found")

    try:
        result = get_match_scorecard(deliveries, match_id)
        return json_safe(result)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "The match was found, but the scorecard function failed. "
                f"Check its signature and implementation: {exc}"
            ),
        )
