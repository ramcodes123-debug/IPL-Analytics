import numpy as np
import pandas as pd

from .preprocessing import (
    get_bowler_wicket_mask,
    safe_divide,
)


def get_batting_stats(deliveries, player=None):
    df = deliveries.copy()

    if player:
        df = df[df["striker"] == player].copy()

    # Count each match + innings combination separately.
    df["_innings_key"] = (
        df["match_id"].astype(str)
        + "_"
        + df["innings"].astype(str)
    )

    result = df.groupby("striker", dropna=True).agg(
        innings=("_innings_key", "nunique"),
        runs=("runs_off_bat", "sum"),
        balls=("is_batter_ball", "sum"),
        fours=("is_boundary_four", "sum"),
        sixes=("is_boundary_six", "sum"),
        matches=("match_id", "nunique"),
    ).reset_index()

    result = result.rename(columns={"striker": "player"})

    # Calculate dismissals from the full dataset so that a player
    # dismissed as a non-striker is not accidentally excluded.
    dismissal_df = deliveries[
        deliveries["player_dismissed"].notna()
    ].copy()

    dismissal_df["_innings_key"] = (
        dismissal_df["match_id"].astype(str)
        + "_"
        + dismissal_df["innings"].astype(str)
    )

    dismissals = (
        dismissal_df.groupby("player_dismissed")["_innings_key"]
        .nunique()
        .rename("dismissals")
    )

    result = result.merge(
        dismissals,
        left_on="player",
        right_index=True,
        how="left",
    )

    result["dismissals"] = result["dismissals"].fillna(0)

    result["average"] = result.apply(
        lambda row: safe_divide(
            row["runs"], row["dismissals"]
        ),
        axis=1,
    )

    result["strike_rate"] = result.apply(
        lambda row: safe_divide(
            row["runs"] * 100, row["balls"]
        ),
        axis=1,
    )

    return result.sort_values(
        "runs", ascending=False
    ).reset_index(drop=True)


def get_bowling_stats(deliveries, player=None):
    df = deliveries.copy()

    if player:
        df = df[df["bowler"] == player].copy()

    df["credited_wicket"] = get_bowler_wicket_mask(df)

    result = df.groupby("bowler", dropna=True).agg(
        runs_conceded=("bowler_runs", "sum"),
        legal_balls=("is_legal_ball", "sum"),
        matches=("match_id", "nunique"),
    ).reset_index().rename(columns={"bowler": "player"})

    wickets = (
        df[df["credited_wicket"]]
        .groupby("bowler")
        .size()
        .rename("wickets")
    )

    result = result.merge(
        wickets,
        left_on="player",
        right_index=True,
        how="left",
    )

    result["wickets"] = result["wickets"].fillna(0).astype(int)

    result["overs"] = result["legal_balls"].apply(
        lambda balls: f"{int(balls) // 6}.{int(balls) % 6}"
    )

    result["economy"] = result.apply(
        lambda row: safe_divide(
            row["runs_conceded"] * 6,
            row["legal_balls"],
        ),
        axis=1,
    )

    result["bowling_average"] = result.apply(
        lambda row: safe_divide(
            row["runs_conceded"], row["wickets"]
        ),
        axis=1,
    )

    result["bowling_strike_rate"] = result.apply(
        lambda row: safe_divide(
            row["legal_balls"], row["wickets"]
        ),
        axis=1,
    )

    return result.sort_values(
        ["wickets", "economy"],
        ascending=[False, True],
    ).reset_index(drop=True)


def get_player_top_performances(deliveries, player, limit=5):
    df = deliveries[deliveries["striker"] == player].copy()

    performances = df.groupby(
        ["match_id", "season", "start_date",
         "batting_team", "bowling_team"]
    ).agg(
        runs=("runs_off_bat", "sum"),
        balls=("is_batter_ball", "sum"),
        fours=("is_boundary_four", "sum"),
        sixes=("is_boundary_six", "sum"),
    ).reset_index()

    performances["strike_rate"] = (
        performances["runs"] * 100
        / performances["balls"].replace(0, np.nan)
    )

    return performances.sort_values(
        ["runs", "strike_rate"],
        ascending=False,
    ).head(limit).reset_index(drop=True)


def get_player_season_stats(deliveries, player):
    df = deliveries[deliveries["striker"] == player].copy()

    return (
        df.groupby("season")
        .agg(
            runs=("runs_off_bat", "sum"),
            balls=("is_batter_ball", "sum"),
            fours=("is_boundary_four", "sum"),
            sixes=("is_boundary_six", "sum"),
        )
        .reset_index()
        .sort_values("season")
    )


def get_player_of_match_awards(matches, player):
    if "player_of_match" not in matches.columns:
        return 0

    return int(
        (matches["player_of_match"] == player).sum()
    )