import pandas as pd

from .config import (
    DELIVERIES_PATH,
    MATCHES_PATH,
    REQUIRED_DELIVERY_COLUMNS,
    REQUIRED_MATCH_COLUMNS,
)


def load_data(
    deliveries_path=DELIVERIES_PATH,
    matches_path=MATCHES_PATH,
):
    """Load and validate the processed IPL datasets."""
    deliveries = pd.read_csv(deliveries_path, low_memory=False)
    matches = pd.read_csv(matches_path, low_memory=False)

    validate_columns(
        deliveries, REQUIRED_DELIVERY_COLUMNS, "deliveries"
    )
    validate_columns(matches, REQUIRED_MATCH_COLUMNS, "matches")

    return deliveries, matches


def validate_columns(df, required_columns, dataset_name):
    missing = sorted(set(required_columns) - set(df.columns))

    if missing:
        raise ValueError(
            f"{dataset_name} dataset is missing columns: {missing}"
        )


def get_dataset_summary(deliveries, matches):
    return {
        "delivery_rows": len(deliveries),
        "match_rows": len(matches),
        "delivery_match_ids": deliveries["match_id"].nunique(),
        "seasons": sorted(
            matches["season"].dropna().unique().tolist()
        ),
        "venues": matches["venue"].nunique(),
    }