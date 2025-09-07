'''`
    File: rank.py
    Description:
    Usage: python3 rank.py <team pages directory>
'''

from typing import List, Dict, Tuple
import sys
import os

import espn_team_pages
from cfb_module import Team, Game

def compare_rankings(rank1: List[Team], rank2: List[Team], n_biggest_diff: int = 5):
    '''
        Prints out summary data comparing the two rankings:
        1) The teams with the biggest changes in each direction (n_biggest_diff each)
        2) Changes to the top 25
    '''

    # map team name to its rank for both rankings
    rank1_dict: Dict[str, int] = {}
    for i, team in enumerate(rank1):
        rank1_dict[team.get_name()] = i
    rank2_dict: Dict[str, int] = {}
    for i, team in enumerate(rank2):
        rank2_dict[team.get_name()] = i

    # get the difference in rankings for each team
    rank_differentials: List[List[str]] = [[] for _ in range((len(rank1)*2) - 1)]
    for team in rank1:
        try:
            difference = rank1_dict[team.get_name()] - rank2_dict[team.get_name()]
        except KeyError:
            continue

        rank_differentials[difference + len(rank1) - 1].append(team.get_name())

    # compute which teams dropped the most
    biggest_droppers: List[Tuple[str, int]] = []
    for i, teams in enumerate(rank_differentials):
        if len(teams) == 0:
            continue
        for team_name in teams:
            biggest_droppers.append((team_name, i - len(rank1) + 1))
        if len(biggest_droppers) >= n_biggest_diff:
            break
    print("Biggest Droppers:")
    for tup in biggest_droppers:
        print(f"\t{tup[0]}: {tup[1]} ({rank1_dict[tup[0]]+1} -> {rank2_dict[tup[0]]+1})")

    # compute which teams improved the most
    biggest_improvers: List[Tuple[str, int]] = []
    for i, teams in reversed(list(enumerate(rank_differentials))):
        if len(teams) == 0:
            continue
        for team_name in teams:
            biggest_improvers.append((team_name, i - len(rank1) + 1))
        if len(biggest_improvers) >= n_biggest_diff:
            break
    print("Biggest Improvers:")
    for tup in biggest_improvers:
        print(f"\t{tup[0]}: {tup[1]} ({rank1_dict[tup[0]]+1} -> {rank2_dict[tup[0]]+1})")

    # compute which teams exited/entered the top 25
    rank1_top25: Dict[str, int] = {}
    rank2_top25: Dict[str, int] = {}
    for i in range(25):
        rank1_top25[rank1[i].get_name()] = i
        rank2_top25[rank2[i].get_name()] = i
    for i in range(25):
        team_name = rank2[i].get_name()
        if team_name not in rank1_top25:
            print(f"{i+1}. {team_name} (NEW)")
        else:
            print(f"{i+1}. {team_name} ({(rank1_top25[team_name] - i):+d})")
    dropped = "Dropped from last Top 25:"
    prefix = ""
    for team_name in rank1_top25:
        if team_name not in rank2_top25:
            dropped += f"{prefix} {team_name} ({rank1_top25[team_name] + 1})"
            prefix = ","
    print(dropped)
        
def filter_ranking(ranking: List[Team], conference: str = '', division: str = '') -> List[Tuple[Team, int]]:
    '''
        Filters the given ranking by selecting only teams which match the input criteria
        Returns a list of tuples: (team, overall_ranking)
    '''

    filtered_ranking: List[Tuple[Team, int]] = []
    for i, team in enumerate(ranking):
        if conference == '' or team.get_conference() == conference:
            filtered_ranking.append((team, i))

    filtered_ranking2: List[Tuple[Team, int]] = []
    for team_tuple in filtered_ranking:
        if division == '' or (division == "FBS" and team_tuple[0].is_fbs) or (division == 'FCS' and not team_tuple[0].is_fbs and team_tuple[0].d1):
            filtered_ranking2.append(team_tuple)

    return filtered_ranking2

def rank_conferences(ranking: List[Team]):
    conferences: Dict[str, List[Tuple(Team, int)]] = {}
    for i, team in enumerate(ranking):
        if team.get_conference() in conferences:
            conferences[team.get_conference()].append((team, i+1))
        else:
            conferences[team.get_conference()] = [(team, i+1)]
    
    average_ranking: Dict[str, float] = {}
    average_top3_ranking: Dict[str, float] = {}
    average_bot3_ranking: Dict[str, float] = {}
    average_mid3_ranking: Dict[str, float] = {}
    total_ranking: Dict[str, float] = {}
    for conf, teams in conferences.items():
        average_rank = 0
        for team in teams:
            average_rank += team[1]
        average_rank /= len(teams)

        top3_average_rank = (teams[0][1] + teams[1][1] + teams[2][1]) / 3
        bot3_average_rank = (teams[-1][1] + teams[-2][1] + teams[-3][1]) / 3
        mid3_average_rank = (teams[len(teams)//2][1] + teams[(len(teams)//2)+1][1] + teams[(len(teams)//2)+1][1]) / 3

        average_ranking[conf] = average_rank
        average_top3_ranking[conf] = top3_average_rank
        average_bot3_ranking[conf] = bot3_average_rank
        average_mid3_ranking[conf] = mid3_average_rank
        total_ranking[conf] = (average_rank + top3_average_rank + bot3_average_rank + mid3_average_rank) / 4

    average_ranking = list(sorted(average_ranking.items(), key=lambda item: item[1]))
    average_top3_ranking = list(sorted(average_top3_ranking.items(), key=lambda item: item[1]))
    average_bot3_ranking = list(sorted(average_bot3_ranking.items(), key=lambda item: item[1]))
    average_mid3_ranking = list(sorted(average_mid3_ranking.items(), key=lambda item: item[1]))
    total_ranking = list(sorted(total_ranking.items(), key=lambda item: item[1]))

    print("Average Ranking:")
    for i, conf in enumerate(average_ranking):
        print(f"\t{i+1}. {conf[0]} ({conf[1]})")
    print("\nAverage Middle 3 Ranking:")
    for i, conf in enumerate(average_mid3_ranking):
        print(f"\t{i+1}. {conf[0]} ({conf[1]})")
    print("\nAverage Top 3 Ranking:")
    for i, conf in enumerate(average_top3_ranking):
        print(f"\t{i+1}. {conf[0]} ({conf[1]})")
    print("\nAverage Bottom 3 Ranking:")
    for i, conf in enumerate(average_bot3_ranking):
        print(f"\t{i+1}. {conf[0]} ({conf[1]})")
    print("\nTotal Ranking:")
    for i, conf in enumerate(total_ranking):
        print(f"\t{i+1}. {conf[0]} ({conf[1]})")

def read_ranking(filename: str) -> List[Team]:
    '''
        Reads the ranking stored in the file and returns it
    '''

    ranking: List[Team] = []
    with open(filename, "r") as f:
        for line in f:
            team_name: str = " ".join(line.split(" ")[1:-1])
            team: Team = Team(team_name)
            ranking.append(team)
    return ranking

def main():
    team_pages_directory: str = sys.argv[1]
    previous_season_team_pages_directory: str = os.path.join("team_pages/2024/2024-week15-results")

    Game.away_disadvantage = 4

    Game.adjusted_margin_cap = 28

    Game.fcs_game_scalar = 0.15
    Game.g5_game_scalar = 0.6

    Game.loss_adjustment = 10
    Game.win_adjustment = 10

    Game.previous_season_scalar = 0

    Team.ignore_all_non_d1 = True

    teams: List[Team] = espn_team_pages.create_teams(team_pages_directory, previous_season_team_pages_directory)

    rank1 = sorted(teams, key=lambda Team: Team.get_avg_game_metric(ignore_worst_n=0,ignore_best_n=0,opp_strength_weight=0.5,recency_bias=0,exclude_team_from_opponent=True), reverse=True)
    
    for i, team in enumerate(rank1):
        print(f"{i+1}. {team.get_name()} ({team.get_avg_game_metric(ignore_worst_n=0,ignore_best_n=0,opp_strength_weight=0.5,recency_bias=0,exclude_team_from_opponent=True)})")

    # for i, team in enumerate(filter_ranking(rank1, conference="SEC")):
    #     print(f"{i+1}. ({team[1]+1}) {team[0].get_name()} ({team[0].get_avg_game_metric(0,0,opp_strength_weight=.5,recency_bias=0.03,exclude_team_result_from_opp=True)})")

    # rank_conferences(rank1)

    # rank2 = sorted(teams, key=lambda Team: Team.get_avg_game_metric(0,0,opp_strength_weight=.5,exclude_team_result_from_opp=True), reverse=True)
    # for i, team in enumerate(rank2):
    #     print(f"{i+1}. {team.get_name()} ({team.get_avg_game_metric(0,0,opp_strength_weight=.5,exclude_team_result_from_opp=True)})")

    compare_rankings(read_ranking("rankings/2024/2024-week15.txt"), rank1)

if __name__ == "__main__":
    main()
