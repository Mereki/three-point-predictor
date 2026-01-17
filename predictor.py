import numpy as np

class ThreePointPredictor:
    def __init__(self):
        self.league_avg_3p_pct = 0.365 # range of 0.360 - 0.365, will just use max here for testing purposes

        self.perimeter_defenders = {
            'ATL': ['Dyson Daniels', 'Nickeil Alexander-Walker', 'Caleb Houstan'],
            'BOS': ['Jaylen Brown', 'Jordan Walsh', 'Jayson Tatum', 'Derrick White'],
            'MIA': ['Bam Adebayo', 'Davion Mitchell', 'Norman Powell'],
            'LAL': ['Marcus Smart', 'Jarred Vanderbilt', 'Jake LaRavia'],
            'MEM': ['Jaren Jackson Jr.', 'Kentavious Caldwell-Pope', 'Jaylen Wells', 'Vince Williams Jr.'],
            'GSW': ['Draymond Green', 'Jimmy Butler', 'Gary Payton II', 'De\'Anthony Melton'],
            'MIN': ['Jaden McDaniels', 'Anthony Edwards', 'Mike Conley', 'Donte DiVincenzo', 'Jaylen Clark'],
            'OKC': ['Luguentz Dort', 'Alex Caruso', 'Jalen Williams', 'Cason Wallace', 'Shai Gilgeous-Alexander'],
            'PHI': ['Quentin Grimes'],
            'CLE': ['De\'Andre Hunter', 'Evan Mobley', 'Lonzo Ball'],
            'BKN': ['Nic Claxton'],
            'CHA': [], # they really don't have anyone considered a "good" perimeter defender aside from like josh green lol
            'CHI': ['Issac Okoro'],
            'DAL': ['P.J. Washington', 'Cooper Flagg', 'Anthony Davis', 'Max Christie'],
            'DEN': ['Aaron Gordon'],
            'DET': ['Ausar Thompson'],
            'HOU': ['Amen Thompson', 'Tari Eason', 'Dorian Finney-Smith', 'Fred VanVleet'],
            'IND': ['Andrew Nembhard', 'T.J. McConnell'],
            'LAC': ['Kawhi Leonard', 'Kris Dunn', 'Derrick Jones Jr.'],
            'MIL': ['Giannis Antetokounmpo', 'Gary Harris'],
            'NOP': ['Herbert Jones', 'Jose Alvarado'],
            'NYK': ['OG Anunoby', 'Mikal Bridges', 'Josh Hart', 'Miles McBride'],
            'ORL': ['Jalen Suggs', 'Anthony Black', 'Jonathan Issac'],
            'PHX': ['Dillon Brooks', 'Royce O\'Neale', 'Ryan Dunn'],
            'POR': ['Toumani Camara', 'Jrue Holiday'],
            'SAC': ['Keon Ellis'],
            'SAS': ['De\'Aaron Fox', 'Stephon Castle', 'Devin Vassell', 'Victor Wembanyama'],
            'TOR': ['R.J. Barrett', 'Scottie Barnes', 'Immanuel Quickley'],
            'UTA': [], # they suck perimeter-y too
            'WAS': ['Bilal Coulibaly']
        }

    def get_position_group(self, position):
        """Convert NBA position to defensive grouping"""
        if position in ['PG', 'SG', 'G']:
            return 'guard'
        elif position in ['SF', 'PF', 'F']:
            return 'forward'
        else:  # C
            return 'center'

    def calculate_prediction(self, player_stats, opponent_stats, position):
        """
        player_stats: dict with 'last_10_3pm', etc.
        opponent_stats: dict with position-specific defense
        position: player's position (PG, SG, SF, PF, C)
        """

        # Base prediction on recent average
        last_10_avg = np.mean(player_stats['last_10_3pm'])

        # Use position-specific defense if available
        position_group = self.get_position_group(position)
        defense_key = f'{position_group}_3p_pct_allowed'

        if defense_key in opponent_stats:
            opp_3p_allowed = opponent_stats[defense_key]
        else:
            # Fallback to overall team defense
            opp_3p_allowed = opponent_stats.get('opp_3p_pct_allowed', self.league_avg_3p_pct)

        # Adjust for opponent defense
        defense_multiplier = opp_3p_allowed / self.league_avg_3p_pct

        prediction = last_10_avg * defense_multiplier

        return round(prediction, 1)

    def adjust_for_injuries(self, prediction, injuries, opponent_team_abbrev):
        """Adjust prediction if key defenders are out"""
        boost = 0
        injured_defenders = []

        for injury in injuries:
            if injury.get('status') == 'OUT':
                player_name = injury.get('athlete', {}).get('displayName', '')

                # Check if this is an elite defender
                if opponent_team_abbrev in self.perimeter_defenders:
                    if player_name in self.perimeter_defenders[opponent_team_abbrev]:
                        boost += 0.3
                        injured_defenders.append(player_name)

        return prediction + boost, injured_defenders

    def calculate_confidence(self, player_stats, opponent_stats, position, injuries, opponent_team_abbrev):
        """Returns confidence score 0-100 and list of factor flags"""
        score = 0
        flags = []

        # Recent performance (35%)
        last_5_avg = np.mean(player_stats['last_5_3pm'])
        recent_score = min((last_5_avg / 5) * 35, 35)
        score += recent_score

        if last_5_avg >= 3:
            flags.append(f"✓ Averaging {last_5_avg:.1f} 3PM last 5 games")

        # Position-specific matchup (30%)
        position_group = self.get_position_group(position)
        defense_key = f'{position_group}_3p_pct_allowed'

        if defense_key in opponent_stats:
            opp_3p_allowed = opponent_stats[defense_key]
        else:
            opp_3p_allowed = opponent_stats.get('opp_3p_pct_allowed', self.league_avg_3p_pct)

        if opp_3p_allowed > self.league_avg_3p_pct:
            matchup_bonus = ((opp_3p_allowed - self.league_avg_3p_pct) / self.league_avg_3p_pct) * 30
            score += min(matchup_bonus, 30)
            flags.append(
                f"✓ Opponent allows {opp_3p_allowed:.1%} to {position_group}s (league avg: {self.league_avg_3p_pct:.1%})")
        else:
            flags.append(f"⚠ Tough matchup: Opponent allows {opp_3p_allowed:.1%} to {position_group}s")

        # Volume (15%)
        attempts = player_stats['3pa_per_game']
        if attempts >= 6:
            score += 15
            flags.append(f"High volume shooter ({attempts:.1f} 3PA/game)")
        elif attempts >= 4:
            score += 10
            flags.append(f"Moderate volume ({attempts:.1f} 3PA/game)")
        elif attempts >= 2:
            score += 5
        else:
            flags.append(f"Low volume shooter ({attempts:.1f} 3PA/game)")

        # Consistency (10%)
        variance = np.std(player_stats['last_10_3pm'])
        if variance < 1.5:
            score += 10
            flags.append(f"Consistent shooter (variance: {variance:.1f})")
        elif variance < 2.5:
            score += 5
        else:
            flags.append(f"Inconsistent (variance: {variance:.1f})")

        # Injury adjustment (10%)
        injured_defenders = []
        for injury in injuries:
            if injury.get('status') == 'OUT':
                player_name = injury.get('athlete', {}).get('displayName', '')
                if opponent_team_abbrev in self.perimeter_defenders:
                    if player_name in self.perimeter_defenders[opponent_team_abbrev]:
                        score += 10
                        injured_defenders.append(player_name)

        if injured_defenders:
            flags.append(f"Key defender(s) OUT: {', '.join(injured_defenders)}")

        return min(int(score), 100), flags

    def get_confidence_tier(self, score):
        if score >= 70:
            return "HIGH"
        elif score >= 50:
            return "MEDIUM"
        else:
            return "LOW"