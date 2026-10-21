#!/usr/bin/env python3
"""Validate the processed October 1, 2026 Louisiana registration snapshot."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
STATE_FILE = DATA / "registration_statewide_2026-10-01.csv"
DISTRICT_FILE = DATA / "registration_districts_2026-10-01.csv"

FIELDS = [
    "total_registered",
    "white_registered",
    "black_registered",
    "other_race_registered",
    "democratic",
    "republican",
    "no_party",
    "other_parties",
]


def read_one(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1:
        raise ValueError(f"Expected one statewide row in {path}; found {len(rows)}")
    return rows[0]


def read_many(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    statewide = read_one(STATE_FILE)
    districts = read_many(DISTRICT_FILE)
    errors: list[str] = []

    if len(districts) != 6:
        errors.append(f"expected six districts; found {len(districts)}")

    for field in FIELDS:
        state_value = int(statewide[field])
        district_sum = sum(int(row[field]) for row in districts)
        if state_value != district_sum:
            errors.append(f"{field}: statewide={state_value:,}; districts={district_sum:,}")

    district_ids = sorted(int(row["district"]) for row in districts)
    if district_ids != [1, 2, 3, 4, 5, 6]:
        errors.append(f"district IDs are {district_ids}, expected 1-6")

    if errors:
        raise SystemExit("Registration validation failed:\n- " + "\n- ".join(errors))

    print("Registration validation passed.")
    print("Six districts reconcile exactly to statewide controls for all tested fields.")


if __name__ == "__main__":
    main()
