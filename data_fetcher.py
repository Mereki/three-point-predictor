from nba_api.stats.endpoints import playergamelog, commonplayerinfo, teamdashboardbygeneralsplits, commonteamroster, \
    scoreboardv2, leaguedashptdefend
from nba_api.stats.static import players, teams
import time
from datetime import datetime, timedelta


class NBADataFetcher:
    def __init__(self):
        self.all_players = players.get_players()
        self.all_teams = teams.get_teams()

    def find_player_by_name(self, name):
        """Find player by name (fuzzy matching)"""
        name_lower = name.lower()
        for player in self.all_players:
            if name_lower in player['full_name'].lower():
                return player
        return None

    def find_team_by_abbrev(self, abbrev):
        """Find team by abbreviation"""
        for team in self.all_teams:
            if team['abbreviation'] == abbrev:
                return team
        return None

    def find_team_by_id(self, team_id):
        """Find team by ID"""
        for team in self.all_teams:
            if team['id'] == team_id:
                return team
        return None

    def get_player_game_log(self, player_id, season="2025-26"):
        """Get last games for a player"""
        try:
            game_log = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=season,
                season_type_all_star='Regular Season'
            )
            time.sleep(0.6)
            return game_log.get_dict()
        except Exception as e:
            print(f"    Error: {e}")
            return None

    def get_player_info(self, player_id):
        """Get player position and basic info"""
        try:
            player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
            time.sleep(0.6)
            return player_info.get_dict()
        except Exception as e:
            print(f"    Error: {e}")
            return None

    def get_team_defense_stats(self, team_id, season="2025-26"):
        """Get opponent's overall 3P defense"""
        try:
            team_dashboard = teamdashboardbygeneralsplits.TeamDashboardByGeneralSplits(
                team_id=team_id,
                season=season,
                season_type_all_star='Regular Season',
                measure_type_detailed_defense='Opponent'
            )
            time.sleep(0.6)
            return team_dashboard.get_dict()
        except Exception as e:
            print(f"    Error: {e}")
            return None

    def get_position_defense(self, season="2025-26"):
        """
        Get league-wide position defense data
        This returns how each team defends different positions
        """
        try:
            defense_data = leaguedashptdefend.LeagueDashPtDefend(
                season=season,
                season_type_all_star='Regular Season',
                per_mode_simple='PerGame',
                defense_category='3 Pointers'  # Specifically 3-point defense
            )
            time.sleep(0.6)
            return defense_data.get_dict()
        except Exception as e:
            print(f"    Error getting position defense: {e}")
            return None

    def get_team_roster(self, team_id, season="2025-26"):
        """Get team's current roster"""
        try:
            roster = commonteamroster.CommonTeamRoster(
                team_id=team_id,
                season=season
            )
            time.sleep(0.6)
            return roster.get_dict()
        except Exception as e:
            print(f"    Error getting roster: {e}")
            return None

    def get_todays_games(self, days_ahead=0):
        """
        Get games for today or future date
        days_ahead: 0 for today, 1 for tomorrow, etc.
        """
        try:
            target_date = datetime.now() + timedelta(days=days_ahead)
            game_date = target_date.strftime('%Y-%m-%d')

            scoreboard = scoreboardv2.ScoreboardV2(game_date=game_date)
            time.sleep(0.6)
            return scoreboard.get_dict()
        except Exception as e:
            print(f"    Error getting games: {e}")
            return None

    def get_team_injuries(self, team_abbrev):
        """Get ESPN injury report for a team"""
        import requests
        team_abbrev_lower = team_abbrev.lower()
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_abbrev_lower}/injuries"

        try:
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                return {'injuries': []}
            return response.json()
        except Exception as e:
            print(f"    Error fetching injuries: {e}")
            return {'injuries': []}