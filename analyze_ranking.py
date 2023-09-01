'''
'''

import sys
import os
import requests
from typing import Dict, List, Tuple, Optional

from cfb_module import Game, Team
from lib import ESPNParserV1 as parser

def get_preview_page(preview_url: str) -> str:
    # get the preview page from preview_game_pages
    preview_filename = os.path.join("preview_game_pages", preview_url.split("=")[1] + ".html")
    if not os.path.isfile(preview_filename):
        headers = {"User-Agent": "Chrome/58.0.3029.110"}
        preview_page: str = requests.get(preview_url, headers=headers).text

        if parser.get_game_state(preview_page) != "preview":
            return ""

        # cache result if the game is not complete
        with open(preview_filename, "w") as f:
            f.write(str(preview_page))

        return preview_page

    with open(preview_filename, "r") as f:
        return f.read()

def get_result_page(result_url: str) -> str:
    # get the results page either from local cache or espn.com
    result_filename = os.path.join("completed_game_pages", result_url.split("=")[1] + ".html")
    if not os.path.isfile(result_filename):
        headers = {"User-Agent": "Chrome/58.0.3029.110"}
        result_page: str = requests.get(result_url, headers=headers).text

        if parser.get_game_state(result_page) != "complete":
            return ""

        # cache result if the game is complete
        with open(result_filename, "w") as f:
            f.write(str(result_page))

        return result_page
    
    with open(result_filename, "r") as f:
        return f.read()

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
    games: List[Game] = parser.get_games_on_schedule(espn_schedule_url)

    # update each game with result and betting info
    for game in games:
        preview_page = get_preview_page(game.get_url())
        parser.process_game_preview(preview_page, game)

        result_page = get_result_page(game.get_url())
        parser.process_game_result(result_page, game, abbrevs)

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

        if winning_team is None or losing_team is None:
            continue

        if winning_team.get_name() not in ranking or losing_team.get_name() not in ranking:
            continue

        games_predicted += 1

        winner_ml: int = game.get_winner_ml()

        winning_rank: int = ranking[winning_team.get_name()]
        losing_rank: int = ranking[losing_team.get_name()]

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