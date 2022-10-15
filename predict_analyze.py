'''
File: predict_analyze.py
Description: Used to make predictions based on a ranking on a given schedule of games,
    and analyze the predictions, comparing results to a sportsbook.    
Usage:
    python3 predict_analyze.py <ranking file> predict
    python3 predict_analyze.py <ranking file> analyze
'''

import requests
from bs4 import BeautifulSoup
from typing import List, Tuple, Dict
import sys
import os.path
import json
import re
from cfb_module import Game, Team

def process_game_result(result_url: str, game_data: dict, abbrevs: Dict[str, str]):
    '''
        Reads the final score and spread for the completed game
    '''

    # get the results page, checking if it's already saved locally in game_pages
    result_filename = os.path.join("completed_game_pages", result_url.split("=")[1] + ".html")
    if not os.path.isfile(result_filename):
        result = requests.get(result_url).text
        with open(result_filename, "w") as f:
            f.write(str(result))
    else:
        with open(result_filename, "r") as f:
            result = f.read()

    # parse the results page, getting the scores
    result_soup = BeautifulSoup(result, "html.parser")
    final_scores = result_soup.find_all("td", {"class", "final-score"})
    away_score = int(final_scores[0].text)
    home_score = int(final_scores[1].text)
    winning_team_name = game_data["home_team_name"]
    if away_score > home_score:
        winning_team_name = game_data["away_team_name"]

    # parse the results page, getting the sportsbook prediction
    odds = result_soup.find("div", {"class": "odds-lines-plus-logo"}).find("ul").find("li").text
    odds_favorite = abbrevs[odds.split(" ")[1]]
    if odds_favorite[:7] == "San Jos":
        # TODO: awful hack
        odds_favorite = "San Jose State"
    spread = float(odds.split(" ")[2])

    # fill in game_data with this data
    game_data["odds_favorite"] = odds_favorite
    game_data["spread"] = spread
    game_data["home_score"] = home_score
    game_data["away_score"] = away_score
    game_data["winning_team_name"] = winning_team_name

def process_game_preview(preview_url: str, game_data: dict):
    '''
        Reads the moneyline for the game
    '''

    # get the results page, checking if it's already saved locally in game_pages
    preview_filename = os.path.join("preview_game_pages", preview_url.split("=")[1] + ".html")
    if os.path.isfile(preview_filename):
        with open(preview_filename, "r") as f:
            preview = f.read()

        soup: BeautifulSoup = BeautifulSoup(preview, "html.parser")
        try:
            pick_center = soup.find("div", {"class": "pick-center-content"})
            re.DOTALL = True
            home_moneyline = pick_center.find("td", text=re.compile(".*Money Line.*")).next_sibling.next_sibling.text.replace("\\", "").replace("n", "").replace("t", "")
            away_moneyline = pick_center.find("td", text=re.compile(".*Money Line.*")).previous_sibling.previous_sibling.text.replace("\\", "").replace("n", "").replace("t", "")
            if home_moneyline != "--" and away_moneyline != "--":
                game_data["home_ml"] = int(home_moneyline.replace(",", ""))
                game_data["away_ml"] = int(away_moneyline.replace(",", ""))
        except AttributeError:
            # no pick center for this game preview
            return

def save_preview_page(preview_url: str):
    '''
        Saves the game page at this url into preview_game_pages
    '''

    preview_filename = os.path.join("preview_game_pages", preview_url.split("=")[1] + ".html")
    if not os.path.isfile(preview_filename):
        preview = requests.get(preview_url).text
        with open(preview_filename, "w") as f:
            f.write(str(preview))

def get_games_to_play(get_results: bool, schedule_url: str, abbrevs: Dict[str, str] = {}) -> List[Game]:
    '''
        Extracts all of the games that are on the schedule, getting the results pages if necessary
    '''

    schedule = requests.get(schedule_url).text
    soup = BeautifulSoup(schedule, 'html.parser')

    games_to_play: List[Game] = []
    mls = {}
    game_days = soup.find_all("div", {"class": "ScheduleTables mb5 ScheduleTables--ncaaf ScheduleTables--football"})
    have_read_mls = False
    for game_day in game_days:
        games = game_day.find_all("tr", {"class": "Table__TR Table__TR--sm Table__even"})
        for game in games:
            teams = game.find_all("span", {"class": "Table__Team"})
            away_team_name: str = teams[0].find_all("a")[1].text
            if away_team_name[:7] == "San Jos":
                # TODO: awful hack
                away_team_name = "San Jose State"
            home_team_name: str = teams[1].find_all("a")[1].text
            if home_team_name[:7] == "San Jos":
                # TODO: awful hack
                home_team_name = "San Jose State"

            if not get_results:
                # we don't need to extract the game's results, so we have all we need
                games_to_play.append(Game(Team(home_team_name), Team(away_team_name), False, 0, 0))
            else:
                try:
                    result_url = "https://espn.com" + game.find("td", {"class", "teams__col Table__TD"}).find("a")["href"]
                    
                    game_data = {}
                    game_data["home_team_name"] = home_team_name
                    game_data["away_team_name"] = away_team_name
                    process_game_preview(result_url, game_data)
                    process_game_result(result_url, game_data, abbrevs)

                    game = Game(Team(home_team_name), Team(away_team_name), False, game_data["home_score"], game_data["away_score"])
                    game.set_odds(game_data["odds_favorite"], game_data["spread"])
                    if "home_ml" in game_data:
                        print(home_team_name, game_data["home_ml"], away_team_name, game_data["away_ml"])
                        game.set_mls(game_data["home_ml"], game_data["away_ml"])

                    games_to_play.append(game)
                except AttributeError:
                    # we will get here if the game hasn't been played yet, cheap hack :)
                    # save the preview game page in case we want its data after the game is complete
                    preview_url = "https://espn.com" + game.find("td", {"class", "date__col Table__TD"}).find("a")["href"]
                    save_preview_page(preview_url)

    return games_to_play

def predict_games(ranking: Dict[str, str], espn_schedule_url: str):
    '''
        Prints the predictions of each game to be played based on the ranking and the supplied espn schedule
    '''

    games: List[Game] = get_games_to_play(False, espn_schedule_url)
    for game in games:
        home_team: Team = game.get_home_team()
        home_rank: int = ranking[home_team.get_name()]
        away_team: Team = game.get_away_team()
        away_rank: int = ranking[away_team.get_name()]

        if home_rank < away_rank:
            print(f"{away_team.get_name()} @ {home_team.get_name()}: Predicted winner: {home_team.get_name()}")
        else:
            print(f"{away_team.get_name()} @ {home_team.get_name()}: Predicted winner: {away_team.get_name()}")

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
    games: List[Game] = get_games_to_play(True, espn_schedule_url, abbrevs)

    # go through each game, and summarize data about the prediction
    num_correct: int = 0
    upsets: List[Tuple[int, str]] = []
    projs_differ: List[str] = []
    num_beat_ml: int = 0
    total_revenue: float = 0
    games_with_ml: int = 0
    for game in games:
        winning_team: Team = game.get_winner()
        winner_ml: int = game.get_winner_ml()
        winning_rank: int = ranking[winning_team.get_name()]
        losing_team: Team = game.get_loser()
        losing_rank: int = ranking[losing_team.get_name()]

        rankings_favorite: Team = winning_team
        if losing_rank < winning_rank:
            rankings_favorite = losing_team

        if winning_team == rankings_favorite:
            num_correct += 1
            if winner_ml != 0:
                games_with_ml += 1
                if winner_ml < 0:
                    total_revenue += 100 + 100*(100/abs(winner_ml))
                else:
                    total_revenue += winner_ml + 100
        else:
            rank_diff: int = abs(winning_rank - losing_rank)
            upsets.append((rank_diff, f"{winning_team.get_name()} ({winning_rank}) def. {losing_team.get_name()} ({losing_rank}): {rank_diff} difference"))
            if winner_ml != 0:
                print(winning_team.get_name(), losing_team.get_name())
                games_with_ml += 1
                net_profit -= 100

        sportsbook_favorite: Optional[Team] = game.get_sportsbook_favorite()
        if sportsbook_favorite is not None and rankings_favorite != sportsbook_favorite:
            projs_differ.append(f"{winning_team.get_name()} def. {losing_team.get_name()}: sportsbook selected {sportsbook_favorite.get_name()} ({game.get_spread()}), ranking selected {rankings_favorite.get_name()}")
            if rankings_favorite == winning_team:
                num_beat_ml += 1

    print(f"Correctly predicted {num_correct/len(games):.2%} ({num_correct}/{len(games)})")
    upsets = sorted(upsets, key=lambda x: x[0], reverse=True)
    amount_wagered = 100*games_with_ml
    
    print("Biggest upsets:")
    for i in range(len(upsets)):
        print("\t", upsets[i][1])
    
    print(f"If you bet $100 on each game (${amount_wagered:,} total) with an ML available ({games_with_ml}) on the ML of the ranking's projected winner, you ended up with ${total_revenue:,.2f}, or ${total_revenue - amount_wagered:,.2f} profit")
    
    print(f"In games with different projection than sportsbook, {num_beat_ml/len(projs_differ) if len(projs_differ) > 0 else 0:.2%} ({num_beat_ml}/{len(projs_differ)}) games were selected correctly.")
    for diff in projs_differ:
        print("\t", diff)

def main(
    ranking_filename: str,
    compare_predict: str,
    espn_schedule_url: str = "https://www.espn.com/college-football/schedule/"):

    # read the ranking
    ranking: Dict[str, int] = {}
    with open(ranking_filename, "r") as f:
        for i, line in enumerate(f):
            team_name: str = " ".join(line.split(" ")[1:-1])
            ranking[team_name] = i + 1
    
    # read the games to play and either compare the results to rankings or predict results
    if compare_predict == "compare":
        analyze_predictions(ranking, espn_schedule_url)
    else:
        predict_games(espn_schedule_url)

if __name__ == "__main__":
    if len(sys.argv) >= 4:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        main(sys.argv[1], sys.argv[2])
