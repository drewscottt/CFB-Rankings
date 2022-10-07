from bs4 import BeautifulSoup
import requests
import os.path
import sys
from cfb_module import Team, Game
from typing import List, Optional, Dict, Set, Tuple

def get_espn_team_links(espn_url: str, team_links_filename: str):
    # read all of the team links from espn, if they haven't already
    if not os.path.isfile(team_links_filename):
        espn_teams_url: str = f"{espn_url}/college-football/teams"
        teams_content: str = requests.get(espn_teams_url).content
        teams_soup: BeautifulSoup = BeautifulSoup(teams_content, "html.parser")

        team_link_prefix: str = "/college-football/team/_/id/"
        team_links: List[Dict[str, str]] = teams_soup.select(f"a[href*='{team_link_prefix}']")
        prev_link: Optional[Dict[str, str]] = None
        for team_link in team_links:
            if prev_link is not None and team_link["href"] == prev_link["href"]:
                continue
            prev_link = team_link

            with open(team_links_filename, "a") as f:
                f.write(f"{team_link['href']}\n")

def get_teams(espn_url: str, team_links_filename: str, team_pages_dir: str, trunc_to_full: Dict[str, str]) -> Tuple[Set[Team], Dict[str, Team]]:
    # read each team
    teams_seen: Dict[str, Team] = {}
    fbs_seen: Set[Team] = set()
    with open(team_links_filename, "r") as f:
        for team_link in f:
            # either read team page from espn.com or from locally saved
            team_filename: str = f"{team_pages_dir}{team_link.split('/')[-1].strip()}"
            if not os.path.isfile(team_filename):
                team_content: str = requests.get(f"{espn_url}{team_link}").content
                with open(team_filename, "w") as f:
                    f.write(str(team_content))
            else:
                with open(team_filename, "r") as f:
                    team_content = f.read()
            
            # process team page to get the team name
            team_soup: BeautifulSoup = BeautifulSoup(team_content, "html.parser")
            team_name: str = team_soup.find("h1", {"class": "ClubhouseHeader__Name"}).find("span", {"class": "db pr3 nowrap fw-bold"}).text
            team_conf: str = " ".join(team_soup.find("section", {"class": "Card TeamStandings"}).find("h3", {"class": "Card__Header__Title"}).text.split(" ")[1:-1])
            team: Optional[Team] = None
            if team_name in trunc_to_full:
                team = Team(team_name, trunc_to_full[team_name], team_conf)
            else:
                team = Team(team_name, team_name, team_conf)
            
            team.set_fbs(True)
            teams_seen[team_name] = team
            fbs_seen.add(team)

    return fbs_seen, teams_seen

def process_games(team_links_filename: str, team_pages_dir: str, fbs_seen: Set[Team], teams_seen: Dict[str, Team], trunc_to_full: Dict[str, str]):
    # process each game for each team
    with open(team_links_filename, "r") as f:
        for team_link in f:
            # read team espn page from local save
            team_filename: str = f"{team_pages_dir}{team_link.split('/')[-1].strip()}"
            with open(team_filename, "r") as f:
                team_content = f.read()
            
            # process team page to get the team name
            team_soup: BeautifulSoup = BeautifulSoup(team_content, "html.parser")
            team_name: str = team_soup.find("h1", {"class": "ClubhouseHeader__Name"}).find("span", {"class": "db pr3 nowrap fw-bold"}).text
            team: Optional[Team] = None
            if team_name in trunc_to_full:
                team = teams_seen[trunc_to_full[team_name]]
            else:
                team = teams_seen[team_name]

            # process all the game results for the team
            result_spans = team_soup.find_all("span", {"class": "Schedule__Result"})

            game_num: int = 0
            for result_span in result_spans:
                game, opp_team = process_game(result_span, team, trunc_to_full, teams_seen)

                added: bool = team.add_game(game, game_num)
                if added:
                    game_num += 1
                opp_team.add_game(game)

def process_game(result_span, team: Team, trunc_to_full: Dict[str, str], teams_seen: Dict[str, Team]) -> Tuple[Game, Team]:
    game_div = result_span.find_parent("div").find_parent("div")

    # get the opponent for the game
    game_opp_trunc: str = game_div.find("span", {"class": "Schedule__Team"}).text
    game_opp_full: str = ""
    if game_opp_trunc in trunc_to_full:
        game_opp_full = trunc_to_full[game_opp_trunc]
    else:
        game_opp_full = game_opp_trunc
    opp_team: Optional[Team] = None
    if game_opp_full in teams_seen:
        opp_team = teams_seen[game_opp_full]
    else:
        opp_team = Team(game_opp_full, game_opp_trunc, "FCS")
        teams_seen[game_opp_full] = opp_team

    # determine home/away
    game_at_vs: str = game_div.find("span", {"class": "Schedule_atVs"}).text
    home_team: Optional[Team] = None
    if game_at_vs == "@":
        home_team = opp_team
        away_team = team
    else:
        home_team = team
        away_team = opp_team

    # determine game result in terms of home/away
    game_result: str = game_div.find("span", {"class": "Schedule__Result"}).text
    game_score: str = game_div.find("span", {"class": "Schedule__Score"}).text
    winner_score: int = int(game_score.split("-")[0])
    loser_score: int = int(game_score.split("-")[1])
    home_score: int = 0
    away_score: int = 0
    if home_team == team:
        if game_result == "W":
            home_score = winner_score
            away_score = loser_score
        else:
            home_score = loser_score
            away_score = winner_score
    else:
        if game_result == "L":
            home_score = winner_score
            away_score = loser_score
        else:
            home_score = loser_score
            away_score = winner_score

    # create the game
    game: Game = Game(home_team, away_team, False, home_score, away_score)

    return game, opp_team

def process_data(team_pages_dir: str = "teams/") -> Set[Team]:
    espn_url: str = "https://www.espn.com"
    team_links_filename: str = "teams_links.csv"
    
    teams_trunc_filename: str = "teams_trunc.csv"
    trunc_to_full: Dict[str, str] = {}
    with open(teams_trunc_filename, "r") as f:
        for line in f:
            trunc_to_full[line.split(",")[1].strip()] = line.split(",")[0]
    
    get_espn_team_links(espn_url, team_links_filename)
    fbs_seen, teams_seen = get_teams(espn_url, team_links_filename, team_pages_dir, trunc_to_full)
    process_games(team_links_filename, team_pages_dir, fbs_seen, teams_seen, trunc_to_full)

    return fbs_seen
                
if __name__ == "__main__":
    process_data()