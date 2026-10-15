import ast
import json
import pandas as pd


def _player_is_in_squad(player, squad):
    """Check whether a player appears in a pipe-separated squad list."""
    if player is None or pd.isna(player):
        return False

    if not isinstance(squad, str) or not squad.strip():
        return False

    players = [
        name.strip()
        for name in squad.split("|")
        if name.strip()
    ]

    return str(player).strip() in players


def get_team_stats(matches, team):
    df = matches[
        (matches["team_1"] == team)
        | (matches["team_2"] == team)
    ].copy()

    wins = int((df["winner"] == team).sum())
    total = len(df)

    # Count awards only when the award recipient appears in this
    # team's recorded player list for that match.
    awards = 0

    roster_column = None
    if "team_1_players" in df.columns and "team_2_players" in df.columns:
        for _, row in df.iterrows():
            if row.get("player_of_match") is None or pd.isna(
                row.get("player_of_match")
            ):
                continue

            if row["team_1"] == team:
                roster_column = row.get("team_1_players")
            elif row["team_2"] == team:
                roster_column = row.get("team_2_players")
            else:
                continue

            if _player_is_in_squad(
                row["player_of_match"], roster_column
            ):
                awards += 1

    return {
        "team": team,
        "matches": total,
        "wins": wins,
        "losses": int(
            ((df["winner"].notna()) & (df["winner"] != team)).sum()
        ),
        "no_result_or_tie": int(df["winner"].isna().sum()),
        "win_percentage": round(wins * 100 / total, 2) if total else None,
        "player_of_match_awards": awards,
    }


def get_head_to_head(matches, team_1, team_2):
    df = matches[
        (
            (matches["team_1"] == team_1)
            & (matches["team_2"] == team_2)
        )
        | (
            (matches["team_1"] == team_2)
            & (matches["team_2"] == team_1)
        )
    ].copy()

    return {
        "team_1": team_1,
        "team_2": team_2,
        "matches": len(df),
        "team_1_wins": int((df["winner"] == team_1).sum()),
        "team_2_wins": int((df["winner"] == team_2).sum()),
        "no_result_or_tie": int(df["winner"].isna().sum()),
        "match_list": df.sort_values("date", ascending=False),
    }


def get_team_season_stats(matches, team):
    df = matches[
        (matches["team_1"] == team)
        | (matches["team_2"] == team)
    ].copy()

    df["won"] = (df["winner"] == team).astype(int)

    return (
        df.groupby("season")
        .agg(
            matches=("match_id", "nunique"),
            wins=("won", "sum"),
        )
        .reset_index()
        .sort_values("season")
    )


def get_team_top_batters(deliveries, team, limit=10):
    df = deliveries[deliveries["batting_team"] == team].copy()

    return (
        df.groupby("striker")
        .agg(
            runs=("runs_off_bat", "sum"),
            balls=("is_batter_ball", "sum"),
            fours=("is_boundary_four", "sum"),
            sixes=("is_boundary_six", "sum"),
        )
        .reset_index()
        .rename(columns={"striker": "player"})
        .sort_values("runs", ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )


def get_team_top_bowlers(deliveries, team, limit=10):
    from .player_analytics import get_bowling_stats

    df = deliveries[deliveries["bowling_team"] == team]
    stats = get_bowling_stats(df)

    return stats.head(limit).reset_index(drop=True)