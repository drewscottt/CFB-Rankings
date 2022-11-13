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

    ```python3 rank.py <team_results_directory>```

    ```python3 rank.py team_pages/2022-week6-results/```

    This has a function to compare a ranking to another ranking (change in Top 25, biggest movers) and another function to filter a ranking based on conference.

    Note: before running for a new week of results, first craate the results directory under ```team_pages```, then it will populate the directory.

* predict_analyze.py: Used to predict a schedule of games based on a previously generated ranking, or analyze a schedule of results and sportsbook predictions in relation to a ranking.

    ```python3 predict_analyze.py <ranking_filename> <predict_analyze> <optional: espn_schedule_url>```

    ```python3 predict_analyze.py rankings/2022-week6.txt predict```

    ```python3 predict_analyze.py rankings/2022-week6.txt analyze https://www.espn.com/college-football/schedule/_/week/9/year/2022/seasontype/2```

    Note: To capture the pre-game view of game pages, just run with the analyze option on the appropriate schedule before the games have started. These will be saved under ```./preview_game_pages```

## Current Top 25

1. Georgia (+1)
2. Ohio State (-1)
3. Michigan (+0)
4. Tennessee (+0)
5. TCU (+1)
6. Alabama (-1)
7. Utah (+1)
8. Clemson (+5)
9. Penn State (+0)
10. USC (+1)
11. UCF (+4)
12. LSU (+0)
13. Oregon (-6)
14. North Carolina (+7)
15. Florida State (+5)
16. South Alabama (+6)
17. Kansas State (+8)
18. UCLA (-8)
19. Notre Dame (-1)
20. UTSA (NEW)
21. Tulane (-7)
22. Oregon State (NEW)
23. Washington (NEW)
24. Texas (-8)
25. Ole Miss (-6)

    Dropped from last Top 25: Louisville (16), Baylor (22), Illinois (23)

## Track Record

| Season, Week | Games Registered | Games Correct | Percent Correct | Games Differ Sportsbook | Games Differ Sportsbook Correct | Percent Differ Sportsbook Correct | Amount on ML | Profit From ML | Percent Profit ML |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2022, Week 11 | 64 | 43 | 67.19% | 11 | 4 | 36.36% | $6,100 | -$641.04 | -10.50% |
| 2022, Week 10 | 60 | 39 | 65.00% | 11 | 4 | 36.36% | $5,800 | -$350.67 | -6.04% |
| 2022, Week 9 | 47 | 36 | 76.60% | 9 | 5 | 55.56% | $4,600 | $513.16 | 11.16% |
| 2022, Week 8 | 52 | 32 | 61.54% | 14 | 6 | 42.86% | $5,200 | $139.75 | 2.69% |
| 2022, Week 7 | 51 | 30 | 58.82% | 7 | 2 | 28.57% | $4,400 | -$925.57 | -21.04% |
| 2022, Week 6 | 57 | 39 | 68.42% | 11 | 4 | 36.36% | N/A | N/A | N/A |
| **Totals** | **331** | **219** | **66.16%** | **63** | **25** | **39.68%** | **$26,100** | **-$1,264.37** | **-4.84%** |

Notes:
* Games Registered includes only FBS vs. FBS matchups for the week.
* Sometimes ESPN doesn't include sportsbook data ~~([example](https://www.espn.com/college-football/game?gameId=401415240))~~ or sportsbook doesn't have a favorite ([example](https://www.espn.com/college-football/game?gameId=401403923)).
* 2022, Week 7 was the first week collecting moneyline data and is incomplete due to data collection after some games had been played.

## Ranking Methodology Change Log

2022, Week 12 Rankings:

* Began ranking FCS teams along with FBS teams
    * Removed 21 point adjusted scoring penalty in FBS vs. FCS games
    * Apply a 0.25 weight to adjusted scoring margins for FCS vs. FCS wins (and 1/0.25 weight for FCS vs. FCS losses)
* Lowered adjusted scoring margin cap from 38 to 28
* Lowered recency bias from 0.05 to 0.03

2022, Week 9 Rankings:

* Major bug fix: neutral site games no longer double counted.

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