# Week 10 2026 post-mortem and model review

## Scorecard

| Method | Winners | Log loss | Brier | Margin MAE |
|---|---|---|---|---|
| Model + market blend (published, Thursday build) | 9 / 14 | 0.563 | 0.192 | 9.9 |
| Pure model | 9 / 14 | 0.535 | 0.182 | 9.5 |
| Market spread | 9 / 14 | 0.598 | 0.207 | 10.6 |
| Market moneyline | 9 / 14 | 0.572 | 0.196 | |
| Coin flip | 7 / 14 | 0.693 | 0.250 | |

The first week on the corrected settings (sd 12.7, market share 50 percent, heavier quarterback
weight with the in-season baseline) beat the market on log loss, and the pure model had its best
week relative to the market since Week 4. All three Very High picks won by 17 or more (Bills,
Jaguars, Rams), as did the one High pick (Seahawks). The misses:

- **Vikings 30, Packers 10 (58% GB).** Kirk Cousins started four days after the trade and Minnesota
  won by 20 at Lambeau. Tuesday's Vikings +170 value flag paid.
- **Browns 27, Texans 24 (68% HOU).** Watson returned and Cleveland won at home.
- **Chargers 23, Ravens 20 (64% BAL).** The Chargers' first win, against Brissett's debut.
- **Commanders 24, Giants 21 and Panthers 20, Saints 17.** Two leans and coin flips decided by
  a field goal.

Value bets at the Tuesday table (first week at the 5 percent cut): 2 of 2, Vikings +170 and
49ers -205, for +2.2 flat units and +$37 on the quarter-Kelly bankroll. Season to date: flat
$10 is -$75.57 on $860 staked (32-53 with one push); quarter-Kelly from $1,000 stands at $1,064.

## Ten weeks pooled (149 games)

| Method | Winners | Log loss |
|---|---|---|
| Blend | 98 / 149 | 0.622 |
| Pure model | 94 / 149 | 0.622 |
| Market spread | 100 / 149 | 0.627 |
| Market moneyline | 99 / 149 | 0.622 |

Blend, pure model and market moneyline are level to the third decimal.

- **Market weight.** At a fixed sd of 12.7 the grid is flat from 0.2 to 0.5 (0.6176 to 0.6183)
  and worse above 0.65. Over Weeks 6 to 10 it is flat from 0.35 to 0.65. The 0.50 share stays.
- **Variance.** Flat from 11 to 12.7 (0.6187 to 0.6193), worse above 13.5. Stays at 12.7.
- **Home field.** Home teams are 72 of 149 (48 percent) and both the model and the market have
  them 1.8 points too high. The base is already down to 0.5; no change.
- **Calibration.** Coin flip 12/23, Lean 17/29, Moderate 38/57 (67% at 64%), High 23/31 (74%
  at 75%), Very High 8/9 (89% at 83%).

## Model changes for Week 11

None. One week is not evidence, every grid is flat at the current settings, and the Week 9
review committed to not tuning on single weeks.

Frozen: Weeks 1 to 10 outputs are the record.
