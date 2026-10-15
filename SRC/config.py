from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "DATA"
PROCESSED_DIR = DATA_DIR / "PROCESSED"

DELIVERIES_PATH = PROCESSED_DIR / "deliveries.csv"
MATCHES_PATH = PROCESSED_DIR / "matches.csv"

REQUIRED_DELIVERY_COLUMNS = [
    "match_id", "season", "start_date", "venue", "innings", "ball",
    "batting_team", "bowling_team", "striker", "bowler",
    "runs_off_bat", "extras", "wides", "noballs",
    "byes", "legbyes", "penalty", "wicket_type",
    "player_dismissed",
]

REQUIRED_MATCH_COLUMNS = [
    "match_id", "season", "date", "team_1", "team_2",
    "venue", "winner", "player_of_match", "toss_winner",
    "toss_decision", "winner_runs", "winner_wickets",
]

# Historical franchise names are mapped to their canonical names.
# This mapping is deliberately conservative.
TEAM_ALIASES = {
    "Delhi Daredevils": "Delhi Capitals",
    "Kings XI Punjab": "Punjab Kings",
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Rising Pune Supergiant": "Rising Pune Supergiants",
}