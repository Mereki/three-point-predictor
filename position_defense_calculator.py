from nba_api.stats.endpoints import teamgamelog, boxscoretraditionalv2
import time
import numpy as np


class PositionDefenseCalculator:
    """Calculate position-specific defense by aggregating game data"""

    def __init__(self):
        self.cache = {}

    def get_position_defense_stats(self, fetcher, parser, team_id, season="2025-26"):
        """
        Calculate how a team defends each position by analyzing their games
        Returns: dict with guard/forward/center 3P% allowed
        """

        # Check cache first
        cache_key = f"{team_id}_{season}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        print(f"      Calculating position defense for team {team_id}...")

        try:
            # Get team's game log for the season
            team_games = teamgamelog.TeamGameLog(
                team_id=team_id,
                season=season,
                season_type_all_star='Regular Season'
            )
            time.sleep(0.6)

            games_data = team_games.get_dict()
            games = self._parse_team_game_log(games_data)

            # Filter to only completed games (have 'W' or 'L' result)
            completed_games = [g for g in games if g['wl'] in ['W', 'L']]

            print(f"      Found {len(completed_games)} completed games")

            if len(completed_games) == 0:
                print(f"      No completed games found, using league average")
                return {
                    'guard_3p_pct_allowed': 0.365,
                    'forward_3p_pct_allowed': 0.365,
                    'center_3p_pct_allowed': 0.365,
                    'opp_3p_pct_allowed': 0.365
                }

            # For each game, get opponent players' stats and aggregate by position
            position_stats = {
                'guard': {'made': 0, 'attempted': 0},
                'forward': {'made': 0, 'attempted': 0},
                'center': {'made': 0, 'attempted': 0}
            }

            games_processed = 0
            games_to_process = min(10, len(completed_games))  # Process up to 10 recent games

            for i, game in enumerate(completed_games):
                if games_processed >= games_to_process:
                    break

                game_id = game['game_id']

                print(f"        Processing game {games_processed + 1}/{games_to_process} (ID: {game_id})...")

                # Get box score for this game
                try:
                    box_score = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
                    time.sleep(0.6)

                    box_data = box_score.get_dict()

                    # Check if box score has data
                    if not self._has_box_score_data(box_data):
                        print(f"        No box score data available for game {game_id}")
                        continue

                    # Get opponent team ID from box score (the team that's NOT our team)
                    opponent_id = self._get_opponent_from_box_score(box_data, team_id)

                    if opponent_id is None:
                        print(f"        Could not identify opponent in game {game_id}")
                        continue

                    print(f"        Opponent team ID: {opponent_id}")

                    # Get opponent player stats
                    opponent_player_stats = self._parse_opponent_box_score(box_data, opponent_id)

                    print(f"        Found {len(opponent_player_stats)} opponent players")

                    # Get positions for each player and aggregate
                    for player_stat in opponent_player_stats:
                        player_id = player_stat['player_id']
                        fg3m = player_stat['fg3m']
                        fg3a = player_stat['fg3a']

                        if fg3a == 0:  # Skip players who didn't attempt any 3s
                            continue

                        # Get player position
                        position_group = self._get_player_position_cached(fetcher, parser, player_id)

                        if position_group in position_stats:
                            position_stats[position_group]['made'] += fg3m
                            position_stats[position_group]['attempted'] += fg3a

                    games_processed += 1

                except Exception as e:
                    print(f"        Error processing game {game_id}: {e}")
                    continue

            if games_processed == 0:
                print(f"      Could not process any games, using league average")
                return {
                    'guard_3p_pct_allowed': 0.365,
                    'forward_3p_pct_allowed': 0.365,
                    'center_3p_pct_allowed': 0.365,
                    'opp_3p_pct_allowed': 0.365
                }

            # Calculate percentages
            result = {
                'guard_3p_pct_allowed': self._calc_percentage(position_stats['guard']),
                'forward_3p_pct_allowed': self._calc_percentage(position_stats['forward']),
                'center_3p_pct_allowed': self._calc_percentage(position_stats['center']),
            }

            # Add overall average
            total_made = sum(pos['made'] for pos in position_stats.values())
            total_attempted = sum(pos['attempted'] for pos in position_stats.values())
            result['opp_3p_pct_allowed'] = total_made / total_attempted if total_attempted > 0 else 0.365

            print(f"      Position defense calculated from {games_processed} games:")
            print(
                f"        Guards: {result['guard_3p_pct_allowed']:.1%} ({position_stats['guard']['made']}/{position_stats['guard']['attempted']})")
            print(
                f"        Forwards: {result['forward_3p_pct_allowed']:.1%} ({position_stats['forward']['made']}/{position_stats['forward']['attempted']})")
            print(
                f"        Centers: {result['center_3p_pct_allowed']:.1%} ({position_stats['center']['made']}/{position_stats['center']['attempted']})")

            # Cache the result
            self.cache[cache_key] = result

            return result

        except Exception as e:
            print(f"      Error calculating position defense: {e}")
            import traceback
            traceback.print_exc()
            # Return league average as fallback
            return {
                'guard_3p_pct_allowed': 0.365,
                'forward_3p_pct_allowed': 0.365,
                'center_3p_pct_allowed': 0.365,
                'opp_3p_pct_allowed': 0.365
            }

    def _parse_team_game_log(self, games_data):
        """Extract game IDs and W/L from team game log"""
        result_set = games_data['resultSets'][0]
        headers = result_set['headers']
        rows = result_set['rowSet']

        game_id_idx = headers.index('Game_ID')
        wl_idx = headers.index('WL')

        games = []
        for row in rows:
            games.append({
                'game_id': row[game_id_idx],
                'wl': row[wl_idx] if row[wl_idx] else None  # W, L, or None for unplayed
            })

        return games

    def _has_box_score_data(self, box_data):
        """Check if box score actually has data (game has been played)"""
        for result_set in box_data['resultSets']:
            if result_set['name'] == 'PlayerStats':
                return len(result_set['rowSet']) > 0
        return False

    def _get_opponent_from_box_score(self, box_data, our_team_id):
        """Extract opponent team ID from box score"""
        # Use LineScore which is more reliable
        for result_set in box_data['resultSets']:
            if result_set['name'] == 'LineScore':
                headers = result_set['headers']
                rows = result_set['rowSet']

                if 'TEAM_ID' in headers:
                    team_id_idx = headers.index('TEAM_ID')

                    for row in rows:
                        team_id = row[team_id_idx]
                        if team_id != our_team_id:
                            return team_id

        # Fallback to TeamStats
        for result_set in box_data['resultSets']:
            if result_set['name'] == 'TeamStats':
                headers = result_set['headers']
                rows = result_set['rowSet']

                if 'TEAM_ID' in headers and len(rows) > 0:
                    team_id_idx = headers.index('TEAM_ID')

                    for row in rows:
                        team_id = row[team_id_idx]
                        if team_id != our_team_id:
                            return team_id

        return None

    def _parse_opponent_box_score(self, box_data, opponent_id):
        """Extract opponent player stats from box score"""
        # Find PlayerStats result set
        player_stats_set = None
        for result_set in box_data['resultSets']:
            if result_set['name'] == 'PlayerStats':
                player_stats_set = result_set
                break

        if not player_stats_set:
            return []

        headers = player_stats_set['headers']
        rows = player_stats_set['rowSet']

        team_id_idx = headers.index('TEAM_ID')
        player_id_idx = headers.index('PLAYER_ID')
        fg3m_idx = headers.index('FG3M')
        fg3a_idx = headers.index('FG3A')

        opponent_stats = []
        for row in rows:
            # Only get stats for opponent team
            if row[team_id_idx] == opponent_id:
                opponent_stats.append({
                    'player_id': row[player_id_idx],
                    'fg3m': row[fg3m_idx] or 0,
                    'fg3a': row[fg3a_idx] or 0
                })

        return opponent_stats

    def _get_player_position_cached(self, fetcher, parser, player_id):
        """Get player position with caching"""
        cache_key = f"pos_{player_id}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            player_info = fetcher.get_player_info(player_id)
            if player_info:
                position = parser.parse_player_info(player_info)

                # Map to position group
                if position in ['PG', 'SG', 'G']:
                    pos_group = 'guard'
                elif position in ['SF', 'PF', 'F']:
                    pos_group = 'forward'
                else:  # C
                    pos_group = 'center'

                self.cache[cache_key] = pos_group
                return pos_group
        except:
            pass

        # Default to guard if can't determine
        return 'guard'

    def _calc_percentage(self, stats_dict):
        """Calculate percentage from made/attempted dict"""
        made = stats_dict['made']
        attempted = stats_dict['attempted']

        if attempted == 0:
            return 0.365  # League average

        return made / attempted