'''
'''

import sys
from typing import Dict, List, Tuple, Optional

from cfb_module import Game, Team
from lib import ESPNParserV1 as parser

def analyze_predictions(ranking: Dict[str, str], espn_schedule_url: str):
    '''
        Prints comparison of the predictions of the schedule of games between the input ranking and the sportsbook
    '''

    # read espn abbreviations, which are used for the game spreads
    abbrevs: Dict[str, str] = {}
    with open("espn_team_abbrevs.csv", "r") as f:
        for line in f:
            name, abbrev = line.strip().split(",")
            abbrevs[abbrev] = name

    # get the games and their outcomes
    games: List[Game] = parser.get_games_to_play(True, espn_schedule_url, abbrevs)

    # go through each game, and summarize data about the prediction
    num_correct: int = 0
    upsets: List[Tuple[int, str]] = []
    games_diff_sportsbook: List[str] = []
    num_beat_ml: int = 0
    profit: float = 0
    revenue: float = 0
    games_with_ml: int = 0
    games_predicted: int = 0
    for game in games:
        winning_team: Team = game.get_winner()
        losing_team: Team = game.get_loser()

        if winning_team.get_name() not in ranking or losing_team.get_name() not in ranking:
            continue

        winner_ml: int = game.get_winner_ml()
        winning_rank: int = ranking[winning_team.get_name()]
        losing_rank: int = ranking[losing_team.get_name()]

        games_predicted += 1

        rankings_favorite: Team = winning_team
        if losing_rank < winning_rank:
            rankings_favorite = losing_team

        if winning_team == rankings_favorite:
            num_correct += 1
            if winner_ml != 0:
                games_with_ml += 1
                if winner_ml < 0:
                    profit += 100*(100/abs(winner_ml))
                    revenue += 100*(100/abs(winner_ml)) + 100
                else:
                    profit += winner_ml
                    revenue += winner_ml + 100
        else:
            rank_diff: int = abs(winning_rank - losing_rank)
            upsets.append((rank_diff, f"{winning_team.get_name()} ({winning_rank}) def. {losing_team.get_name()} ({losing_rank}): {rank_diff} difference"))
            if winner_ml != 0:
                games_with_ml += 1
                profit -= 100

        sportsbook_favorite: Optional[Team] = game.get_sportsbook_favorite()
        if sportsbook_favorite is not None and rankings_favorite != sportsbook_favorite:
            games_diff_sportsbook.append(f"{winning_team.get_name()} def. {losing_team.get_name()}: sportsbook selected {sportsbook_favorite.get_name()} ({game.get_spread()}), ranking selected {rankings_favorite.get_name()}")
            if rankings_favorite == winning_team:
                num_beat_ml += 1

    if games_predicted > 0:
        print(f"Correctly predicted {num_correct/games_predicted:.2%} ({num_correct}/{games_predicted})")
        upsets = sorted(upsets, key=lambda x: x[0], reverse=True)
    
    if len(upsets) > 0:
        print("Biggest upsets:")
        for i in range(len(upsets)):
            print("\t", upsets[i][1])

    if games_with_ml > 0:
        amount_wagered = 100*games_with_ml
        print(f"If you bet $100 on each game (${amount_wagered:,} total) with an ML available ({games_with_ml}) on the ML of the ranking's projected winner, you ended up with ${revenue:,.2f}, or ${profit:,.2f} profit")
    
    if len(games_diff_sportsbook) > 0:
        print(f"In games with different projection than sportsbook, {num_beat_ml/len(games_diff_sportsbook) if len(games_diff_sportsbook) > 0 else 0:.2%} ({num_beat_ml}/{len(games_diff_sportsbook)}) games were selected correctly.")
        for diff in games_diff_sportsbook:
            print("\t", diff)

def main():
    ranking_filename: str = sys.argv[1]
    espn_schedule_url: str = "https://www.espn.com/college-football/schedule/" if len(sys.argv) == 2 else sys.argv[2]

    # read the ranking
    ranking: Dict[str, int] = {}
    with open(ranking_filename, "r") as f:
        for i, line in enumerate(f):
            team_name: str = " ".join(line.split(" ")[1:-1])
            ranking[team_name] = i + 1
    
    analyze_predictions(ranking, espn_schedule_url)

if __name__ == "__main__":
    main()