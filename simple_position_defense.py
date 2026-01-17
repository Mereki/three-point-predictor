class SimplePositionDefense:
    """
    Estimate position-specific defense using team's overall defense
    and league-wide position tendencies
    """

    def __init__(self):
        # League-wide baseline: how different positions shoot from 3
        # These are approximate NBA averages
        self.league_position_baselines = {
            'guard': 0.365,  # Guards shoot league average
            'forward': 0.360,  # Forwards slightly below
            'center': 0.340  # Centers significantly below
        }

        # How much position matters in defense
        # If a team is good at defending 3s overall, they're typically
        # better against all positions, but the splits still exist
        self.position_variance = {
            'guard': 1.0,  # Guards see full team effect
            'forward': 0.95,  # Forwards see 95% of team effect
            'center': 0.85  # Centers less affected (fewer attempts)
        }

    def get_position_defense_stats(self, team_overall_defense):
        """
        Estimate position-specific defense from overall team defense

        Args:
            team_overall_defense: Team's overall 3P% allowed (e.g., 0.350)

        Returns:
            dict with guard/forward/center 3P% allowed
        """

        # Calculate how much better/worse than league average
        league_avg = 0.365
        team_diff = team_overall_defense - league_avg

        # Apply team's defensive quality to each position
        result = {}
        for position in ['guard', 'forward', 'center']:
            baseline = self.league_position_baselines[position]
            variance_factor = self.position_variance[position]

            # Adjust position baseline by team's defensive quality
            adjusted = baseline + (team_diff * variance_factor)

            result[f'{position}_3p_pct_allowed'] = adjusted

        result['opp_3p_pct_allowed'] = team_overall_defense

        return result