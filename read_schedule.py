import requests
from bs4 import BeautifulSoup
from typing import List, Tuple, Dict
import sys

def get_games_to_play() -> List[Tuple[str, str, str]]:
    schedule_url = "https://www.espn.com/college-football/schedule"
    schedule = requests.get(schedule_url).content
    soup = BeautifulSoup(schedule, 'html.parser')

    games_to_play: List[Tuple[str, str, str]] = []
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

            try:
                result_url = "https://espn.com" + game.find("td", {"class", "teams__col Table__TD"}).find("a")["href"]
            except AttributeError:
                continue

            result = requests.get(result_url).content
            result_soup = BeautifulSoup(result, "html.parser")
            final_scores = result_soup.find_all("td", {"class", "final-score"})
            away_score = int(final_scores[0].text)
            home_score = int(final_scores[1].text)

            winning_team_name = home_team_name
            if away_score > home_score:
                winning_team_name = away_team_name

            games_to_play.append((away_team_name, home_team_name, winning_team_name))

    return games_to_play

def main():
    games: List[Tuple[str, str]] = get_games_to_play()
    
    ranking: Dict[str, int] = {}
    with open(sys.argv[1], "r") as f:
        for i, line in enumerate(f):
            team_name: str = " ".join(line.split(" ")[1:-1])
            ranking[team_name] = i + 1

    num_correct = 0
    upsets = []
    for game in games:
        away_team = game[0]
        home_team = game[1]
        winning_team = game[2]
        losing_team = away_team
        if winning_team == away_team:
            losing_team = home_team

        winning_rank = ranking[winning_team]
        losing_rank = ranking[losing_team]

        projected_winner = winning_team
        if losing_rank < winning_rank:
            projected_winner = losing_team

        if game[2] == projected_winner:
            num_correct += 1
        else:
            rank_diff = abs(winning_rank - losing_rank)
            upsets.append((rank_diff, f"{winning_team} ({winning_rank}) def. {losing_team} ({losing_rank})"))

    print(f"Correctly predicted {num_correct/len(games):.2%}")
    upsets = sorted(upsets, key=lambda x: x[0], reverse=True)
    print("Biggest upsets:")
    for i in range(min(10, len(upsets))):
        print(upsets[i][1])

if __name__ == "__main__":
    main()