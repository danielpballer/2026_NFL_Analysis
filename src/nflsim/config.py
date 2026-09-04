"""Paths and model parameters. Every tunable number lives here so it is documented."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
MANUAL = ROOT / "data" / "manual"
PROCESSED = ROOT / "data" / "processed"
OUTPUT = ROOT / "output"

SEASON = 2026
WEEK = 1
PRIOR_SEASON = 2025

NFLVERSE = "https://github.com/nflverse/nflverse-data/releases/download"
RAW_FILES = {
    "games.csv": f"{NFLVERSE}/schedules/games.csv",
    "play_by_play_2025.csv.gz": f"{NFLVERSE}/pbp/play_by_play_2025.csv.gz",
    "play_by_play_2024.csv.gz": f"{NFLVERSE}/pbp/play_by_play_2024.csv.gz",
    "roster_2026.csv": f"{NFLVERSE}/rosters/roster_2026.csv",
    "depth_charts_2026.csv": f"{NFLVERSE}/depth_charts/depth_charts_2026.csv",
    "injuries_2025.csv": f"{NFLVERSE}/injuries/injuries_2025.csv",
    "stats_team_reg_2025.csv": f"{NFLVERSE}/stats_team/stats_team_reg_2025.csv",
    "qbr_season_level.csv": f"{NFLVERSE}/espn_data/qbr_season_level.csv",
}

# ---- Stage 2: team strength ---------------------------------------------------
PLAYS_PER_GAME = 63.0          # offensive snaps per team per game, converts EPA/play to points
LATE_SEASON_WEIGHT = 0.5       # week-18 plays weigh (1 + this) times week-1 plays
PLAYOFF_WEIGHT = 1.25
RIDGE_LAMBDA = 30.0            # shrinkage on per-team EPA coefficients (in plays)
EPA_VS_MARGIN_BLEND = 0.7      # weight of EPA rating vs adjusted point margin rating
OFFSEASON_KEEP_OFF = 0.62      # fraction of last year's offensive rating retained
OFFSEASON_KEEP_DEF = 0.48      # defense regresses harder year to year

# ---- Stage 3: quarterbacks -------------------------------------------------------
DROPBACKS_PER_GAME = 36.0
QB_SHRINK_DROPBACKS = 250.0    # shrink QB EPA/dropback toward prior with this many pseudo-dropbacks
QB_CHANGE_WEIGHT = 0.6         # how much of a QB swap shows up beyond the team rating
NEW_HC_REGRESSION = 0.10       # extra regression toward mean for new head coach
NEW_HC_EXTRA_SD = 1.0          # extra margin sd (points) for a new head coach
NEW_QB_EXTRA_SD = 1.0

# ---- Stage 4: injuries -------------------------------------------------------------
# points per game a starter at the position is worth over a replacement-level backup
POSITION_VALUE = {
    "QB": 0.0,   # handled by the QB module, never double counted here
    "LT": 1.0, "RT": 0.6, "OT": 0.8, "T": 0.8, "LG": 0.45, "RG": 0.45, "G": 0.45, "C": 0.5, "OL": 0.5,
    "WR1": 1.0, "WR2": 0.55, "WR3": 0.3, "WR": 0.55, "TE": 0.5, "TE1": 0.5, "TE2": 0.15,
    "RB": 0.45, "RB1": 0.45, "RB2": 0.15, "FB": 0.05,
    "EDGE": 0.8, "DE": 0.7, "OLB": 0.6, "DT": 0.45, "IDL": 0.45, "NT": 0.35, "DL": 0.5,
    "LB": 0.35, "ILB": 0.35, "MLB": 0.4,
    "CB": 0.7, "CB1": 0.85, "CB2": 0.5, "NCB": 0.35, "S": 0.4, "FS": 0.4, "SS": 0.4, "DB": 0.4,
    "K": 0.35, "P": 0.1, "LS": 0.05,
}
STAR_MULTIPLIER = 1.75
NON_STARTER_MULTIPLIER = 0.25
MISS_PROBABILITY = {
    "IR": 1.0, "PUP": 1.0, "NFI": 1.0, "Suspended": 1.0, "Out": 1.0,
    "Doubtful": 0.85, "Questionable": 0.45, "Probable": 0.1,
    "Returning-expected-to-play": 0.08,
}
INJURY_CAP_POINTS = 6.0

# ---- Stage 5: situational --------------------------------------------------------------
HOME_FIELD = 1.5
LOUD_VENUES = {"SEA": 0.5, "KC": 0.5, "BUF": 0.25, "PHI": 0.25, "GB": 0.25, "BAL": 0.25, "DEN": 0.25, "NO": 0.25}
DIVISION_GAME_SD_ADJ = -0.5
TRAVEL_PENALTY_PER_TZ = 0.15   # points per time zone crossed by the away team beyond one
WIND_COMPRESSION_PER_MPH = 0.012   # margin multiplier drops this much per mph above WIND_FREE
WIND_FREE = 10.0
RAIN_COMPRESSION = 0.03
WEATHER_EXTRA_SD = 0.5

# ---- Stage 6/7: blend and simulation ---------------------------------------------------
MARKET_WEIGHT = 0.55
MARGIN_SD = 13.3
TOTAL_SD = 10.0
N_SIMS = 20000
SEED = 20260913
OT_MARGIN_SENSITIVITY = 0.02   # tie-break win prob = 0.5 + this * expected margin

CONFIDENCE_TIERS = [
    (0.80, "Very High"), (0.70, "High"), (0.60, "Moderate"), (0.55, "Lean"), (0.0, "Coin flip"),
]

TIME_ZONES = {
    "ARI": -7, "ATL": -5, "BAL": -5, "BUF": -5, "CAR": -5, "CHI": -6, "CIN": -5, "CLE": -5,
    "DAL": -6, "DEN": -7, "DET": -5, "GB": -6, "HOU": -6, "IND": -5, "JAX": -5, "KC": -6,
    "LA": -8, "LAC": -8, "LV": -8, "MIA": -5, "MIN": -6, "NE": -5, "NO": -6, "NYG": -5,
    "NYJ": -5, "PHI": -5, "PIT": -5, "SEA": -8, "SF": -8, "TB": -5, "TEN": -6, "WAS": -5,
}
