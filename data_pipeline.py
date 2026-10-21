#!/usr/bin/env python3
"""Current public-data pipeline entry point.

The original 2026 redistricting pipeline is preserved at:
    archive/data_pipeline_legacy.py

This root script now validates the October 1, 2026 Louisiana Secretary of
State registration snapshot used by the live voter-information dashboard.

It intentionally does not regenerate the archived Census/VAP redistricting
findings. Historical redistricting analysis should be reproduced from the
archived pipeline only after its documented methodology issues are resolved.
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "processed"
STATE_FILE = DATA / "registration_statewide_2026-10-01.csv"
DISTRICT_FILE = DATA / "registration_districts_2026-10-01.csv"

FIELDS = (
    "total_registered",
    "white_registered",
    "black_registered",
    "other_race_registered",
    "democratic",
    "republican",
    "no_party",
    "other_parties",
)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    statewide_rows = _read_rows(STATE_FILE)
    districts = _read_rows(DISTRICT_FILE)

    if len(statewide_rows) != 1:
        raise SystemExit(f"Expected one statewide row; found {len(statewide_rows)}")
    if len(districts) != 6:
        raise SystemExit(f"Expected six congressional districts; found {len(districts)}")

    statewide = statewide_rows[0]
    errors: list[str] = []

    for field in FIELDS:
        state_value = int(statewide[field])
        district_sum = sum(int(row[field]) for row in districts)
        if state_value != district_sum:
            errors.append(
                f"{field}: statewide={state_value:,}; district_sum={district_sum:,}"
            )

    district_ids = sorted(int(row["district"]) for row in districts)
    if district_ids != [1, 2, 3, 4, 5, 6]:
        errors.append(f"district IDs are {district_ids}, expected [1, 2, 3, 4, 5, 6]")

    if errors:
        raise SystemExit("Validation failed:\n- " + "\n- ".join(errors))

    black_total = int(statewide["black_registered"])
    d2_black = int(next(row for row in districts if row["district"] == "2")["black_registered"])
    outside_d2 = black_total - d2_black

    print("October 1, 2026 registration snapshot validated.")
    print(f"Statewide registered: {int(statewide['total_registered']):,}")
    print(f"Black registered statewide: {black_total:,}")
    print(f"Black registered in District 2: {d2_black:,}")
    print(
        "Black registered outside District 2: "
        f"{outside_d2:,} ({outside_d2 / black_total * 100:.2f}%)"
    )
    print("All district party-and-race totals reconcile exactly to statewide controls.")


if __name__ == "__main__":
    main()
