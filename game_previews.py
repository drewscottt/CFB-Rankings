'''
'''

import sys
import os
import requests
from typing import List, Dict

from lib import ESPNParserV1 as parser
from cfb_module import Game

def save_preview_page(preview_url: str):
    '''
        Saves the game page at this url into preview_game_pages
    '''

    headers = {
        'User-Agent': 'Chrome/58.0.3029.110'
    }
    
    preview_filename = os.path.join("preview_game_pages", preview_url.split("=")[1] + ".html")
    if not os.path.isfile(preview_filename):
        preview = requests.get(preview_url, headers=headers).text
        with open(preview_filename, "w") as f:
            f.write(str(preview))

def main():
    espn_schedule_url: str = "https://www.espn.com/college-football/schedule/" if len(sys.argv) == 1 else sys.argv[1]

    # read espn abbreviations, which are used for the game spreads
    abbrevs: Dict[str, str] = {}
    with open("espn_team_abbrevs.csv", "r") as f:
        for line in f:
            name, abbrev = line.strip().split(",")
            abbrevs[abbrev] = name

    games: List[Game] = parser.get_games_on_schedule(espn_schedule_url)

    for game in games:
        if game.get_url() == "":
            continue

        save_preview_page(game.get_url())


if __name__ == "__main__":
    main()