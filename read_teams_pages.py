from bs4 import BeautifulSoup
import requests
import os.path
import sys
from cfb_module import Team, Game
from typing import List, Optional, Dict, Set, Tuple

def get_espn_team_links(espn_url: str, team_links_filename: str):
    # read all of the team links from espn, if they haven't already
    if not os.path.isfile(team_links_filename):
        team_link_prefix: str = "/college-football/team/_/id/"

        # read the FBS teams
        espn_fbs_teams_url: str = f"{espn_url}/college-football/teams"
        fbs_teams_content: str = requests.get(espn_fbs_teams_url).text
        fbs_teams_soup: BeautifulSoup = BeautifulSoup(fbs_teams_content, "html.parser")

        # process the FBS teams
        fbs_team_links: List[Dict[str, str]] = fbs_teams_soup.select(f"a[href*='{team_link_prefix}']")
        prev_link: Optional[Dict[str, str]] = None
        for team_link in fbs_team_links:
            # there are 2 links to the same page in a row, so skip the second
            if prev_link is not None and team_link["href"] == prev_link["href"]:
                continue
            prev_link = team_link

            conference = ""
            for ancestor in team_link.parents:
                if ancestor.has_attr("class") and set(ancestor["class"]) == set(["ContentList", "mt4", "ContentList--NoBorder"]):
                    conference = ancestor.previous_sibling.text.strip()
                    break

            with open(team_links_filename, "a") as f:
                f.write(f"{team_link['href']},FBS,{conference}\n")

        # read the FCS teams
        espn_fcs_teams_url: str = f"{espn_url}/college-football/standings/_/view/fcs-i-aa"
        fcs_teams_content: str = requests.get(espn_fcs_teams_url).text
        fcs_teams_soup: BeautifulSoup = BeautifulSoup(fcs_teams_content, "html.parser")

        # process the FCS teams
        fcs_team_links: List[Dict[str, str]] = fcs_teams_soup.select(f"a[href*='{team_link_prefix}']")
        prev_link: Optional[Dict[str, str]] = None
        for team_link in fcs_team_links:
            # there are 3 links to the same page in a row, so skip the the extras
            if prev_link is not None and team_link["href"] == prev_link["href"]:
                continue
            prev_link = team_link

            conference = ""
            for ancestor in team_link.parents:
                if ancestor.has_attr("class") and set(ancestor["class"]) == set(["flex"]):
                    conference = ancestor.previous_sibling.text.strip()
                    break

            with open(team_links_filename, "a") as f:
                f.write(f"{team_link['href']},FCS,{conference}\n")


def get_teams(espn_url: str, team_links_filename: str, team_pages_dir: str) -> Tuple[Set[Team], Dict[str, Team]]:
    # read each team
    teams_seen: Dict[str, Team] = {}
    div1_teams: Set[Team] = set()
    with open(team_links_filename, "r") as f:
        for team_row in f:
            team_link = team_row.split(",")[0]
            # either read team page from espn.com or from locally saved
            team_filename: str = os.path.join(team_pages_dir, team_link.split('/')[-1].strip() + ".html")
            if not os.path.isfile(team_filename):
                team_content: str = requests.get(f"{espn_url}{team_link}").text
                with open(team_filename, "w") as f:
                    f.write(team_content)
            else:
                with open(team_filename, "r") as f:
                    team_content = f.read()
            
            # process team page to get the team name
            team_soup: BeautifulSoup = BeautifulSoup(team_content, "html.parser")
            team_name: str = team_soup.find("h1", {"class": "ClubhouseHeader__Name"}).find("span", {"class": "db pr3 nowrap fw-bold"}).text
            team_conf: str = team_row.split(",")[2].strip()
            team: Team = Team(team_name, team_conf)
            team.is_d1 = True
            
            if team_row.split(",")[1].strip() == "FBS":
                team.set_fbs(True)

            teams_seen[team_name] = team
            div1_teams.add(team)

    return div1_teams, teams_seen

def process_games(team_links_filename: str, team_pages_dir: str, teams_seen: Dict[str, Team], trunc_to_full: Dict[str, str]):
    # process each game for each team
    with open(team_links_filename, "r") as f:
        for team_row in f:
            team_link = team_row.split(",")[0]
            # read team espn page from local save
            team_filename: str = os.path.join(team_pages_dir, team_link.split('/')[-1].strip() + ".html")
            with open(team_filename, "r") as f:
                team_content = f.read()
            
            # process team page to get the team name
            team_soup: BeautifulSoup = BeautifulSoup(team_content, "html.parser")
            team_name: str = team_soup.find("h1", {"class": "ClubhouseHeader__Name"}).find("span", {"class": "db pr3 nowrap fw-bold"}).text
            team: Team = teams_seen[team_name]

            # process all the game results for the team
            result_spans = team_soup.find_all("span", {"class": "Schedule__Result"})

            game_num: int = 0
            for result_span in result_spans:
                game, opp_team = process_game(result_span, team, trunc_to_full, teams_seen)
                if game is None:
                    continue

                added: bool = team.add_game(game, game_num)
                if added:
                    game_num += 1
                opp_team.add_game(game)

def process_game(result_span, team: Team, trunc_to_full: Dict[str, str], teams_seen: Dict[str, Team]) -> Tuple[Game, Team]:
    game_div = result_span.find_parent("div").find_parent("div")
    
    espn_game_id = game_div.find_parent("a")["href"].split("/")[-1]

    # get the opponent for the game
    game_opp_trunc: str = game_div.find("span", {"class": "Schedule__Team"}).text

    # find the opponent's full name based on its truncated name
    game_opp_full: str = ""
    if game_opp_trunc in trunc_to_full:
        game_opp_full = trunc_to_full[game_opp_trunc]
    else:
        game_opp_full = game_opp_trunc

    # use the opponent's full name to find the Team itself
    opp_team: Optional[Team] = None
    if game_opp_full in teams_seen:
        opp_team = teams_seen[game_opp_full]
    else:
        opp_team = Team(game_opp_full)
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
    if game_result == "PPD" or game_score == "PPD":
        return None, None

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
    game: Game = Game(home_team, away_team, home_score, away_score, espn_game_id)

    return game, opp_team

def main(team_pages_dir: str) -> Set[Team]:
    espn_url: str = "https://www.espn.com"
    team_links_filename: str = "team_links.csv"
    
    teams_trunc_filename: str = "espn_team_truncs.csv"
    trunc_to_full: Dict[str, str] = {}
    with open(teams_trunc_filename, "r") as f:
        for line in f:
            trunc_to_full[line.split(",")[1].strip()] = line.split(",")[0]
    
    get_espn_team_links(espn_url, team_links_filename)
    div1_teams, teams_seen = get_teams(espn_url, team_links_filename, team_pages_dir)
    process_games(team_links_filename, team_pages_dir, teams_seen, trunc_to_full)

    return div1_teams
                
if __name__ == "__main__":
    main(sys.argv[1])
    