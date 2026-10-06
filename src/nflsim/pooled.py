"""Pooled evaluation across completed weeks: scores the blend, pure model and market, and
grid-searches the market weight and margin sd so the weekly review has numbers to act on.

    PYTHONPATH=src python -m nflsim.pooled 2026 1 4
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from scipy.stats import norm

from . import config as C
from .evaluate import evaluate


def pooled(season: int, weeks: list[int]) -> pd.DataFrame:
    frames = []
    for w in weeks:
        df, _ = evaluate(season, w)
        df["week"] = w
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def p_from_margin(margin, sd):
    return 1 - norm.cdf(0, loc=margin, scale=sd)


def logloss(p, y):
    p = np.clip(p, 0.01, 0.99)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def main():
    season = int(sys.argv[1]) if len(sys.argv) > 1 else C.SEASON
    first = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    last = int(sys.argv[3]) if len(sys.argv) > 3 else C.WEEK - 1
    df = pooled(season, list(range(first, last + 1)))
    y = df.home_won.to_numpy()
    print(f"{len(df)} games, weeks {first}-{last}")
    rows = []
    for name, col in [("blend", "p_home_win"), ("pure_model", "p_pure"), ("market_spread", "p_mkt_spread"), ("market_ml", "p_mkt_ml")]:
        p = df[col].to_numpy()
        rows.append({"method": name, "acc": ((p >= 0.5) == (y == 1)).mean(), "logloss": logloss(p, y), "brier": np.mean((np.clip(p, .01, .99) - y) ** 2)})
    print(pd.DataFrame(rows).round(4).to_string(index=False))
    print("\nper-week picks:", df.groupby("week").pick_won.agg(["sum", "count"]).T.to_string())
    # market-weight grid using the recorded sd (model margin and market spread are stored per game)
    print("\nmarket weight grid (logloss / accuracy, normal approx with recorded sd):")
    for w in np.arange(0.0, 0.81, 0.1):
        m = w * df.market_spread_home + (1 - w) * df.model_margin_home
        p = p_from_margin(m, df.margin_sd)
        print(f"  w={w:.1f}  logloss={logloss(p, y):.4f}  acc={((p >= 0.5) == (y == 1)).mean():.3f}  mae={np.abs(df.result - m).mean():.2f}")
    print("\nsd grid at current blend:")
    for sd in [11, 12, 12.7, 13.5, 14.5, 16]:
        p = p_from_margin(df.final_margin_home, sd)
        print(f"  sd={sd:<5} logloss={logloss(p, y):.4f}")
    print("\nmargin bias (actual - predicted): blend %.2f  model %.2f  market %.2f" % (df.err_final.mean(), df.err_model.mean(), df.err_market.mean()))
    print("home teams won %.0f%% ; mean actual margin %.2f ; mean market spread %.2f" % (100 * y.mean(), df.result.mean(), df.market_spread_home.mean()))
    big = df[df.adj_home_net.abs() >= 1.5]
    print(f"\ninjury/QB adjustments >=1.5 pts: {len(big)} games, helped vs market in {int(big.adj_helped.sum())}; corr(adj, err_market)={np.corrcoef(df.adj_home_net, df.err_market)[0,1]:.3f}")
    print("\ncalibration by tier:")
    print(df.groupby("confidence").agg(n=("pick_won", "size"), won=("pick_won", "sum"), avg_p=("win_probability", "mean")).to_string())
    print("\nby pick side: home picks", df[df.predicted_winner == df.home].pick_won.agg(["sum", "count"]).tolist(), " away picks", df[df.predicted_winner != df.home].pick_won.agg(["sum", "count"]).tolist())
    print("favorites (market) won", int(((df.market_spread_home > 0) == (df.result > 0)).sum()), "of", int((df.market_spread_home != 0).sum()))


if __name__ == "__main__":
    main()
