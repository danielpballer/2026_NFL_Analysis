# Week 9 2026 post-mortem and model changes

## Scorecard

| Method | Winners | Log loss | Brier | Margin MAE |
|---|---|---|---|---|
| Model + market blend (published, Thursday build) | 14 / 15 | 0.438 | 0.130 | 7.6 |
| Pure model | 14 / 15 | 0.431 | 0.128 | 7.3 |
| Market spread | 14 / 15 | 0.455 | 0.137 | 8.5 |
| Market moneyline | 14 / 15 | 0.412 | 0.120 | |
| Coin flip | 7.5 / 15 | 0.693 | 0.250 | |

Fourteen of fifteen, the best week of the season for every method: favorites won 14 games and
only the Packers (45-27 at New England, a 57% Lean the other way) broke the pattern. All six High
picks and all four Moderate picks won. The market moneyline still scored best because it priced
the favorites more heavily than the blend did.

Value bets at the Tuesday table: 3 of 12 (Broncos -148, Texans -198, Bengals -162 won; all nine
underdogs lost) for -7.2 flat units and -$128 on the quarter-Kelly bankroll, the fourth straight
losing week.

## Nine weeks pooled (135 games)

| Method | Winners | Log loss |
|---|---|---|
| Blend | 89 / 135 | 0.628 |
| Pure model | 85 / 135 | 0.631 |
| Market spread | 91 / 135 | 0.631 |
| Market moneyline | 90 / 135 | 0.627 |

The market moneyline has caught the blend. Split by period the picture is clear: in Weeks 1 to 5
the blend led the market 0.641 to 0.652; in Weeks 6 to 9 the market led 0.594 to 0.611. The
model's edge was an early-season edge.

### What the review found

1. **The variance increases were a mistake.** MARGIN_SD went 12.7, 13.5, 14.0 after the upset
   weeks 6 and 7. Two chalk weeks later the 135-game grid favours 12 to 12.7 (0.6248 to 0.6251)
   over 14 (0.6264). Widening the distribution compressed the favorites exactly when favorites
   started winning, which is most of the gap to the market moneyline in Weeks 8 and 9. Reverted
   to 12.7, the 2023-25 closing-line value, and it will not be tuned on single weeks again.
2. **The declining market weight went the wrong way.** The schedule assumed the market's
   information advantage fades as in-season data accumulates. The data say the opposite: at a
   fixed sd, more market weight is monotonically better in Weeks 6 to 9 (0.604 at 0.35, 0.598
   at 1.0) and worse in Weeks 1 to 5. Pooled, 0.35 to 0.50 is flat (0.6242 to 0.6240). From
   Week 10 the market's share is a flat 0.50.
3. **Quarterback adjustments were under-weighted.** Scaling them by 1.25 to 1.5 improves the
   pooled log loss on every blend (0.6242 to 0.6232 at 1.25); teams on backup quarterbacks have
   lost by more than the model expected all season. QB_CHANGE_WEIGHT goes from 0.6 to 0.75.
4. **The value table is losing, and the losses are in modest underdogs.** Tuesday value bets
   are 30-53 for -$97 at flat $10 (quarter-Kelly bankroll $1,027 from $1,000, down from $1,278
   after Week 5). By price: favorites 15 of 25 (model said 66%), dogs at +100 to +249 only 10
   of 38 (model said 43%, about two standard errors short), longshots +250 and up 5 of 20, all
   five in Weeks 1 to 5. The model's disagreements with the market in favor of modest underdogs
   have not been edges. The same rule applied to the late-week build (final injury news, later
   line) comes out roughly break-even to slightly positive across thresholds, so the Tuesday
   prices are not the bargain the early weeks suggested. The value table's cut is raised from 2
   to 5 percent of expected value from Week 10, and the three changes above all shrink the
   model's distance from the market.
5. **Home field and injuries.** Home teams are exactly 50 percent; the grid slightly prefers
   0.0 to the current 0.5 but the difference is 0.0008. Injury scale is flat below 0.5. Both
   unchanged.

Calibration by tier: Coin flip 11/21, Lean 17/27, Moderate 34/51 (67% at 64%), High 22/30 (73%
at 75%), Very High 5/6. Picks are calibrated; it is the disagreement with the market that is not.

## Model changes for Week 10

1. Margin sd 14.0 back to 12.7.
2. Market weight 0.35 to a flat 0.50.
3. Quarterback change weight 0.6 to 0.75, measured against an in-season baseline: the 2025 fielded
   value (worth nine games, like the rating prior) averaged with this season's actual starters.
   Backtested neutral on Weeks 1 to 9 (0.6243 against 0.6240) and adopted because the old 2025-only
   baseline double counts more every week and gave Minnesota a bonus for starting its backup.
4. Value-table threshold 2% to 5% expected value.
5. Process: the Tuesday value table is now snapshotted to `output/weekN_2026_value_tuesday.json`
   (the betting record no longer depends on git history), and the research prompts are generated
   by `nflsim.research_prompts`.

Frozen: Weeks 1 to 9 outputs are the record.
