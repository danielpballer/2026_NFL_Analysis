"""Stage 4 helper: turn the research files (data/research/group_*.json) plus curated
overrides (data/manual/player_overrides.json) into data/manual/injuries_2026_wk1.json,
cross-checking each player against the 2026 roster file."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from . import config as C

RESEARCH = C.ROOT / "data" / "research"
STATUS_NORMALISE = {"exempt": "Suspended", "commissioner exempt": "Suspended", "ir-return": "IR", "ir (designated to return)": "IR"}
POS_NORMALISE = {"T": "OT", "OT": "OT", "G": "G", "OL": "OL", "C": "C", "DE": "DE", "EDGE": "EDGE", "OLB": "OLB", "DT": "DT",
                 "DL": "DL", "NT": "NT", "LB": "LB", "ILB": "ILB", "CB": "CB", "S": "S", "FS": "S", "SS": "S", "DB": "DB",
                 "WR": "WR", "TE": "TE", "RB": "RB", "FB": "FB", "QB": "QB", "K": "K", "P": "P", "LS": "LS", "LT": "LT", "RT": "RT"}


def norm_pos(p: str) -> str:
    tok = re.split(r"[/(\s]", (p or "").strip())[0].upper()
    return POS_NORMALISE.get(tok, tok or "LB")


def _last(name: str) -> str:
    toks = [t for t in re.sub(r"[^A-Za-z' ]", " ", name).split() if t.lower() not in ("jr", "sr", "ii", "iii", "iv")]
    return toks[-1].lower() if toks else name.lower()


def match_override(team: str, name: str, players: dict) -> dict:
    """Exact key first, then a unique team + last-name match (research spells names inconsistently)."""
    key = f"{team}|{name}"
    if key in players:
        return players[key]
    cands = [k for k in players if k.startswith(team + "|") and _last(k.split("|", 1)[1]) == _last(name)
             and k.split("|", 1)[1][:1].lower() == name[:1].lower()]
    return players[cands[0]] if len(cands) == 1 else {}


def roster_index() -> dict[str, tuple[str, str]]:
    r = pd.read_csv(C.RAW / "roster_2026.csv", low_memory=False)
    out = {}
    for _, x in r.iterrows():
        key = re.sub(r"[^a-z]", "", str(x.full_name).lower())
        out[key] = (x.team, x.status, x.status_description_abbr)
    return out


def build(season: int = C.SEASON, week: int = C.WEEK) -> dict:
    ovr = json.loads((C.MANUAL / "player_overrides.json").read_text())
    roster = roster_index()
    teams: dict[str, dict] = {}
    warnings = []
    for f in sorted(RESEARCH.glob("group_*.json")):
        d = json.loads(f.read_text())
        for team, info in d.get("teams", {}).items():
            entry = teams.setdefault(team, {"players": [], "notes": [], "sources": []})
            entry["notes"].extend(info.get("context_notes", []) or [])
            entry["sources"].extend(info.get("sources", []) or [])
            for p in info.get("injuries", []) or []:
                name = (p.get("player") or "").strip()
                key = f"{team}|{name}"
                if not name or key in ovr.get("drop", []):
                    continue
                status = p.get("status") or "Questionable"
                status = STATUS_NORMALISE.get(status.lower(), status)
                if status not in C.MISS_PROBABILITY:
                    status = "Questionable"
                row = {"player": name, "position": norm_pos(p.get("position", "")), "status": status,
                       "starter": bool(p.get("starter", False)), "star": False,
                       "injury": p.get("injury", ""), "source": p.get("source", "")}
                rk = re.sub(r"[^a-z]", "", name.lower())
                if rk in roster:
                    rteam, rstatus, rcode = roster[rk]
                    if rteam != team:
                        warnings.append(f"{name}: research says {team}, roster says {rteam}; dropped")
                        continue
                    row["roster_status"] = f"{rstatus}/{rcode}"
                    if rstatus in ("RES",) and status in ("Questionable", "Probable", "Returning-expected-to-play"):
                        warnings.append(f"{name}: roster reserve list but research status {status}; using roster (IR)")
                        row["status"] = "IR"
                    if rstatus == "EXE":
                        row["status"] = "Suspended"
                else:
                    row["roster_status"] = "not-on-2026-roster-file"
                row.update(match_override(team, name, ovr["players"]))
                entry["players"].append(row)
    # de-duplicate by name within team (keep the most severe status)
    sev = {s: i for i, s in enumerate(["Returning-expected-to-play", "Probable", "Questionable", "Doubtful", "Out", "Suspended", "NFI", "PUP", "IR"])}
    for team, e in teams.items():
        best = {}
        for p in e["players"]:
            k = p["player"]
            if k not in best or sev[p["status"]] > sev[best[k]["status"]]:
                best[k] = p
        e["players"] = sorted(best.values(), key=lambda p: (-sev[p["status"]], p["player"]))
        e["sources"] = sorted(set(e["sources"]))
    out = {"season": season, "week": week, "collected_on": "2026-09-05", "method": "web search summaries cross-checked with nflverse roster_2026 status codes; see data/research/", "warnings": warnings, "teams": teams}
    (C.MANUAL / f"injuries_{season}_wk{week}.json").write_text(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    o = build()
    for w in o["warnings"]:
        print("WARN", w)
    for t, e in sorted(o["teams"].items()):
        print(t, len(e["players"]), "players;", ", ".join(f"{p['player']}({p['position']},{p['status']}{',S' if p['starter'] else ''}{',*' if p['star'] else ''})" for p in e["players"] if p["starter"] or p["star"]))
