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

    def __init__(self, home_team: cfb_module.Team, away_team: cfb_module.Team, neutral_game: bool, home_score: int, away_score: int):
        self.home_team: cfb_module.Team = home_team
        self.away_team: cfb_module.Team = away_team
        self.neutral_game: bool = neutral_game
        self.home_score: int = home_score
        self.away_score: int = away_score

        self.adj_home_score: float = self.home_score - Game.home_advantage
        self.adj_away_score: float = self.away_score + Game.away_disadvantage
        if self.home_score > self.away_score:
            self.adj_home_score += Game.winner_bonus
        else:
            self.adj_away_score += Game.winner_bonus

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

    def get_adj_victory_margin(self) -> float:
        '''
            Returns the absolute difference between the two adjusted scores of this game
        '''

        margin: float = abs(self.adj_home_score - self.adj_away_score)
        if not self.get_winner().is_fbs:
            margin *= Game.non_fbs_loss_multiplier

        return min(margin, Game.adj_margin_max)

    def __str__(self) -> str:
        return f"{self.away_team.get_name()} ({self.away_score}) @ {self.home_team.get_name()} ({self.home_score})"

    def __eq__(self, other) -> bool:
        '''
            Two games are equal if they have the same away teams, home teams, away scores and home scores
            TODO: It is feasible for 2 teams to play twice to the same result, so a date should be included
        '''

        if isinstance(other, Game):
            same = self.away_team == other.away_team
            same = same and self.home_team == other.home_team
            same = same and self.away_score == other.away_score
            same = same and self.home_score == other.home_score
            return same
        else:
            return False
