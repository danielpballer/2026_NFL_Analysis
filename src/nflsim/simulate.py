"""Stage 6-7: blend model and market, then Monte Carlo the margin and total."""
from __future__ import annotations

import numpy as np

from . import config as C


def blend_margin(model_margin: float, market_margin: float | None, w_market: float = C.MARKET_WEIGHT) -> float:
    if market_margin is None or np.isnan(market_margin):
        return model_margin
    return w_market * market_margin + (1 - w_market) * model_margin


def simulate_game(exp_margin: float, exp_total: float, sd_margin: float = C.MARGIN_SD,
                  n: int = C.N_SIMS, seed: int = C.SEED) -> dict:
    rng = np.random.default_rng(seed)
    margin = rng.normal(exp_margin, sd_margin, n)
    total = np.clip(rng.normal(exp_total, C.TOTAL_SD, n), 6, None)
    home = np.rint((total + margin) / 2)
    away = np.rint((total - margin) / 2)
    m = home - away
    ties = m == 0
    # overtime sub-model for tied regulation scores
    p_ot = np.clip(0.5 + C.OT_MARGIN_SENSITIVITY * exp_margin, 0.2, 0.8)
    ot = rng.random(n) < p_ot
    home_win = (m > 0) | (ties & ot)
    return {
        "p_home": float(home_win.mean()),
        "p_tie_regulation": float(ties.mean()),
        "mean_margin": float(m.mean()),
        "median_margin": float(np.median(m)),
        "margin_q10": float(np.quantile(m, 0.1)),
        "margin_q90": float(np.quantile(m, 0.9)),
        "mean_home_pts": float(home.mean()),
        "mean_away_pts": float(away.mean()),
        "p_home_by_7plus": float((m >= 7).mean()),
        "p_away_by_7plus": float((m <= -7).mean()),
    }


def confidence_tier(p_win: float) -> str:
    for cut, label in C.CONFIDENCE_TIERS:
        if p_win >= cut:
            return label
    return "Coin flip"
