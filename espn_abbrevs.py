'''
File: espn_abbrevs.py
Description: Extracts the full team name to abbreviations from ESPN team webpage,
    then writes these pairs to espn_abbrevs.csv
Usage: python3 espn_abbrevs.py
'''

from typing import Dict
from bs4 import BeautifulSoup
import json

def main():
    name_to_abbrev: Dict[str, str] = {}
    with open("team_links.csv", "r") as f:
        for line in f:
            team_name = line.split("/")[-1].strip()
            with open(f"teams/2022-week7/{team_name}", "r") as team_file:
                team_html = team_file.read().strip()
                team_soup = BeautifulSoup(team_html, "html.parser")

                script_text = team_soup.find_all("script")[3].text
                json_text = script_text[len("window['__espnfitt__']=") : -1]
                json_body = json.loads(json_text)

                games = json_body["page"]["content"]["clubhouse"]["columns"]["leftColumn"]["schedule"]["seasons"][0]["feed"]
                for game in games:
                    opp_name = game["opponentLocation"]
                    opp_abbrev = game["opponentAbbreviation"]
                    name_to_abbrev[opp_name] = opp_abbrev

    with open("espn_team_abbrevs.csv", "w") as f:
        for name, abbrev in name_to_abbrev.items():
            f.write(f"{name},{abbrev}\n")

if __name__ == "__main__":
    main()