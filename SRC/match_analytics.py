import pandas as pd


def get_match_scorecard(deliveries, match_id):
    """Generate a scorecard for every innings in a match."""

    df = deliveries[
        deliveries["match_id"] == match_id
    ].copy()

    if df.empty:
        return {
            "match_id": match_id,
            "innings": {},
        }

    innings_data = {}

    for innings_number, group in df.groupby("innings", sort=True):

        batting_teams = group["batting_team"].dropna()
        team_name = (
            batting_teams.iloc[0]
            if not batting_teams.empty
            else "Unknown"
        )

        # Batting scorecard
        batters = (
            group.groupby("striker")
            .agg(
                runs=("runs_off_bat", "sum"),
                balls=("is_legal_ball", "sum"),
                fours=("is_boundary_four", "sum"),
                sixes=("is_boundary_six", "sum"),
            )
            .reset_index()
            .rename(columns={"striker": "batter"})
        )

        batters["strike_rate"] = (
            batters["runs"] * 100
            / batters["balls"].replace(0, float("nan"))
        )

        # Bowling scorecard
        bowlers = (
            group.groupby("bowler")
            .agg(
                runs_conceded=("bowler_runs", "sum"),
                legal_balls=("is_legal_ball", "sum"),
            )
            .reset_index()
            .rename(columns={"bowler": "bowler_name"})
        )

        bowlers["overs"] = bowlers["legal_balls"].apply(
            lambda balls: f"{int(balls) // 6}.{int(balls) % 6}"
        )

        innings_data[int(innings_number)] = {
            "batting_team": team_name,
            "runs": int(group["total_runs"].sum()),
            "wickets": int(
                group["player_dismissed"].notna().sum()
            ),
            "legal_balls": int(
                group["is_legal_ball"].sum()
            ),
            "batters": batters.sort_values(
                "runs", ascending=False
            ).reset_index(drop=True),
            "bowlers": bowlers.reset_index(drop=True),
        }

    return {
        "match_id": match_id,
        "innings": innings_data,
    }


def get_over_by_over(deliveries, match_id, innings_number):
    """Calculate runs and wickets by over."""

    df = deliveries[
        (deliveries["match_id"] == match_id)
        & (deliveries["innings"] == innings_number)
    ].copy()

    if df.empty:
        return pd.DataFrame(
            columns=[
                "over_number",
                "runs",
                "wickets",
                "legal_balls",
            ]
        )

    # Cricsheet ball values typically look like 0.1, 0.2, ... 19.6.
    ball_values = pd.to_numeric(df["ball"], errors="coerce")
    df["over_number"] = ball_values.apply(
        lambda value: int(value) if pd.notna(value) else None
    )

    return (
        df.groupby("over_number")
        .agg(
            runs=("total_runs", "sum"),
            wickets=(
                "player_dismissed",
                lambda values: values.notna().sum(),
            ),
            legal_balls=("is_legal_ball", "sum"),
        )
        .reset_index()
        .sort_values("over_number")
    )


def get_innings_summary(deliveries, match_id, innings_number):
    """Return a compact summary of one innings."""

    df = deliveries[
        (deliveries["match_id"] == match_id)
        & (deliveries["innings"] == innings_number)
    ]

    if df.empty:
        return None

    batting_teams = df["batting_team"].dropna()
    bowling_teams = df["bowling_team"].dropna()

    return {
        "match_id": match_id,
        "innings": innings_number,
        "batting_team": (
            batting_teams.iloc[0]
            if not batting_teams.empty
            else "Unknown"
        ),
        "bowling_team": (
            bowling_teams.iloc[0]
            if not bowling_teams.empty
            else "Unknown"
        ),
        "runs": int(df["total_runs"].sum()),
        "wickets": int(
            df["player_dismissed"].notna().sum()
        ),
        "legal_balls": int(df["is_legal_ball"].sum()),
    }
