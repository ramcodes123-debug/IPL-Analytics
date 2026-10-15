import pandas as pd


def get_match_scorecard(deliveries, match_id):
    df = deliveries[deliveries["match_id"] == match_id].copy()

    if df.empty:
        return {"match_id": match_id, "innings": {}}

    innings_data = {}

    for innings_number, group in df.groupby("innings"):
        batting_team = group["batting_team"].dropna()
        team_name = batting_team.iloc[0] if not batting_team.empty else "Unknown"

        batters = group.groupby("striker").agg(
            runs=("runs_off_bat", "sum"),
            balls=("is_legal_ball", "sum"),
            fours=("is_boundary_four", "sum"),
            sixes=("is_boundary_six", "sum"),
        ).reset_index().rename(columns={"striker": "batter"})

        batters["strike_rate"] = (
            batters["runs"] * 100 / batters["balls"].replace(0, pd.NA)
        )

        bowlers = group.groupby("bowler").agg(
            runs_conceded=("bowler_runs", "sum"),
            legal_balls=("is_legal_ball", "sum"),
        ).reset_index().rename(columns={"bowler": "bowler_name"})

        bowlers["overs"] = bowlers["legal_balls"].apply(
            lambda n: f"{int(n) // 6}.{int(n) % 6}"
        )

        innings_data[int(innings_number)] = {
            "batting_team": team_name,
            "runs": int(group["total_runs"].sum()),
            "legal_balls": int(group["is_legal_ball"].sum()),
            "wickets": int(group["player_dismissed"].notna().sum()),
            "batters": batters.sort_values("runs", ascending=False),
            "bowlers": bowlers,
        }

    return {"match_id": match_id, "innings": innings_data}


def get_over_by_over(deliveries, match_id, innings_number):
    df = deliveries[
        (deliveries["match_id"] == match_id)
        & (deliveries["innings"] == innings_number)
    ].copy()

    if df.empty:
        return pd.DataFrame()

    # Cricsheet ball values such as 0.1, 0.2 ... 19.6.
    # The integer part identifies the over in this representation.
    df["over_number"] = pd.to_numeric(
        df["ball"], errors="coerce"
    ).apply(
        lambda value: int(value) if pd.notna(value) else None
    )

    return (
        df.groupby("over_number")
        .agg(
            runs=("total_runs", "sum"),
            wickets=("player_dismissed", lambda s: s.notna().sum()),
            legal_balls=("is_legal_ball", "sum"),
        )
        .reset_index()
        .sort_values("over_number")
    )


def get_innings_summary(deliveries, match_id, innings_number):
    df = deliveries[
        (deliveries["match_id"] == match_id)
        & (deliveries["innings"] == innings_number)
    ]

    if df.empty:
        return None

    return {
        "runs": int(df["total_runs"].sum()),
        "wickets": int(df["player_dismissed"].notna().sum()),
        "legal_balls": int(df["is_legal_ball"].sum()),
        "batting_team": df["batting_team"].dropna().iloc[0],
        "bowling_team": df["bowling_team"].dropna().iloc[0],
    }
import pandas as pd

from .preprocessing import get_bowler_wicket_mask


def get_batter_bowler_matchup(deliveries, batter, bowler):
    """Return IPL batter-versus-bowler career totals from deliveries."""
    df = deliveries[
        (deliveries["striker"] == batter) & (deliveries["bowler"] == bowler)
    ].copy()
    if df.empty:
        return {
            "batter": batter, "bowler": bowler, "runs": 0, "balls_faced": 0,
            "strike_rate": 0.0, "dismissals": 0, "dot_balls": 0,
            "fours": 0, "sixes": 0, "matches": 0,
        }

    balls = df["is_batter_ball"].sum() if "is_batter_ball" in df else (
        df.get("wides", pd.Series(0, index=df.index)).fillna(0).eq(0).sum()
    )
    dots = df["is_dot_ball"].sum() if "is_dot_ball" in df else (
        df["total_runs"].fillna(0).eq(0).sum()
    )
    credited = get_bowler_wicket_mask(df)
    dismissals = (credited & df["player_dismissed"].eq(batter)).sum()
    runs = df["runs_off_bat"].sum()
    return {
        "batter": batter, "bowler": bowler, "runs": int(runs),
        "balls_faced": int(balls),
        "strike_rate": round(float(runs * 100 / balls), 2) if balls else 0.0,
        "dismissals": int(dismissals), "dot_balls": int(dots),
        "fours": int(df.get("is_boundary_four", pd.Series(0, index=df.index)).sum()),
        "sixes": int(df.get("is_boundary_six", pd.Series(0, index=df.index)).sum()),
        "matches": int(df["match_id"].nunique()) if "match_id" in df else 0,
    }
