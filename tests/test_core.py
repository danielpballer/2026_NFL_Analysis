import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nflsim import config as C
from nflsim.adjustments import GameContext, injury_adjustment
from nflsim.schedule import devig, moneyline_to_prob, prob_to_moneyline
from nflsim.simulate import blend_margin, confidence_tier, simulate_game


def test_moneyline_round_trip():
    for ml in (-300, -150, -110, 110, 150, 300):
        p = moneyline_to_prob(ml)
        assert abs(prob_to_moneyline(p) - ml) <= 1


def test_devig_sums_to_one():
    h, a = devig(moneyline_to_prob(-185), moneyline_to_prob(154))
    assert abs(h + a - 1) < 1e-9 and h > a


def test_simulation_symmetry():
    s1 = simulate_game(3.0, 45.0, n=40000)
    s2 = simulate_game(-3.0, 45.0, n=40000)
    assert abs(s1["p_home"] - (1 - s2["p_home"])) < 0.02
    assert abs(simulate_game(0.0, 45.0, n=40000)["p_home"] - 0.5) < 0.02


def test_simulation_monotone_in_margin():
    ps = [simulate_game(m, 45.0, n=20000)["p_home"] for m in (-7, -3, 0, 3, 7)]
    assert ps == sorted(ps)
    assert 0.68 < ps[-1] < 0.74  # 7-point favorite wins about 70 percent


def test_blend():
    assert blend_margin(4.0, 2.0, 0.5) == 3.0
    assert blend_margin(4.0, None) == 4.0


def test_confidence_tiers():
    assert confidence_tier(0.85) == "Very High"
    assert confidence_tier(0.72) == "High"
    assert confidence_tier(0.65) == "Moderate"
    assert confidence_tier(0.57) == "Lean"
    assert confidence_tier(0.51) == "Coin flip"


def test_injury_cap_and_qb_exclusion():
    inj = {"teams": {"X": {"players": [
        {"player": f"P{i}", "position": "LT", "status": "Out", "starter": True, "star": True} for i in range(20)
    ] + [{"player": "QB", "position": "QB", "status": "Out", "starter": True}]}}}
    r = injury_adjustment("X", inj)
    assert r["injury_pts"] == -C.INJURY_CAP_POINTS
    assert "QB" not in r["injury_details"]


def test_home_field_and_weather():
    ctx = GameContext("g", "SEA", "NE", False, False, "outdoors", {"wind_mph": 20, "precip_chance_pct": 60})
    assert ctx.home_field() == C.HOME_FIELD + C.LOUD_VENUES["SEA"]
    assert ctx.travel() > 0
    mult, sd, note = ctx.weather_factor()
    assert mult < 1.0 and sd > 0 and "wind" in note
    neutral = GameContext("g", "LA", "SF", True, True, "dome", {})
    assert neutral.home_field() == 0.0 and neutral.weather_factor()[0] == 1.0
