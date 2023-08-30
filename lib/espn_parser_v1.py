'''
    File: espn_parser_v1.py
    Description: 
'''

from __future__ import annotations
import requests
from typing import List, Dict, Optional, Set, Tuple
import os.path
import re

from bs4 import BeautifulSoup

from cfb_module import Game, Team

import lib

class ESPNParserV1(lib.Parser):
    @classmethod
    def get_games_to_play(
        cls: lib.Parser,
        get_results: bool,
        schedule_url: str,
        abbrevs: Dict[str, str] = {}
    ) -> List[Game]:
        '''
            Extracts all of the games that are on the schedule, getting the results pages if necessary
        '''

        schedule = requests.get(schedule_url).text
        soup = BeautifulSoup(schedule, 'html.parser')

        games_to_play: List[Game] = []
        game_days = soup.find_all("div", {"class": "ScheduleTables mb5 ScheduleTables--ncaaf ScheduleTables--football"})
        for game_day in game_days:
            games = game_day.find_all("tr", {"class": "Table__TR Table__TR--sm Table__even"})
            for game in games:
                teams = game.find_all("span", {"class": "Table__Team"})

                try:
                    away_team_name: str = teams[0].find_all("a")[1].text
                    home_team_name: str = teams[1].find_all("a")[1].text
                except IndexError:
                    # a team doesn't have ESPN team page linked, so we just ignore this game
                    continue

                if not get_results:
                    # we don't need to extract the game's results, so we have all we need
                    games_to_play.append(Game(Team(home_team_name), Team(away_team_name)))
                else:
                    try:
                        result_link = game.find("td", {"class", "teams__col Table__TD"})
                        if result_link.text == "Postponed" or result_link.text == "Canceled":
                            continue

                        result_url = "https://espn.com" + result_link.find("a")["href"]
                        game_data = {}
                        game_data["home_team_name"] = home_team_name
                        game_data["away_team_name"] = away_team_name
                        cls.process_game_preview(result_url, game_data)
                        cls.process_game_result(result_url, game_data, abbrevs)

                        game = Game(Team(home_team_name), Team(away_team_name), game_data["home_score"], game_data["away_score"], result_url.split("/")[-1])
                        if "sportsbook_favorite" in game_data and "spread" in game_data:
                            game.set_odds(game_data["sportsbook_favorite"], game_data["spread"])
                        
                        if "home_ml" in game_data and "away_ml" in game_data:
                            game.set_mls(game_data["home_ml"], game_data["away_ml"])

                        games_to_play.append(game)
                    except AttributeError:
                        # we will get here if the game hasn't been played yet, cheap hack :)
                        # save the preview game page in case we want its data after the game is complete
                        preview_url = "https://espn.com" + game.find("td", {"class", "date__col Table__TD"}).find("a")["href"]
                        cls.save_preview_page(preview_url)

        return games_to_play

    @classmethod
    def process_game_result(cls: lib.Parser, result_url: str, game_data: dict, abbrevs: Dict[str, str]):
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

        game_data["home_score"] = home_score
        game_data["away_score"] = away_score
        game_data["winning_team_name"] = winning_team_name

        # parse the results page, getting the sportsbook prediction
        try:
            odds = result_soup.find("div", {"class": "odds-lines-plus-logo"}).find("ul").find("li").text
            line_info = odds.split(" ")
            if len(line_info) == 2:
                sportsbook_favorite = ""
                spread = 0
            else:
                sportsbook_favorite = abbrevs[line_info[1]]
                spread = float(line_info[2])

            game_data["sportsbook_favorite"] = sportsbook_favorite
            game_data["spread"] = spread
        except AttributeError:
            return

    @classmethod
    def process_game_preview(cls: lib.Parser, preview_url: str, game_data: dict):
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
                home_moneyline = pick_center.find("td", text=re.compile(".*Money Line.*")).next_sibling.next_sibling.text.strip()
                away_moneyline = pick_center.find("td", text=re.compile(".*Money Line.*")).previous_sibling.previous_sibling.text.strip()
                if home_moneyline != "--" and away_moneyline != "--":
                    game_data["home_ml"] = int(home_moneyline.replace(",", ""))
                    game_data["away_ml"] = int(away_moneyline.replace(",", ""))
            except AttributeError:
                # no pick center for this game preview
                return

    @classmethod 
    def save_preview_page(cls: lib.Parser, preview_url: str):
        '''
            Saves the game page at this url into preview_game_pages
        '''

        preview_filename = os.path.join("preview_game_pages", preview_url.split("=")[1] + ".html")
        if not os.path.isfile(preview_filename):
            preview = requests.get(preview_url).text
            with open(preview_filename, "w") as f:
                f.write(str(preview))

    @classmethod 
    def get_team_data_from_subdivision_pages(
        cls: lib.Parser,
        espn_url: str,
    ) -> List[Dict[str, str]]:
        team_data: List[Dict[str, str]] = []

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

                team_data.append({
                    "url": team_link["href"],
                    "subdivision": "FBS",
                    "conference": conference
                })

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

                team_data.append({
                    "url": team_link["href"],
                    "subdivision": "FCS",
                    "conference": conference
                })

        return team_data

    @classmethod
    def create_teams(
        cls: lib.Parser,
        team_data: List[Dict[str, str]],
        trunc_to_full: Dict[str, str],
    ) -> List[Team]:
        # first, create all of the team objects based on simple data
        teams: List[Team] = []
        teams_lookup: Dict[str, Team] = {}
        for team_fields in team_data:
            # process team page
            team_soup: BeautifulSoup = BeautifulSoup(team_fields["team_page"], "html.parser")

            team_name: str = team_soup.find("h1", {"class": "ClubhouseHeader__Name"}).find("span", {"class": "db pr3 nowrap fw-bold"}).text
            team_conf: str = team_fields["conference"].strip()

            team: Team = Team(team_name, team_conf)
            team.is_d1 = True
            if team_fields["subdivision"].strip() == "FBS":
                team.set_fbs(True)

            teams.append(team)
            teams_lookup[team.get_name()] = team

        # second, add all of the games to each team
        # we waited to do this because we need opponent team objects first
        for team_fields in team_data:
            # process team page to get the team name
            team_soup: BeautifulSoup = BeautifulSoup(team_fields["team_page"], "html.parser")

            team_name: str = team_soup.find("h1", {"class": "ClubhouseHeader__Name"}).find("span", {"class": "db pr3 nowrap fw-bold"}).text

            team: Team = teams_lookup[team_name]

            # process all the game results for the team
            result_spans = team_soup.find_all("span", {"class": "Schedule__Result"})

            game_num: int = 0
            for result_span in result_spans:
                game, opp_team = cls.process_game(result_span, team, trunc_to_full, teams_lookup)
                if game is None:
                    continue

                added: bool = team.add_game(game, game_num)
                if added:
                    game_num += 1
                opp_team.add_game(game)

        return teams

    @classmethod
    def process_game(
        cls: lib.Parser,
        result_span,
        team: Team,
        trunc_to_full: Dict[str, str],
        teams_seen: Dict[str, Team]
    ) -> Tuple[Game, Team]:
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
