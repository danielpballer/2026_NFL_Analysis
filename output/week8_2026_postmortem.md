# Week 8 2026 post-mortem and model changes

## Scorecard

| Method | Winners | Log loss | Brier | Margin MAE |
|---|---|---|---|---|
| Model + market blend (published, Thursday build) | 10 / 14 | 0.570 | 0.193 | 11.2 |
| Pure model | 10 / 14 | 0.574 | 0.196 | 11.5 |
| Market spread | 10 / 14 | 0.568 | 0.191 | 10.8 |
| Market moneyline | 10 / 14 | 0.553 | 0.184 | |
| Coin flip | 7 / 14 | 0.693 | 0.250 | |

The best raw week of the season (all four High picks won, three by 15 or more) but the market
moneyline scored better still: the favorites that won, won big, and the market had priced them
a little heavier than the blend. After home teams went 4-10 in Week 7 they went 10-4 and beat
every method's number by five to six points. The misses:

- **Bears 34, Seahawks 17 (65% SEA).** Charles Cross out at left tackle; Williams and the Bears
  ran away with it on Monday night. The largest miss of the week.
- **Lions 19, Vikings 15 (54% MIN).** The week's biggest market disagreement went the market's
  way, barely; Minnesota's offense scored 15 again.
- **Cardinals 33, Cowboys 30 (66% DAL).** A 7-point favorite lost at home to Minshew's Cardinals.
- **Broncos 28, Chiefs 24 (53% KC).** A coin flip that went to the home team.

Value bets at the Tuesday table: 2 of 8 (Cardinals +230 and Raiders -110 won; Vikings +140,
Titans +455, Eagles +170, Dolphins +310, Seahawks -170 and Browns +150 lost) for -2.8 flat units and -$51 on the quarter-Kelly
bankroll, its third straight losing week. Season to date: flat $10 is -$25 on $720 staked;
quarter-Kelly from $1,000 stands at $1,155.

## Eight weeks pooled (120 games)

| Method | Winners | Log loss |
|---|---|---|
| Blend | 75 / 120 | 0.652 |
| Pure model | 71 / 120 | 0.656 |
| Market spread | 77 / 120 | 0.653 |
| Market moneyline | 76 / 120 | 0.654 |

- **Home field.** After last week's cut to 0.5, the grid is flat between 0.0 and 0.5 and worse
  above 1.0; the blend's home bias is down to 1.4 points (market 1.3). No further change.
- **Variance.** Flat from 13.5 to 16 at the current 14.0. No change.
- **Injuries.** Fourth straight review favouring a lower weight (0.4 scores 0.6498, 0.6 scores
  0.6504, full weight 0.6521). **INJURY_SCALE goes from 0.6 to 0.5.**
- **Quarterbacks.** Removing the adjustment costs 0.0034; kept.
- **Market weight.** Flat from 0.3 to 0.7; the schedule sits at its 0.35 floor. No change.
- **Calibration.** Coin flip 11/21, Lean 13/22, Moderate 30/47 (64% at 63%), High 16/24 (67%
  at 75%), Very High 5/6. Overall 75 of 120 (62.5%) at an average published probability of 63%.

## Model changes for Week 9

1. Injury scale 0.6 to 0.5.

Frozen: Weeks 1 to 8 outputs are the record.
