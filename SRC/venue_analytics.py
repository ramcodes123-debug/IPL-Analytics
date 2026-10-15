import pandas as pd


def get_venue_stats(matches, venue):
    df = matches[matches["venue"] == venue].copy()

    # Some alternate match exports omit participating-team fields. Venue
    # summaries still have useful match and winner data in that case.
    team_1 = df["team_1"] if "team_1" in df else pd.Series(dtype=object)
    team_2 = df["team_2"] if "team_2" in df else pd.Series(dtype=object)
    winners = df["winner"] if "winner" in df else pd.Series(dtype=object)
    awards = df["player_of_match"] if "player_of_match" in df else pd.Series(dtype=object)

    return {
        "venue": venue,
        "matches": df["match_id"].nunique() if "match_id" in df else len(df),
        "teams": sorted(set(team_1.dropna()) | set(team_2.dropna())),
        "wins_by_team": winners.value_counts(dropna=True).to_dict(),
        "player_of_match_counts": awards.value_counts(dropna=True).head(10).to_dict(),
    }


def get_venue_season_stats(matches, venue):
    df = matches[matches["venue"] == venue]

    if "season" not in df:
        return pd.DataFrame(columns=["season", "matches"])
    return df.groupby("season").agg(
        matches=("match_id", "nunique") if "match_id" in df else ("season", "size")
    ).reset_index().sort_values("season")


def get_venue_score_stats(deliveries, venue):
    df = deliveries[deliveries["venue"] == venue]

    if df.empty:
        return pd.DataFrame(
            columns=["match_id", "innings", "batting_team", "runs", "wickets"]
        )

    return (
        df.groupby(["match_id", "innings", "batting_team"])
        .agg(
            runs=("total_runs", "sum"),
            wickets=("player_dismissed", lambda s: s.notna().sum()),
        )
        .reset_index()
    )
