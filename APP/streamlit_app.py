from pathlib import Path
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# =========================================================
# 1. PROJECT PATHS AND IMPORTS
# =========================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from SRC.data_loader import load_data
from SRC.preprocessing import prepare_deliveries, prepare_matches
from SRC.player_analytics import get_batting_stats, get_bowling_stats
from SRC.team_analytics import (
    get_team_stats,
    get_head_to_head,
    get_team_season_stats,
    get_team_top_batters,
    get_team_top_bowlers,
)
from SRC.match_analytics import get_match_scorecard
from SRC.venue_analytics import get_venue_stats, get_venue_season_stats
from SRC.matchup_analytics import get_batter_bowler_matchup


# =========================================================
# 2. PAGE CONFIGURATION AND THEME
# =========================================================
st.set_page_config(
    page_title="IPL Analytics Dashboard",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BG = "#0B1E23"
SIDEBAR = "#0F3A40"
CARD = "#134E4A"
PRIMARY = "#06B6D4"
ACCENT = "#67E8F9"
TEXT = "#E2E8F0"
MUTED = "#94A3B8"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {BG};
        color: {TEXT};
    }}

    [data-testid="stSidebar"] {{
        background-color: {SIDEBAR};
        border-right: 1px solid #226A66;
    }}

    [data-testid="stMetric"] {{
        background-color: {CARD};
        border: 1px solid #226A66;
        border-radius: 14px;
        padding: 16px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);
    }}

    [data-testid="stMetricLabel"] {{
        color: {MUTED};
    }}

    [data-testid="stMetricValue"] {{
        color: {ACCENT};
    }}

    h1, h2, h3 {{
        color: {ACCENT};
    }}

    p, label, li {{
        color: {TEXT};
    }}

    div.stButton > button {{
        background-color: {PRIMARY};
        color: #06252B;
        border: none;
        border-radius: 9px;
        font-weight: 700;
    }}

    div.stButton > button:hover {{
        background-color: {ACCENT};
        color: #06252B;
    }}

    .hero {{
        background: linear-gradient(120deg, #134E4A, #0F3A40);
        padding: 25px;
        border-radius: 16px;
        border: 1px solid #226A66;
        margin-bottom: 22px;
    }}

    .hero h1 {{
        margin-bottom: 6px;
    }}

    .hero p {{
        color: {TEXT};
        margin-bottom: 0;
    }}

    .section-note {{
        color: {MUTED};
        font-size: 0.9rem;
    }}

    div[data-baseweb="select"] > div {{
        background-color: #102F35;
        border-color: #226A66;
        border-radius: 10px;
    }}

    div[data-testid="stDataFrame"] {{
        border: 1px solid #226A66;
        border-radius: 12px;
    }}

    .block-container {{
        padding-top: 2.5rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }}

    /* Keep the Streamlit toolbar from overlapping the dashboard content. */
    [data-testid="stHeader"] {{
        background: {BG};
        height: 0;
        min-height: 0;
    }}

    [data-testid="stToolbar"] {{
        display: none;
    }}

    [data-testid="stDecoration"] {{
        display: none;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 3. LOAD AND PREPARE DATA
# =========================================================
@st.cache_data(show_spinner="Loading IPL datasets...")
def load_prepared_data():
    deliveries, matches = load_data()
    deliveries = prepare_deliveries(deliveries)
    matches = prepare_matches(matches)
    return deliveries, matches


def safe_number(value, default=0):
    """Convert a value to a safe numeric value."""
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def format_number(value):
    """Format numeric values for display."""
    number = safe_number(value, None)
    if number is None:
        return str(value)
    if number.is_integer():
        return f"{int(number):,}"
    return f"{number:,.2f}"


def display_label(value):
    """Convert a snake_case field name into a readable label."""
    return str(value).replace("_", " ").strip().title()


def metric_row(items):
    """Display a row of KPI cards."""
    if not items:
        return

    columns = st.columns(len(items))

    for column, (label, value, help_text) in zip(columns, items):
        column.metric(
            label=label,
            value=value,
            help=help_text,
        )


def show_table(data):
    """Display a DataFrame, list, dictionary, or scalar as readable content."""
    if data is None:
        st.info("No data is available.")
        return

    if isinstance(data, pd.DataFrame):
        if data.empty:
            st.info("No data is available for this selection.")
        else:
            st.dataframe(
                data,
                use_container_width=True,
                hide_index=True,
            )
        return

    if isinstance(data, pd.Series):
        show_table(data.to_frame().reset_index())
        return

    if isinstance(data, list):
        if not data:
            st.info("No data is available.")
        elif all(isinstance(item, dict) for item in data):
            show_table(pd.DataFrame(data))
        else:
            show_table(pd.DataFrame({"Value": data}))
        return

    if isinstance(data, dict):
        # Render dictionary fields as a clean label/value table.
        rows = []
        for key, value in data.items():
            if isinstance(value, (dict, list, tuple, pd.DataFrame)):
                continue
            rows.append({
                "Metric": display_label(key),
                "Value": value,
            })

        if rows:
            show_table(pd.DataFrame(rows))
        else:
            st.info("No simple summary values are available.")
        return

    st.write(data)


def show_summary_cards(data, preferred_fields=None):
    """Display dictionary values as metric cards when possible."""
    if not isinstance(data, dict) or not data:
        show_table(data)
        return

    preferred_fields = preferred_fields or []
    fields = []

    for key in preferred_fields:
        if key in data and not isinstance(data[key], (dict, list, tuple)):
            fields.append(key)

    if not fields:
        fields = [
            key for key, value in data.items()
            if isinstance(value, (int, float, np.integer, np.floating))
            and not isinstance(value, (bool, np.bool_))
        ][:6]

    if fields:
        items = []
        for key in fields:
            value = data[key]
            label = display_label(key)

            if isinstance(value, (float, np.floating)):
                display_value = format_number(value)
            else:
                display_value = format_number(value)

            items.append((
                label,
                display_value,
                f"{label} from the analytics results",
            ))

        # Streamlit displays a practical maximum of four cards per row.
        for start in range(0, len(items), 4):
            metric_row(items[start:start + 4])

    remaining = {
        key: value
        for key, value in data.items()
        if key not in fields
    }

    if remaining:
        st.markdown("#### Additional Details")
        show_table(remaining)


def style_chart(fig, title=None):
    """Apply the dashboard's dark theme to Plotly charts."""
    fig.update_layout(
        title=title,
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(color=TEXT),
        title_font=dict(color=ACCENT, size=19),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT),
        ),
        margin=dict(l=15, r=15, t=55, b=15),
    )

    fig.update_xaxes(
        gridcolor="#24434A",
        zerolinecolor="#24434A",
    )

    fig.update_yaxes(
        gridcolor="#24434A",
        zerolinecolor="#24434A",
    )

    return fig


def get_column(df, candidates):
    """Return the first candidate column present in a DataFrame."""
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return None


def get_match_history(matches_df, team_1, team_2):
    """Return matches between two teams."""
    return matches_df[
        (
            (matches_df["team_1"] == team_1)
            & (matches_df["team_2"] == team_2)
        )
        | (
            (matches_df["team_1"] == team_2)
            & (matches_df["team_2"] == team_1)
        )
    ].copy()


try:
    deliveries, matches = load_prepared_data()
except Exception as exc:
    st.error("The IPL datasets could not be loaded.")
    st.exception(exc)
    st.info(
        "Verify that DATA/PROCESSED/deliveries.csv and "
        "DATA/PROCESSED/matches.csv exist and that SRC/data_loader.py "
        "points to those files."
    )
    st.stop()


# =========================================================
# 4. BUILD FILTER OPTIONS
# =========================================================
seasons = sorted(
    pd.to_numeric(deliveries["season"], errors="coerce")
    .dropna()
    .astype(int)
    .unique()
    .tolist()
)

teams = sorted(
    set(matches["team_1"].dropna().astype(str))
    | set(matches["team_2"].dropna().astype(str))
)

players = sorted(
    set(deliveries["striker"].dropna().astype(str))
    | set(deliveries["bowler"].dropna().astype(str))
)

venues = sorted(
    deliveries["venue"].dropna().astype(str).unique().tolist()
)



# =========================================================
# 5. TOP NAVIGATION — NO GLOBAL FILTERS
# =========================================================

PAGES = [
    "Overview",
    "Player Analytics",
    "Team Analytics",
    "Head-to-Head",
    "Player vs Player",
    "Venue Analytics",
    "Match Explorer",
]

st.markdown(
    """
    <div style="
        padding: 8px 0 2px 0;
        color: #67E8F9;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 2px;
    ">
        🏏 IPL CRICKET INTELLIGENCE
    </div>
    """,
    unsafe_allow_html=True,
)

page = st.radio(
    "Dashboard Navigation",
    PAGES,
    horizontal=True,
    label_visibility="collapsed",
    key="top_navigation",
)

st.markdown(
    """
    <div style="
        height: 3px;
        background: linear-gradient(
            90deg, #06B6D4, #67E8F9, #134E4A
        );
        border-radius: 3px;
        margin: 0 0 22px 0;
    "></div>
    """,
    unsafe_allow_html=True,
)



# =========================================================
# 6. HERO HEADER
# =========================================================
st.markdown(
    """
    <div class="hero">
        <h1>🏏 IPL Analytics Dashboard</h1>
        <p>
            Explore player performance, team records, match results,
            venue trends, and season-wise cricket statistics.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)




# =========================================================
# 7. OVERVIEW
# =========================================================
if page == "Overview":
    st.subheader("Competition Overview")

    # -----------------------------------------------------
    # 7.1 PAGE-SPECIFIC SEASON FILTER
    # -----------------------------------------------------
    overview_seasons = st.multiselect(
        "Filter Overview by Season",
        options=seasons,
        default=seasons,
        key="overview_seasons",
        placeholder="Choose seasons to analyse",
        label_visibility="visible",
    )

    # Convert season columns to numeric values before filtering.
    delivery_seasons = pd.to_numeric(
        deliveries["season"], errors="coerce"
    )
    match_seasons = pd.to_numeric(
        matches["season"], errors="coerce"
    )

    filtered_deliveries = deliveries[
        delivery_seasons.isin(overview_seasons)
    ].copy()

    filtered_matches = matches[
        match_seasons.isin(overview_seasons)
    ].copy()


    if not overview_seasons:
        st.info("Select at least one season to view the overview.")
        st.stop()

    # -----------------------------------------------------
    # 7.3 KEY PERFORMANCE INDICATORS
    # -----------------------------------------------------
    st.markdown("### Tournament at a Glance")

    metric_row([
        (
            "Matches",
            f"{filtered_matches['match_id'].nunique():,}",
            "Unique matches in the selected seasons",
        ),
        (
            "Delivery Records",
            f"{len(filtered_deliveries):,}",
            "Delivery records in the selected seasons",
        ),
        (
            "Teams",
            f"{len(teams):,}",
            "Teams represented in the dataset",
        ),
        (
            "Venues",
            f"{filtered_matches['venue'].nunique():,}",
            "Venues in the selected match records",
        ),
    ])

    st.divider()

    # -----------------------------------------------------
    # 7.4 MATCHES BY SEASON
    # -----------------------------------------------------
    left, right = st.columns(2)

    with left:
        st.markdown("### Matches by Season")

        if not filtered_matches.empty:
            season_counts = (
                filtered_matches.groupby("season")["match_id"]
                .nunique()
                .reset_index(name="Matches")
            )

            season_counts["season"] = (
                pd.to_numeric(
                    season_counts["season"], errors="coerce"
                )
                .astype("Int64")
                .astype(str)
            )

            fig = px.bar(
                season_counts,
                x="season",
                y="Matches",
                text="Matches",
                color="Matches",
                color_continuous_scale=[PRIMARY, ACCENT],
            )

            fig.update_traces(textposition="outside")

            st.plotly_chart(
                style_chart(fig, "Season-wise Match Count"),
                use_container_width=True,
            )
        else:
            st.info("No matches found for the selected seasons.")

    # -----------------------------------------------------
    # 7.5 RUNS BY SEASON
    # -----------------------------------------------------
    with right:
        st.markdown("### Runs by Season")

        if not filtered_deliveries.empty:
            run_col = get_column(
                filtered_deliveries,
                ["total_runs", "runs_off_bat"],
            )

            if run_col:
                run_counts = (
                    filtered_deliveries.groupby("season")[run_col]
                    .sum()
                    .reset_index(name="Runs")
                )

                run_counts["season"] = (
                    pd.to_numeric(
                        run_counts["season"], errors="coerce"
                    )
                    .astype("Int64")
                    .astype(str)
                )

                fig = px.line(
                    run_counts,
                    x="season",
                    y="Runs",
                    markers=True,
                )

                fig.update_traces(
                    line_color=ACCENT,
                    marker_color=PRIMARY,
                    line_width=3,
                    marker_size=8,
                )

                st.plotly_chart(
                    style_chart(fig, "Season-wise Runs"),
                    use_container_width=True,
                )
            else:
                st.info("No suitable runs column was found.")
        else:
            st.info("No delivery records found for these seasons.")

    st.divider()

    # -----------------------------------------------------
    # 7.6 TEAMS WITH THE MOST WINS
    # -----------------------------------------------------
    st.markdown("### Teams with the Most Wins")

    if "winner" in filtered_matches.columns:
        winner_counts = (
            filtered_matches["winner"]
            .dropna()
            .value_counts()
            .head(10)
            .rename_axis("Team")
            .reset_index(name="Wins")
        )

        if not winner_counts.empty:
            fig = px.bar(
                winner_counts.sort_values("Wins"),
                x="Wins",
                y="Team",
                orientation="h",
                text="Wins",
                color="Wins",
                color_continuous_scale=[PRIMARY, ACCENT],
            )

            fig.update_traces(textposition="outside")

            st.plotly_chart(
                style_chart(fig, "Most Wins in Selected Seasons"),
                use_container_width=True,
            )
        else:
            st.info("No recorded winners found for these seasons.")
    else:
        st.info("The match dataset has no winner column.")

    st.divider()

    # -----------------------------------------------------
    # 7.7 RECENT MATCHES
    # -----------------------------------------------------
    st.markdown("### Recent Matches")

    recent = filtered_matches.copy()

    if "date" in recent.columns:
        recent["date"] = pd.to_datetime(
            recent["date"], errors="coerce"
        )
        recent = recent.sort_values(
            "date", ascending=False, na_position="last"
        )

    recent_columns = [
        column
        for column in [
            "date",
            "season",
            "team_1",
            "team_2",
            "winner",
            "venue",
            "player_of_match",
        ]
        if column in recent.columns
    ]

    if not recent.empty and recent_columns:
        show_table(recent[recent_columns].head(10))
    else:
        st.info("No recent matches are available for this selection.")


# =========================================================
# 8. PLAYER ANALYTICS
# =========================================================
elif page == "Player Analytics":
    st.subheader("Player Analytics")

    if not players:
        st.warning("No players were found in the dataset.")
        st.stop()

    player = st.selectbox("Select Player", players)

    stat_type = st.radio(
        "Statistics",
        ["Batting", "Bowling"],
        horizontal=True,
    )

    try:
        if stat_type == "Batting":
            stats = get_batting_stats(deliveries, player=player)
        else:
            stats = get_bowling_stats(deliveries, player=player)

        if stats.empty:
            st.info("No statistics found for this player.")
        else:
            st.markdown(f"### {player} — {stat_type}")
            player_row = stats.iloc[0]
            if stat_type == "Batting":
                metric_row([
                    ("Runs", format_number(player_row.get("runs", 0)), "Career IPL runs"),
                    ("Innings", format_number(player_row.get("innings", 0)), "Innings at the crease"),
                    ("Average", format_number(player_row.get("average", 0)), "Runs per dismissal"),
                    ("Strike Rate", format_number(player_row.get("strike_rate", 0)), "Runs per 100 balls faced"),
                    ("Fours · Sixes", f"{format_number(player_row.get('fours', 0))} · {format_number(player_row.get('sixes', 0))}", "Career boundaries"),
                ])

                # Best individual batting innings in the available delivery data.
                player_innings = deliveries[
                    deliveries["striker"].astype(str) == player
                ].copy()

                if not player_innings.empty:
                    innings_group_cols = [
                        column for column in ["match_id", "innings", "season", "start_date", "venue"]
                        if column in player_innings.columns
                    ]
                    if "match_id" in innings_group_cols and "innings" in innings_group_cols:
                        best_innings = (
                            player_innings.groupby(innings_group_cols, dropna=False)["runs_off_bat"]
                            .sum()
                            .reset_index(name="Score")
                            .sort_values("Score", ascending=False)
                        )
                        if not best_innings.empty:
                            best = best_innings.iloc[0]
                            score_text = f"{int(best['Score'])} runs"
                            context_parts = []
                            if "season" in best_innings.columns and pd.notna(best.get("season")):
                                context_parts.append(f"Season {int(best['season'])}")
                            if "venue" in best_innings.columns and pd.notna(best.get("venue")):
                                context_parts.append(str(best["venue"]))
                            if "match_id" in best_innings.columns:
                                context_parts.append(f"Match {best['match_id']}")
                            st.markdown("#### 🏏 Best Batting Score")
                            metric_row([
                                (
                                    "Highest Innings",
                                    score_text,
                                    "Highest runs scored by this batter in one innings",
                                ),
                                (
                                    "Match Details",
                                    " · ".join(context_parts) if context_parts else "Details unavailable",
                                    "Season, venue and match where available",
                                ),
                            ])
                    else:
                        st.info("Match and innings identifiers are required to calculate a best innings score.")
            else:
                metric_row([
                    ("Wickets", format_number(player_row.get("wickets", 0)), "Bowler-credited wickets"),
                    ("Matches", format_number(player_row.get("matches", 0)), "Matches bowled in"),
                    ("Economy", format_number(player_row.get("economy", 0)), "Runs conceded per over"),
                    ("Average", format_number(player_row.get("bowling_average", 0)), "Runs conceded per wicket"),
                    ("Overs", str(player_row.get("overs", "0.0")), "Legal balls expressed as overs"),
                ])

                # Best bowling innings figures, calculated from delivery records.
                player_bowling = deliveries[
                    deliveries["bowler"].astype(str) == player
                ].copy()

                if not player_bowling.empty and {"match_id", "innings", "wicket_type"}.issubset(player_bowling.columns):
                    if "is_legal_ball" in player_bowling.columns:
                        player_bowling["legal_balls"] = player_bowling["is_legal_ball"].astype(int)
                    else:
                        wides = player_bowling["wides"] if "wides" in player_bowling.columns else 0
                        noballs = player_bowling["noballs"] if "noballs" in player_bowling.columns else 0
                        player_bowling["legal_balls"] = (
                            (pd.Series(wides, index=player_bowling.index).fillna(0) == 0)
                            & (pd.Series(noballs, index=player_bowling.index).fillna(0) == 0)
                        ).astype(int)

                    if "bowler_runs" in player_bowling.columns:
                        player_bowling["runs_conceded_calc"] = pd.to_numeric(
                            player_bowling["bowler_runs"], errors="coerce"
                        ).fillna(0)
                    else:
                        batter_runs = pd.to_numeric(
                            player_bowling.get("runs_off_bat", 0), errors="coerce"
                        )
                        extras = pd.to_numeric(
                            player_bowling.get("extras", 0), errors="coerce"
                        ).fillna(0)
                        player_bowling["runs_conceded_calc"] = (
                            pd.Series(batter_runs, index=player_bowling.index).fillna(0) + extras
                        )

                    # Exclude run-outs, retired hurt, obstructing the field and other
                    # dismissals not credited to the bowler.
                    credited_dismissals = {
                        "bowled", "caught", "caught and bowled", "lbw",
                        "stumped", "hit wicket", "hit the ball twice",
                        "handled the ball",
                    }
                    player_bowling["credited_wicket"] = (
                        player_bowling["wicket_type"]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                        .str.lower()
                        .isin(credited_dismissals)
                    ).astype(int)

                    bowling_group_cols = [
                        column for column in [
                            "match_id", "innings", "season", "start_date", "venue"
                        ] if column in player_bowling.columns
                    ]
                    bowling_figures = (
                        player_bowling.groupby(bowling_group_cols, dropna=False)
                        .agg(
                            Runs_Conceded=("runs_conceded_calc", "sum"),
                            Wickets=("credited_wicket", "sum"),
                        )
                        .reset_index()
                        .sort_values(
                            ["Wickets", "Runs_Conceded"],
                            ascending=[False, True],
                        )
                    )
                    if not bowling_figures.empty:
                        best = bowling_figures.iloc[0]
                        figures_text = (
                            f"{int(best['Wickets'])}/{int(best['Runs_Conceded'])}"
                        )
                        context_parts = []
                        if "season" in bowling_figures.columns and pd.notna(best.get("season")):
                            context_parts.append(f"Season {int(best['season'])}")
                        if "venue" in bowling_figures.columns and pd.notna(best.get("venue")):
                            context_parts.append(str(best["venue"]))
                        if "match_id" in bowling_figures.columns:
                            context_parts.append(f"Match {best['match_id']}")
                        st.markdown("#### 🎯 Best Bowling Figures")
                        metric_row([
                            (
                                "Best Figures",
                                figures_text,
                                "Wickets taken / runs conceded in one innings",
                            ),
                            (
                                "Match Details",
                                " · ".join(context_parts) if context_parts else "Details unavailable",
                                "Season, venue and match where available",
                            ),
                        ])
                else:
                    st.info("Not enough match, innings or wicket data to calculate best bowling figures.")

            if stat_type == "Batting":
                player_deliveries = deliveries[
                    deliveries["striker"] == player
                ].copy()

                run_col = get_column(
                    player_deliveries,
                    ["runs_off_bat", "batter_runs"],
                )

                if run_col:
                    player_deliveries["season"] = pd.to_numeric(
                        player_deliveries["season"],
                        errors="coerce",
                    )

                    season_runs = (
                        player_deliveries.groupby("season")[run_col]
                        .sum()
                        .reset_index(name="Runs")
                        .dropna()
                    )

                    if not season_runs.empty:
                        season_runs["season"] = (
                            season_runs["season"].astype(int).astype(str)
                        )

                        fig = px.bar(
                            season_runs,
                            x="season",
                            y="Runs",
                            text="Runs",
                        )
                        fig.update_traces(marker_color=PRIMARY)

                        st.plotly_chart(
                            style_chart(
                                fig,
                                f"{player} — Runs by Season",
                            ),
                            use_container_width=True,
                        )

            else:
                player_bowling = deliveries[
                    deliveries["bowler"] == player
                ].copy()

                if "is_legal_ball" in player_bowling.columns:
                    player_bowling["legal_balls"] = (
                        player_bowling["is_legal_ball"].astype(int)
                    )
                else:
                    player_bowling["legal_balls"] = (
                        (
                            player_bowling["wides"].fillna(0) == 0
                        )
                        & (
                            player_bowling["noballs"].fillna(0) == 0
                        )
                    ).astype(int)

                player_bowling["season"] = pd.to_numeric(
                    player_bowling["season"],
                    errors="coerce",
                )

                overs = (
                    player_bowling.groupby("season")["legal_balls"]
                    .sum()
                    .reset_index(name="Legal Balls")
                    .dropna()
                )

                overs["Overs"] = overs["Legal Balls"] / 6
                overs["season"] = (
                    overs["season"].astype(int).astype(str)
                )

                if not overs.empty:
                    fig = px.bar(
                        overs,
                        x="season",
                        y="Overs",
                    )
                    fig.update_traces(marker_color=ACCENT)

                    st.plotly_chart(
                        style_chart(
                            fig,
                            f"{player} — Overs Bowled by Season",
                        ),
                        use_container_width=True,
                    )

    except Exception as exc:
        st.error("Unable to calculate this player's statistics.")
        st.exception(exc)

    st.divider()
    st.markdown("### Top Batters")

    top_n = st.slider(
        "Number of batters",
        min_value=5,
        max_value=30,
        value=10,
        key="top_batters_limit",
    )

    try:
        all_batting = get_batting_stats(deliveries)

        if not all_batting.empty:
            runs_col = get_column(all_batting, ["runs", "Runs"])
            player_col = get_column(all_batting, ["player", "Player", "striker"])

            if runs_col and player_col:
                top_batters = (
                    all_batting.sort_values(runs_col, ascending=False)
                    .head(top_n)
                )
                fig = px.bar(
                    top_batters.sort_values(runs_col),
                    x=runs_col,
                    y=player_col,
                    orientation="h",
                    color=runs_col,
                    color_continuous_scale=[PRIMARY, ACCENT],
                )
                st.plotly_chart(
                    style_chart(fig, f"Top {len(top_batters)} IPL run scorers"),
                    use_container_width=True,
                )
                with st.expander("View batting leaderboard data"):
                    show_table(top_batters)
            else:
                show_table(all_batting.head(top_n))
        else:
            st.info("No batting leaderboard is available.")

    except Exception as exc:
        st.warning(f"Unable to load the batting leaderboard: {exc}")

    st.divider()
    st.markdown("### Top Bowlers")

    bowling_top_n = st.slider(
        "Number of bowlers",
        min_value=5,
        max_value=30,
        value=10,
        key="top_bowlers_limit",
    )

    try:
        all_bowling = get_bowling_stats(deliveries)

        if not all_bowling.empty:
            wickets_col = get_column(
                all_bowling, ["wickets", "Wickets", "total_wickets"]
            )
            bowler_col = get_column(
                all_bowling, ["player", "Player", "bowler"]
            )

            if wickets_col and bowler_col:
                top_bowlers = (
                    all_bowling.sort_values(wickets_col, ascending=False)
                    .head(bowling_top_n)
                )

                fig = px.bar(
                    top_bowlers.sort_values(wickets_col),
                    x=wickets_col,
                    y=bowler_col,
                    orientation="h",
                    color=wickets_col,
                    color_continuous_scale=[PRIMARY, ACCENT],
                )
                st.plotly_chart(
                    style_chart(
                        fig,
                        f"Top {len(top_bowlers)} IPL wicket takers",
                    ),
                    use_container_width=True,
                )

                with st.expander("View bowling leaderboard data"):
                    show_table(top_bowlers)
            else:
                st.info(
                    "The bowling statistics do not contain the expected "
                    "player and wickets columns."
                )
                show_table(all_bowling.head(bowling_top_n))
        else:
            st.info("No bowling leaderboard is available.")

    except Exception as exc:
        st.warning(f"Unable to load the bowling leaderboard: {exc}")


# =========================================================
# 9. TEAM ANALYTICS
# =========================================================
elif page == "Team Analytics":
    st.subheader("Team Analytics")

    if not teams:
        st.warning("No teams were found in the dataset.")
        st.stop()

    team = st.selectbox("Select Team", teams)

    try:
        summary = get_team_stats(matches, team)

        if isinstance(summary, dict):
            # Use the actual fields returned by get_team_stats().
            preferred = [
                "matches",
                "wins",
                "losses",
                "win_percentage",
            ]

            show_summary_cards(summary, preferred_fields=preferred)

            # Display remaining non-card values as a formatted table.
            st.markdown("### Team Summary")
            show_table(summary)
        else:
            show_table(summary)

    except Exception as exc:
        st.error("Could not load the team summary.")
        st.exception(exc)

    st.divider()
    st.markdown("### Team Performance by Season")

    try:
        season_stats = get_team_season_stats(matches, team)
        show_table(season_stats)

        if isinstance(season_stats, pd.DataFrame) and not season_stats.empty:
            season_col = get_column(
                season_stats,
                ["season", "Season"],
            )
            wins_col = get_column(
                season_stats,
                ["wins", "Wins", "total_wins"],
            )

            if season_col and wins_col:
                chart_data = season_stats.copy()
                chart_data[season_col] = chart_data[season_col].astype(str)

                fig = px.line(
                    chart_data,
                    x=season_col,
                    y=wins_col,
                    markers=True,
                )
                fig.update_traces(
                    line_color=ACCENT,
                    line_width=3,
                )

                st.plotly_chart(
                    style_chart(fig, f"{team} — Wins by Season"),
                    use_container_width=True,
                )

    except Exception as exc:
        st.warning(f"Season statistics could not be displayed: {exc}")

    st.divider()
    st.markdown("### Top Batters for the Team")

    try:
        team_batters = get_team_top_batters(deliveries, team, 10)
        if not team_batters.empty:
            fig = px.bar(team_batters.sort_values("runs"), x="runs", y="player", orientation="h", color="runs", color_continuous_scale=[PRIMARY, ACCENT])
            st.plotly_chart(style_chart(fig, f"Leading run scorers · {team}"), use_container_width=True)
            with st.expander("View team batting statistics"):
                show_table(team_batters)
        else:
            st.info("No batting data is available for this team.")
    except Exception as exc:
        st.warning(f"Team batting leaderboard unavailable: {exc}")

    st.markdown("### Top Bowlers for the Team")

    try:
        team_bowlers = get_team_top_bowlers(deliveries, team, 10)
        if not team_bowlers.empty:
            fig = px.bar(team_bowlers.sort_values("wickets"), x="wickets", y="player", orientation="h", color="wickets", color_continuous_scale=[PRIMARY, ACCENT])
            st.plotly_chart(style_chart(fig, f"Leading wicket takers · {team}"), use_container_width=True)
            with st.expander("View team bowling statistics"):
                show_table(team_bowlers)
        else:
            st.info("No bowling data is available for this team.")
    except Exception as exc:
        st.warning(f"Team bowling leaderboard unavailable: {exc}")


# =========================================================
# 10. HEAD-TO-HEAD
# =========================================================
elif page == "Head-to-Head":
    st.subheader("Team Head-to-Head Comparison")

    if len(teams) < 2:
        st.warning("At least two teams are required for comparison.")
        st.stop()

    left, right = st.columns(2)

    with left:
        team_1 = st.selectbox("First Team", teams, index=0)

    with right:
        team_2 = st.selectbox("Second Team", teams, index=1)

    if team_1 == team_2:
        st.warning("Select two different teams.")
    else:
        history = get_match_history(matches, team_1, team_2)

        # Calculate the comparison from the actual match records.
        # This avoids relying on undocumented dictionary key names.
        if history.empty:
            st.info("No head-to-head matches were found for these teams.")
        else:
            total_matches = int(history["match_id"].nunique())

            if "winner" in history.columns:
                team_1_wins = int((history["winner"] == team_1).sum())
                team_2_wins = int((history["winner"] == team_2).sum())
                no_result = int(history["winner"].isna().sum())
            else:
                team_1_wins = 0
                team_2_wins = 0
                no_result = total_matches

            metric_row([
                (
                    "Matches Played",
                    f"{total_matches:,}",
                    "Recorded meetings between the two teams",
                ),
                (
                    team_1,
                    f"{team_1_wins:,}",
                    "Recorded wins",
                ),
                (
                    team_2,
                    f"{team_2_wins:,}",
                    "Recorded wins",
                ),
                (
                    "No Winner Recorded",
                    f"{no_result:,}",
                    "Matches with a missing winner field",
                ),
            ])

            comparison = pd.DataFrame({
                "Team": [team_1, team_2],
                "Wins": [team_1_wins, team_2_wins],
            })

            fig = px.bar(
                comparison,
                x="Team",
                y="Wins",
                text="Wins",
            )
            fig.update_traces(
                marker_color=PRIMARY,
                textposition="outside",
            )

            st.plotly_chart(
                style_chart(fig, "Head-to-Head Wins"),
                use_container_width=True,
            )

            try:
                # Run the project analytics function too, so its
                # result is checked without displaying raw JSON.
                result = get_head_to_head(matches, team_1, team_2)

                if isinstance(result, dict):
                    st.caption(
                        "The comparison chart above is calculated "
                        "from the match records. Additional summary "
                        "fields returned by the analytics module follow."
                    )

                    extras = {
                        key: value
                        for key, value in result.items()
                        if key not in {
                            "matches", team_1, team_2,
                            "wins", "losses", "no_result_or_tie",
                            "win_percentage",
                        }
                        and not isinstance(value, (dict, list, tuple))
                    }

                    if extras:
                        show_table(extras)

            except Exception as exc:
                st.caption(
                    f"The optional head-to-head summary function could "
                    f"not be displayed: {exc}"
                )

            st.divider()
            st.markdown("### Match History")

            if "date" in history.columns:
                history = history.sort_values(
                    "date",
                    ascending=False,
                )

            history_columns = [
                column for column in [
                    "date",
                    "season",
                    "team_1",
                    "team_2",
                    "winner",
                    "venue",
                    "player_of_match",
                ]
                if column in history.columns
            ]

            show_table(history[history_columns])


# =========================================================
# 11. PLAYER VS PLAYER — BATTER/BOWLER MATCHUPS
# =========================================================
elif page == "Player vs Player":
    st.subheader("Player vs Player")
    st.caption(
        "Compare real ball-by-ball IPL batter-versus-bowler records. "
        "Choose one of three matchup formats below."
    )

    matchup_mode = st.radio(
        "Matchup format",
        [
            "One batter vs one bowler",
            "Two batters vs one bowler",
            "One batter vs two bowlers",
        ],
        horizontal=True,
        key="pvp_mode",
    )

    batters = sorted(
        deliveries["striker"].dropna().astype(str).unique().tolist()
    )
    bowlers = sorted(
        deliveries["bowler"].dropna().astype(str).unique().tolist()
    )

    pvp_seasons = st.multiselect(
        "Filter Player Matchups by Season",
        options=seasons,
        default=seasons,
        key="pvp_seasons",
        placeholder="Choose seasons to compare",
    )

    comparison_data = deliveries[
        pd.to_numeric(deliveries["season"], errors="coerce").isin(pvp_seasons)
    ].copy()

    if not pvp_seasons:
        st.info("Select at least one season to compare player matchups.")
    elif not batters or not bowlers:
        st.warning("The delivery dataset does not contain enough player data.")
    else:
        if matchup_mode == "One batter vs one bowler":
            col1, col2 = st.columns(2)
            with col1:
                batter = st.selectbox(
                    "Batter",
                    batters,
                    key="pvp_one_batter",
                )
            with col2:
                bowler = st.selectbox(
                    "Bowler",
                    bowlers,
                    key="pvp_one_bowler",
                )
            pairs = [(batter, bowler)]

        elif matchup_mode == "Two batters vs one bowler":
            col1, col2, col3 = st.columns(3)
            with col1:
                batter_1 = st.selectbox(
                    "Batter 1",
                    batters,
                    key="pvp_batter_1",
                )
            with col2:
                batter_2 = st.selectbox(
                    "Batter 2",
                    batters,
                    index=min(1, len(batters) - 1),
                    key="pvp_batter_2",
                )
            with col3:
                bowler = st.selectbox(
                    "Bowler",
                    bowlers,
                    key="pvp_shared_bowler",
                )
            pairs = [(batter_1, bowler), (batter_2, bowler)]

        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                batter = st.selectbox(
                    "Batter",
                    batters,
                    key="pvp_shared_batter",
                )
            with col2:
                bowler_1 = st.selectbox(
                    "Bowler 1",
                    bowlers,
                    key="pvp_bowler_1",
                )
            with col3:
                bowler_2 = st.selectbox(
                    "Bowler 2",
                    bowlers,
                    index=min(1, len(bowlers) - 1),
                    key="pvp_bowler_2",
                )
            pairs = [(batter, bowler_1), (batter, bowler_2)]

        if len(pairs) == 2 and pairs[0] == pairs[1]:
            st.warning("Choose two different matchups to compare.")
        else:
            matchup_rows = [
                get_batter_bowler_matchup(comparison_data, batter_name, bowler_name)
                for batter_name, bowler_name in pairs
            ]

            matchup_df = pd.DataFrame(matchup_rows)
            matchup_df["matchup"] = [
                f"{row['batter']} vs {row['bowler']}"
                for row in matchup_rows
            ]

            if len(matchup_rows) == 1:
                result = matchup_rows[0]
                st.markdown("### Matchup summary")
                metric_row([
                    ("Runs", format_number(result.get("runs", 0)), "Runs scored by the batter against this bowler"),
                    ("Balls Faced", format_number(result.get("balls_faced", 0)), "Balls faced in this matchup"),
                    ("Strike Rate", format_number(result.get("strike_rate", 0)), "Runs per 100 balls faced"),
                    ("Dismissals", format_number(result.get("dismissals", 0)), "Dismissals credited to this bowler"),
                ])
                metric_row([
                    ("Dot Balls", format_number(result.get("dot_balls", 0)), "Deliveries where the batter scored no runs"),
                    ("Fours", format_number(result.get("fours", 0)), "Fours hit in this matchup"),
                    ("Sixes", format_number(result.get("sixes", 0)), "Sixes hit in this matchup"),
                    ("Matches", format_number(result.get("matches", 0)), "Matches containing this matchup"),
                ])

            else:
                st.markdown("### Head-to-head comparison")
                metric_row([
                    (
                        "Runs",
                        f"{format_number(matchup_rows[0].get('runs', 0))} · {format_number(matchup_rows[1].get('runs', 0))}",
                        "First matchup · second matchup",
                    ),
                    (
                        "Balls Faced",
                        f"{format_number(matchup_rows[0].get('balls_faced', 0))} · {format_number(matchup_rows[1].get('balls_faced', 0))}",
                        "First matchup · second matchup",
                    ),
                    (
                        "Strike Rate",
                        f"{safe_number(matchup_rows[0].get('strike_rate', 0)):.1f} · {safe_number(matchup_rows[1].get('strike_rate', 0)):.1f}",
                        "First matchup · second matchup",
                    ),
                    (
                        "Dismissals",
                        f"{format_number(matchup_rows[0].get('dismissals', 0))} · {format_number(matchup_rows[1].get('dismissals', 0))}",
                        "First matchup · second matchup",
                    ),
                ])

            st.markdown("### Compare statistics")
            stat_labels = {
                "runs": "Runs",
                "balls_faced": "Balls faced",
                "strike_rate": "Strike rate",
                "dismissals": "Dismissals",
                "dot_balls": "Dot balls",
                "fours": "Fours",
                "sixes": "Sixes",
            }
            stat_key = st.selectbox(
                "Statistic",
                options=list(stat_labels.keys()),
                format_func=lambda key: stat_labels[key],
                key="pvp_statistic",
            )

            fig = px.bar(
                matchup_df,
                x="matchup",
                y=stat_key,
                color="matchup",
                text=stat_key,
                color_discrete_sequence=[PRIMARY, ACCENT],
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(
                style_chart(fig, f"{stat_labels[stat_key]} by matchup"),
                use_container_width=True,
            )

            display = matchup_df.rename(
                columns={
                    "balls_faced": "Balls Faced",
                    "strike_rate": "Strike Rate",
                    "dot_balls": "Dot Balls",
                    "matches": "Matches",
                }
            )
            display_columns = [
                column for column in [
                    "batter", "bowler", "matches", "runs",
                    "Balls Faced", "Strike Rate", "dismissals",
                    "Dot Balls", "fours", "sixes",
                ]
                if column in display.columns
            ]
            show_table(display[display_columns])


# =========================================================
# 12. VENUE ANALYTICS
# =========================================================
elif page == "Venue Analytics":
    st.subheader("Venue Analytics")

    if not venues:
        st.warning("No venues were found in the dataset.")
        st.stop()

    venue = st.selectbox("Select Venue", venues)
    venue_seasons_selected = st.multiselect(
        "Filter Venue Analysis by Season",
        options=seasons,
        default=seasons,
        key="venue_seasons",
    )

    st.markdown("### IPL grounds across India")
    location_path = PROJECT_ROOT / "DATA" / "PROCESSED" / "GEOGRAPHIC" / "venue_locations.csv"
    locations = pd.read_csv(location_path)
    locations["latitude"] = pd.to_numeric(locations["latitude"], errors="coerce")
    locations["longitude"] = pd.to_numeric(locations["longitude"], errors="coerce")
    india_grounds = locations[
        locations["latitude"].between(6, 38)
        & locations["longitude"].between(68, 98)
    ].drop_duplicates("venue").copy()
    venue_match_data = matches[
        pd.to_numeric(matches["season"], errors="coerce").isin(venue_seasons_selected)
    ]
    ground_counts = venue_match_data.groupby("venue").agg(
        matches=("match_id", "nunique")
    ).reset_index()
    india_grounds = india_grounds.merge(ground_counts, on="venue", how="left").fillna({"matches": 0})
    india_grounds["map_size"] = india_grounds["matches"].clip(lower=1)
    india_grounds["selected"] = india_grounds["venue"].eq(venue)
    fig = px.scatter_geo(
        india_grounds, lat="latitude", lon="longitude", size="map_size",
        color="selected", hover_name="venue", hover_data={"city": True, "state": True, "matches": True, "latitude": False, "longitude": False, "selected": False},
        color_discrete_map={True: ACCENT, False: PRIMARY}, size_max=22,
    )
    fig.update_geos(
        lataxis_range=[6, 38], lonaxis_range=[68, 98],
        showcountries=True, countrycolor="#3B646B", showsubunits=True,
        subunitcolor="#24434A", showland=True, landcolor="#102F35",
        showocean=True, oceancolor=BG, bgcolor=BG, projection_type="mercator",
    )
    fig.update_layout(showlegend=False, height=470)
    st.plotly_chart(style_chart(fig, f"IPL stadium locations · {venue}"), use_container_width=True)
    if not india_grounds["venue"].eq(venue).any():
        st.info("This selected venue is outside India or has no verified coordinate in the processed venue-location file.")

    try:
        venue_summary = get_venue_stats(
            venue_match_data,
            venue,
        )

        st.markdown("### Venue Summary")

        if isinstance(venue_summary, dict):
            show_summary_cards(venue_summary)
        else:
            show_table(venue_summary)

    except Exception as exc:
        st.warning(f"Venue summary could not be displayed: {exc}")

    st.divider()
    st.markdown("### Venue Statistics by Season")

    try:
        venue_seasons = get_venue_season_stats(
            venue_match_data,
            venue,
        )

        show_table(venue_seasons)

        if isinstance(venue_seasons, pd.DataFrame) and not venue_seasons.empty:
            season_col = get_column(
                venue_seasons,
                ["season", "Season"],
            )

            runs_col = get_column(
                venue_seasons,
                [
                    "total_runs",
                    "runs",
                    "Runs",
                    "total_runs_scored",
                ],
            )

            if season_col and runs_col:
                chart_data = venue_seasons.copy()
                chart_data[season_col] = chart_data[season_col].astype(str)

                fig = px.line(
                    chart_data,
                    x=season_col,
                    y=runs_col,
                    markers=True,
                )
                fig.update_traces(
                    line_color=ACCENT,
                    line_width=3,
                )

                st.plotly_chart(
                    style_chart(
                        fig,
                        "Runs Recorded by Season at This Venue",
                    ),
                    use_container_width=True,
                )

    except Exception as exc:
        st.warning(f"Venue season statistics unavailable: {exc}")

    st.divider()
    st.markdown("### Venue Overview")

    venue_deliveries = deliveries[
        (deliveries["venue"] == venue)
        & pd.to_numeric(deliveries["season"], errors="coerce").isin(venue_seasons_selected)
    ].copy()

    venue_run_col = get_column(
        venue_deliveries,
        ["total_runs", "runs_off_bat"],
    )

    venue_match_count = int(
        venue_deliveries["match_id"].nunique()
    )

    venue_total_runs = (
        venue_deliveries[venue_run_col].sum()
        if venue_run_col
        else 0
    )

    metric_row([
        (
            "Delivery Records",
            f"{len(venue_deliveries):,}",
            "Delivery rows recorded at this venue",
        ),
        (
            "Total Runs",
            f"{safe_number(venue_total_runs):,.0f}",
            "Runs recorded in the delivery data",
        ),
        (
            "Matches",
            f"{venue_match_count:,}",
            "Distinct matches represented at this venue",
        ),
    ])

    if not venue_deliveries.empty and "season" in venue_deliveries.columns:
        run_col = get_column(
            venue_deliveries,
            ["total_runs", "runs_off_bat"],
        )

        if run_col:
            venue_deliveries["season"] = pd.to_numeric(
                venue_deliveries["season"],
                errors="coerce",
            )

            venue_runs = (
                venue_deliveries.groupby("season")[run_col]
                .sum()
                .reset_index(name="Runs")
                .dropna()
            )

            if not venue_runs.empty:
                venue_runs["season"] = (
                    venue_runs["season"].astype(int).astype(str)
                )

                fig = px.bar(
                    venue_runs,
                    x="season",
                    y="Runs",
                )
                fig.update_traces(marker_color=PRIMARY)

                st.plotly_chart(
                    style_chart(fig, "Runs by Season at Selected Venue"),
                    use_container_width=True,
                )


# =========================================================
# 12. MATCH EXPLORER
# =========================================================
elif page == "Match Explorer":
    st.subheader("Match Explorer")

    filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns(5)

    with filter_col1:
        match_season = st.selectbox(
            "Season",
            ["All"] + seasons,
            index=0,
        )

    with filter_col2:
        match_team = st.selectbox(
            "Team",
            ["All"] + teams,
            index=0,
        )

    with filter_col3:
        match_venue = st.selectbox("Venue", ["All"] + venues)

    with filter_col4:
        match_winner = st.selectbox("Winner", ["All"] + teams)

    with filter_col5:
        row_limit = st.selectbox(
            "Maximum rows",
            [25, 50, 100, 250],
            index=1,
        )

    match_view = matches.copy()

    if match_season != "All":
        match_view = match_view[
            pd.to_numeric(match_view["season"], errors="coerce")
            == int(match_season)
        ]

    if match_team != "All":
        match_view = match_view[
            (match_view["team_1"] == match_team)
            | (match_view["team_2"] == match_team)
        ]

    if match_venue != "All":
        match_view = match_view[match_view["venue"] == match_venue]

    if match_winner != "All":
        match_view = match_view[match_view["winner"] == match_winner]

    if "date" in match_view.columns:
        match_view = match_view.sort_values(
            "date",
            ascending=False,
        )

    st.caption(f"{len(match_view):,} matching match records")

    if not match_view.empty:
        venue_counts = match_view["venue"].value_counts().head(10).sort_values().rename_axis("Venue").reset_index(name="Matches")
        fig = px.bar(venue_counts, x="Matches", y="Venue", orientation="h", color="Matches", color_continuous_scale=[PRIMARY, ACCENT])
        st.plotly_chart(style_chart(fig, "Most active venues in this selection"), use_container_width=True)

    display_columns = [
        column for column in [
            "match_id",
            "date",
            "season",
            "team_1",
            "team_2",
            "winner",
            "venue",
            "player_of_match",
        ]
        if column in match_view.columns
    ]

    show_table(match_view[display_columns].head(row_limit))

    st.divider()
    st.markdown("### Match Scorecard")

    match_ids = sorted(
        pd.to_numeric(match_view["match_id"], errors="coerce")
        .dropna()
        .astype(int)
        .unique()
        .tolist(),
        reverse=True,
    )

    if not match_ids:
        st.info("No matches are available for the selected filters.")
    else:
        selected_match_id = st.selectbox(
            "Select Match ID",
            match_ids,
        )

        match_info = match_view[
            pd.to_numeric(match_view["match_id"], errors="coerce")
            == selected_match_id
        ]

        if not match_info.empty:
            st.markdown("#### Match Details")

            detail_columns = [
                column for column in [
                    "date",
                    "season",
                    "team_1",
                    "team_2",
                    "winner",
                    "venue",
                    "player_of_match",
                    "toss_winner",
                    "toss_decision",
                    "winner_runs",
                    "winner_wickets",
                ]
                if column in match_info.columns
            ]

            show_table(match_info[detail_columns])

        if st.button("Load Scorecard", type="primary"):
            try:
                scorecard = get_match_scorecard(
                    deliveries,
                    selected_match_id,
                )

                st.markdown("#### Scorecard")

                if isinstance(scorecard, pd.DataFrame):
                    show_table(scorecard)

                elif isinstance(scorecard, dict):
                    innings = scorecard.get("innings", {})
                    innings_rows = [
                        {
                            "Innings": f"Innings {number}",
                            "Batting Team": detail.get("batting_team", "Unknown"),
                            "Runs": detail.get("runs", 0),
                            "Wickets": detail.get("wickets", 0),
                        }
                        for number, detail in innings.items()
                        if isinstance(detail, dict)
                    ]
                    if innings_rows:
                        innings_chart = pd.DataFrame(innings_rows)
                        innings_chart["Score"] = innings_chart.apply(
                            lambda row: f"{row['Runs']}/{row['Wickets']}", axis=1
                        )
                        fig = px.bar(
                            innings_chart, x="Batting Team", y="Runs",
                            color="Batting Team", text="Score",
                            color_discrete_sequence=[PRIMARY, ACCENT],
                        )
                        st.plotly_chart(style_chart(fig, "Innings score comparison"), use_container_width=True)
                    # Render nested scorecard sections as tables
                    # instead of exposing a raw JSON viewer.
                    for section, content in scorecard.items():
                        st.markdown(
                            f"##### {display_label(section)}"
                        )

                        if isinstance(content, pd.DataFrame):
                            show_table(content)

                        elif isinstance(content, dict):
                            show_table(content)

                        elif isinstance(content, list):
                            show_table(content)

                        else:
                            st.write(content)

                elif isinstance(scorecard, list):
                    show_table(scorecard)

                else:
                    st.write(scorecard)

            except Exception as exc:
                st.error(
                    "The match was found, but the scorecard could "
                    "not be loaded."
                )
                st.exception(exc)
                st.caption(
                    "Check the get_match_scorecard() function in "
                    "SRC/match_analytics.py if this error persists."
                )


# =========================================================
# 13. FOOTER
# =========================================================
st.divider()

st.markdown(
    f"""
    <div style="text-align:center; color:{MUTED}; padding:10px;">
        IPL Analytics Dashboard · Cricket Intelligence Platform<br>
        Built with Python, Pandas, Plotly and Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)
