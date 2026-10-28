"""Validate the published early voting data before marking it final_verified."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
d = json.loads((root / "data/processed/early_voting_2026.json").read_text())
if d["status"] != "final_verified":
    print("PENDING: primary source and parish reconciliation not complete")
    raise SystemExit(0)
assert d["reporting_period_end"] == "2026-10-27"
assert d["report_printed_at"] and d["verified_at"] and d["source_url"]
assert len(d["parishes"]) == 64
state = d["statewide"]
assert state["total"] == state["in_person"] + state["absentee"]
assert len({p["parish_code"] for p in d["parishes"]}) == 64
for p in d["parishes"]:
    assert p["total"] == p["in_person"] + p["absentee"]
    for group in ("party", "race"):
        assert sum(p["breakdowns"][group].values()) == p["total"]
for key in ("total", "in_person", "absentee"):
    assert sum(p[key] for p in d["parishes"]) == state[key]
for group in ("party", "race"):
    for key, value in state["breakdowns"][group].items():
        assert sum(p["breakdowns"][group][key] for p in d["parishes"]) == value
assert d["observations"][-1]["date"] == "2026-10-27"
print("PASS: 64 parishes and statewide totals reconcile")
