'''
'''

import sys
from typing import Dict, List

from cfb_module import Game, Team
from lib import ESPNParserV1 as parser  

def predict_schedule(
    ranking_filename: str,
    espn_schedule_url: str 
):
    '''
        Prints the predictions of each game to be played based on the ranking and the supplied espn schedule
    '''
        
    # read the ranking
    ranking: Dict[str, int] = {}
    with open(ranking_filename, "r") as f:
        for i, line in enumerate(f):
            team_name: str = " ".join(line.split(" ")[1:-1])
            ranking[team_name] = i + 1

    # read the games from the schedule
    games: List[Game] = parser.get_games_to_play(False, espn_schedule_url)
    for game in games:
        home_team: Team = game.get_home_team()
        away_team: Team = game.get_away_team()

        if home_team.get_name() not in ranking or away_team.get_name() not in ranking:
            continue

        home_rank: int = ranking[home_team.get_name()]
        away_rank: int = ranking[away_team.get_name()]

        if home_rank < away_rank:
            print(f"{away_team.get_name()} @ {home_team.get_name()}: Predicted winner: {home_team.get_name()}")
        else:
            print(f"{away_team.get_name()} @ {home_team.get_name()}: Predicted winner: {away_team.get_name()}")

def main():
    ranking_filename: str = sys.argv[1]
    espn_schedule_url: str = "https://www.espn.com/college-football/schedule/" if len(sys.argv) == 2 else sys.argv[2]
    
    predict_schedule(ranking_filename, espn_schedule_url)

if __name__ == "__main__":
    main()