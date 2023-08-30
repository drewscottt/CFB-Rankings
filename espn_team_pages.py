'''
    File: get_espn_team_pages.py
    Description: Gets all FBS and FCS team pages from ESPN.
    Usage: python3 get_espn_team_pages.py <team_pages_dir>
'''

import requests
import os.path
import sys
from typing import List, Dict

from cfb_module import Team
from lib import ESPNParserV1 as parser 

espn_url: str = "https://www.espn.com"

def _get_team_data_from_subdivision_page() -> List[Dict[str, str]]:
    team_data: List[Dict[str, str]] = []

    # get the team data from the subdivision pages
    team_data_from_subdivision_pages_filename: str = "team_links.csv"
    if not os.path.isfile(team_data_from_subdivision_pages_filename):
        # we haven't already sent this request, so go to espn.com
        team_data: List[Dict[str, str]] = parser.get_team_data_from_subdivision_pages(espn_url)

        # cache the result
        with open(team_data_from_subdivision_pages_filename, "a") as f:
            for team in team_data:
                f.write(f"{team['url']},{team['subdivision']},{team['conference']}\n")
    else:
        # read in the previously cached result
        with open(team_data_from_subdivision_pages_filename, "r") as f:
            for team_row in f:
                team_fields: List[str] = team_row.split(",")
                team_data.append({
                    "url": team_fields[0],
                    "subdivision": team_fields[1],
                    "conference": team_fields[2],
                })

    return team_data

def _add_espn_team_pages_to_team_data(
    team_data: List[Dict[str, str]],
    team_pages_dir: str
) -> List[Dict[str, str]]:
    # use the team data from the previous step to get individual team pages
    for team_fields in team_data:    
        # get the team page
        team_url: str = team_fields["url"]
        
        team_fields["team_page"] = _get_espn_team_page(f"{espn_url}{team_url}", team_pages_dir)

    return team_data

def create_teams(
    team_pages_dir: str
) -> List[Team]:
    # get the raw team data, along with their pages
    team_data: List[Dict[str, str]] = _get_team_data_from_subdivision_page()
    _add_espn_team_pages_to_team_data(team_data, team_pages_dir)

    # get the truncated team name mappings
    teams_trunc_filename: str = "espn_team_truncs.csv"
    trunc_to_full: Dict[str, str] = {}
    with open(teams_trunc_filename, "r") as f:
        for line in f:
            trunc_to_full[line.split(",")[1].strip()] = line.split(",")[0]

    # create the teams
    teams: List[Team] = parser.create_teams(team_data, trunc_to_full)

    return teams

def get_espn_team_pages(
    team_pages_dir: str
):
    team_data: List[Dict[str, str]] = _get_team_data_from_subdivision_page()

    for team_fields in team_data:
        _ = _get_espn_team_page(f"{espn_url}{team_fields['url']}", team_pages_dir)

def _get_espn_team_page(
    url: str,
    team_pages_dir: str
) -> str:
    team_filename: str = os.path.join(team_pages_dir, url.split('/')[-1].strip() + ".html")
    team_page: str = ""
    if not os.path.isfile(team_filename):
        # we haven't cached it yet, so go get it from espn.com
        headers = {
            'User-Agent': 'Chrome/58.0.3029.110'
        }
        team_page = requests.get(url, headers=headers).text

        # cache it
        with open(team_filename, "w") as f:
            f.write(team_page)
    else:
        # get the cached apge
        with open(team_filename, "r") as f:
            team_page = f.read()

    return team_page

def main():
    team_pages_dir: str = sys.argv[1]

    get_espn_team_pages(team_pages_dir)
                
if __name__ == "__main__":
    main()
    