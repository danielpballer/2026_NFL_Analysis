# Week 11 2026 post-mortem and model review

## Scorecard

| Method | Winners | Log loss | Brier | Margin MAE |
|---|---|---|---|---|
| Model + market blend (published, Thursday build) | 9 / 13 | 0.548 | 0.189 | 8.2 |
| Pure model | 9 / 13 | 0.583 | 0.202 | 8.7 |
| Market spread | 9 / 13 | 0.519 | 0.178 | 7.8 |
| Market moneyline | 9 / 13 | 0.533 | 0.184 | |
| Coin flip | 6.5 / 13 | 0.693 | 0.250 | |

Every method picked the same nine winners; the market was sharper on the size of its favorites.
Home teams went 12-1 and won by a touchdown more than anyone projected (margin bias +7.0 for the
blend, +6.2 for the market). Both Very High picks won by 17 or more (Bills, Chiefs). The misses:

- **Giants 23, Jaguars 18 (74% JAX).** The model liked Jacksonville by more than the market
  (9.9 against 6) and the top-rated team lost on the road.
- **Commanders 22, Bengals 20 (71% CIN).** Washington won at home with McLaurin, Tunsil, Payne
  and Kinlaw all on IR; the capped injury hit pushed the model further toward Cincinnati.
- **Eagles 19, Steelers 16 (63% PIT).** Joe Milton won his second start. The only winning value
  side of the week (Eagles +180).
- **Jets 27, Chargers 24 (58% LAC).** A lean decided by a field goal.

The biggest model-versus-market gaps went the market's way: Texans 26-3 over the Colts (model 6.7,
market 12.5), Cowboys 51-30 over the Titans (5.6 against 8.5), Bears and Lions covered the
market number as well. Where the model shaded an underdog, the favorite won comfortably.

Value bets at the Tuesday table: 1 of 7 (Eagles +180 won; Colts, Titans, Saints, Buccaneers,
Cardinals and Raiders lost), -4.2 flat units and -$54 on the quarter-Kelly bankroll. Season to
date: flat $10 is -$117.57 on $930 staked (33-59 with one push); quarter-Kelly from $1,000
stands at $1,010.73.

| Price bucket (season) | Bets | Won | Modelled win rate | Flat $10 result |
|---|---|---|---|---|
| Favorites | 26 | 16 | 66% | -$2 |
| +100 to +149 | 16 | 4 | 48% | -$61 |
| +150 to +299 | 31 | 9 | 38% | -$41 |
| +300 and longer | 20 | 4 | 23% | -$14 |

Underdog value sides have won 17 of 67 (25 percent) against a modelled 36 percent, and none of
the eleven sides at +300 or longer since Week 6 has won. When the model disagrees with the market
in favor of an underdog, the market has been right.

## Eleven weeks pooled (162 games)

| Method | Winners | Log loss |
|---|---|---|
| Blend | 107 / 162 | 0.616 |
| Pure model | 103 / 162 | 0.619 |
| Market spread | 109 / 162 | 0.619 |
| Market moneyline | 108 / 162 | 0.615 |

- **Market weight.** Flat from 0.3 to 0.6 (0.6154 to 0.6158), best at 0.4 to 0.5. Stays at 0.50.
- **Variance.** Flat from 11 to 12.7 (0.6134 to 0.6140), worse above 13.5. Stays at 12.7.
- **Home field.** Home teams have won 51 percent with a mean margin of +0.5 against a mean market
  spread of +1.7. One 12-1 week does not change that; the base stays at 0.5.
- **Calibration.** Coin flip 12/23, Lean 18/31, Moderate 40/60 (67% at 64%), High 27/37 (73% at
  75%), Very High 10/11 (91% at 85%).

## Model changes for Week 12

No parameter changes: every grid is flat at the current settings.

One process fix carried over from the Thursday refresh: the preseason ratings and 2025 quarterback
table are read from the files saved before the season, and weekly quarterback overrides are set
on that scale.

Frozen: Weeks 1 to 11 outputs are the record.
