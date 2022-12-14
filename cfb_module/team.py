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
import cfb_module
import math
from typing import List, Optional

class Team:
    # use to tweak settings on processing FCS games
    ignore_all_non_fbs: bool = False
    ignore_wins_vs_non_fbs: bool = False
    ignore_all_non_d1: bool = False
    non_conference_weight: float = 1

    power_5 = ["Pac-12", "Big Ten", "SEC", "Big 12", "ACC"]

    def __init__(self, team_name: str, conference: str = ""):
        self.team_name: str = team_name
        self.conference: str = conference
        self.games: List[cfb_module.Game] = []
        self.point_differential: float = 0
        self.is_fbs: bool = False
        self.is_d1: bool = False
        self.num_losses: int = 0
        self.num_wins: int = 0
    
    def add_game(self, game: cfb_module.Game, correct_position: int = -1) -> bool:
        '''
            Adds the game to the game list, returns True if added or was already in the list
            If opponent is non-FBS, then it may or may not be added depending on the flags set
            Reorganizes the list by swapping this game to the correct_position in game list
        '''

        if game not in self.games:
            opp_team: Optional[Team] = game.get_opponent(self)
            if opp_team is None:
                return False

            # do not add the game if it is non-fbs opponent and the ignore_all_non_fbs flag is set
            if Team.ignore_all_non_fbs and not opp_team.is_fbs:
                return False

            if Team.ignore_all_non_d1 and not opp_team.is_d1:
                return False

            if game.get_loser() == self:
                self.num_losses += 1
            else:
                # do not add the game if it is a win against a non-fbs opponent and the ignore_wins_vs_non_fbs flag is set
                if Team.ignore_wins_vs_non_fbs and not opp_team.is_fbs:
                    return False

                self.num_wins += 1

            self.games.append(game)
        else:
            # the way that we process games from ESPN pages results in two versions of a neutral game: the home/away teams are swapped
            # so if we identify a match (based on the ESPN game id), but find the home/away teams are flipped, then the game is neutral
            existing_game = self.games[self.games.index(game)]
            if existing_game.get_home_team() != game.get_home_team():
                existing_game.set_neutral(True)

        # the game might've been added previously if we processed the opponent first, but we want to maintain chronological ordering
        if correct_position != -1:
            cur_position = self.games.index(game)
            existing_game = self.games[cur_position]
            self.games[cur_position] = self.games[correct_position]
            self.games[correct_position] = existing_game

        return True

    def set_fbs(self, is_fbs: bool):
        '''
            Sets the is_fbs flag for this team
        '''

        self.is_fbs = is_fbs

    def get_avg_game_metric(self, 
        ignore_worst_n: int = 0, ignore_best_n: int = 0, 
        win_factor: float = 0, loss_factor: float = 0,
        opp_strength_weight: float = 1,
        recency_bias: float = 0,
        exclude_team_result_from_opp: bool = False) -> float:
        '''
            Returns the teams average game metric (see explanation in README)

            recency_bias is the absolute difference between the weight of the first game and the most recent game played
                ex: through 10 games played, the base weight of each game is 0.1 and with a recency_bias of 0.05:
                    the first game is weighted 0.1 - (0.05/2) = 0.075 and the most recent game is 0.1 + (0.05/2) = 0.125
                    then, the second and second to last games have weights: 0.1 +/- (0.05/4)
                    for the ith and (n - i + 1)th game: 0.1 +/- (0.05/2^i)
        '''

        # calculate the game metric for each game this team has
        game_metrics: List[float] = []
        for game in self.games:
            opp_team: Optional[Team] = game.get_opponent(self)
            if opp_team is None:
                continue

            # the metrics to calculate
            opp_avg_adj_diff: float = 0
            game_mov: float = 0
            opp_win_avg: float = 0
            result_factor: float = 0

            if exclude_team_result_from_opp:
                opp_avg_adj_diff = opp_team.get_avg_differential(self)
                num_games: int = opp_team.get_num_wins(self) + opp_team.get_num_losses(self)
                opp_win_avg = opp_team.get_num_wins(self) / num_games if num_games > 0 else 0
            else:
                opp_avg_adj_diff = opp_team.get_avg_differential()
                opp_win_avg = opp_team.get_num_wins() / (opp_team.get_num_wins() + opp_team.get_num_losses())

            game_mov = game.get_adj_score_margin(self)

            if self == game.get_loser():
                result_factor = -loss_factor * (1 - opp_win_avg)
            else:
                result_factor = win_factor * opp_win_avg
                
            if not opp_team.is_fbs:
                if result_factor >= 0:
                    result_factor *= cfb_module.Game.fcs_game_factor
                else:
                    result_factor *= (1/cfb_module.Game.fcs_game_factor)
            elif self.get_conference() not in Team.power_5 and opp_team.get_conference() not in Team.power_5:
                if result_factor >= 0:
                    result_factor *= cfb_module.Game.g5_game_factor
                else:
                    result_factor *= 1/cfb_module.Game.g5_game_factor

            game_metric = (opp_strength_weight * opp_avg_adj_diff) + game_mov + result_factor
            
            # if self.get_conference() != opp_team.get_conference() and self.get_conference() != "FBS Independents":
            #     game_metric *= Team.non_conference_weight

            game_metrics.append(game_metric)

        # weigh each game metric according to the recency bias
        base_weight: float = 1 / len(game_metrics)
        for i in range(0, len(game_metrics) // 2):
            adjusted_weight = base_weight - (recency_bias / math.pow(2, i+1))
            game_metrics[i] *= adjusted_weight
        if len(game_metrics) % 2 == 1:
            game_metrics[len(game_metrics) // 2] *= base_weight
        for i in range(math.ceil(len(game_metrics) / 2), len(game_metrics)): 
            adjusted_weight = base_weight + (recency_bias / math.pow(2, len(game_metrics) - i))   
            game_metrics[i] *= adjusted_weight

        # sum the weighted metrics we want
        if ignore_worst_n != 0 or ignore_best_n != 0:
            # TODO: how should this work with recency bias?
            game_metrics.sort()
            inner_sum: float = 0
            for i in range(ignore_worst_n, len(game_metrics) - ignore_best_n):
                inner_sum += game_metrics[i]
            return inner_sum
        else:
            return sum(game_metrics)

    def get_avg_differential(self, exclude_team: Optional[Team] = None) -> float:
        '''
            Returns the average adjusted point differential for each of the team's games in their game list
            
            Exlcudes games played against exclude_team
        '''
        
        diff: float = 0
        counted_games: int = 0
        for game in self.games:
            opp_team: Optional[Team] = game.get_opponent(self)
            if opp_team is None:
                continue

            if opp_team == exclude_team:
                continue

            diff += game.get_adj_score_margin(self)
            counted_games += 1

        return diff / counted_games if counted_games > 0 else 0

    def get_games(self) -> List[cfb_module.Game]:
        '''
            Returns the list of this team's games
        '''

        return self.games

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
