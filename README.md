# 2026 NFL Week 1 Moneyline Simulation

Monte Carlo simulation of all 16 Week 1 games of the 2026 NFL season (Sept 9 to 14, 2026).
For every game it produces a predicted winner, a win probability, a confidence tier, a fair
moneyline, projected score, and the reasoning behind it (last season's strength, quarterback
situation, injuries and player status, coaching changes, venue and weather, and the market line).

Results: [`output/week1_2026_report.md`](output/week1_2026_report.md)
(also `output/week1_2026_predictions.csv` and `.json`).

The step-by-step approach is documented in [`PLAN.md`](PLAN.md).

## How it works

1. **Schedule and market** (`nflsim.schedule`): the Week 1 slate, kickoff, venue, roof, rest and
   opening moneyline/spread/total come from the nflverse `games.csv` release.
2. **Team strength from 2025** (`nflsim.strength`): opponent-adjusted EPA per play (ridge
   regression on every 2025 pass and rush play, late-season and playoff plays weighted up)
   blended with an opponent-adjusted point-margin rating, then regressed toward the mean for
   the offseason (offense keeps 62 percent, defense 48 percent).
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
6. **Blend and simulate** (`nflsim.simulate`, `nflsim.run_week1`): the model margin is blended
   with the market spread (market weight 0.55), then each game is simulated 20,000 times with a
   margin standard deviation of about 13.3 points widened by game-specific uncertainty.
7. **Validation** (`nflsim.backtest`, `tests/`): the same pipeline predicts 2025 Week 1 from 2024
   data; see `output/backtest_2025_wk1_scores.csv`. Unit tests cover the odds math,
   simulation invariants and adjustment logic.

## Reproduce

```bash
pip install -r requirements.txt
make fetch      # downloads nflverse files (about 90 MB)
make inputs     # rebuilds data/manual/injuries_2026_wk1.json from data/research
make run        # writes output/week1_2026_*.csv/.json/.md
make backtest   # optional: 2025 Week 1 validation
make test
```

## Refreshing before kickoff

- Injuries: edit `data/research/group_*.json` or `data/manual/player_overrides.json`, then
  `make inputs && make run`. Official practice reports are published Wednesday to Friday of
  game week and will supersede the Sept 4 snapshot.
- Quarterbacks: edit `data/manual/qb_2026.json` (starter, `value_override`, `extra_sd`).
- Weather: edit `data/manual/weather_2026_wk1.json` (`temp_f`, `wind_mph`, `precip_chance_pct`,
  `roof_closed_expected`).
- Model parameters all live in `src/nflsim/config.py`.

## Data sources and limitations

- nflverse releases (schedule with lines, play-by-play 2024 and 2025, 2026 rosters and depth
  charts, 2025 injuries, ESPN QBR) are the only structured feeds reachable from the build
  environment; ESPN, NFL.com and weather APIs were blocked, so injury and weather inputs come
  from web search summaries with source URLs recorded in `data/research/`.
- The nflverse opening lines predate most training-camp news; blending them with the model is
  how late injury information enters the prediction.
- Tampa Bay and Cincinnati research was thinner than the other 30 teams because the search
  budget ran out; their entries are flagged in the report.
- Forecasts for Sept 13 and 14 were mostly beyond the reliable range on Sept 4 and are marked
  medium or low confidence.
