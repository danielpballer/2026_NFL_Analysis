"""Stage 3 (data part): quarterback value from last season's dropbacks.

value = points per game above an average starter, shrunk toward a prior by sample size.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C
from .config import RAW
from .strength import load_pbp


SEASON_WEIGHTS = {0: 1.0, 1: 0.5}   # offset from the most recent season -> weight


def _dropbacks(season: int) -> pd.DataFrame:
    pbp = load_pbp(season)
    db = pbp[(pbp.qb_dropback == 1) & pbp.passer_player_name.notna()].copy()
    db["qb_epa"] = db.qb_epa - db.qb_epa.mean()   # centre each season on its own league mean
    db["season"] = season
    return db


def qb_values(season: int, prior_epa: float = -0.05, seasons_back: int = 1) -> pd.DataFrame:
    """QB value using the last `seasons_back + 1` seasons, most recent weighted highest."""
    parts = []
    for k in range(seasons_back + 1):
        if not (RAW / f"play_by_play_{season - k}.csv.gz").exists():
            continue  # older season not downloaded: fall back to what is available
        d = _dropbacks(season - k)
        d["w"] = SEASON_WEIGHTS.get(k, 0.25)
        parts.append(d)
    db = pd.concat(parts, ignore_index=True)
    lg = 0.0
    latest = db[db.season == season]
    g = db.groupby(["passer_player_id", "passer_player_name"])
    gl = latest.groupby(["passer_player_id", "passer_player_name"])
    q = pd.DataFrame({
        "dropbacks": g.w.sum(),
        "dropbacks_latest": gl.size(),
        "epa_per_db": g.apply(lambda x: np.average(x.qb_epa, weights=x.w)),
        "cpoe": g.cpoe.mean(),
        "sack_rate": g.sack.mean(),
        "teams": g.posteam.agg(lambda s: ",".join(sorted(set(s)))),
        "primary_team": gl.posteam.agg(lambda s: s.value_counts().index[0]),
    }).reset_index()
    q["dropbacks_latest"] = q.dropbacks_latest.fillna(0).astype(int)
    q["primary_team"] = q.primary_team.fillna("")
    n = q.dropbacks
    # shrink toward a below-average prior (unknown QBs are usually backups)
    q["epa_shrunk"] = (n * q.epa_per_db + C.QB_SHRINK_DROPBACKS * (lg + prior_epa)) / (n + C.QB_SHRINK_DROPBACKS)
    q["value_pts"] = (q.epa_shrunk - lg) * C.DROPBACKS_PER_GAME
    q["league_epa_per_db"] = lg
    return q.sort_values("dropbacks", ascending=False).reset_index(drop=True)


def team_primary_qb(season: int) -> pd.DataFrame:
    """Dropback-weighted average QB value each team actually fielded last season."""
    pbp = load_pbp(season)
    db = pbp[(pbp.qb_dropback == 1) & pbp.passer_player_name.notna()]
    qv = qb_values(season).groupby("passer_player_name")["value_pts"].max()
    rows = []
    for team, grp in db.groupby("posteam"):
        counts = grp.passer_player_name.value_counts()
        fielded = float(sum(qv.get(n, -2.0) * c for n, c in counts.items()) / counts.sum())
        rows.append({"team": team, "primary_qb_2025": counts.index[0], "primary_share": counts.iloc[0] / counts.sum(),
                     "fielded_qb_value": fielded, "primary_qb_value": float(qv.get(counts.index[0], -2.0))})
    return pd.DataFrame(rows).set_index("team")


if __name__ == "__main__":
    season = C.PRIOR_SEASON
    q = qb_values(season)
    C.PROCESSED.mkdir(parents=True, exist_ok=True)
    q.round(4).to_csv(C.PROCESSED / f"qb_values_{season}.csv", index=False)
    t = team_primary_qb(season)
    t.round(3).to_csv(C.PROCESSED / f"team_qb_{season}.csv")
    pd.set_option("display.width", 200)
    print(q[q.dropbacks >= 150][["passer_player_name", "primary_team", "dropbacks", "epa_per_db", "cpoe", "value_pts"]].round(3).head(45).to_string())
    print(t.round(2))
