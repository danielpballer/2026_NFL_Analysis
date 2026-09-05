"""Stage 8 helper: pure-data and market-only win probabilities alongside the blended ones."""
from __future__ import annotations

import json

from . import config as C
from .simulate import simulate_game


def decimal_odds(ml: float) -> float:
    ml = float(ml)
    return 1 + ml / 100 if ml > 0 else 1 + 100 / (-ml)


def value_table(rows: list[dict]) -> list[dict]:
    """Expected value and Kelly fraction for every side at the market moneyline (vig included)."""
    legs = []
    for r in rows:
        for side, p, ml in ((r["home"], r["p_home_win"], r["market_home_moneyline"]),
                            (r["away"], 1 - r["p_home_win"], r["market_away_moneyline"])):
            d = decimal_odds(ml)
            ev = p * d - 1
            kelly = max(0.0, (p * d - 1) / (d - 1))
            legs.append({"game_id": r["game_id"], "matchup": f"{r['away']} at {r['home']}", "side": side,
                         "is_pick": side == r["predicted_winner"], "model_p": round(p, 4), "market_ml": int(ml),
                         "implied_p": round(1 / d, 4), "ev_per_dollar": round(ev, 4),
                         "kelly": round(kelly, 4), "quarter_kelly": round(kelly / 4, 4)})
    return sorted(legs, key=lambda x: -x["ev_per_dollar"])


def main():
    rows = json.load(open(C.OUTPUT / f"week{C.WEEK}_{C.SEASON}_predictions.json"))
    legs = value_table(rows)
    vpath = C.OUTPUT / f"week{C.WEEK}_{C.SEASON}_value.json"
    vpath.write_text(json.dumps(legs, indent=2))
    print(f"wrote {vpath}; positive-EV sides: {[(l['side'], l['market_ml']) for l in legs if l['ev_per_dollar'] > 0.02]}")
    out = {}
    for r in rows:
        p_pure = simulate_game(r["model_margin_home"], r["proj_total"], r["margin_sd"])["p_home"]
        p_mkt = simulate_game(r["market_spread_home"], r["proj_total"], C.MARGIN_SD)["p_home"]
        pick_pure = r["home"] if p_pure >= 0.5 else r["away"]
        out[r["game_id"]] = {"p_home_pure": round(p_pure, 4), "p_home_market": round(p_mkt, 4),
                             "pick_pure": pick_pure, "flip": pick_pure != r["predicted_winner"]}
    path = C.OUTPUT / f"week{C.WEEK}_{C.SEASON}_pure_vs_blend.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"wrote {path}; flips: {[g for g, v in out.items() if v['flip']]}")


if __name__ == "__main__":
    main()
