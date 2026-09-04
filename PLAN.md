# 2026 NFL Week 1 Simulation: Plan

Goal: produce a moneyline winner and a confidence level for all 16 Week 1 games of
the 2026 NFL season (Sept 9 to Sept 14, 2026), using injuries, individual player
status, weather, last season's data, and other relevant context.

This document is written before any model code. It lays out the stages, what
each stage consumes and produces, the constraints found during reconnaissance,
and the decisions taken to work within them.

## Stage 0: Reconnaissance and constraints (done)

Findings from the environment probe:

| Source | Status | Use |
|---|---|---|
| nflverse `games.csv` (GitHub releases) | Reachable | Full 2026 schedule incl. Week 1 with opening moneylines, spreads, totals, roof, surface, coaches, rest days; all 2025 results |
| nflverse 2025 play-by-play | Reachable | EPA, success rate, pass/rush splits for team strength |
| nflverse 2026 rosters and depth charts | Reachable | Starting QB identity, roster continuity |
| nflverse 2025 injuries, team and player stats, ESPN QBR, PFR advanced stats | Reachable | QB quality, last-season injury exposure |
| nflverse 2026 injuries file | 404 (not published yet) | Cannot use |
| ESPN, NFL.com, weather.gov, Open-Meteo, PFR, RotoWire, Footballguys, etc. | Blocked by egress proxy | Cannot fetch directly |
| WebSearch tool | Works | Only channel for 2026 injury news and weather forecasts, returns summarized text rather than structured data |
| PyPI | Reachable | pandas, numpy, scipy, pyarrow installed |

Decisions driven by these constraints:

1. Injury and player-status data for 2026 Week 1 will be collected via web search,
   one query set per game, and hand-curated into a versioned JSON file with a source
   URL per entry. The code consumes that JSON so it can be refreshed later without
   touching the model.
2. Weather will be collected the same way. As of Sept 4 most forecasts only reach
   Sept 10, so Sunday and Monday games will use climatological expectations flagged
   as low confidence, with dome and closed-roof games marked as weather-neutral.
3. The market line from nflverse (opening lines) is used as one input among
   several, not as the answer. The model reports where it disagrees with the market.

## Stage 1: Repository scaffold and data ingestion

- Create the package layout (`src/nflsim/`), `requirements.txt`, `.gitignore`
  (large raw files excluded, derived tables committed).
- `fetch_data.py`: download the nflverse files listed above into `data/raw/`
  with checksums and a manifest. Idempotent, skips existing files.
- Load the 2026 Week 1 slate: 16 games, kickoff, venue, roof, surface, neutral
  site (SF vs LA in Melbourne), rest days, opening lines, head coaches.

Output: `data/raw/*`, `data/processed/schedule_2026_wk1.csv`.

## Stage 2: Last-season team strength (2025)

From 2025 play-by-play compute per team, regular season plus playoffs weighted:

- Offensive and defensive EPA per play, split into pass and rush.
- Success rate, explosive play rate, early-down EPA, red-zone efficiency.
- Points for and against, Pythagorean expectation, point differential per game.
- Opponent adjustment: iterative adjustment of each unit's EPA by the quality of
  the opponents faced (ridge-style, a few passes).
- Second-half-of-season weighting so late-season form counts more than September.

Convert to a net rating in points per game and regress toward the league mean
(offseason regression, roughly 35 to 45 percent, larger for defense than offense
because defensive EPA is less stable year to year).

Output: `data/processed/team_strength_2025.csv` with a rating per team and its
components.

## Stage 3: Personnel and offseason change

- Identify each team's 2026 Week 1 starting QB from the depth chart and roster,
  cross-checked with news.
- Score QB quality using 2025 EPA per dropback, CPOE, ESPN QBR, and sacks, with
  rookies and career backups given prior-based values.
- Compare the 2026 starter with the QB who generated most of the team's 2025
  offensive EPA. Apply a QB-change adjustment in points.
- Head coach and coordinator changes: schedule data shows new head coaches (for
  example BAL, CLE, PIT, TEN, MIA, LV, NYG). New-coach and scheme-change
  uncertainty widens the outcome distribution and mildly regresses the rating.
- Roster continuity: share of 2025 snap-weighted contributors still on the 2026
  roster, by unit.

Output: `data/manual/qb_2026.json`, `data/processed/personnel_adjustments.csv`.

## Stage 4: Injuries and individual player status

- For each of the 16 games, run web searches on the official injury report,
  IR and PUP lists, suspensions, and beat-writer expectations.
- Record each relevant player: team, name, position, status (Out, IR, PUP,
  Suspended, Doubtful, Questionable, Probable), and source URL.
- Positional value table converts absences into points: starting QB largest,
  then LT, EDGE, WR1, CB1, and so on, with depth-chart-aware replacement
  quality. Questionable players are weighted by an assumed play probability.
- Produce a per-team injury adjustment in points and an uncertainty widening.

Output: `data/manual/injuries_2026_wk1.json`, `data/processed/injury_adjustments.csv`.

## Stage 5: Venue, weather, travel, and situational factors

- Home-field advantage: base value about 1.5 points, reduced for neutral sites,
  increased slightly for known loud venues, zero for the Melbourne game aside from
  travel and time-zone effects on both clubs.
- Weather: for outdoor games, search forecasts for wind, precipitation and
  temperature. Wind above about 15 mph and heavy rain reduce passing efficiency
  and lower totals; effects on win probability are small but the model includes
  them and widens variance. Dome and closed-roof games are neutral.
- Rest and travel: Week 1 gives equal rest, but cross-country and international
  travel are noted.
- Divisional matchups get slightly narrower distributions.

Output: `data/manual/weather_2026_wk1.json`, `data/processed/situational_adjustments.csv`.

## Stage 6: Rating model and expected margin

For each game compute the model's expected margin:

```
model_margin = (rating_home - rating_away)
             + home_field
             + qb_adj + injury_adj + coaching_adj + weather_adj
```

Then blend with the market spread using a fixed weight (market weight about
0.5 to 0.6, reflecting that opening lines are efficient but the model carries
fresh injury information the opening line did not have):

```
final_margin = w_market * market_spread + (1 - w_market) * model_margin
```

The blend weight is a documented parameter so it can be changed.

## Stage 7: Monte Carlo simulation

- Simulate each game 20,000 times. Margin is drawn from a normal distribution
  centered on `final_margin` with a standard deviation of about 13.5 points,
  widened by game-specific uncertainty (new coaches, new QBs, weather, injury
  uncertainty). Ties are resolved with an overtime sub-model.
- Team totals are simulated from the blended total and margin so the output also
  includes expected scores.
- Aggregate: home win probability, mean and median margin, distribution
  quantiles, probability of a blowout.

## Stage 8: Predictions, confidence, and report

- Winner = side with higher simulated win probability.
- Confidence tiers: Very High (over 80 percent), High (70 to 80), Moderate (60 to 70),
  Lean (55 to 60), Coin flip (50 to 55).
- Fair moneyline implied by the simulation, compared to the market moneyline, with
  an edge column.
- Outputs: `output/week1_2026_predictions.csv`, `.json`, and a Markdown report
  with per-game rationale (key injuries, weather, QB situation, model versus
  market).

## Stage 9: Validation

- Backtest the same pipeline on 2025 Week 1 using only 2024 data plus 2025
  opening lines, and score log loss and Brier score against actual results
  versus a market-only baseline. This checks that the blend is not worse than
  the market alone.
- Unit tests for rating math, moneyline conversions, and simulation invariants
  (probabilities sum to one, symmetric under home and away swap).

## Stage 10: Reproducibility and delivery

- `make run` or `python -m nflsim.run_week1` regenerates everything from the raw
  files and the curated JSON.
- README explains data sources, limitations, and how to refresh injuries or
  weather closer to kickoff.
- Commit and push to the `claude/nfl-week-one-simulation-00iyhz` branch.

## Known limitations to state up front

- Injury and weather inputs come from search summaries, not a structured feed,
  so they are as good as the news coverage on Sept 4 and should be refreshed on
  game day.
- Forecasts for Sept 13 and 14 do not exist yet as of writing; those games use
  climatology.
- Preseason ratings carry wide uncertainty. Even a strong Week 1 favorite loses
  roughly one time in four.
