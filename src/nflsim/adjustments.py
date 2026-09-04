"""Stages 3-5: personnel, injury, coaching and situational adjustments in points.

All manual inputs are JSON files under data/manual so they can be refreshed without code changes.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

import pandas as pd

from . import config as C
from .config import MANUAL, RAW


def load_json(name: str) -> dict:
    p = MANUAL / name
    return json.loads(p.read_text()) if p.exists() else {}


# ---------------------------------------------------------------- coaching -------------------
def head_coach_changes(season: int) -> dict[str, dict]:
    """Teams whose Week 1 head coach differs from the coach who finished the prior season."""
    g = pd.read_csv(RAW / "games.csv", low_memory=False)
    prev = g[(g.season == season - 1) & (g.game_type == "REG")].sort_values("week")
    last = {}
    for _, r in prev.iterrows():
        last[r.home_team] = r.home_coach
        last[r.away_team] = r.away_coach
    cur = g[(g.season == season) & (g.game_type == "REG") & (g.week == 1)]
    out = {}
    for _, r in cur.iterrows():
        for side in ("home", "away"):
            t, c = r[f"{side}_team"], r[f"{side}_coach"]
            if isinstance(c, str) and last.get(t) != c:
                out[t] = {"new_coach": c, "previous": last.get(t)}
    return out


# ---------------------------------------------------------------- quarterbacks ---------------
def qb_adjustment(team: str, qb_manual: dict, qb_vals: pd.DataFrame, team_qb: pd.DataFrame) -> dict:
    """Points to add to the team rating for its 2026 starter relative to what it fielded in 2025."""
    entry = qb_manual.get("teams", {}).get(team, {})
    starter = entry.get("starter")
    fielded = float(team_qb.loc[team, "fielded_qb_value"]) if team in team_qb.index else -1.0
    value = None
    match = None
    if entry.get("value_override") is not None:
        value = float(entry["value_override"])
        match = "override"
    elif starter:
        key = entry.get("pbp_name") or _short_name(starter)
        hit = qb_vals[qb_vals.passer_player_name == key]
        if len(hit):
            value = float(hit.value_pts.iloc[0])
            match = key
    if value is None:
        value = float(entry.get("prior_value", -1.5))
        match = "prior"
    delta = C.QB_CHANGE_WEIGHT * (value - fielded)
    extra_sd = C.NEW_QB_EXTRA_SD if entry.get("new_to_team") or entry.get("rookie") else 0.0
    extra_sd = max(extra_sd, float(entry.get("extra_sd", 0.0)))
    return {"team": team, "qb": starter, "qb_value": value, "fielded_2025": fielded,
            "qb_adj": delta, "qb_extra_sd": extra_sd, "match": match, "notes": entry.get("notes", "")}


def _short_name(full: str) -> str:
    parts = full.replace(" Jr.", "").replace(" Sr.", "").replace(" II", "").replace(" III", "").split()
    return f"{parts[0][0]}.{parts[-1]}" if len(parts) >= 2 else full


# ---------------------------------------------------------------- injuries -------------------
def injury_adjustment(team: str, injuries: dict) -> dict:
    """Expected points lost to absences, with a cap, plus an uncertainty term."""
    rows = injuries.get("teams", {}).get(team, {}).get("players", [])
    total, unc, details = 0.0, 0.0, []
    for p in rows:
        pos = p.get("slot") or p.get("position", "")
        base = C.POSITION_VALUE.get(pos, C.POSITION_VALUE.get(p.get("position", ""), 0.3))
        if pos == "QB" or p.get("position") == "QB":
            base = 0.0  # QB handled in qb_adjustment via the manual starter entry
        if p.get("star"):
            base *= C.STAR_MULTIPLIER
        if not p.get("starter", True):
            base *= C.NON_STARTER_MULTIPLIER
        miss = C.MISS_PROBABILITY.get(p.get("status", "Questionable"), 0.45)
        pts = base * miss
        total += pts
        unc += base * miss * (1 - miss)  # binary uncertainty contributes variance
        if pts > 0.05:
            details.append(f"{p['player']} ({p.get('position')}, {p.get('status')}) -{pts:.2f}")
    capped = min(total, C.INJURY_CAP_POINTS)
    return {"team": team, "injury_pts": -capped, "injury_raw": -total, "injury_extra_sd": unc ** 0.5,
            "injury_details": "; ".join(details)}


# ---------------------------------------------------------------- situational ----------------
@dataclass
class GameContext:
    game_id: str
    home: str
    away: str
    neutral: bool
    div_game: bool
    roof: str
    weather: dict = field(default_factory=dict)

    def home_field(self) -> float:
        if self.neutral:
            return 0.0
        return C.HOME_FIELD + C.LOUD_VENUES.get(self.home, 0.0)

    def travel(self) -> float:
        """Negative points for the away team (returned as positive number for the home margin)."""
        if self.neutral:
            return 0.0
        tz = abs(C.TIME_ZONES[self.home] - C.TIME_ZONES[self.away])
        return C.TRAVEL_PENALTY_PER_TZ * max(0, tz - 1)

    def weather_factor(self) -> tuple[float, float, str]:
        """Return (margin multiplier, extra sd, note). Indoor and closed-roof games are neutral."""
        w = self.weather
        roof = (w.get("roof") or self.roof or "").lower()
        if roof in ("dome", "closed") or w.get("roof_closed_expected"):
            return 1.0, 0.0, "indoor"
        wind = float(w.get("wind_mph", 8) or 8)
        precip = float(w.get("precip_chance_pct", 20) or 20)
        mult = 1.0 - C.WIND_COMPRESSION_PER_MPH * max(0.0, wind - C.WIND_FREE)
        sd = 0.0
        note = []
        if wind > C.WIND_FREE + 2:
            note.append(f"wind {wind:.0f} mph")
            sd += C.WEATHER_EXTRA_SD
        if precip >= 50:
            mult -= C.RAIN_COMPRESSION
            sd += C.WEATHER_EXTRA_SD
            note.append(f"rain/storm chance {precip:.0f}%")
        temp = w.get("temp_f")
        if temp is not None and temp >= 88:
            note.append(f"heat {temp:.0f}F")
        return max(mult, 0.8), sd, ", ".join(note) or "benign"
