'''
'''

from __future__ import annotations
from typing import Dict, List, Tuple, Set
from abc import abstractclassmethod

import cfb_module

class Parser():
    @abstractclassmethod
    def get_games_on_schedule(
        cls: Parser,
        get_results: bool,
        schedule_url: str,
        abbrevs: Dict[str, str] = {}
    ) -> List[cfb_module.Game]:
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
    ) -> Tuple[Set[cfb_module.Team], Dict[str, cfb_module.Team]]:
        pass

    @abstractclassmethod
    def process_games(
        cls: Parser,
        team_links_filename: str,
        team_pages_dir: str,
        teams_seen: Dict[str, cfb_module.Team],
        trunc_to_full: Dict[str, str]
    ):
        pass

    @abstractclassmethod
    def process_game(
        cls: Parser,
        result_span,
        team: cfb_module.Team,
        trunc_to_full: Dict[str, str],
        teams_seen: Dict[str, cfb_module.Team]
    ) -> Tuple[cfb_module.Game, cfb_module.Team]:
        pass