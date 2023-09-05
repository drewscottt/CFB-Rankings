'''
    File: espn_parser_v1.py
    Description: 
'''

from __future__ import annotations
import requests
from typing import List, Dict, Optional, Tuple
import re

from bs4 import BeautifulSoup

import cfb_module
import lib

class ESPNParserV1(lib.Parser):
    @classmethod
    def get_games_on_schedule(cls: lib.Parser, schedule_url: str) -> List[cfb_module.Game]:
        '''
            Extracts all of the games that are on the schedule, getting the results pages if necessary
        '''

        headers = {"User-Agent": "Chrome/58.0.3029.110"}
        schedule = requests.get(schedule_url, headers=headers).text
        soup = BeautifulSoup(schedule, 'html.parser')

        all_games: List[cfb_module.Game] = []
        game_days = soup.find_all("div", {"class": "ScheduleTables mb5 ScheduleTables--ncaaf ScheduleTables--football"})
        for game_day in game_days:
            game_rows = game_day.find_all("tr", {"class": "Table__TR Table__TR--sm Table__even"})
            for game_row in game_rows:
                teams = game_row.find_all("span", {"class": "Table__Team"})

                try:
                    away_team_name: str = teams[0].find_all("a")[1].text
                    home_team_name: str = teams[1].find_all("a")[1].text
                except IndexError:
                    # a team doesn't have ESPN team page linked, so we just ignore this game
                    continue

                home_team: cfb_module.Team = cfb_module.Team(home_team_name)
                away_team: cfb_module.Team = cfb_module.Team(away_team_name)

                url: str
                try:
                    result_link = game_row.find("td", {"class", "teams__col Table__TD"})
                    if result_link.text == "Postponed" or result_link.text == "Canceled":
                        continue

                    url = lib.ESPN_URL_PREFIX + result_link.find("a")["href"]
                except AttributeError:
                    # we will get here if the game hasn't been played yet
                    url = lib.ESPN_URL_PREFIX + game_row.find("td", {"class", "date__col Table__TD"}).find("a")["href"]

                game: cfb_module.Game = cfb_module.Game(home_team, away_team, espn_game_id=url.split("/")[-1], url=url)
                
                all_games.append(game)

        return all_games

    @classmethod
    def process_game_result(cls: lib.Parser, result_page: str, game: cfb_module.Game, abbrevs: Dict[str, str]):
        '''
            Reads the final score and spread for the completed game
        '''

        if result_page == "":
            return

        # parse the results page, getting the scores
        result_soup: BeautifulSoup = BeautifulSoup(result_page, "html.parser")

        final_scores = result_soup.find_all("td", {"class", "final-score"})
        if len(final_scores) >= 2:
            game.set_away_score(int(final_scores[0].text))
            game.set_home_score(int(final_scores[1].text))
        elif len(final_scores) == 0:
            score_rows = result_soup.find_all("tr", {"class", "Table__TR Table__TR--sm Table__even"})
            scores = []
            for score_row in score_rows[:2]:
                scores.append(int(score_row.find_all("td")[-1].text))
            game.set_away_score(scores[0])
            game.set_home_score(scores[1])

        # TODO: fix this nastiness
        try:
            odds: str = result_soup.find("div", {"class": "odds-lines-plus-logo"}).find("ul").find("li").text

            line_info: str = odds.split(" ")
            if len(line_info) > 2:
                game.set_odds(abbrevs[line_info[1]], float(line_info[2]))
        except AttributeError:
            try:
                odds: str = result_soup.find("div", {"class", "n8 GameInfo__BettingItem flex-expand line"}).text
                line_info: str = odds.split(" ")
                game.set_odds(abbrevs[line_info[1]], float(line_info[2]))
            except:
                return

    @classmethod
    def process_game_preview(cls: lib.Parser, preview_page: str, game: cfb_module.Game):
        '''
            Reads the moneyline for the game
        '''

        soup: BeautifulSoup = BeautifulSoup(preview_page, "html.parser")

        try:
            pick_center = soup.find("div", {"class": "pick-center-content"})

            re.DOTALL = True
            home_moneyline = pick_center.find("td", text=re.compile(".*Money Line.*")).next_sibling.next_sibling.text.strip()
            away_moneyline = pick_center.find("td", text=re.compile(".*Money Line.*")).previous_sibling.previous_sibling.text.strip()
            if home_moneyline != "--" and away_moneyline != "--":
                game.set_mls(int(home_moneyline.replace(",", "")), int(away_moneyline.replace(",", "")))
        except AttributeError:
            # no pick center for this page
            return

    @classmethod 
    def get_team_data_from_subdivision_pages(cls: lib.Parser) -> List[Dict[str, str]]:
        team_data: List[Dict[str, str]] = []

        team_link_prefix: str = "/college-football/team/_/id/"

        # read the FBS teams
        espn_fbs_teams_url: str = f"{lib.ESPN_URL_PREFIX}/college-football/teams"
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
        espn_fcs_teams_url: str = f"{lib.ESPN_URL_PREFIX}/college-football/standings/_/view/fcs-i-aa"
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
        teams_struct: List[Dict[str, str]],
        trunc_to_full: Dict[str, str],
    ) -> List[cfb_module.Team]:
        # first, create all of the team objects based on simple data
        teams: List[cfb_module.Team] = []
        teams_lookup: Dict[str, cfb_module.Team] = {}
        for team_struct in teams_struct:
            # process team page
            team_soup: BeautifulSoup = BeautifulSoup(team_struct["team_page"], "html.parser")

            team_name: str = team_soup.find("h1", {"class": "ClubhouseHeader__Name"}).find("span", {"class": "db pr3 nowrap fw-bold"}).text
            team_conf: str = team_struct["conference"].strip()

            team: cfb_module.Team = cfb_module.Team(team_name, team_conf)
            team.d1 = True
            if team_struct["subdivision"].strip() == "FBS":
                team.set_fbs(True)

            teams.append(team)
            teams_lookup[team.get_name()] = team

        # second, add all of the games to each team
        # we waited to do this because we need opponent team objects first
        for team_struct in teams_struct:
            # process team page to get the team name
            team_soup: BeautifulSoup = BeautifulSoup(team_struct["team_page"], "html.parser")

            team_name: str = team_soup.find("h1", {"class": "ClubhouseHeader__Name"}).find("span", {"class": "db pr3 nowrap fw-bold"}).text

            team: cfb_module.Team = teams_lookup[team_name]

            # process all the game results for the team
            result_spans = team_soup.find_all("span", {"class": "Schedule__Result"})

            game_num: int = 0
            for result_span in result_spans:
                game, opponent = cls.process_game(result_span, team, trunc_to_full, teams_lookup)
                if game is None:
                    continue

                added: bool = team.add_game(game, game_num, False)
                if added:
                    game_num += 1
                opponent.add_game(game, previous_season=False)

            prev_season_team_soup: BeautifulSoup = BeautifulSoup(team_struct["prev_team_page"], "html.parser")

            # process all the game results for the team
            result_spans = prev_season_team_soup.find_all("span", {"class": "Schedule__Result"})

            game_num: int = 0
            for result_span in result_spans:
                game, opponent = cls.process_game(result_span, team, trunc_to_full, teams_lookup)
                if game is None:
                    continue

                game.set_previous_season(True)

                added: bool = team.add_game(game, game_num, True)
                if added:
                    game_num += 1
                opponent.add_game(game, previous_season=True)

        return teams

    @classmethod
    def process_game(
        cls: lib.Parser,
        result_span,
        team: cfb_module.Team,
        trunc_to_full: Dict[str, str],
        teams_seen: Dict[str, cfb_module.Team]
    ) -> Tuple[cfb_module.Game, cfb_module.Team]:
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
        opp_team: Optional[cfb_module.Team] = None
        if game_opp_full in teams_seen:
            opp_team = teams_seen[game_opp_full]
        else:
            opp_team = cfb_module.Team(game_opp_full)
            teams_seen[game_opp_full] = opp_team

        # determine home/away
        game_at_vs: str = game_div.find("span", {"class": "Schedule_atVs"}).text
        home_team: Optional[cfb_module.Team] = None
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
        game: cfb_module.Game = cfb_module.Game(home_team, away_team, home_score, away_score, espn_game_id)

        return game, opp_team
    
    @classmethod
    def get_game_state(cls: lib.Parser, game_page: str) -> str:
        '''
        '''

        soup: BeautifulSoup = BeautifulSoup(game_page, "html.parser")

        winner_icon = soup.select("svg.Gamestrip__WinnerIcon.icon__svg")
        if len(winner_icon) != 0:
            return "complete"
        
        team_score = soup.select("div.Gamestrip__Score.relative.tc.w-100.fw-heavy.h2.clr-gray-01")
        if len(team_score) != 0:
            return "active"
        
        return "preview"
