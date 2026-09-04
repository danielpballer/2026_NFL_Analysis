"""Stage 2: team strength from last season's play-by-play.

Rating = points per game above an average team on a neutral field, built from:
  * opponent-adjusted EPA/play (ridge regression of play EPA on offense and defense dummies,
    fit separately for pass and rush plays, late-season and playoff plays weighted up)
  * opponent-adjusted point margin (Massey-style least squares on game results)
Both are regressed toward zero for the offseason.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C
from .config import RAW

PBP_COLS = [
    "game_id", "season_type", "week", "posteam", "defteam", "home_team", "away_team",
    "play_type", "epa", "success", "pass", "rush", "qb_dropback", "passer_player_id",
    "passer_player_name", "qb_epa", "cpoe", "sack", "down",
]

TEAMS = sorted(C.TIME_ZONES)


def load_pbp(season: int) -> pd.DataFrame:
    df = pd.read_csv(RAW / f"play_by_play_{season}.csv.gz", low_memory=False, usecols=PBP_COLS)
    df = df[df.posteam.notna() & df.defteam.notna() & df.epa.notna()]
    df = df[(df["pass"] == 1) | (df["rush"] == 1)]
    df = df[df.play_type.isin(["pass", "run", "qb_spike", "qb_kneel"]) | df.play_type.isna()]
    df = df[~df.play_type.isin(["qb_spike", "qb_kneel"])]
    return df.reset_index(drop=True)


def play_weights(df: pd.DataFrame) -> np.ndarray:
    reg = 1.0 + C.LATE_SEASON_WEIGHT * (df.week.clip(1, 18) - 1) / 17.0
    w = np.where(df.season_type == "POST", C.PLAYOFF_WEIGHT * (1 + C.LATE_SEASON_WEIGHT), reg)
    return w.astype(float)


def ridge_epa(df: pd.DataFrame, teams: list[str], lam: float) -> tuple[pd.Series, pd.Series]:
    """Weighted ridge: epa ~ off[posteam] - def[defteam] + home. Returns (off, def) EPA/play above average.
    Positive defense value means the defense allows *less* EPA (good)."""
    n = len(df)
    ti = {t: i for i, t in enumerate(teams)}
    k = len(teams)
    X = np.zeros((n, 2 * k + 1))
    oi = df.posteam.map(ti).to_numpy()
    di = df.defteam.map(ti).to_numpy()
    X[np.arange(n), oi] = 1.0
    X[np.arange(n), k + di] = -1.0
    X[:, 2 * k] = np.where(df.posteam == df.home_team, 1.0, -1.0)
    y = df.epa.to_numpy(dtype=float)
    w = play_weights(df)
    Xw = X * w[:, None]
    A = X.T @ Xw + lam * np.eye(2 * k + 1)
    A[2 * k, 2 * k] -= lam  # do not shrink the home effect
    b = Xw.T @ y
    beta = np.linalg.solve(A, b)
    off = pd.Series(beta[:k], index=teams)
    dfn = pd.Series(beta[k:2 * k], index=teams)
    # centre so league average is zero on each side
    return off - off.mean(), dfn - dfn.mean()


def margin_rating(games: pd.DataFrame, teams: list[str], lam: float = 2.0) -> pd.Series:
    """Massey least squares on point margins with late-season weighting."""
    g = games.dropna(subset=["result"]).copy()
    ti = {t: i for i, t in enumerate(teams)}
    k = len(teams)
    X = np.zeros((len(g), k + 1))
    X[np.arange(len(g)), g.home_team.map(ti).to_numpy()] = 1.0
    X[np.arange(len(g)), g.away_team.map(ti).to_numpy()] = -1.0
    X[:, k] = np.where(g.location.str.lower().eq("neutral"), 0.0, 1.0)
    y = g.result.to_numpy(dtype=float).clip(-28, 28)  # cap blowouts
    w = np.where(g.game_type == "REG", 1 + C.LATE_SEASON_WEIGHT * (g.week.clip(1, 18) - 1) / 17.0,
                 C.PLAYOFF_WEIGHT * (1 + C.LATE_SEASON_WEIGHT))
    Xw = X * w[:, None]
    A = X.T @ Xw + lam * np.eye(k + 1)
    A[k, k] -= lam
    beta = np.linalg.solve(A, Xw.T @ y)
    r = pd.Series(beta[:k], index=teams)
    return r - r.mean()


def team_strength(season: int, games: pd.DataFrame | None = None) -> pd.DataFrame:
    pbp = load_pbp(season)
    teams = sorted(set(pbp.posteam) | set(pbp.defteam))
    out = pd.DataFrame(index=teams)
    for label, mask in [("pass", pbp["pass"] == 1), ("rush", pbp["rush"] == 1)]:
        off, dfn = ridge_epa(pbp[mask], teams, C.RIDGE_LAMBDA)
        out[f"off_{label}_epa"] = off
        out[f"def_{label}_epa"] = dfn
    # raw (unadjusted) descriptive stats
    grp = pbp.groupby("posteam")
    out["off_epa_raw"] = grp.epa.mean()
    out["off_success"] = grp.success.mean()
    out["def_epa_raw"] = -pbp.groupby("defteam").epa.mean()
    pass_share = pbp.groupby("posteam")["pass"].mean().reindex(teams).fillna(0.58)
    lg_pass = float(pbp["pass"].mean())
    # combine pass/rush by league-average play mix so dropback-heavy teams are not over-credited
    out["off_epa_adj"] = lg_pass * out.off_pass_epa + (1 - lg_pass) * out.off_rush_epa
    out["def_epa_adj"] = lg_pass * out.def_pass_epa + (1 - lg_pass) * out.def_rush_epa
    out["off_pts"] = out.off_epa_adj * C.PLAYS_PER_GAME
    out["def_pts"] = out.def_epa_adj * C.PLAYS_PER_GAME
    out["epa_rating"] = out.off_pts + out.def_pts
    if games is None:
        games = pd.read_csv(RAW / "games.csv", low_memory=False)
    gs = games[(games.season == season) & games.result.notna()]
    out["margin_rating"] = margin_rating(gs, teams)
    out["rating_raw"] = C.EPA_VS_MARGIN_BLEND * out.epa_rating + (1 - C.EPA_VS_MARGIN_BLEND) * out.margin_rating
    # regress the two EPA components separately (defense regresses harder), then re-blend with margin
    off_reg = out.off_pts * C.OFFSEASON_KEEP_OFF
    def_reg = out.def_pts * C.OFFSEASON_KEEP_DEF
    keep_avg = (C.OFFSEASON_KEEP_OFF + C.OFFSEASON_KEEP_DEF) / 2
    out["rating_regressed"] = C.EPA_VS_MARGIN_BLEND * (off_reg + def_reg) + (1 - C.EPA_VS_MARGIN_BLEND) * out.margin_rating * keep_avg
    out["pass_share"] = pass_share
    out.index.name = "team"
    return out.sort_values("rating_regressed", ascending=False)


if __name__ == "__main__":
    import sys
    season = int(sys.argv[1]) if len(sys.argv) > 1 else C.PRIOR_SEASON
    ts = team_strength(season)
    C.PROCESSED.mkdir(parents=True, exist_ok=True)
    ts.round(4).to_csv(C.PROCESSED / f"team_strength_{season}.csv")
    pd.set_option("display.width", 200)
    print(ts[["off_pts", "def_pts", "epa_rating", "margin_rating", "rating_raw", "rating_regressed"]].round(2))
