'''
'''

from __future__ import annotations
from typing import Dict, List, Tuple, Set
from abc import abstractclassmethod

from cfb_module import Game, Team

class Parser():
    @abstractclassmethod
    def get_games_to_play(
        cls: Parser,
        get_results: bool,
        schedule_url: str,
        abbrevs: Dict[str, str] = {}
    ) -> List[Game]:
        pass
    
    @abstractclassmethod
    def process_game_result(
        cls: Parser,
        result_url: str,
        game_data: dict, 
        abbrevs: Dict[str, str]
    ):
        pass

    @abstractclassmethod
    def process_game_preview(
        cls: Parser, preview_url:
        str, game_data: dict
    ):
        pass

    @abstractclassmethod
    def save_preview_page(
        cls: Parser,
        preview_url: str
    ):
        pass

    @abstractclassmethod 
    def get_team_data_from_subdivision_pages(
        cls: Parser,
        espn_url: str,
        team_links_filename: str
    ):
        pass
    
    @abstractclassmethod
    def create_teams(
        cls: Parser,
        espn_url: str,
        team_links_filename: str,
        team_pages_dir: str
    ) -> Tuple[Set[Team], Dict[str, Team]]:
        pass

    @abstractclassmethod
    def process_games(
        cls: Parser,
        team_links_filename: str,
        team_pages_dir: str,
        teams_seen: Dict[str, Team],
        trunc_to_full: Dict[str, str]
    ):
        pass

    @abstractclassmethod
    def process_game(
        cls: Parser,
        result_span,
        team: Team,
        trunc_to_full: Dict[str, str],
        teams_seen: Dict[str, Team]
    ) -> Tuple[Game, Team]:
        pass