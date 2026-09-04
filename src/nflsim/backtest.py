"""Stage 9: backtest the method on last season's Week 1.

Predict 2025 Week 1 using only 2024 play-by-play, 2025 Week 1 opening lines, the QBs who
actually started (from the schedule file) and the official Week 1 injury report. Compare
log loss and Brier score against a market-only baseline and a coin flip.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from . import config as C
from .adjustments import GameContext, head_coach_changes, injury_adjustment, qb_adjustment
from .qb import qb_values, team_primary_qb
from .schedule import devig, moneyline_to_prob, week_slate
from .simulate import blend_margin, simulate_game
from .strength import team_strength

POS_MAP = {"T": "OT", "G": "G", "C": "C", "DE": "DE", "DT": "DT", "LB": "LB", "CB": "CB", "S": "S",
           "WR": "WR", "TE": "TE", "RB": "RB", "QB": "QB", "K": "K", "P": "P", "OL": "OL", "DL": "DL", "DB": "DB", "OLB": "OLB", "ILB": "ILB", "FS": "FS", "SS": "SS", "NT": "NT", "LS": "LS", "FB": "FB"}


def injuries_from_report(season: int, week: int) -> dict:
    inj = pd.read_csv(C.RAW / f"injuries_{season}.csv")
    inj = inj[(inj.season == season) & (inj.week == week) & (inj.game_type == "REG")]
    teams = {}
    for _, r in inj.iterrows():
        status = r.report_status if isinstance(r.report_status, str) else None
        if status is None:
            continue
        teams.setdefault(r.team, {"players": []})["players"].append({
            "player": r.full_name, "position": POS_MAP.get(r.position, r.position), "status": status,
            "starter": True, "star": False})
    return {"teams": teams}


def run(season: int = 2025, week: int = 1, n_sims: int = 5000, w_market: float = C.MARKET_WEIGHT) -> pd.DataFrame:
    slate = week_slate(season, week)
    slate = slate[slate.result.notna()]
    strength = team_strength(season - 1)
    qvals = qb_values(season - 1)
    tqb = team_primary_qb(season - 1)
    injuries = injuries_from_report(season, week)
    coaching = head_coach_changes(season)
    games = pd.read_csv(C.RAW / "games.csv", low_memory=False)
    qb_names = games[(games.season == season) & (games.week == week) & (games.game_type == "REG")].set_index("game_id")
    rows = []
    for _, g in slate.iterrows():
        home, away = g.home_team, g.away_team
        ctx = GameContext(g.game_id, home, away, bool(g.neutral_site), bool(g.div_game), str(g.roof), {})
        side = {}
        for team, col in ((home, "home_qb_name"), (away, "away_qb_name")):
            qb_name = qb_names.loc[g.game_id, col]
            manual = {"teams": {team: {"starter": qb_name}}}
            q = qb_adjustment(team, manual, qvals, tqb)
            inj = injury_adjustment(team, injuries)
            base = float(strength.loc[team, "rating_regressed"])
            new_hc = team in coaching
            rating = (base * (1 - C.NEW_HC_REGRESSION) if new_hc else base) + q["qb_adj"] + inj["injury_pts"]
            side[team] = {"rating": rating, "new_hc": new_hc, **q, **inj}
        h, a = side[home], side[away]
        model_margin = h["rating"] - a["rating"] + ctx.home_field() + ctx.travel()
        market = float(g.market_home_margin)
        final = blend_margin(model_margin, market, w_market)
        extras = [h["qb_extra_sd"], a["qb_extra_sd"], h["injury_extra_sd"], a["injury_extra_sd"],
                  C.NEW_HC_EXTRA_SD if h["new_hc"] else 0, C.NEW_HC_EXTRA_SD if a["new_hc"] else 0]
        sd = math.sqrt(C.MARGIN_SD ** 2 + sum(e ** 2 for e in extras)) + (C.DIVISION_GAME_SD_ADJ if ctx.div_game else 0)
        sim = simulate_game(final, float(g.total_line), sd, n=n_sims)
        model_only = simulate_game(model_margin, float(g.total_line), sd, n=n_sims)["p_home"]
        mkt_only = simulate_game(market, float(g.total_line), C.MARGIN_SD, n=n_sims)["p_home"]
        mh, ma = devig(moneyline_to_prob(g.home_moneyline), moneyline_to_prob(g.away_moneyline))
        rows.append({"game_id": g.game_id, "home": home, "away": away, "result": g.result, "home_won": int(g.result > 0),
                     "p_blend": sim["p_home"], "p_model": model_only, "p_market_spread": mkt_only, "p_market_ml": mh,
                     "model_margin": model_margin, "market": market, "final": final})
    return pd.DataFrame(rows)


def score(df: pd.DataFrame) -> pd.DataFrame:
    y = df.home_won.to_numpy()
    out = []
    for col in ["p_blend", "p_model", "p_market_spread", "p_market_ml"]:
        p = np.clip(df[col].to_numpy(), 0.01, 0.99)
        ll = -np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))
        brier = np.mean((p - y) ** 2)
        acc = np.mean((p >= 0.5) == (y == 1))
        out.append({"method": col, "log_loss": ll, "brier": brier, "accuracy": acc})
    out.append({"method": "coin_flip", "log_loss": math.log(2), "brier": 0.25, "accuracy": 0.5})
    return pd.DataFrame(out)


if __name__ == "__main__":
    df = run()
    pd.set_option("display.width", 200)
    print(df.round(3).to_string())
    print(score(df).round(4).to_string())
    C.OUTPUT.mkdir(parents=True, exist_ok=True)
    df.round(4).to_csv(C.OUTPUT / "backtest_2025_wk1.csv", index=False)
    score(df).round(4).to_csv(C.OUTPUT / "backtest_2025_wk1_scores.csv", index=False)
