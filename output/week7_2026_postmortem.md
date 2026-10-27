# Week 7 2026 post-mortem and model changes

## Scorecard

| Method | Winners | Log loss | Brier | Margin MAE |
|---|---|---|---|---|
| Model + market blend (published) | 9 / 14 | 0.710 | 0.254 | 11.0 |
| Pure model | 9 / 14 | 0.722 | 0.259 | 11.3 |
| Market spread | 9 / 14 | 0.693 | 0.247 | 10.5 |
| Market moneyline | 9 / 14 | 0.701 | 0.250 | |
| Coin flip | 7 / 14 | 0.693 | 0.250 | |

Nine winners but a poor log loss for the second straight week, and a second straight week behind
the market. Home teams went 4-10 and were outscored by 6.3 points a game more than every method
expected (the market included). The misses:

- **Bengals 35, Ravens 13 (52% BAL).** The coin flip the pure data had already flipped to
  Cincinnati; Huntley started a third game and Baltimore scored 13 again.
- **Bucs 43, Panthers 13 (63% CAR).** Mayfield returned (we had priced him at 30% to start) and
  Tampa Bay scored 43 on the road. The largest margin error of the season.
- **Giants 27, Texans 21 (80% HOU).** McCarthy's first start beat a ten-point favorite.
- **Dolphins 28, Jets 25 (62% NYJ).** Miami's first win.
- **Falcons 29, 49ers 20 (67% SF).** San Francisco's first loss, on six days' rest; Mike Evans and
  Bosa were questionable.

Winners: Seahawks 20-3 over the Chiefs (the biggest market disagreement of the week), Cowboys
38-21 in Philadelphia, Broncos, Rams, Vikings, Lions, Steelers in Paris, Bears, Browns.

Value bets at the Tuesday table: 3 of 7 (Dolphins +195, Bengals +124 and Seahawks -148 won;
Eagles +180, Raiders +185, Patriots +130 and 49ers -175 lost): -0.1 flat units and -$35 on the quarter-Kelly bankroll, its second straight losing
week. Season to date: flat $10 is +$2.48 on $640 staked; quarter-Kelly from $1,000 stands at
$1,206.

## Seven weeks pooled (106 games)

| Method | Winners | Log loss |
|---|---|---|
| Blend | 65 / 106 | 0.663 |
| Pure model | 61 / 106 | 0.667 |
| Market spread | 67 / 106 | 0.666 |
| Market moneyline | 66 / 106 | 0.668 |

- **Home field.** Home teams are 52-54 (49%) and have been outscored on average; the blend's
  home margin is 2.35 points too high and the market's 2.16. Removing 1.0 to 1.5 points of home
  field improves the pooled log loss on both the blend (0.6618 to 0.6590/0.6579) and the pure
  model (0.6651 to 0.6613/0.6607). **HOME_FIELD goes from 1.5 to 0.5**; the venue bumps (Seattle,
  Kansas City and the others) are unchanged.
- **Variance.** The sd grid still rises to 16 (0.6585 at 16, 0.6591 at 14.5, 0.6602 at 13.5).
  **MARGIN_SD goes from 13.5 to 14.0.**
- **Injuries.** Flat between 0.4 and 0.6; stays at 0.6.
- **Market weight.** Flat from 0.3 to 0.6; the schedule has reached its 0.35 floor. No change.
- **Calibration.** Coin flip 10/18, Lean 11/20, Moderate 27/42 (64% at 64%), High 12/20 (60% at
  75%), Very High 5/6. The High tier is still the overconfident bucket; the sd increase addresses
  it.

## Model changes for Week 8

1. Home field 1.5 to 0.5.
2. Margin sd 13.5 to 14.0.

Frozen: Weeks 1 to 7 outputs are the record.
