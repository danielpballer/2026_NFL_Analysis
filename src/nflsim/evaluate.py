"""Score a week's predictions against the results in games.csv.

Reports accuracy, log loss and Brier score for the blended model, the pure model, the market
spread and the market moneyline, calibration by confidence tier, and a per-game decomposition
of where the margin error came from.
"""
from __future__ import annotations

import json
import math
import sys

import numpy as np
import pandas as pd

from . import config as C
from .schedule import devig, moneyline_to_prob
from .simulate import simulate_game


def evaluate(season: int, week: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    pred = pd.read_json(C.OUTPUT / f"week{week}_{season}_predictions.json")
    g = pd.read_csv(C.RAW / "games.csv", low_memory=False)
    g = g[(g.season == season) & (g.week == week) & (g.game_type == "REG")][["game_id", "home_score", "away_score", "result"]]
    pred = pred.rename(columns={"home_rating_2025": "home_rating_prior", "away_rating_2025": "away_rating_prior"})
    df = pred.merge(g, on="game_id")
    df = df[df.result.notna()].copy()
    df["home_won"] = (df.result > 0).astype(int)
    df["pick_won"] = ((df.predicted_winner == df.home) == (df.result > 0)).astype(int)
    df["p_pure"] = [simulate_game(m, t, s)["p_home"] for m, t, s in zip(df.model_margin_home, df.proj_total, df.margin_sd)]
    df["p_mkt_spread"] = [simulate_game(m, t, C.MARGIN_SD)["p_home"] for m, t in zip(df.market_spread_home, df.proj_total)]
    df["p_mkt_ml"] = [devig(moneyline_to_prob(h), moneyline_to_prob(a))[0] for h, a in zip(df.market_home_moneyline, df.market_away_moneyline)]
    df["err_final"] = df.result - df.final_margin_home
    df["err_model"] = df.result - df.model_margin_home
    df["err_market"] = df.result - df.market_spread_home
    df["adj_home_net"] = (df.home_rating_adj - df.home_rating_prior) - (df.away_rating_adj - df.away_rating_prior)
    df["adj_helped"] = np.sign(df.adj_home_net) == np.sign(df.err_market)
    scores = []
    y = df.home_won.to_numpy()
    for name, col in [("blend", "p_home_win"), ("pure_model", "p_pure"), ("market_spread", "p_mkt_spread"), ("market_ml", "p_mkt_ml")]:
        p = np.clip(df[col].to_numpy(), 0.01, 0.99)
        scores.append({"method": name, "accuracy": float(((p >= 0.5) == (y == 1)).mean()),
                       "log_loss": float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))),
                       "brier": float(np.mean((p - y) ** 2))})
    for name, col in [("blend", "final_margin_home"), ("pure_model", "model_margin_home"), ("market_spread", "market_spread_home")]:
        scores[[s["method"] for s in scores].index(name)]["margin_mae"] = float((df.result - df[col]).abs().mean())
        scores[[s["method"] for s in scores].index(name)]["margin_bias"] = float((df.result - df[col]).mean())
    scores.append({"method": "coin_flip", "accuracy": 0.5, "log_loss": math.log(2), "brier": 0.25})
    return df, pd.DataFrame(scores)


def main():
    season = int(sys.argv[1]) if len(sys.argv) > 1 else C.SEASON
    week = int(sys.argv[2]) if len(sys.argv) > 2 else C.WEEK
    df, scores = evaluate(season, week)
    pd.set_option("display.width", 250)
    cols = ["game_id", "predicted_winner", "win_probability", "confidence", "pick_won", "away_score", "home_score", "result",
            "final_margin_home", "model_margin_home", "market_spread_home", "err_final", "err_model", "err_market", "adj_home_net", "adj_helped"]
    print(df[cols].round(2).to_string())
    print()
    print(scores.round(4).to_string())
    print()
    tiers = df.groupby("confidence").agg(n=("pick_won", "size"), won=("pick_won", "sum"), avg_p=("win_probability", "mean"))
    print(tiers)
    df.round(4).to_csv(C.OUTPUT / f"week{week}_{season}_evaluation.csv", index=False)
    scores.round(4).to_csv(C.OUTPUT / f"week{week}_{season}_evaluation_scores.csv", index=False)


if __name__ == "__main__":
    main()
