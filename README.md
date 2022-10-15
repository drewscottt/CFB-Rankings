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

    ```python3 predict_analyze.py past_rankings/2022-week6.txt predict```

    ```python3 predict_analyze.py past_rankings/2022-week6.txt analyze```

## Current Top 25

1. Ohio State (+1)
2. Alabama (-1)
3. Georgia (+0)
4. Tennessee (+0)
5. Michigan (+0)
6. Clemson (+3)
7. James Madison (-1)
8. Ole Miss (+0)
9. USC (+4)
10. TCU (-3)
11. Texas (+9)
12. UCLA (+0)
13. Penn State (+1)
14. Mississippi State (-4)
15. Syracuse (+3)
16. Wake Forest (-1)
17. Minnesota (+2)
18. Kansas (-7)
19. Illinois (+3)
20. Oklahoma State (NEW)
21. Purdue (NEW)
22. UCF (NEW)
23. NC State (+1)
24. Utah (-1)
25. Oregon (NEW)

    Dropped from last Top 25: Maryland (15), LSU (16), Kansas State (20), Duke (24)

## Track Record

* 2022, Week 6: Correctly predicted 68.42% (39/57) of games. In games with different favorite than Caesar's Sportsbook (as reported by ESPN), 36.36% (4/11) were chosen correctly.