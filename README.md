## Motivation

I wanted a metric which answers the question: on average, how much does a team over/under-perform in games compared to their opponents typical result? For example, if Team A loses to Team B by 10 points, but Team B typically wins by 20 points, Team A over-performed by 10 (-10 + 20) points. So, for this game Team A would earn 10 points. Then across all games, their results would be average.

Additionally, I wanted a metric to acknowledge that winning (or losing) is also an important aspect (not just margin of victory). So, if Team A beats Team B, and Team B wins 90% of their games, Team A should be awared further. So, the game metric becomes: -10 + 20 + (N * .9), where N is left to be determined. 

## Methodology

Each team is ranked based on their average performance from each game (game metric). For each game, the game metric is calculated as: 

* margin of victory (negative if a loss) + 
* (w * opponent's average margin of victory (not including game(s) played against this team)) + 
* (result factor = (x1 * opponent win percent (if win) or -x2 * opponent loss percent (if loss) (not including game(s) played against this team)))

Here, w=.5, x1=10, x2=10, but they are tweakable constants.

Further, the raw score of each game is adjusted by:

* The winning team gets +5 points
* The away team gets +2 points
* If an FBS team loses to an FCS team, the victory margin is multiplied by 3 (after the previous adjustments are made)
* FBS wins vs. FCS teams are completely ignored

Again, each of the mentioned constants are tweakable.

Note: calculating the "result factor" of the game metric is used by counting real-life wins/losses; the point adjustments listed above only affect the first two factors of the game metric.

## Usage

There are two main programs:

* rank.py: Used to compute a ranking, or compare rankings.

    ```python3 rank.py <team_directory>```

    ```python3 rank.py team_pages/2022-week6-results/```

* predict_analyze.py: Used to predict a schedule of games based on a previously generated ranking, or analyze a schedule of results and sportsbook predictions in relation to a ranking.

    ```python3 predict_analyze.py <ranking_filename> <predict_analyze> <optional: espn_schedule_url>```

    ```python3 predict_analyze.py rankings/2022-week6.txt predict```

    ```python3 predict_analyze.py rankings/2022-week6.txt analyze```

## Current Top 25

1. Ohio State (+0)
2. Georgia (+1)
3. Michigan (+2)
4. Tennessee (+0)
5. Clemson (+1)
6. TCU (+4)
7. Alabama (-5)
8. Texas (+3)
9. Ole Miss (-1)
10. UCLA (+2)
11. Syracuse (+4)
12. USC (-3)
13. Utah (+11)
14. UCF (+8)
15. Wake Forest (+1)
16. Oklahoma State (+4)
17. James Madison (-10)
18. Illinois (+1)
19. Penn State (-6)
20. Tulane (NEW)
21. Mississippi State (-7)
22. Purdue (-1)
23. Minnesota (-6)
24. Cincinnati (NEW)
25. Kansas State (NEW)

    Dropped from last Top 25: Kansas (17), NC State (22), Oregon (24)

## Track Record

Overall predictive accuracy: 63.89% (69/108) of games predicted correctly. (Note: only FBS vs. FBS considered)

Overall performance compared to Caesar's Sportsbook: 33.33% (6/18) of games with different predictions were correct. (Note: spread must be available on ESPN game page to be considered)

Profit from $100 ML wagers: -$2,725.57 (out of $4,400)

* 2022, Week 7: Correctly predicted 58.82% (30/51) of games. In games with different favorite than Caesar's Sportsbook (as reported by ESPN), 28.57% (2/7) were chosen correctly. Betting $100 on each predicted winner's ML resulted in $2,725.57 loss out of $4,400 wagered.

* 2022, Week 6: Correctly predicted 68.42% (39/57) of games. In games with different favorite than Caesar's Sportsbook (as reported by ESPN), 36.36% (4/11) were chosen correctly.

## Ranking Methodology Change Log

2022, Week 8 Rankings:

* Remove 3x multiplier for FCS losses, replace with 21 point adjusted scoring margin penalty vs. FCS teams
* Consider all FCS games, not just losses
* Apply recency bias 0.05
* Apply adjusted scoring margin cap at 38

Base:

* Ignore FCS wins
* Apply a 3x multiplier to adjusted score margin in losses vs. FCS teams
* Away team receives 2 points in adjusted score
* Winning team receives 5 points in adjusted score
* Win factor: 10, loss factor: 10 in calculating game metric
* Opponent strength weight in calculating game metric: 0.5