import numpy as np
from datetime import datetime


class NBADataParser:
    """Parses JSON responses from nba_api"""

    def parse_player_game_log(self, response_dict, use_season_avg=True):
        """
        Extract games' 3PM from player game log
        use_season_avg: If True, use full season average for 3PA, else use last 10 games
        Returns: dict with last_5_3pm, last_10_3pm, 3pa_per_game, and dates
        """
        try:
            result_set = response_dict['resultSets'][0]
            headers = result_set['headers']
            rows = result_set['rowSet']

            # Find column indices
            fg3m_idx = headers.index('FG3M')
            fg3a_idx = headers.index('FG3A')
            game_date_idx = headers.index('GAME_DATE')

            # Extract last 10 games
            last_10_3pm = []
            last_10_3pa = []
            last_10_dates = []

            # Also collect ALL games for season average
            all_3pa = []

            for i, row in enumerate(rows):
                # Collect all 3PA for season average
                all_3pa.append(row[fg3a_idx])

                # Only collect last 10 for recent stats
                if i < 10:
                    last_10_3pm.append(row[fg3m_idx])
                    last_10_3pa.append(row[fg3a_idx])

                    date_str = row[game_date_idx]
                    try:
                        date_obj = datetime.strptime(date_str, '%b %d, %Y')
                        formatted_date = date_obj.strftime('%-m/%-d/%Y')
                    except:
                        formatted_date = date_str

                    last_10_dates.append(formatted_date)

            if len(last_10_3pm) < 5:
                return None

            last_5_3pm = last_10_3pm[:5]
            last_5_dates = last_10_dates[:5]

            # Calculate averages
            if use_season_avg:
                avg_3pa = np.mean(all_3pa) if all_3pa else 0
            else:
                avg_3pa = np.mean(last_10_3pa) if last_10_3pa else 0

            return {
                'last_5_3pm': last_5_3pm,
                'last_10_3pm': last_10_3pm,
                'last_5_dates': last_5_dates,
                'last_10_dates': last_10_dates,
                'last_10_3pa': last_10_3pa,
                '3pa_per_game': round(avg_3pa, 1),
                'season_3pa_avg': round(np.mean(all_3pa), 1) if all_3pa else 0,
                'last_10_3pa_avg': round(np.mean(last_10_3pa), 1) if last_10_3pa else 0,
                'games_played': len(all_3pa)
            }
        except (KeyError, IndexError, ValueError) as e:
            print(f"    Error parsing game log: {e}")
            return None

    def parse_player_info(self, response_dict):
        """Extract player position"""
        try:
            result_set = response_dict['resultSets'][0]
            headers = result_set['headers']
            row = result_set['rowSet'][0]

            position_idx = headers.index('POSITION')
            position = row[position_idx]

            if not position:
                return 'SG'

            if 'Guard' in position:
                return 'SG'
            elif 'Forward' in position:
                if 'Center' in position:
                    return 'PF'
                return 'SF'
            elif 'Center' in position:
                return 'C'

            return position
        except (KeyError, IndexError) as e:
            print(f"    Error parsing player info: {e}")
            return 'SG'

    def parse_team_defense_stats(self, response_dict):
        """Extract opponent 3P% allowed"""
        try:
            for result_set in response_dict['resultSets']:
                if result_set['name'] == 'OverallTeamDashboard':
                    headers = result_set['headers']
                    row = result_set['rowSet'][0]

                    if 'FG3_PCT' in headers:
                        fg3_pct_idx = headers.index('FG3_PCT')
                        opp_3p_pct = row[fg3_pct_idx]
                        return float(opp_3p_pct) if opp_3p_pct else 0.365

            return 0.365
        except (KeyError, IndexError) as e:
            print(f"    Error parsing team defense: {e}")
            return 0.365

    def parse_position_defense(self, response_dict, team_id):
        """
        Extract position-specific 3P% allowed for a specific team
        Returns: dict with guard/forward/center 3P% allowed
        """
        try:
            # Debug: print available result sets
            print(f"    DEBUG: Available result sets: {[rs.get('name') for rs in response_dict.get('resultSets', [])]}")

            result_set = response_dict['resultSets'][0]
            headers = result_set['headers']

            # Debug: print headers
            print(f"    DEBUG: Headers: {headers}")

            rows = result_set['rowSet']

            # Try to find team identifier column (could be TEAM_ID, TEAM_NAME, etc.)
            team_identifier_idx = None
            team_identifier_key = None

            for possible_key in ['TEAM_ID', 'TEAM_NAME', 'TEAM_ABBREVIATION', 'CLOSE_DEF_PERSON_ID']:
                if possible_key in headers:
                    team_identifier_idx = headers.index(possible_key)
                    team_identifier_key = possible_key
                    break

            if not team_identifier_idx:
                print(f"    Warning: Could not find team identifier in headers")
                # Return league average
                return {
                    'guard_3p_pct_allowed': 0.365,
                    'forward_3p_pct_allowed': 0.365,
                    'center_3p_pct_allowed': 0.365
                }

            print(f"    DEBUG: Using {team_identifier_key} at index {team_identifier_idx}")

            # Find defense category column
            def_category_idx = None
            for possible_key in ['DEF_PLAYER_CLASS', 'PLAYER_POSITION', 'DEFENSE_CATEGORY']:
                if possible_key in headers:
                    def_category_idx = headers.index(possible_key)
                    break

            if not def_category_idx:
                print(f"    Warning: Could not find defense category in headers")
                return {
                    'guard_3p_pct_allowed': 0.365,
                    'forward_3p_pct_allowed': 0.365,
                    'center_3p_pct_allowed': 0.365
                }

            # Find FG3 percentage column
            fg3_pct_idx = None
            for possible_key in ['FG3_PCT', 'FG3_PCTAGE', 'D_FG3_PCT']:
                if possible_key in headers:
                    fg3_pct_idx = headers.index(possible_key)
                    break

            if not fg3_pct_idx:
                print(f"    Warning: Could not find FG3 PCT in headers")
                return {
                    'guard_3p_pct_allowed': 0.365,
                    'forward_3p_pct_allowed': 0.365,
                    'center_3p_pct_allowed': 0.365
                }

            # Initialize with league average
            position_defense = {
                'guard_3p_pct_allowed': 0.365,
                'forward_3p_pct_allowed': 0.365,
                'center_3p_pct_allowed': 0.365
            }

            # Debug: print first few rows
            print(f"    DEBUG: Sample rows (first 3):")
            for i, row in enumerate(rows[:3]):
                print(f"      Row {i}: {row[:min(5, len(row))]}")

            # Find this team's defense by position
            # Note: team_id might need to be converted or matched differently
            team_matches = []
            for row in rows:
                team_val = row[team_identifier_idx]
                if str(team_val) == str(team_id):
                    team_matches.append(row)

            print(f"    DEBUG: Found {len(team_matches)} rows matching team_id {team_id}")

            for row in team_matches:
                player_class = row[def_category_idx]
                fg3_pct = row[fg3_pct_idx]

                if fg3_pct is None:
                    continue

                fg3_pct = float(fg3_pct)

                print(f"    DEBUG: Position {player_class} -> {fg3_pct:.3f}")

                # Map position classes to our categories
                if player_class in ['Guard', 'Guards', 'G']:
                    position_defense['guard_3p_pct_allowed'] = fg3_pct
                elif player_class in ['Forward', 'Forwards', 'F']:
                    position_defense['forward_3p_pct_allowed'] = fg3_pct
                elif player_class in ['Center', 'Centers', 'C']:
                    position_defense['center_3p_pct_allowed'] = fg3_pct

            return position_defense

        except (KeyError, IndexError) as e:
            print(f"    Error parsing position defense: {e}")
            import traceback
            traceback.print_exc()
            # Return league average fallback
            return {
                'guard_3p_pct_allowed': 0.365,
                'forward_3p_pct_allowed': 0.365,
                'center_3p_pct_allowed': 0.365
            }

    def parse_team_roster(self, response_dict):
        """Extract player IDs from team roster"""
        try:
            result_set = response_dict['resultSets'][0]
            headers = result_set['headers']
            rows = result_set['rowSet']

            player_id_idx = headers.index('PLAYER_ID')

            player_ids = []
            for row in rows:
                player_ids.append(row[player_id_idx])

            return player_ids
        except (KeyError, IndexError) as e:
            print(f"    Error parsing roster: {e}")
            return []

    def parse_scoreboard(self, response_dict):
        """Extract today's games"""
        try:
            games = []

            game_header = response_dict['resultSets'][0]
            headers = game_header['headers']
            rows = game_header['rowSet']

            game_id_idx = headers.index('GAME_ID')
            home_team_id_idx = headers.index('HOME_TEAM_ID')
            visitor_team_id_idx = headers.index('VISITOR_TEAM_ID')
            game_status_idx = headers.index('GAME_STATUS_TEXT')

            for row in rows:
                game_status = row[game_status_idx]
                if 'Final' not in game_status:
                    games.append({
                        'game_id': row[game_id_idx],
                        'home_team_id': row[home_team_id_idx],
                        'visitor_team_id': row[visitor_team_id_idx],
                        'status': game_status
                    })

            return games
        except (KeyError, IndexError) as e:
            print(f"    Error parsing scoreboard: {e}")
            return []

    def parse_injuries(self, espn_json):
        """Extract injury list from ESPN API"""
        try:
            if 'injuries' not in espn_json:
                return []

            injuries = []
            for injury in espn_json['injuries']:
                injuries.append({
                    'status': injury.get('status', 'UNKNOWN'),
                    'athlete': {
                        'displayName': injury.get('athlete', {}).get('displayName', 'Unknown')
                    }
                })

            return injuries
        except (KeyError, TypeError) as e:
            print(f"    Error parsing injuries: {e}")
            return []