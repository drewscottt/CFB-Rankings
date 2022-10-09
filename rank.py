from typing import List, Dict, Set, Tuple
import read_teams_results
from cfb_module import Team, Game
import sys

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
        difference = rank1_dict[team.get_name()] - rank2_dict[team.get_name()]
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
    print("Dropped from Top 25:")
    for team_name in rank1_top25:
        if team_name not in rank2_top25:
            print(f"\t{team_name}")
    print("New to Top 25:")
    for team_name in rank2_top25:
        if team_name not in rank1_top25:
            print(f"\t{team_name}")
    for i in range(25):
        team_name = rank2[i].get_name()
        if team_name not in rank1_top25:
            print(f"{i+1}. {team_name} NEW")
        else:
            print(f"{i+1}. {team_name} {(rank1_top25[team_name] - i):+d}")
        
def filter_ranking(ranking: List[Team], conference: str) -> List[Tuple[Team, int]]:
    '''
        Filters the given ranking by selecting only teams which match the input criteria
        Returns a list of tuples: (team, overall_ranking)
    '''

    filtered_ranking: List[Tuple[Team, int]] = []
    for i, team in enumerate(ranking):
        if team.get_conference() == conference:
            filtered_ranking.append((team, i))
    return filtered_ranking

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

def main(teams_directory):
    Game.away_disadvantage = 2
    Game.winner_bonus = 5
    Game.non_fbs_loss_multiplier = 3
    Team.ignore_all_non_fbs = False
    Team.ignore_wins_vs_non_fbs = True

    # fbs_seen: Set[Team] = read_teams_results.read_all_results(teams_directory)

    # rank1 = sorted(list(fbs_seen), key=lambda Team: Team.get_avg_game_metric(0,0,win_factor=10,loss_factor=10,opp_strength_weight=.5,recency_bias=0,exclude_team_result_from_opp=True), reverse=True)
    # for i, team in enumerate(rank1):
    #     print(f"{i+1}. {team.get_name()} ({team.get_avg_game_metric(0,0,win_factor=10,loss_factor=10,opp_strength_weight=.5,recency_bias=0,exclude_team_result_from_opp=True)})")

    # for i, team in enumerate(filter_ranking(rank1, "American")):
    #     print(f"{i+1}. ({team[1]+1}) {team[0].get_name()} ({team[0].get_avg_game_metric(0,0,win_factor=10,loss_factor=10,opp_strength_weight=.5,recency_bias=0,exclude_team_result_from_opp=True)})")

    # rank2 = sorted(list(fbs_seen), key=lambda Team: Team.get_avg_game_metric(0,0,win_factor=10,loss_factor=10,opp_strength_weight=.5,exclude_team_result_from_opp=True), reverse=True)
    # for i, team in enumerate(rank2):
    #     print(f"{i+1}. {team.get_name()} ({team.get_avg_game_metric(0,0,win_factor=10,loss_factor=10,opp_strength_weight=.5,exclude_team_result_from_opp=True)})")

    compare_rankings(read_ranking("rankings/2022-week6.txt"), read_ranking("rankings/2022-week7.txt"))

if __name__ == "__main__":
    main(sys.argv[1])
