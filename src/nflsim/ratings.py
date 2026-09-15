"""Current team ratings: preseason prior updated with each played week of the current season.

For every completed game a team's performance is measured as
    perf = PERF_EPA_WEIGHT * (net EPA per play * plays per game) + (1 - PERF_EPA_WEIGHT) * capped margin
then adjusted for the opponent's rating and home field. The rating is the precision-weighted
average of the preseason prior (worth PRIOR_GAMES games) and the games played so far.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from . import config as C
from .strength import load_pbp, team_strength


def game_performance(season: int, week: int) -> pd.DataFrame:
    """One row per team-game for the given week: net EPA in points, margin, opponent, home flag."""
    pbp = load_pbp(season)
    pbp = pbp[pbp.week == week]
    if pbp.empty:
        return pd.DataFrame(columns=["team", "week", "opp", "home", "net_epa_pts", "margin"])
    games = pd.read_csv(C.RAW / "games.csv", low_memory=False)
    games = games[(games.season == season) & (games.week == week) & games.result.notna()]
    margin = {}
    for _, g in games.iterrows():
        margin[g.home_team] = g.result
        margin[g.away_team] = -g.result
    rows = []
    for team, grp in pbp.groupby("posteam"):
        d = pbp[pbp.defteam == team]
        if team not in margin:
            continue
        rows.append({"team": team, "week": week, "opp": grp.defteam.iloc[0], "home": bool(grp.home_team.iloc[0] == team),
                     "net_epa_pts": float((grp.epa.mean() - d.epa.mean()) * C.PLAYS_PER_GAME), "margin": float(margin[team])})
    return pd.DataFrame(rows)


def current_ratings(season: int, week: int, verbose: bool = False) -> pd.DataFrame:
    """Ratings entering `week`: preseason prior plus every completed week before it."""
    prior = team_strength(season - 1)["rating_regressed"].rename("prior")
    out = prior.to_frame()
    out["games"] = 0
    out["perf_sum"] = 0.0
    rating = prior.copy()
    history = []
    for w in range(1, week):
        perf = game_performance(season, w)
        if perf.empty:
            continue
        perf["perf"] = C.PERF_EPA_WEIGHT * perf.net_epa_pts + (1 - C.PERF_EPA_WEIGHT) * perf.margin.clip(-C.PERF_MARGIN_CAP, C.PERF_MARGIN_CAP)
        # opponent adjustment uses ratings entering that week (not the result itself)
        perf["opp_rating"] = perf.opp.map(rating)
        perf["hfa"] = np.where(perf.home, C.HOME_FIELD, -C.HOME_FIELD)
        perf["perf_adj"] = perf.perf + perf.opp_rating - perf.hfa
        for _, r in perf.iterrows():
            out.loc[r.team, "games"] += 1
            out.loc[r.team, "perf_sum"] += r.perf_adj
        rating = (C.PRIOR_GAMES * out.prior + out.perf_sum) / (C.PRIOR_GAMES + out.games)
        history.append(perf.assign(rating_after=perf.team.map(rating)))
    out["rating"] = rating
    out["change"] = out.rating - out.prior
    out.index.name = "team"
    if verbose and history:
        pd.set_option("display.width", 200)
        print(pd.concat(history)[["team", "week", "opp", "home", "margin", "net_epa_pts", "perf_adj", "rating_after"]].round(2).to_string())
    return out.sort_values("rating", ascending=False)


if __name__ == "__main__":
    season = int(sys.argv[1]) if len(sys.argv) > 1 else C.SEASON
    week = int(sys.argv[2]) if len(sys.argv) > 2 else C.WEEK
    r = current_ratings(season, week, verbose=True)
    C.PROCESSED.mkdir(parents=True, exist_ok=True)
    r.round(3).to_csv(C.PROCESSED / f"ratings_{season}_wk{week}.csv")
    print(r.round(2).to_string())
