# Week 6 2026 post-mortem and model changes

## Scorecard

| Method | Winners | Log loss | Brier | Margin MAE |
|---|---|---|---|---|
| Model + market blend (published, Sunday build) | 8 / 14 | 0.741 | 0.267 | 7.3 |
| Pure model | 6 / 14 | 0.765 | 0.279 | 7.9 |
| Market spread | 9 / 14 | 0.712 | 0.253 | 6.5 |
| Market moneyline | 8 / 14 | 0.722 | 0.258 | |
| Coin flip | 7 / 14 | 0.693 | 0.250 | |

The worst week of the season for everyone: the market lost to a coin flip on log loss and the
blend lost to the market for the first time since Week 1. The pure model was the worst of all,
its first week below the blend by a wide margin. The misses:

- **Cardinals 18, Rams 16 (Very High, 86%).** A 12.5-point favorite on a short week after a
  Monday night overtime loss scored 16 points. The biggest log-loss hit of the season.
- **Titans 26, Colts 20 (High, 74%).** Tennessee's first win, at Indianapolis, with Cam Ward
  rated the weakest starter in the league.
- **Texans 34, Jaguars 31 (62%).** Houston scored 34 in London without David Montgomery.
- **Browns 13, Saints 34-27 over the Giants, Broncos 17-14 over the Seahawks.** Three one-score
  games that all went against the pick, two of them against the home-dog Browns and Saints that
  the data had slightly behind.

Winners: Panthers over McKee's Eagles (the Sunday flip), Bears with Williams back (the coin flip),
Patriots, Steelers at Tampa, Bills, Chiefs 22-6, Packers on Sunday night, 49ers on Monday.

Value bets at the Tuesday table: 3 of 8 (Packers -118, 49ers -395 and Browns +190 won; Falcons
+145, Giants -110, Raiders +225, Bucs +124 and Jaguars -148 lost). Week 6 was -2.0 flat units and -$37 on the
quarter-Kelly bankroll, its first losing week. Season to date: flat $10 is +$3.82 on $570
staked; quarter-Kelly from $1,000 stands at $1,241.

## Six weeks pooled (92 games)

| Method | Winners | Log loss |
|---|---|---|
| Blend | 56 / 92 | 0.656 |
| Pure model | 52 / 92 | 0.658 |
| Market spread | 58 / 92 | 0.663 |
| Market moneyline | 57 / 92 | 0.662 |

- **Variance.** The sd grid has moved: 12.7 scores 0.6543, 13.5 scores 0.6533, 14.5 to 16 score
  0.6525. Two upset-heavy weeks say the margin distribution is wider than the 2023-25 closing-line
  residual. **MARGIN_SD goes from 12.7 to 13.5**, which also trims the big-favorite probabilities
  by one to two points.
- **Injuries.** Third straight review favouring a lower weight: scale 0.5 scores 0.6538 against
  0.6548 at 0.75 and 0.6560 at full weight, on both the blend and the pure model.
  **INJURY_SCALE goes from 0.75 to 0.6.**
- **Quarterbacks.** Removing the quarterback adjustment costs 0.006 of log loss; kept.
- **Market weight.** Flat from 0.3 to 0.5; the schedule gives 0.37 for Week 7. No change.
- **Home field.** Home teams are 47 of 92 (51%); the blend's home margin is 1.75 points high
  and the market's 1.5. That is about 1.2 standard errors. Not changed yet, but the market
  itself is overrating home teams this season, so the preseason 1.5-point base is on watch.
- **Calibration.** Picks at 72% or better are 15 of 19 (79% at an average 78.5%): the top tiers
  are calibrated even after the Rams and Colts misses. Coin flip 8/15, Lean 9/18, Moderate 23/35.

## Model changes for Week 7

1. Margin sd 12.7 to 13.5.
2. Injury scale 0.75 to 0.6.

Frozen: Weeks 1 to 6 outputs are the record.
