# Week 2 2026 post-mortem and model changes

## Scorecard

| Method | Winners | Log loss | Brier | Margin MAE |
|---|---|---|---|---|
| Model + market blend (published) | 10 / 16 | 0.649 | 0.229 | 11.6 |
| Pure model | 9 / 16 | 0.650 | 0.230 | 11.6 |
| Market spread | 11 / 16 | 0.659 | 0.232 | 11.7 |
| Market moneyline | 11 / 16 | 0.653 | 0.228 | |
| Coin flip | 8 / 16 | 0.693 | 0.250 | |

The market picked one more winner, but the blend's probabilities were better (lower log loss),
mostly because it was less confident than the market in three favorites that lost: Houston
(Collins, Clowney and two linebackers out), Baltimore (Madubuike out, Flowers doubtful, three
linemen questionable), and the Chargers (line injuries). The pure model, using only two games
of in-season data on top of the prior, matched the market on margin error (11.6 vs 11.7).

## Two weeks pooled (32 games)

| Method | Winners | Log loss | Brier |
|---|---|---|---|
| Blend | 22 / 32 | 0.638 | 0.223 |
| Pure model | 20 / 32 | 0.645 | 0.228 |
| Market spread | 23 / 32 | 0.643 | 0.223 |
| Market moneyline | 23 / 32 | 0.646 | 0.224 |

Sensitivity checks on the 32 games: the market weight is flat between 0.50 and 0.60 (log loss
0.6374 to 0.6375) and gets worse toward either end, so 0.55 stays. The margin standard
deviation is flat between 12 and 13.5. Adjustments (QB, injuries, coaching) pointed the same
way as the result-versus-market error in 21 of 32 games, and 9 of the 12 where they exceeded
two points; the injury differential correlates 0.22 with the market's error. That is modest but
consistent support for keeping the injury model as is.

Calibration by stated probability: 50 to 55 percent picks won 3 of 5, 55 to 60 won 5 of 6,
60 to 70 won 10 of 14, 70 to 80 won 3 of 6, 80 plus won 1 of 1. Home teams have won 17 of 32
and underperformed the market by about three points per game; that is within noise for two
weeks and home field is unchanged.

## Where the Week 2 picks were off

- **CIN 20, HOU 6** (pick HOU 56 percent). The injury model took 5.7 points off Houston and the
  model still leaned Texans on the strength of last year's rating. Directionally right, not
  enough; the rating update will move Houston down further after two poor games.
- **CLE 23, TB 19** (pick TB 72 percent). Cleveland was the top value bet at +350 and won
  outright. Nothing in the inputs anticipated it.
- **MIN 9, CHI 3** (pick CHI 60 percent). Wentz in, Mason and Jennings out, and the Vikings
  still won on the road in a game with almost no offense. The model was much less confident
  than the market (4.5) and Minnesota was a value side.
- **NO 24, BAL 17** (pick BAL 72 percent). The Ravens' Friday report was the worst on the slate
  and the blend had already dropped from 75 to 72 percent; still a loss.
- **LV 26, LAC 14** (pick LAC 64 percent). The Chargers' line injuries were the story again,
  and Las Vegas was the top value side at +250.
- **DEN 20, JAX 13** (pick JAX 53 percent). The one game where the data picked against the
  market, and the market was right.

Value bets: 4 of 11 positive-EV sides won (CLE +350, LV +250, NO +310, MIN +180) for roughly
+5.9 units at one unit each. Two weeks of value picks are now 8 of 20 and about +9 units, which
is encouraging but still small-sample.

## Model changes for Week 3

1. **International games get extra variance.** Ravens-Cowboys is at the Maracanã in Rio, the
   second neutral-site game abroad this season. Neutral sites already drop home field and
   travel; they now also add 1.0 point of margin standard deviation for the unfamiliar
   surface, crowd and travel on both sides.
2. **Rest differential.** The schedule's rest days now count: 0.2 points per extra day of rest
   over the opponent, capped at one point. Buffalo and Detroit come off Thursday games with ten
   days of rest this week; the Rams play on six.
3. **Nothing else.** Market weight, variance and injury weights all survived the sensitivity
   check. The in-season rating update now has two games per team behind the nine-game prior.

Frozen: Week 1 and Week 2 outputs are the record; played games keep their pre-kickoff row.
