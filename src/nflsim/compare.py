"""Stage 8 helper: pure-data and market-only win probabilities alongside the blended ones."""
from __future__ import annotations

import json

from . import config as C
from .simulate import simulate_game


def main():
    rows = json.load(open(C.OUTPUT / f"week{C.WEEK}_{C.SEASON}_predictions.json"))
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
