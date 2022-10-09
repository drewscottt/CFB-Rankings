import requests
from bs4 import BeautifulSoup
from typing import List, Tuple, Dict
import sys
import os.path
from cfb_module import Game, Team

def get_games_to_play(get_results: bool, abbrevs: Dict[str, str] = {}) -> List[Game]:
    schedule_url = "https://www.espn.com/college-football/schedule"
    schedule = requests.get(schedule_url).content
    soup = BeautifulSoup(schedule, 'html.parser')

    games_to_play: List[Game] = []
    game_days = soup.find_all("div", {"class": "ScheduleTables mb5 ScheduleTables--ncaaf ScheduleTables--football"})
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

            if get_results:
                try:
                    result_url = "https://espn.com" + game.find("td", {"class", "teams__col Table__TD"}).find("a")["href"]
                except AttributeError:
                    continue

                result_filename = "results/" + result_url.split("=")[1]
                if not os.path.isfile(result_filename):
                    result = requests.get(result_url).content
                    with open(result_filename, "w") as f:
                        f.write(str(result))
                else:
                    with open(result_filename, "r") as f:
                        result = f.read()

                # get the results of the game
                result_soup = BeautifulSoup(result, "html.parser")
                final_scores = result_soup.find_all("td", {"class", "final-score"})
                away_score = int(final_scores[0].text)
                home_score = int(final_scores[1].text)
                winning_team_name = home_team_name
                if away_score > home_score:
                    winning_team_name = away_team_name

                # get the odds favorite of the game
                odds = result_soup.find("div", {"class": "odds-lines-plus-logo"}).find("ul").find("li").text
                odds_favorite = abbrevs[odds.split(" ")[1]]
                if odds_favorite[:7] == "San Jos":
                    # TODO: awful hack
                    odds_favorite = "San Jose State"
                odds_line = float(odds.split(" ")[2])

                game = Game(Team(home_team_name), Team(away_team_name), False, home_score, away_score)
                game.set_odds(odds_favorite, odds_line)
                games_to_play.append(game)
            else:
                games_to_play.append(Game(Team(home_team_name), Team(away_team_name), False, 0, 0))

    return games_to_play

def main(ranking_filename: str, compare_predict: str = "predict"):
    # read the ranking
    ranking: Dict[str, int] = {}
    with open(ranking_filename, "r") as f:
        for i, line in enumerate(f):
            team_name: str = " ".join(line.split(" ")[1:-1])
            ranking[team_name] = i + 1

    # read espn abbreviations
    abbrevs: Dict[str, str] = {}
    with open("espn_abbrevs.csv", "r") as f:
        for line in f:
            name, abbrev = line.strip().split(",")
            abbrevs[abbrev] = name
    
    # read the games to play and either compare the results to rankings or predict results
    games: List[Game] = []
    if compare_predict == "compare":
        games = get_games_to_play(True, abbrevs)

        num_correct: int = 0
        upsets: List[Tuple[int, str]] = []
        projs_differ: List[str] = []
        num_better_than_odds: int = 0
        for game in games:
            winning_team: Team = game.get_winner()
            winning_rank: int = ranking[winning_team.get_name()]
            losing_team: Team = game.get_loser()
            losing_rank: int = ranking[losing_team.get_name()]

            projected_winner: Team = winning_team
            if losing_rank < winning_rank:
                projected_winner = losing_team

            if winning_team == projected_winner:
                num_correct += 1
            else:
                rank_diff: int = abs(winning_rank - losing_rank)
                upsets.append((rank_diff, f"{winning_team.get_name()} ({winning_rank}) def. {losing_team.get_name()} ({losing_rank}): {rank_diff} difference"))

            if projected_winner != game.get_odds_favorite_team():
                projs_differ.append(f"{winning_team.get_name()} def. {losing_team.get_name()}: sportsbook selected {game.get_odds_favorite_team().get_name()} ({game.get_odds_line()}), ranking selected {projected_winner.get_name()}")
                if projected_winner == winning_team:
                    num_better_than_odds += 1

        print(f"Correctly predicted {num_correct/len(games):.2%} ({num_correct}/{len(games)})")
        upsets = sorted(upsets, key=lambda x: x[0], reverse=True)
        print("Biggest upsets:")
        for i in range(len(upsets)):
            print("\t", upsets[i][1])
        print(f"Differ from sportsbook favorites: {num_better_than_odds/len(projs_differ):.2%} ({num_better_than_odds}/{len(projs_differ)})")
        for diff in projs_differ:
            print("\t", diff)
    else:
        games = get_games_to_play(False)
        for game in games:
            home_team: Team = game.get_home_team()
            home_rank: int = ranking[home_team.get_name()]
            away_team: Team = game.get_away_team()
            away_rank: int = ranking[away_team.get_name()]

            if home_rank < away_rank:
                print(f"{away_team.get_name()} @ {home_team.get_name()}: Predicted winner: {home_team.get_name()}")
            else:
                print(f"{away_team.get_name()} @ {home_team.get_name()}: Predicted winner: {away_team.get_name()}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
