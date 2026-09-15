# 2026 NFL Weekly Moneyline Simulation

Monte Carlo simulation of every game of the 2026 NFL season, one week at a time (Week 1 predicted
Sept 4 to 5, Week 2 predicted Sept 15).
For every game it produces a predicted winner, a win probability, a confidence tier, a fair
moneyline, projected score, and the reasoning behind it (last season's strength, quarterback
situation, injuries and player status, coaching changes, venue and weather, and the market line).

Results per week: `output/week{N}_2026_report.md`, the interactive page `output/week{N}_2026_slate.html`
(open it in a browser), and `output/week{N}_2026_predictions.csv` / `.json`. Completed weeks are
scored in `output/week{N}_2026_evaluation*.csv`; the Week 1 review is in
[`output/week1_2026_postmortem.md`](output/week1_2026_postmortem.md).

The step-by-step approach is documented in [`PLAN.md`](PLAN.md).

## How it works

1. **Schedule and market** (`nflsim.schedule`): the Week 1 slate, kickoff, venue, roof, rest and
   opening moneyline/spread/total come from the nflverse `games.csv` release.
2. **Team strength** (`nflsim.strength`, `nflsim.ratings`): the preseason prior is opponent-adjusted
   EPA per play (ridge regression on every 2025 pass and rush play, late-season and playoff plays
   weighted up) blended with an opponent-adjusted point-margin rating, regressed toward the mean
   for the offseason (offense keeps 62 percent, defense 48 percent). From Week 2 on, each played
   game updates the rating: the prior counts as nine games of evidence and each game adds one,
   measured by opponent-adjusted net EPA and capped margin.
3. **Quarterbacks** (`nflsim.qb`, `data/manual/qb_2026.json`): each 2026 starter is valued from
   2024 and 2025 EPA per dropback (shrunk by sample size) and compared with the QB play the
   team actually fielded in 2025. Rookies, returning-from-injury QBs and tiny samples use
   documented overrides.
4. **Injuries and player status** (`nflsim.build_manual`, `data/research/*.json`,
   `data/manual/player_overrides.json`): per-team injury, IR, PUP, suspension and
   questionable lists were collected by web search on Sept 4, 2026, cross-checked against the
   nflverse 2026 roster status codes, and converted into expected points lost by position
   (starter and star weightings, probability of missing by status, capped at 6 points).
5. **Coaching, venue, weather** (`nflsim.adjustments`, `data/manual/weather_2026_wk1.json`,
   `data/manual/coaching_2026.json`): new head coaches regress ratings and widen variance;
   home field is 1.5 points plus a venue bump; travel across time zones costs the visitor;
   wind and storm chances compress margins and lower totals; domes and closed roofs are
   weather-neutral; the Melbourne game is a neutral site.
6. **Blend and simulate** (`nflsim.simulate`, `nflsim.run_week`): the model margin is blended
   with the market spread (market weight 0.55), then each game is simulated 20,000 times with a
   margin standard deviation of 12.7 points (the 2023 to 2025 spread of results around closing
   lines), an early-season allowance that fades by Week 4, and game-specific widening.
7. **Validation** (`nflsim.backtest`, `nflsim.evaluate`, `tests/`): the pipeline is backtested on
   2025 Week 1 and every completed 2026 week is scored against results (accuracy, log loss,
   Brier, margin error) for the blend, the pure model and the market. Unit tests cover the odds
   math, simulation invariants, rating update and adjustment logic.

## Reproduce

```bash
pip install -r requirements.txt
make fetch            # downloads nflverse files (about 90 MB)
make inputs WEEK=2    # rebuilds data/manual/injuries_2026_wk2.json from data/research/wk2 + official report
make run WEEK=2       # writes output/week2_2026_*.csv/.json/.md and the HTML page
make evaluate WEEK=1  # scores a completed week
make backtest         # optional: 2025 Week 1 validation
make test
```

## Refreshing before kickoff

- Injuries: edit `data/research/wk{N}/group_*.json` or `data/manual/player_overrides_2026_wk{N}.json`,
  re-download `injuries_2026.csv` once the official Wednesday to Friday reports post, then
  `make inputs WEEK=N && make run WEEK=N`.
- Quarterbacks: edit `data/manual/qb_2026_wk{N}.json` (starter, `value_override`, `extra_sd`).
- Weather: edit `data/manual/weather_2026_wk{N}.json` (`temp_f`, `wind_mph`, `precip_chance_pct`,
  `roof_closed_expected`).
- Predictions for a week are frozen once published; rerunning after kickoff would pick up
  closing lines and official reports and no longer represent what was predicted.
- Model parameters all live in `src/nflsim/config.py`.

## Data sources and limitations

- nflverse releases (schedule with lines, play-by-play 2024 and 2025, 2026 rosters and depth
  charts, 2025 injuries, ESPN QBR) are the only structured feeds reachable from the build
  environment; ESPN, NFL.com and weather APIs were blocked, so injury and weather inputs come
  from web search summaries with source URLs recorded in `data/research/`.
- The nflverse opening lines predate most training-camp news; blending them with the model is
  how late injury information enters the prediction.
- Research was collected in two passes: Sept 4 for all teams (`data/research/group_A-D.json`)
  and a Sept 5 follow-up (`data/research/group_E_followup.json`) that completed Tampa Bay,
  Cincinnati, Dallas, the Giants, Denver and Kansas City and refreshed game-week status
  elsewhere. Official practice reports are not published until game week.
- Forecasts for Sept 13 and 14 were mostly beyond the reliable range on Sept 4 and are marked
  medium or low confidence.
