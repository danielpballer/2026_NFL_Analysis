"""Stage 6-8 orchestrator: build every Week 1 prediction and write the outputs."""
from __future__ import annotations

import json
import math
from datetime import date

import numpy as np
import pandas as pd

from . import config as C
from .adjustments import (GameContext, head_coach_changes, injury_adjustment, load_json, qb_adjustment)
from .qb import qb_values, team_primary_qb
from .report import write_outputs
from .schedule import devig, moneyline_to_prob, prob_to_moneyline, week_slate
from .simulate import blend_margin, confidence_tier, simulate_game
from .strength import team_strength


def build_predictions(season: int = C.SEASON, week: int = C.WEEK, verbose: bool = True) -> pd.DataFrame:
    slate = week_slate(season, week)
    strength = team_strength(season - 1)
    qvals = qb_values(season - 1)
    tqb = team_primary_qb(season - 1)
    qb_manual = load_json(f"qb_{season}.json")
    injuries = load_json(f"injuries_{season}_wk{week}.json")
    weather = load_json(f"weather_{season}_wk{week}.json").get("games", {})
    coaching = head_coach_changes(season)
    coaching.update(load_json(f"coaching_{season}.json").get("teams", {}))

    rows = []
    for _, g in slate.iterrows():
        home, away = g.home_team, g.away_team
        wx = weather.get(g.game_id, {})
        roof = wx.get("roof") or str(g.roof)   # weather file may correct the schedule's roof (e.g. Melbourne)
        ctx = GameContext(g.game_id, home, away, bool(g.neutral_site), bool(g.div_game), roof, wx)
        side = {}
        for team in (home, away):
            base = float(strength.loc[team, "rating_regressed"])
            new_hc = team in coaching
            base_hc = base * (1 - C.NEW_HC_REGRESSION) if new_hc else base
            q = qb_adjustment(team, qb_manual, qvals, tqb)
            inj = injury_adjustment(team, injuries)
            rating = base_hc + q["qb_adj"] + inj["injury_pts"]
            side[team] = {"base": base, "new_hc": new_hc, "rating": rating, **q, **inj}
        h, a = side[home], side[away]
        hfa, travel = ctx.home_field(), ctx.travel()
        model_margin = (h["rating"] - a["rating"]) + hfa + travel
        market_margin = float(g.market_home_margin) if not pd.isna(g.market_home_margin) else None
        wx_mult, wx_sd, wx_note = ctx.weather_factor()
        blended = blend_margin(model_margin, market_margin)
        final_margin = blended * wx_mult
        extras = [wx_sd, h["qb_extra_sd"], a["qb_extra_sd"], h["injury_extra_sd"], a["injury_extra_sd"],
                  C.NEW_HC_EXTRA_SD if h["new_hc"] else 0.0, C.NEW_HC_EXTRA_SD if a["new_hc"] else 0.0]
        sd = math.sqrt(C.MARGIN_SD ** 2 + sum(e ** 2 for e in extras)) + (C.DIVISION_GAME_SD_ADJ if ctx.div_game else 0.0)
        total = float(g.total_line) if not pd.isna(g.total_line) else 44.0
        if wx_note not in ("indoor", "benign"):
            total -= 0.5 * max(0.0, float(ctx.weather.get("wind_mph", 8) or 8) - C.WIND_FREE)
            if float(ctx.weather.get("precip_chance_pct", 0) or 0) >= 50:
                total -= 1.5
        sim = simulate_game(final_margin, total, sd)
        p_home = sim["p_home"]
        winner = home if p_home >= 0.5 else away
        p_win = max(p_home, 1 - p_home)
        mh, ma = moneyline_to_prob(g.home_moneyline), moneyline_to_prob(g.away_moneyline)
        mkt_home, mkt_away = devig(mh, ma)
        rows.append({
            "game_id": g.game_id, "kickoff": f"{g.gameday} {g.gametime} ET", "away": away, "home": home,
            "venue": g.stadium, "roof": roof, "neutral_site": ctx.neutral, "div_game": ctx.div_game,
            "predicted_winner": winner, "win_probability": round(p_win, 4), "confidence": confidence_tier(p_win),
            "p_home_win": round(p_home, 4), "fair_home_moneyline": prob_to_moneyline(p_home),
            "fair_away_moneyline": prob_to_moneyline(1 - p_home),
            "market_home_moneyline": int(g.home_moneyline), "market_away_moneyline": int(g.away_moneyline),
            "market_p_home_devig": round(mkt_home, 4), "edge_vs_market_home": round(p_home - mkt_home, 4),
            "market_spread_home": market_margin, "model_margin_home": round(model_margin, 2),
            "final_margin_home": round(final_margin, 2), "margin_sd": round(sd, 2),
            "proj_home_pts": round(sim["mean_home_pts"], 1), "proj_away_pts": round(sim["mean_away_pts"], 1),
            "proj_total": round(total, 1),
            "home_rating_2025": round(h["base"], 2), "away_rating_2025": round(a["base"], 2),
            "home_rating_adj": round(h["rating"], 2), "away_rating_adj": round(a["rating"], 2),
            "home_field_pts": round(hfa + travel, 2),
            "home_qb": h["qb"], "away_qb": a["qb"], "home_qb_adj": round(h["qb_adj"], 2), "away_qb_adj": round(a["qb_adj"], 2),
            "home_injury_pts": round(h["injury_pts"], 2), "away_injury_pts": round(a["injury_pts"], 2),
            "home_injury_details": h["injury_details"], "away_injury_details": a["injury_details"],
            "home_new_hc": h["new_hc"], "away_new_hc": a["new_hc"],
            "weather_note": wx_note, "weather_temp_f": ctx.weather.get("temp_f"), "weather_wind_mph": ctx.weather.get("wind_mph"),
            "weather_precip_pct": ctx.weather.get("precip_chance_pct"), "weather_confidence": ctx.weather.get("confidence"),
            "p_home_by_7plus": round(sim["p_home_by_7plus"], 3), "p_away_by_7plus": round(sim["p_away_by_7plus"], 3),
            "home_qb_notes": h["notes"], "away_qb_notes": a["notes"],
        })
    df = pd.DataFrame(rows)
    if verbose:
        pd.set_option("display.width", 220)
        print(df[["game_id", "predicted_winner", "win_probability", "confidence", "final_margin_home", "market_spread_home", "model_margin_home", "edge_vs_market_home"]].to_string())
    return df


def main():
    df = build_predictions()
    write_outputs(df, C.SEASON, C.WEEK)


if __name__ == "__main__":
    main()
