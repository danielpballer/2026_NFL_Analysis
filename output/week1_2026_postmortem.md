# Week 1 2026 post-mortem and model changes

## Scorecard

| Method | Winners | Log loss | Brier | Margin MAE | Margin bias (home) |
|---|---|---|---|---|---|
| Model + market blend (published) | 12 / 16 | 0.628 | 0.218 | 12.0 | -2.5 |
| Pure model | 11 / 16 | 0.640 | 0.225 | 12.6 | -3.1 |
| Market spread (opening) | 12 / 16 | 0.628 | 0.215 | 11.6 | -1.9 |
| Market moneyline (opening) | 12 / 16 | 0.638 | 0.219 | | |
| Coin flip | 8 / 16 | 0.693 | 0.250 | | |

The blend matched the market spread on log loss and beat the market moneyline. The pure model
was worse than either, which supports keeping the market as the majority partner in the blend.

Calibration by tier: Coin flip 2 of 3, Lean 5 of 5, Moderate 2 of 4, High 3 of 4. Favorites
averaged a 61.5 percent stated probability and won 75 percent, so if anything the model was
slightly under-confident, but 16 games cannot distinguish that from noise.

## Where the predictions were off

- **SF 27, LA 7** (pick LA 66 percent). The largest miss for both the model and the market. The
  Rams' 2025 rating was the second highest in the league; one game does not overturn that, but
  the in-season update below now moves them down 3.3 points and the 49ers up 3.3.
- **NYJ 23, TEN 10** (pick TEN 62 percent). The model liked Tennessee far more than the market
  (6.7 versus 1.5). The extra confidence came from the 2025 rating gap between two bad teams,
  which is exactly where regressed ratings are least informative. Lesson: when both teams are
  in the bottom quarter, the model's edge over the market is unlikely to be real.
- **ARI 26, LAC 14** (pick LAC 73 percent). The model was much less confident than the market
  (4.6 versus 10.5) because of the Chargers' offensive-line injuries, and the Cardinals were the
  top-value underdog at +455. Right direction, still a loss on the pick.
- **NYG 28, DAL 20** (pick DAL 52 percent). The pure model had the Giants; the market blend
  tipped it to Dallas by a hair. The Giants were the second-best value bet.
- **BAL 41, IND 23** (pick BAL 52 percent). The pure model leaned Indianapolis on last year's
  ratings and Baltimore's new coaching staff. The market was right and by a lot.

Adjustments (QB, injuries, coaching) pointed the right way in 9 of 16 games, which is a coin
flip. The market underrated home teams by 1.9 points on average and the model by 3.1, but the
three-season average home margin is 2.2 points, so home field is not changed.

Value bets: 4 of 9 positive-EV sides won (ARI +455, NYG +124, MIN -118, PHI -218), 5 lost. At
one unit each that was roughly +3.3 units, almost entirely from Arizona, which is the kind of
single-outcome result that should not be read as validation.

## Model changes for Week 2

1. **In-season rating update** (`nflsim.ratings`). Each team's rating is now the
   precision-weighted average of the preseason prior (worth 9 games of evidence) and its
   opponent-adjusted game performances (70 percent net EPA in points, 30 percent capped
   margin). One game moves a rating by at most about 3.4 points; Week 1 performance correlated
   only 0.05 with the priors, which is why the prior keeps most of the weight.
2. **Margin variance re-estimated from data.** The base standard deviation is now 12.7 points,
   the actual spread of results around closing lines over 2023 to 2025, plus an early-season
   allowance of 1.0 point in Week 1 tapering to zero by Week 4. Week 2 uses 13.4.
3. **Official injury report ingestion.** The nflverse injuries file now carries 2026 rows;
   `build_manual` merges its Out, Doubtful and Questionable designations with the research
   entries once the Wednesday to Friday reports post.
4. **Quarterback identity check.** Atlanta started Cooper Rush in Week 1, not Penix as the
   research expected. The schedule file's projected starter is now cross-checked against the
   research for every team.
5. **Predictions are frozen once made.** Rerunning Week 1 today would use closing lines and the
   official report and produce different numbers; the committed Week 1 outputs are the record.

Not changed, with reasons: market weight (blend matched the market, pure model did not), home
field (three-season data supports the current value), injury position weights (no evidence
either way from 16 games).
