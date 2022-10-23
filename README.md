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
2. Georgia (+0)
3. Michigan (+0)
4. Tennessee (+0)
5. Alabama (+2)
6. Clemson (-1)
7. TCU (-1)
8. USC (+4)
9. Penn State (+10)
10. Wake Forest (+5)
11. Oklahoma State (+5)
12. Texas (-4)
13. Utah (+0)
14. Syracuse (-3)
15. Illinois (+3)
16. Tulane (+4)
17. Ole Miss (-8)
18. UCLA (-8)
19. Cincinnati (+5)
20. LSU (NEW)
21. NC State (NEW)
22. Oregon (NEW)
23. UCF (-9)
24. North Carolina (NEW)
25. Kansas State (+0)

    Dropped from last Top 25: James Madison (16), Mississippi State (20), Purdue (21), Minnesota (22)

## Track Record

| Season, Week | Games Registered | Games Correct | Percent Correct | Games Differ Sportsbook | Games Differ Sportsbook Correct | Percent Differ Sportsbook Correct | Amount on ML | Profit From ML |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2022, Week 8 | 52 | 32 | 61.54% | 14 | 6 | 42.86% | $5,200 | $139.75 |
| 2022, Week 7 | 51 | 30 | 58.82% | 7 | 2 | 28.57% | $4,400 | -$925.57 |
| 2022, Week 6 | 57 | 39 | 68.42% | 11 | 4 | 36.36% | N/A | N/A |
| Totals | 160 | 101 | 63.13% | 32 | 12 | 37.50% | $9,600 | -$785.82 |

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