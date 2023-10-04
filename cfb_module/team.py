'''
    Class: Team
    Description: Contains data associated with each team
    Public methods:
        add_game(game): adds a new game to this team's game list
        get_games(): returns the list of this teams games
        set_fbs(is_fbs): updates the team's is_fbs
        get_avg_game_metric(opts): returns the ranking metric
        get_avg_differential(exlude_team): gets the average adjusted point differential for this team
        get_num_wins(exclude_team): gets the number of real-life wins for this team
        get_num_losses(exclude_team): gets the number of real-life losses for this team
        get_name(): gets the name of this team
        get_conference(): gets the conference of this team
    Public static variables:
        ignore_all_non_fbs: use to ignore any game that is played against a non-fbs opponent
        ignore_wins_vs_non_fbs: use to ignore a win vs. a non-fbs opponent
'''

from __future__ import annotations
import math
from typing import List, Optional, Set

import cfb_module

class Team:
    # use to tweak settings on processing FCS games
    ignore_all_non_fbs: bool = False
    ignore_wins_vs_non_fbs: bool = False
    ignore_all_non_d1: bool = False

    def __init__(self, team_name: str, conference: str = ""):
        self.team_name: str = team_name
        self.conference: str = conference
        self.games: List[cfb_module.Game] = []
        self.point_differential: float = 0
        self.fbs: bool = False
        self.d1: bool = False
        self.num_losses: int = 0
        self.num_wins: int = 0

        self.previous_season_games: List[cfb_module.Game] = []
    
    def add_game(self, game: cfb_module.Game, correct_position: int = -1, previous_season: bool = False) -> bool:
        '''
            Adds the game to the game list, returns True if added or was already in the list
            If opponent is non-FBS, then it may or may not be added depending on the flags set
            Reorganizes the list by swapping this game to the correct_position in game list
        '''

        games: List[cfb_module.Game] = self.games
        if previous_season:
            games = self.previous_season_games

        if game not in games:
            opp_team: Optional[Team] = game.get_opponent(self)
            if opp_team is None:
                return False

            # do not add the game if it is non-fbs opponent and the ignore_all_non_fbs flag is set
            if Team.ignore_all_non_fbs and not opp_team.is_fbs():
                return False

            if Team.ignore_all_non_d1 and not opp_team.d1:
                return False

            if game.get_loser() == self:
                self.num_losses += 1
            else:
                # do not add the game if it is a win against a non-fbs opponent and the ignore_wins_vs_non_fbs flag is set
                if Team.ignore_wins_vs_non_fbs and not opp_team.is_fbs():
                    return False

                self.num_wins += 1

            games.append(game)
        else:
            # the way that we process games from ESPN pages results in two versions of a neutral game: the home/away teams are swapped
            # so if we identify a match (based on the ESPN game id), but find the home/away teams are flipped, then the game is neutral
            existing_game = games[games.index(game)]
            if existing_game.get_home_team() != game.get_home_team():
                existing_game.set_neutral(True)

        # the game might've been added previously if we processed the opponent first, but we want to maintain chronological ordering
        if correct_position != -1:
            cur_position = games.index(game)
            existing_game = games[cur_position]
            games[cur_position] = games[correct_position]
            games[correct_position] = existing_game

        return True

    def set_fbs(self, fbs: bool):
        '''
            Sets the fbs flag for this team
        '''

        self.fbs = fbs

    def get_avg_game_metric(self, 
        ignore_worst_n: int = 0,
        ignore_best_n: int = 0,
        recency_bias: float = 0,
        opp_strength_weight: float = 1,
        exclude_team_from_opponent: bool = False,
        non_conference_scalar: float = 1
    ) -> float:
        '''
            Returns the teams average game metric (see explanation in README)

            recency_bias is the absolute difference between the weight of the first game and the most recent game played
                ex: through 10 games played, the base weight of each game is 0.1 and with a recency_bias of 0.05:
                    the first game is weighted 0.1 - (0.05/2) = 0.075 and the most recent game is 0.1 + (0.05/2) = 0.125
                    then, the second and second to last games have weights: 0.1 +/- (0.05/4)
                    for the ith and (n - i + 1)th game: 0.1 +/- (0.05/2^i)
        '''

        all_games: List[cfb_module.Game] = self.get_all_games()

        game_metrics: List[float] = []
        for game in all_games:
            game_metric: float = self.calculate_game_metric(
                game,
                exclude_team_from_opponent,
                opp_strength_weight,
                non_conference_scalar
            )

            game_metrics.append(game_metric)

        avg_game_metric: float = self.process_game_metrics(
            game_metrics,
            ignore_worst_n,
            ignore_best_n,
            recency_bias
        )

        return avg_game_metric

    def calculate_game_metric(self,
        game: cfb_module.Game,
        exclude_team_from_opponent: bool,
        opp_strength_weight: float,
        non_conference_scalar: float,
    ) -> float:
        opponent: Optional[Team] = game.get_opponent(self)
        if opponent is None:
            return 0

        opponent_avg_adjusted_margin: float = opponent.get_avg_adjusted_margin(
            opponent.get_all_games(),
            self,
            exclude_team_from_opponent
        )

        game_adjusted_margin: float = game.get_adjusted_margin(self)

        result_adjustment: float = game.get_result_adjustment(self)

        game_metric: float = (opp_strength_weight * opponent_avg_adjusted_margin) + game_adjusted_margin + result_adjustment

        # if self.get_conference() != opponent.get_conference() and self.get_conference() != "FBS Independents":
        #     game_metric *= non_conference_scalar

        return game_metric
    
    def process_game_metrics(
        self,
        game_metrics: List[float],
        ignore_worst_n: int,
        ignore_best_n: int,
        recency_bias: float
    ) -> float:
        # weigh each game metric according to the recency bias
        base_weight: float = 1 / len(game_metrics) if len(game_metrics) > 0 else 0
        for i in range(0, len(game_metrics) // 2):
            adjusted_weight: float = base_weight - (recency_bias / math.pow(2, i+1))
            game_metrics[i] *= adjusted_weight
        if len(game_metrics) % 2 == 1:
            game_metrics[len(game_metrics) // 2] *= base_weight
        for i in range(math.ceil(len(game_metrics) / 2), len(game_metrics)): 
            adjusted_weight: float = base_weight + (recency_bias / math.pow(2, len(game_metrics) - i))   
            game_metrics[i] *= adjusted_weight

        # sum the weighted metrics we want
        if ignore_best_n == 0 and ignore_worst_n == 0:
            return sum(game_metrics)
        
        game_metrics.sort()
        inner_sum: float = 0
        for i in range(ignore_worst_n, len(game_metrics) - ignore_best_n):
            inner_sum += game_metrics[i]
        return inner_sum

    def get_avg_adjusted_margin(
        self,
        all_games: List[cfb_module.Game],
        exclude_team: Optional[Team] = None,
        exclude: bool = True
    ) -> float:
        '''
            Returns the average adjusted point differential for each of the team's games in their game list
            
            Excludes games played against exclude_team
        '''
        
        cumulative_adjusted_margin: float = 0
        counted_games: int = 0
        for game in all_games:
            opponent: Optional[Team] = game.get_opponent(self)
            if opponent is None:
                continue

            if exclude and opponent == exclude_team:
                continue

            cumulative_adjusted_margin += game.get_adjusted_margin(self)

            counted_games += 1

        return cumulative_adjusted_margin / counted_games if counted_games > 0 else 0

    def get_games(self) -> List[cfb_module.Game]:
        '''
            Returns the list of this team's games
        '''

        return self.games
    
    def get_all_games(self) -> List[cfb_module.Game]:
        '''
        '''

        all_games: List[cfb_module.Game] = self.games
        if cfb_module.Game.previous_season_scalar != 0:
            all_games: List[cfb_module.Game] = [*self.previous_season_games, *self.games]

        return all_games
 
    def get_num_wins(self, exclude_team: Optional[Team] = None) -> int:
        '''
            Return the number of real-life wins this team has in their game list
            Exlcuding games against exclude_team
        '''

        if exclude_team is None:
            return self.num_wins

        num_wins = 0
        for game in self.games:
            if game.get_opponent(self) == exclude_team:
                continue
            if game.get_winner() == self:
                num_wins += 1
        return num_wins

    def get_num_losses(self, exclude_team: Optional[Team] = None) -> int:
        '''
            Return the number of real-life loses this team has in their game list
            Exlcuding games against exclude_team
        '''

        if exclude_team is None:
            return self.num_losses

        num_losses: int = 0
        for game in self.games:
            if game.get_opponent(self) == exclude_team:
                continue
            if game.get_loser() == self:
                num_losses += 1
        return num_losses

    def get_name(self) -> str:
        return self.team_name

    def get_conference(self) -> str:
        return self.conference

    def is_power_5(self) -> bool:
        '''
            A team is power 5 if it is in a power 5 conference or is Notre Dame
        '''

        power_5_conferences: Set[str] = {"Pac-12", "Big Ten", "SEC", "Big 12", "ACC"}

        return self.get_conference() in power_5_conferences or self.get_name() == "Notre Dame"
    
    def is_fbs(self) -> bool:
        return self.fbs
    
    def __eq__(self, other) -> bool:
        '''
            Two teams are equal if they have the same name
        '''

        if isinstance(other, Team):
            return self.get_name() == other.get_name()
        else:
            return False
    