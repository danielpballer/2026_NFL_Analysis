"""Stage 1: load the Week 1 slate with market lines and venue info from nflverse games.csv."""
from __future__ import annotations

import pandas as pd

from .config import PROCESSED, RAW, SEASON, WEEK

COLS = [
    "game_id", "season", "game_type", "week", "gameday", "weekday", "gametime",
    "away_team", "home_team", "location", "away_rest", "home_rest",
    "away_moneyline", "home_moneyline", "spread_line", "total_line",
    "div_game", "roof", "surface", "away_coach", "home_coach", "stadium",
    "away_score", "home_score", "result",
]


def load_games() -> pd.DataFrame:
    return pd.read_csv(RAW / "games.csv", low_memory=False)


def week_slate(season: int = SEASON, week: int = WEEK) -> pd.DataFrame:
    g = load_games()
    s = g[(g.season == season) & (g.game_type == "REG") & (g.week == week)][COLS].copy()
    s = s.sort_values(["gameday", "gametime", "game_id"]).reset_index(drop=True)
    # nflverse spread_line is home margin (positive = home favored)
    s["market_home_margin"] = s["spread_line"]
    s["neutral_site"] = s["location"].str.lower().eq("neutral")
    return s


def moneyline_to_prob(ml: float) -> float:
    """American moneyline to implied probability, vig included."""
    ml = float(ml)
    return 100.0 / (ml + 100.0) if ml > 0 else -ml / (-ml + 100.0)


def prob_to_moneyline(p: float) -> int:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return int(round(-100 * p / (1 - p))) if p >= 0.5 else int(round(100 * (1 - p) / p))


def devig(p_home: float, p_away: float) -> tuple[float, float]:
    s = p_home + p_away
    return p_home / s, p_away / s


if __name__ == "__main__":
    PROCESSED.mkdir(parents=True, exist_ok=True)
    s = week_slate()
    s.to_csv(PROCESSED / f"schedule_{SEASON}_wk{WEEK}.csv", index=False)
    print(s[["game_id", "gameday", "gametime", "roof", "spread_line", "home_moneyline", "away_moneyline", "total_line"]])
