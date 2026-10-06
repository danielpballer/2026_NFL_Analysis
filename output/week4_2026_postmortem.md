# Week 4 2026 post-mortem and model changes

## Scorecard

| Method | Winners | Log loss | Brier | Margin MAE |
|---|---|---|---|---|
| Model + market blend (published) | 10 / 16 | 0.609 | 0.214 | 7.3 |
| Pure model | 9 / 16 | 0.597 | 0.210 | 7.4 |
| Market spread | 9 / 16 | 0.637 | 0.225 | 7.5 |
| Market moneyline | 9 / 16 | 0.617 | 0.216 | |
| Coin flip | 8 / 16 | 0.693 | 0.250 | |

The best week so far on every metric and the third straight week beating the market on log
loss. The three Very High picks (Minnesota, Baltimore, Seattle) all won. The six misses:

- **Patriots 29, Bills 26 (High, 71%).** The biggest miss. We had Buffalo by 6.6 with New England
  carrying a 4-point injury hit. The Patriots outgained Buffalo and converted late; nothing in
  the inputs pointed the other way, and the market (Bills by 7) missed by the same amount.
- **Falcons 45, Saints 24 (62%).** Penix's best game of the season against a defense we rated
  near average. The margin error (25 points) is the largest of the season and is pure variance
  on a 3.6-point line.
- **Panthers 32, Lions 26 (62%).** Detroit's 6-point injury hit was the largest on the slate and
  the model had already cut the Lions to a 4-point favorite; Carolina still covered by ten.
- **Cowboys 34, Texans 30 (61%).** Both teams carried heavy injury hits; Houston's depleted
  secondary could not stop Prescott. A shootout the model's 42.5 total did not foresee.
- **Giants 36, Cardinals 24 (54% ARI).** A coin flip that went the other way; Winston's best
  game as a Giant.
- **Browns 27, Steelers 24 (56% PIT).** Thursday night home dog won; the pure-data lean (PIT by
  1.4) was within a field goal of the result.

Value bets: 3 of 7 (Jaguars +120, Bears -170, Seahawks -355 won; Titans +525, Bucs +160,
Raiders +185, Texans -142 lost) for -1.9 units. Four weeks of value picks are 16 of 35 and
roughly +11 units.

## Four weeks pooled (64 games)

| Method | Winners | Log loss | Brier |
|---|---|---|---|
| Blend | 40 / 64 | 0.641 | 0.226 |
| Pure model | 39 / 64 | 0.638 | 0.224 |
| Market spread | 40 / 64 | 0.655 | 0.231 |
| Market moneyline | 40 / 64 | 0.654 | 0.231 |

Weekly log loss, blend vs pure model: 0.628/0.640, 0.649/0.650, 0.676/0.663, 0.609/0.597.

- **Market-weight grid** on 64 games is flat from 0.0 to 0.4 (0.637 to 0.639) and gets worse
  above 0.5. The declining schedule reaches 0.43 for Week 5 and bottoms at 0.40 in Week 6, so
  it already lands on the plateau. No change.
- **Preseason prior weight.** Re-running the rating update with the prior worth 3, 5, 7, 9, 12
  and 20 games and scoring the rating-only line on Weeks 2 to 4: a lighter prior is clearly
  worse (log loss 0.694 at 3 games, 0.661 at 5) and 9 to 12 games is the optimum (0.648 and
  0.647). The current 9 stays.
- **Variance.** The sd grid is flat between 12 and 14.5 at the current 12.7.
- **Home field.** Home teams are 36 of 64; the blend has predicted home margins 1.5 points too
  high and the market 1.3 points too high. The standard error on 64 games is about 1.7 points,
  so this is noise for now. Revisit at the midseason point.
- **Calibration by tier.** Coin flip 5/10, Lean 7/12, Moderate 17/26 (65% at an average 64%),
  High 7/12 (58% at 74%), Very High 4/4. The High tier is the one overconfident bucket; twelve
  games is too few to act on.
- **Adjustments.** Injury and quarterback adjustments of 1.5 points or more pointed the same
  way as the market's error in 19 of 34 games (correlation 0.13). Directionally useful, weaker
  than after Week 3; the weights stay.

## Model changes for Week 5

1. **No parameter changes.** Every grid supports the current settings; the market weight
   continues its schedule to 0.43.
2. **Process.** The carry-over of long-term absences (IR, PUP, NFI, suspensions) is now a
   repo module (`nflsim.carryover`, run by `make inputs`) instead of a scratch script, and the
   pooled scorecard with its parameter grids is `nflsim.pooled` (`make pooled`), so the weekly
   review is reproducible.

Frozen: Weeks 1 to 4 outputs are the record.
