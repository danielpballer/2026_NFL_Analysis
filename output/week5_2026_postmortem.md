# Week 5 2026 post-mortem and model changes

## Scorecard (14 games; the Giants-Commanders tie is excluded from scoring)

| Method | Winners | Log loss | Brier | Margin MAE |
|---|---|---|---|---|
| Model + market blend (published, Friday build) | 8 / 14 | 0.641 | 0.226 | 11.2 |
| Pure model | 7 / 14 | 0.644 | 0.230 | 11.7 |
| Market spread | 9 / 14 | 0.647 | 0.226 | 10.8 |
| Market moneyline | 9 / 14 | 0.643 | 0.224 | |
| Coin flip | 7 / 14 | 0.693 | 0.250 | |

A blowout week: five games decided by 20 or more. The market picked one more winner; the blend
still edged it on log loss (fourth time in five weeks) but only just. The misses:

- **Packers 31, Bears 7 (Lean, 58% CHI).** The worst miss of the season by margin on a pick we
  made against the ratings' recent form. Green Bay's injuries (Cooper, Jacobs, Parsons, Reed,
  two interior linemen) were worth 3.3 points in the model; the Packers did not look hurt.
- **Ravens 30, Falcons 23 (Lean, 56% ATL).** Tyler Huntley won in Atlanta. The quarterback swap
  was priced at three points and the pick flipped on Friday; Baltimore's defense did the rest.
- **Bucs 24, Cowboys 16 (High, 71% DAL).** The pure data said 9.5 was too many and flagged the
  Bucs +370; the blend still had Dallas comfortably.
- **49ers 32, Seahawks 29 (63% SEA).** A coin flip on the field; the rating edge was Seattle's
  home field and San Francisco's injuries, and the 49ers scored 32 without Bosa.
- **Bills 37, Rams 34 (60% LA).** Shootout. Buffalo's four questionable starters all played.
- **Steelers 34, Colts 22 (51% IND).** Pittsburgh ruled out three starters Friday and won by 12;
  the pick had flipped from the Steelers to the Colts on that report.
- **Giants 27, Commanders 27.** Tie; no result.

Winners: Jaguars in London (80%), Bengals (72%), Texans 26-3, Vikings in New Orleans (the
week's biggest market disagreement, won by 10), Broncos, Lions 45-21, Patriots 45-17, Jets.

Value bets at the Tuesday table: 3 of 10 with one push (Bucs +370, Vikings -125, Jaguars -285
won) for -2.2 units. Five weeks of value picks at flat stakes are 19-29 with one push for about +2.4 units, all of it
from five longshot winners (Cardinals +455, Browns +320, Saints +320, Raiders +250, Bucs +370).

## Five weeks pooled (78 games)

| Method | Winners | Log loss |
|---|---|---|
| Blend | 48 / 78 | 0.640 |
| Pure model | 46 / 78 | 0.639 |
| Market spread | 49 / 78 | 0.650 |
| Market moneyline | 49 / 78 | 0.648 |

- **Market weight.** The grid is flat from 0.0 to 0.3 and rises from 0.4. The schedule is at
  0.40 for Week 6; the floor is lowered to 0.35, which the schedule reaches in Week 8.
- **Injuries.** Adjustments of 1.5 points or more now point the same way as the market's error
  in only 21 of 44 games (correlation 0.01). Scaling the injury points by 0.5 to 0.75 improves
  the pooled log loss on every blend weight (pure model 0.6361 at 0.5 against 0.6386 at full
  weight); doubling them is clearly worse. Week by week the evidence is mixed (full weight was
  better in Weeks 1 to 3, half weight better in Weeks 4 and 5), so the change is moderate:
  **injury points are scaled by 0.75** after the cap (effective cap 4.5 points).
- **Quarterbacks.** Removing the quarterback adjustment costs 0.0035 of log loss on the blend
  and 0.011 on the pure model; halving it is also worse. Kept at full weight.
- **Variance.** Flat between 12 and 14.5; 12.7 stays.
- **Calibration.** Coin flip 6/12, Lean 7/15, Moderate 22/32 (69% at 64%), High 9/15 (60% at
  74%), Very High 4/4. The High tier remains the overconfident bucket.
- **Home field.** Home teams are 41 of 78; the blend's home margin is 1.5 points high, the
  market's 1.45. Still inside noise, still watched.

## Model changes for Week 6

1. Injury points scaled by 0.75 (`INJURY_SCALE`).
2. Market-weight floor lowered from 0.40 to 0.35 (no effect until Week 7).
3. Ties are excluded from pick scoring.

Frozen: Weeks 1 to 5 outputs are the record.
