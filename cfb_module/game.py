'''
    Class: Game
    Description: Contains the data associated with a game played
    Public methods:
        get_loser(): returns the loser cfb_module.Team of the game (None if it was a tie)
        get_winner(): returns the winner cfb_module.Team of the game (None if it was a tie)
        get_adj_victory_margin(): returns the number of (adjusted) points the winner won the game by
        get_opponent(team): returns the opponent of team in this game
    Public static variables:
        home_advantage: # points subtracted from home score in adjusted score
        away_disadvantage: # points added to away score in adjusted score
        winner_bonus: # extra points to give to the real-life winner in adjusted score
        non_fbs_loss_multiplier: weight applied to the adjusted victory margin if the winner was non-fbs
'''

from __future__ import annotations
import cfb_module
from typing import Optional

class Game:
    home_advantage: float = 0
    away_disadvantage: float = 0
    winner_bonus: float = 0
    non_fbs_loss_multiplier: float = 1
    adj_margin_max: float = float('inf')
    non_fbs_bonus: float = 0
    fcs_game_factor: float = 1
    g5_game_factor: float = 1

    def __init__(self, home_team: cfb_module.Team, away_team: cfb_module.Team, home_score: int = 0, away_score: int = 0, espn_game_id: str = ""):
        self.home_team: cfb_module.Team = home_team
        self.away_team: cfb_module.Team = away_team
        
        self.home_score: int = home_score
        self.away_score: int = away_score

        self.espn_game_id: str = espn_game_id

        self.neutral_game: bool = False

        self.sportsbook_favorite: Optional[cfb_module.Team] = None
        self.spread: float = 0
        self.home_ml: float = 0
        self.away_ml: float = 0

    def get_opponent(self, team) -> Optional[cfb_module.Team]:
        '''
            Returns the team associated with this game that is not the given team
            If the given team is not in this game, return None
        '''

        if team == self.home_team:
            return self.away_team
        elif team == self.away_team:
            return self.home_team
        else:
            return None

    def get_loser(self) -> cfb_module.Team:
        '''
            Returns the real-life loser of the game
        '''

        if self.home_score < self.away_score:
            return self.home_team
        else:
            return self.away_team

    def get_winner(self) -> cfb_module.Team:
        '''
            Returns the real-life winner of the game
        '''

        if self.home_score > self.away_score:
            return self.home_team
        else:
            return self.away_team

    def get_adj_loser(self) -> cfb_module.Team:
        '''
            Returns the team with the lower adjusted score
        '''
        
        if self.get_adj_home_score() > self.get_adj_away_score():
            return self.away_team
        else:
            return self.home_team

    def get_adj_winner(self) -> cfb_module.Team:
        '''
            Returns the team with the lower adjusted score
        '''
        
        if self.get_adj_home_score() < self.get_adj_away_score():
            return self.away_team
        else:
            return self.home_team

    def get_home_team(self) -> cfb_module.Team:
        '''
            Returns the home team
        '''

        return self.home_team

    def get_away_team(self) -> cfb_module.Team:
        '''
            Returns the away team
        '''

        return self.away_team

    def set_neutral(self, is_neutral: bool):
        '''
            Sets the game's neutral state
        '''
        
        self.neutral_game = is_neutral

    def set_odds(self, favorite_name: str, spread: float):
        '''
            Sets the odds favorite team based on team name
        '''

        if self.home_team.get_name() == favorite_name:
            self.sportsbook_favorite = self.home_team
        elif self.away_team.get_name() == favorite_name:
            self.sportsbook_favorite = self.away_team
        else:
            self.sportsbook_favorite = None

        self.spread = spread

    def set_mls(self, home_ml: int, away_ml: int):
        '''
            Sets the moneylines for the home and away teams
        '''
        
        self.home_ml = home_ml
        self.away_ml = away_ml

    def get_sportsbook_favorite(self) -> Optional[cfb_module.Team]:
        '''
            Returns the odds favorite team
        '''

        return self.sportsbook_favorite

    def get_spread(self) -> float:
        '''
            Returns the odds line for the game
        '''

        return self.spread

    def get_winner_ml(self) -> int:
        '''
            Returns the moneyline of the winning team; 0 if it wasn't set
        '''

        if self.home_team == self.get_winner():
            return self.home_ml
        else:
            return self.away_ml

    def get_loser_ml(self) -> int:
        '''
            Returns the moneyline of the losing team; 0 if it wasn't set
        '''

        if self.home_team == self.get_loser():
            return self.home_ml
        else:
            return self.away_ml

    def get_adj_score_margin(self, query_team: cfb_module.Team) -> float:
        '''
            Returns the query_team's scoring margin in this game
        '''

        margin: float = abs(self.get_adj_home_score() - self.get_adj_away_score())
        if query_team == self.get_adj_loser():
            margin *= -1

        if not self.get_winner().is_fbs and self.get_loser().is_fbs:
            margin *= Game.non_fbs_loss_multiplier

        if not self.home_team.is_fbs and not self.away_team.is_fbs:
            if margin >= 0:
                margin *= Game.fcs_game_factor
            else:
                margin *= 1/Game.fcs_game_factor
        elif self.home_team.get_conference() not in cfb_module.Team.power_5 and self.home_team.get_conference() not in cfb_module.Team.power_5:
            if margin >= 0:
                margin *= Game.g5_game_factor
            else:
                margin *= 1/Game.g5_game_factor

        if margin >= 0:
            return min(margin, Game.adj_margin_max)
        else:
            return max(margin, -Game.adj_margin_max)

    def get_adj_home_score(self) -> float:
        '''
            Returns the adjusted score for the home team
        '''
        
        adj_score = self.home_score
    
        if not self.neutral_game:
            adj_score -= Game.home_advantage

        if self.get_winner() == self.home_team:
            adj_score += Game.winner_bonus

        if not self.home_team.is_fbs and self.away_team.is_fbs:
            adj_score += Game.non_fbs_bonus

        return adj_score

    def get_adj_away_score(self) -> float:
        '''
            Returns the adjusted score for the away team
        '''
        
        adj_score = self.away_score
    
        if not self.neutral_game:
            adj_score += Game.away_disadvantage

        if self.get_winner() == self.away_team:
            adj_score += Game.winner_bonus

        if not self.away_team.is_fbs and self.home_team.is_fbs:
            adj_score += Game.non_fbs_bonus

        return adj_score

    def __repr__(self) -> str:
        if self.neutral_game:
            return f"{self.away_team.get_name()} {self.away_score} vs. {self.home_team.get_name()} {self.home_score}"
        else:
            return f"{self.away_team.get_name()} {self.away_score} @ {self.home_team.get_name()} {self.home_score}"

    def __eq__(self, other) -> bool:
        '''
            Two games are equal if they have the same ESPN game id
        '''

        if isinstance(other, Game):
            return self.espn_game_id == other.espn_game_id
        else:
            return False
