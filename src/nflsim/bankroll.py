"""Season-to-date results of betting the value table as first published each week (the Tuesday
release, taken from the first git commit of each week's value file), under two staking plans:
flat stakes and fractional Kelly on a running bankroll.

    PYTHONPATH=src python -m nflsim.bankroll 2026 1 5 --bankroll 1000 --flat 10
"""
from __future__ import annotations

import argparse
import json
import subprocess

import pandas as pd

from . import config as C

EV_THRESHOLD = 0.02   # the page lists sides above this expected value per dollar


def tuesday_table(season: int, week: int) -> list[dict]:
    path = f"output/week{week}_{season}_value.json"
    commits = subprocess.check_output(["git", "log", "--diff-filter=A", "--format=%H", "--", path], cwd=C.ROOT, text=True).split()
    if not commits:
        return json.loads((C.ROOT / path).read_text())
    return json.loads(subprocess.check_output(["git", "show", f"{commits[-1]}:{path}"], cwd=C.ROOT, text=True))


def profit_per_unit(ml: int, won: bool) -> float:
    if not won:
        return -1.0
    return ml / 100 if ml > 0 else 100 / abs(ml)


def run(season: int, first: int, last: int, bankroll: float, flat: float, kelly_fraction: float = 0.25) -> pd.DataFrame:
    g = pd.read_csv(C.RAW / "games.csv", low_memory=False)
    g = g[g.season == season].set_index("game_id")
    rows = []
    roll = bankroll
    flat_total = 0.0
    for week in range(first, last + 1):
        legs = [l for l in tuesday_table(season, week) if l["ev_per_dollar"] > EV_THRESHOLD]
        start = roll
        for l in legs:
            game = g.loc[l["game_id"]]
            if pd.isna(game.result):
                outcome = "pending"
            elif game.result == 0:
                outcome = "push"
            else:
                outcome = "won" if (game.result > 0) == (l["side"] == game.home_team) else "lost"
            stake_k = round(kelly_fraction * 4 * l["quarter_kelly"] * start, 2)   # quarter_kelly already = kelly/4
            if outcome in ("pending", "push"):
                pk = pf = 0.0
            else:
                pk = round(stake_k * profit_per_unit(l["market_ml"], outcome == "won"), 2)
                pf = round(flat * profit_per_unit(l["market_ml"], outcome == "won"), 2)
            roll += pk
            flat_total += pf
            rows.append({"week": week, "matchup": l["matchup"], "side": l["side"], "ml": l["market_ml"], "model_p": l["model_p"],
                         "outcome": outcome, "kelly_stake": stake_k, "kelly_profit": pk, "bankroll_after": round(roll, 2),
                         "flat_stake": flat, "flat_profit": pf, "flat_total": round(flat_total, 2)})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("season", type=int, nargs="?", default=C.SEASON)
    ap.add_argument("first", type=int, nargs="?", default=1)
    ap.add_argument("last", type=int, nargs="?", default=C.WEEK - 1)
    ap.add_argument("--bankroll", type=float, default=1000.0)
    ap.add_argument("--flat", type=float, default=10.0)
    ap.add_argument("--fraction", type=float, default=0.25)
    a = ap.parse_args()
    df = run(a.season, a.first, a.last, a.bankroll, a.flat, a.fraction)
    pd.set_option("display.width", 250)
    print(df.to_string(index=False))
    print()
    wk = df.groupby("week").agg(bets=("side", "size"), won=("outcome", lambda s: (s == "won").sum()), lost=("outcome", lambda s: (s == "lost").sum()),
                               kelly_staked=("kelly_stake", "sum"), kelly_profit=("kelly_profit", "sum"), flat_staked=("flat_stake", "sum"), flat_profit=("flat_profit", "sum"))
    wk["bankroll_end"] = df.groupby("week").bankroll_after.last()
    print(wk.round(2).to_string())
    print(f"\nflat ${a.flat:.0f}: staked ${df.flat_stake.sum():.0f}, profit ${df.flat_profit.sum():+.2f} ({df.flat_profit.sum() / df.flat_stake.sum():+.1%} ROI)")
    print(f"{a.fraction:.2g} Kelly on ${a.bankroll:.0f}: staked ${df.kelly_stake.sum():.2f}, bankroll ${df.bankroll_after.iloc[-1]:.2f} ({(df.bankroll_after.iloc[-1] / a.bankroll - 1):+.1%}), ROI on stakes {df.kelly_profit.sum() / df.kelly_stake.sum():+.1%}")
    out = C.OUTPUT / f"bankroll_{a.season}_wk{a.first}-{a.last}.csv"
    df.to_csv(out, index=False)
    print("wrote", out)


if __name__ == "__main__":
    main()
