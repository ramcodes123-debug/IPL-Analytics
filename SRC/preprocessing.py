import numpy as np
import pandas as pd

from .config import TEAM_ALIASES


NUMERIC_DELIVERY_COLUMNS = [
    "runs_off_bat",
    "extras",
    "wides",
    "noballs",
    "byes",
    "legbyes",
    "penalty",
]


def normalize_team_name(name):
    if pd.isna(name):
        return name

    name = str(name).strip()
    return TEAM_ALIASES.get(name, name)


def prepare_deliveries(deliveries):
    """Create consistent numeric columns and cricket calculations."""
    df = deliveries.copy()

    for col in NUMERIC_DELIVERY_COLUMNS:
        if col not in df.columns:
            df[col] = 0

        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    for col in ["batting_team", "bowling_team"]:
        df[col] = df[col].map(normalize_team_name)

    df["runs_off_bat"] = df["runs_off_bat"].clip(lower=0)
    df["extras"] = df["extras"].clip(lower=0)

    # Total runs recorded for the delivery.
    df["total_runs"] = df["runs_off_bat"] + df["extras"]

    # Wides and no-balls do not count as legal balls.
    df["is_legal_ball"] = (
        (df["wides"] == 0) & (df["noballs"] == 0)
    )

    # A batter generally faces a no-ball, but does not face a wide.
    df["is_batter_ball"] = df["wides"] == 0

    # Bowler-conceded runs exclude byes, leg-byes and penalty runs.
    df["bowler_runs"] = (
        df["runs_off_bat"] + df["wides"] + df["noballs"]
    )

    df["is_boundary_four"] = (
        (df["runs_off_bat"] == 4)
        & (df.get("non_boundary", 0).fillna(0) == 0)
    )

    df["is_boundary_six"] = (
        (df["runs_off_bat"] == 6)
        & (df.get("non_boundary", 0).fillna(0) == 0)
    )

    df["is_dot_ball"] = (
        (df["total_runs"] == 0) & df["is_legal_ball"]
    )

    df["season"] = pd.to_numeric(df["season"], errors="coerce")

    return df


def prepare_matches(matches):
    df = matches.copy()

    for col in ["team_1", "team_2", "winner", "toss_winner"]:
        if col in df.columns:
            df[col] = df[col].map(normalize_team_name)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["season"] = pd.to_numeric(df["season"], errors="coerce")

    return df


def get_bowler_wicket_mask(deliveries):
    """Wickets credited to the bowler under standard cricket rules."""
    credited_types = {
        "bowled",
        "caught",
        "caught and bowled",
        "lbw",
        "stumped",
        "hit wicket",
        "hit the ball twice",
    }

    return (
        deliveries["wicket_type"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(credited_types)
    )


def balls_to_overs(legal_balls):
    """Format a legal-ball count as cricket overs, e.g. 19.4."""
    legal_balls = int(legal_balls)
    return f"{legal_balls // 6}.{legal_balls % 6}"


def safe_divide(numerator, denominator):
    if denominator is None or pd.isna(denominator) or denominator == 0:
        return np.nan
    return numerator / denominator