"""Stage 4 helper: turn the research files (data/research/group_*.json) plus curated
overrides (data/manual/player_overrides.json) into data/manual/injuries_2026_wk1.json,
cross-checking each player against the 2026 roster file."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from . import config as C

RESEARCH_ROOT = C.ROOT / "data" / "research"
OFFICIAL_STATUS = {"Out": "Out", "Doubtful": "Doubtful", "Questionable": "Questionable"}
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
    weekly = C.RAW / f"roster_weekly_{C.SEASON}.csv"
    if weekly.exists():
        r = pd.read_csv(weekly, low_memory=False)
        r = r[r.week == r.week.max()]
    else:
        r = pd.read_csv(C.RAW / "roster_2026.csv", low_memory=False)
    out: dict[str, list] = {}
    for _, x in r.iterrows():
        key = re.sub(r"[^a-z]", "", str(x.full_name).lower())
        out.setdefault(key, []).append((x.team, x.status, x.status_description_abbr))
    return out


def official_report(season: int, week: int) -> list[dict]:
    """Rows from the nflverse injuries file for this week (published Wed-Fri of game week)."""
    path = C.RAW / f"injuries_{season}.csv"
    if not path.exists():
        return []
    inj = pd.read_csv(path)
    inj = inj[(inj.season == season) & (inj.week == week) & (inj.game_type == "REG") & inj.report_status.isin(OFFICIAL_STATUS)]
    return [{"team": r.team, "player": r.full_name, "position": r.position, "status": OFFICIAL_STATUS[r.report_status],
             "injury": f"official report: {r.report_primary_injury}", "starter": True, "source": "nflverse injuries file"}
            for _, r in inj.iterrows()]


def build(season: int = C.SEASON, week: int = C.WEEK) -> dict:
    ovr = json.loads((C.MANUAL / "player_overrides.json").read_text())
    week_ovr = C.MANUAL / f"player_overrides_{season}_wk{week}.json"
    if week_ovr.exists():
        extra = json.loads(week_ovr.read_text())
        ovr["players"].update(extra.get("players", {}))
        ovr["drop"] = ovr.get("drop", []) + extra.get("drop", [])
    roster = roster_index()
    teams: dict[str, dict] = {}
    warnings = []
    research_dir = RESEARCH_ROOT / f"wk{week}"
    official = official_report(season, week)
    for row in official:
        teams.setdefault(row["team"], {"players": [], "notes": [], "sources": []})["players"].append(
            {**{k: v for k, v in row.items() if k != "team"}, "position": norm_pos(row["position"]), "star": False, "roster_status": "official-report"})
    for f in sorted(research_dir.glob("group_*.json")):
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
                    hits = [h for h in roster[rk] if h[0] == team]
                    if not hits:
                        warnings.append(f"{name}: research says {team}, roster says {sorted({h[0] for h in roster[rk]})}; dropped")
                        continue
                    rteam, rstatus, rcode = hits[0]
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
    GAME_STATUSES = {"Out", "Doubtful", "Questionable", "Probable", "Returning-expected-to-play"}
    official_by_team: dict[str, dict[str, str]] = {}
    for row in official:
        official_by_team.setdefault(row["team"], {})[f"{row['player'][:1].lower()}|{_last(row['player'])}"] = row["status"]
    for team, e in teams.items():
        for p in e["players"]:
            if p.get("roster_status") == "official-report":
                ov = {k: v for k, v in match_override(team, p["player"], ovr["players"]).items() if k != "status"}
                p.update(ov)
            elif team in official_by_team and p["status"] in GAME_STATUSES:
                # the official report is authoritative once published: anyone it lists gets that status,
                # anyone it omits is active (reserve-list players are untouched)
                key = f"{p['player'][:1].lower()}|{_last(p['player'])}"
                if key in official_by_team[team]:
                    p["status"] = official_by_team[team][key]
                else:
                    p["status"] = "Probable"
                    p["injury"] = (p.get("injury") or "") + " [not on official report: active]"
    # de-duplicate by name, then by first initial + last name + position, within team (keep the most severe status)
    sev = {s: i for i, s in enumerate(["Returning-expected-to-play", "Probable", "Questionable", "Doubtful", "Out", "Suspended", "NFI", "PUP", "IR"])}
    for team, e in teams.items():
        best = {}
        for p in e["players"]:
            k = f"{p['player'][:1].lower()}|{_last(p['player'])}"
            if k not in best or sev[p["status"]] > sev[best[k]["status"]]:
                best[k] = p
        e["players"] = sorted(best.values(), key=lambda p: (-sev[p["status"]], p["player"]))
        e["sources"] = sorted(set(e["sources"]))
    collected = max([json.loads(f.read_text()).get("collected_on", "") for f in research_dir.glob("*.json")] or ["n/a"])
    out = {"season": season, "week": week, "collected_on": collected, "official_report_rows": len(official),
           "method": f"web search summaries (data/research/wk{week}) plus the official nflverse injury report when published, cross-checked with roster status codes", "warnings": warnings, "teams": teams}
    (C.MANUAL / f"injuries_{season}_wk{week}.json").write_text(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    o = build()
    for w in o["warnings"]:
        print("WARN", w)
    for t, e in sorted(o["teams"].items()):
        print(t, len(e["players"]), "players;", ", ".join(f"{p['player']}({p['position']},{p['status']}{',S' if p['starter'] else ''}{',*' if p['star'] else ''})" for p in e["players"] if p["starter"] or p["star"]))
