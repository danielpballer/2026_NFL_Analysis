# Week 3 2026 post-mortem and model changes

## Scorecard

| Method | Winners | Log loss | Brier | Margin MAE |
|---|---|---|---|---|
| Model + market blend (published) | 8 / 16 | 0.676 | 0.242 | 8.5 |
| Pure model | 10 / 16 | 0.663 | 0.232 | 9.0 |
| Market spread | 8 / 16 | 0.697 | 0.254 | 8.5 |
| Market moneyline | 8 / 16 | 0.707 | 0.260 | |
| Coin flip | 8 / 16 | 0.693 | 0.250 | |

A week where the favorites lost: Atlanta won 35-14 at Lambeau as a 5.5-point dog, Washington
beat Seattle with Mariota, Chicago beat Philadelphia with a third-string quarterback, Denver
beat the Rams, Cleveland and Pittsburgh won as home dogs. The market was worse than a coin flip
on log loss. The blend was better than the market but, for the first time, worse than the pure
model, which had leaned further from the market on several of the surprises (it had the Bears
as home favorites and the Colts over Houston).

Value bets: 5 of 8 won (Atlanta +235, Chicago +150, Indianapolis +120, Minnesota -122, Miami
push-adjacent loss) for about +4.1 units. Three weeks of value picks are 13 of 28 and roughly
+13 units.

## Three weeks pooled (48 games)

| Method | Winners | Log loss | Brier | Margin MAE |
|---|---|---|---|---|
| Blend | 30 / 48 | 0.651 | 0.230 | 10.7 |
| Pure model | 30 / 48 | 0.651 | 0.229 | 11.1 |
| Market spread | 31 / 48 | 0.661 | 0.234 | 10.6 |
| Market moneyline | 31 / 48 | 0.666 | 0.236 | |

By week, the blend's log loss versus the pure model: Week 1 0.628 vs 0.640, Week 2 0.649 vs
0.650, Week 3 0.676 vs 0.663. The market's information advantage over the model was largest
before any 2026 games had been played and has faded as the ratings absorb real games. The
market-weight grid on the 48 games is now best between 0.30 and 0.40 (log loss 0.6493) and
worse at the current 0.55 (0.6508); after two weeks it had been flat at 0.50 to 0.60.

Calibration: 50 to 55 percent picks 3 of 7, 55 to 60 percent 7 of 11, 60 to 70 percent 12 of
18, 70 to 80 percent 7 of 11, 80 plus 1 of 1. Home teams are 28 of 48 and have slightly
underperformed both the market and the model (about one point per game), within noise.

Adjustments pointed the same way as the market's error in 30 of 48 games and 13 of the 19 where
they exceeded two points. The injury differential correlates 0.23 with the market's error; the
quarterback differential 0.13.

## Model changes for Week 4

1. **The market's share of the blend now declines with the week.** It starts at 0.55 in Week 1
   and falls 0.03 per week to a floor of 0.40, so Week 4 uses 0.46. This is the smallest change
   consistent with the grid; jumping straight to 0.30 on 48 games would be overfitting to one
   bad market week.
2. **Nothing else.** The variance grid is flat between 12.7 and 14.5; the early-season allowance
   has now expired on schedule. Injury and quarterback weights keep their directional support.

Frozen: Weeks 1 to 3 outputs are the record.
