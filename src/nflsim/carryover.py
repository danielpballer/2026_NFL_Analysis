"""Carry last week's long-term absences (IR / PUP / NFI / Suspended) into this week's research
folder as group_E_carryover.json so they are not forgotten when the news cycle moves on.
Players who were activated get removed through the week's override drop list.

    PYTHONPATH=src NFLSIM_WEEK=5 python -m nflsim.carryover
"""
from __future__ import annotations

import datetime as dt
import json

from . import config as C

LONG_TERM = {"IR", "PUP", "NFI", "Suspended"}


def build(season: int = C.SEASON, week: int = C.WEEK) -> dict:
    src = C.ROOT / "data" / "manual" / f"injuries_{season}_wk{week - 1}.json"
    prev = json.loads(src.read_text())
    teams = {}
    for team, blob in prev["teams"].items():
        rows = []
        for p in blob["players"]:
            if p["status"] not in LONG_TERM:
                continue
            rows.append({"player": p["player"], "position": p["position"], "status": p["status"],
                         "starter": bool(p.get("starter", False)),
                         "injury": f"carried over from Week {week - 1}: {p.get('injury', '')[:90]}",
                         "source": str(src.relative_to(C.ROOT))})
        if rows:
            teams[team] = {"injuries": rows}
    out = {"collected_on": dt.date.today().isoformat(),
           "note": f"Automatic carry-over of Week {week - 1} IR/PUP/NFI/suspension absences; remove via the wk{week} drop list if a player was activated.",
           "teams": teams}
    dest = C.ROOT / "data" / "research" / f"wk{week}" / "group_E_carryover.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2))
    print(f"wrote {dest} ({sum(len(t['injuries']) for t in teams.values())} players, {len(teams)} teams)")
    return out


if __name__ == "__main__":
    build()
