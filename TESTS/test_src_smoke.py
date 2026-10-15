from SRC.data_loader import load_data, get_dataset_summary
from SRC.preprocessing import prepare_deliveries, prepare_matches
from SRC.player_analytics import get_batting_stats, get_bowling_stats
from SRC.team_analytics import get_team_stats


def main():
    deliveries, matches = load_data()

    deliveries = prepare_deliveries(deliveries)
    matches = prepare_matches(matches)

    print("DATA SUMMARY")
    print(get_dataset_summary(deliveries, matches))

    print("\nTOP 10 BATTERS")
    print(get_batting_stats(deliveries).head(10).to_string(index=False))

    print("\nTOP 10 BOWLERS")
    print(get_bowling_stats(deliveries).head(10).to_string(index=False))

    teams = sorted(
        set(matches["team_1"].dropna())
        | set(matches["team_2"].dropna())
    )

    if teams:
        print("\nTEAM SUMMARY")
        print(get_team_stats(matches, teams[0]))

    print("\nSRC smoke test completed.")


if __name__ == "__main__":
    main()