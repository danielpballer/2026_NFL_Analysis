"""Stage 8: write CSV, JSON and a Markdown report with per-game rationale."""
from __future__ import annotations

import json
from datetime import date

import pandas as pd

from . import config as C
from .adjustments import load_json


def _fmt_ml(x) -> str:
    x = int(x)
    return f"+{x}" if x > 0 else str(x)


def write_outputs(df: pd.DataFrame, season: int, week: int) -> None:
    C.OUTPUT.mkdir(parents=True, exist_ok=True)
    stem = C.OUTPUT / f"week{week}_{season}_predictions"
    df.to_csv(f"{stem}.csv", index=False)
    df.to_json(f"{stem}.json", orient="records", indent=2)
    (C.OUTPUT / f"week{week}_{season}_report.md").write_text(markdown_report(df, season, week))
    print(f"wrote {stem}.csv, {stem}.json and the markdown report")


def markdown_report(df: pd.DataFrame, season: int, week: int) -> str:
    inj = load_json(f"injuries_{season}_wk{week}.json")
    wx = load_json(f"weather_{season}_wk{week}.json")
    L = []
    L.append(f"# {season} NFL Week {week} Moneyline Simulation\n")
    L.append(f"Generated {date.today().isoformat()}. Injuries collected {inj.get('collected_on', 'n/a')} (follow-up pass Sept 5), weather collected {wx.get('collected_on', 'n/a')}.")
    L.append(f"Each game simulated {C.N_SIMS:,} times. Market weight in the blend: {C.MARKET_WEIGHT:.2f}. See PLAN.md for the method.\n")
    L.append("## Summary\n")
    L.append("| Kickoff (ET) | Matchup | Pick | Win prob | Confidence | Fair ML | Market ML | Proj score | Model vs market |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for _, r in df.iterrows():
        pick_home = r.predicted_winner == r.home
        fair = r.fair_home_moneyline if pick_home else r.fair_away_moneyline
        mkt = r.market_home_moneyline if pick_home else r.market_away_moneyline
        edge = r.edge_vs_market_home if pick_home else -r.edge_vs_market_home
        L.append(f"| {r.kickoff} | {r.away} @ {r.home}{' (neutral)' if r.neutral_site else ''} | **{r.predicted_winner}** | {r.win_probability:.1%} | {r.confidence} | {_fmt_ml(fair)} | {_fmt_ml(mkt)} | {r.away} {r.proj_away_pts:.0f} - {r.home} {r.proj_home_pts:.0f} | {edge:+.1%} |")
    L.append("")
    tiers = df.confidence.value_counts()
    L.append("Confidence tiers: " + ", ".join(f"{k} {v}" for k, v in tiers.items()) + ".")
    L.append("Win probability is the pick's chance to win, fair moneyline is what that probability implies, model vs market is the pick's win probability minus the market's vig-free probability (positive means the model likes the pick more than the market).\n")
    L.append("## Game by game\n")
    for _, r in df.iterrows():
        L.append(f"### {r.away} @ {r.home} — {r.kickoff}{' (neutral site)' if r.neutral_site else ''}\n")
        L.append(f"**Pick: {r.predicted_winner}** ({r.win_probability:.1%}, {r.confidence}). Projected: {r.away} {r.proj_away_pts:.0f}, {r.home} {r.proj_home_pts:.0f}. Simulated margin sd {r.margin_sd:.1f}.\n")
        L.append(f"- Ratings from 2025 (points vs average, regressed): {r.home} {r.home_rating_2025:+.1f}, {r.away} {r.away_rating_2025:+.1f}. After QB, coaching and injury adjustments: {r.home} {r.home_rating_adj:+.1f}, {r.away} {r.away_rating_adj:+.1f}.")
        L.append(f"- Quarterbacks: {r.home} {r.home_qb} ({r.home_qb_adj:+.1f} vs 2025 QB play), {r.away} {r.away_qb} ({r.away_qb_adj:+.1f}).")
        for side, team in (("home", r.home), ("away", r.away)):
            d = r[f"{side}_injury_details"]
            pts = r[f"{side}_injury_pts"]
            L.append(f"- {team} injuries ({pts:+.1f} pts): {d if d else 'no material absences found'}.")
        hc = [t for t, f in ((r.home, r.home_new_hc), (r.away, r.away_new_hc)) if f]
        if hc:
            L.append(f"- New head coach: {', '.join(hc)} (rating regressed, variance widened).")
        L.append(f"- Venue and weather: {r.venue}, roof {r.roof}; {r.weather_note}" + (f", {r.weather_temp_f:.0f}F, wind {r.weather_wind_mph:.0f} mph, precip {r.weather_precip_pct:.0f}% ({r.weather_confidence} confidence)" if pd.notna(r.weather_temp_f) else "") + f". Home edge used: {r.home_field_pts:+.1f}.")
        L.append(f"- Margin: model {r.model_margin_home:+.1f} for {r.home}, market spread {r.market_spread_home:+.1f}, blended {r.final_margin_home:+.1f}. Market ML {r.home} {_fmt_ml(r.market_home_moneyline)} / {r.away} {_fmt_ml(r.market_away_moneyline)}; model fair ML {r.home} {_fmt_ml(r.fair_home_moneyline)} / {r.away} {_fmt_ml(r.fair_away_moneyline)}.")
        notes = [n for n in (r.home_qb_notes, r.away_qb_notes) if isinstance(n, str) and n]
        for n in notes:
            L.append(f"- Note: {n}")
        L.append("")
    L.append("## Caveats\n")
    L.append("- Opening market lines from nflverse predate most camp injuries; the model blends them with its own rating so late news is partially reflected.")
    L.append("- Injury and weather inputs come from web search summaries, not a structured feed. Refresh `data/manual/*.json` and rerun on game day.")
    L.append("- Forecasts beyond about a week out are climatology with low confidence; dome and closed-roof games are weather neutral.")
    L.append("- A 70 percent favorite still loses three times in ten. Confidence tiers describe probability, not certainty.")
    return "\n".join(L) + "\n"
