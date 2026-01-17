from data_fetcher import NBADataFetcher
from predictor import ThreePointPredictor
from parser import NBADataParser
from simple_position_defense import SimplePositionDefense


def analyze_player(fetcher, parser, predictor, pos_def, player_id, player_name, opponent_id, opponent_abbrev):
    """Analyze a single player and return prediction data"""
    try:
        # Get player stats
        game_log_response = fetcher.get_player_game_log(player_id)
        if not game_log_response:
            return None

        player_stats = parser.parse_player_game_log(game_log_response)
        if not player_stats:
            return None

        # Filter: only analyze players with decent 3PT volume
        if player_stats['3pa_per_game'] < 3.0:
            return None

        # Get player position
        player_info_response = fetcher.get_player_info(player_id)
        position = parser.parse_player_info(player_info_response) if player_info_response else 'SG'

        # Get opponent defense - fast and reliable
        defense_response = fetcher.get_team_defense_stats(opponent_id)
        overall_defense = parser.parse_team_defense_stats(defense_response) if defense_response else 0.365

        # Estimate position-specific defense from overall
        opponent_stats = pos_def.get_position_defense_stats(overall_defense)

        # Get injuries
        injury_response = fetcher.get_team_injuries(opponent_abbrev)
        injuries = parser.parse_injuries(injury_response)

        # Calculate prediction
        prediction = predictor.calculate_prediction(player_stats, opponent_stats, position)
        adjusted_prediction, injured_defenders = predictor.adjust_for_injuries(
            prediction, injuries, opponent_abbrev
        )

        confidence_score, flags = predictor.calculate_confidence(
            player_stats, opponent_stats, position, injuries, opponent_abbrev
        )

        confidence_tier = predictor.get_confidence_tier(confidence_score)

        return {
            'name': player_name,
            'position': position,
            'prediction': adjusted_prediction,
            'base_prediction': prediction,
            'confidence_score': confidence_score,
            'confidence_tier': confidence_tier,
            'flags': flags,
            'stats': player_stats,
            'injured_defenders': injured_defenders,
            'opponent_defense': opponent_stats
        }
    except Exception as e:
        print(f"      Error analyzing {player_name}: {e}")
        return None


def main():
    print("=== NBA 3PT Prediction Console ===\n")

    fetcher = NBADataFetcher()
    predictor = ThreePointPredictor()
    parser = NBADataParser()
    pos_def = SimplePositionDefense()

    while True:
        print("\nOptions:")
        print("  1. Today's games")
        print("  2. Tomorrow's games")
        print("  3. Search specific player")
        print("  4. Quit")

        choice = input("\nSelect option (1-4): ").strip()

        if choice == '4':
            break
        elif choice == '3':
            # Original player search functionality
            player_name = input("Enter player name: ").strip()
            player_obj = fetcher.find_player_by_name(player_name)

            if not player_obj:
                print(f"Could not find player: {player_name}")
                continue

            print(f"\nFound: {player_obj['full_name']}")
            opponent_abbrev = input("Enter opponent team abbreviation (e.g., LAL, GSW): ").strip().upper()

            opponent_team = fetcher.find_team_by_abbrev(opponent_abbrev)
            if not opponent_team:
                print(f"Could not find team: {opponent_abbrev}")
                continue

            print(f"\nAnalyzing {player_obj['full_name']} vs {opponent_abbrev}...\n")

            result = analyze_player(
                fetcher, parser, predictor, pos_def,
                player_obj['id'], player_obj['full_name'],
                opponent_team['id'], opponent_abbrev
            )

            if result:
                print(f"{'=' * 60}")
                print(f"{result['name']} ({result['position']}) vs {opponent_abbrev}")
                print(f"{'=' * 60}")
                print(f"Prediction: {result['prediction']} threes")
                if result['prediction'] != result['base_prediction']:
                    print(
                        f"  (Base: {result['base_prediction']}, Injury boost: +{result['prediction'] - result['base_prediction']:.1f})")
                print(f"Confidence: {result['confidence_tier']} ({result['confidence_score']}/100)")

                print(f"\n📊 Key factors:")
                for flag in result['flags']:
                    print(f"  {flag}")

                print(f"\n📈 Recent games:")
                for date, threes in zip(result['stats']['last_5_dates'], result['stats']['last_5_3pm']):
                    print(f"  {date}: {threes} threes")

                print(f"\n📊 3PA Stats:")
                print(f"  Season average: {result['stats']['season_3pa_avg']} 3PA/game")
                print(f"  Last 10 games: {result['stats']['last_10_3pa_avg']} 3PA/game")

                print(f"\n🛡️ {opponent_abbrev} Defense (estimated position splits):")
                print(f"  vs Guards: {result['opponent_defense']['guard_3p_pct_allowed']:.1%}")
                print(f"  vs Forwards: {result['opponent_defense']['forward_3p_pct_allowed']:.1%}")
                print(f"  vs Centers: {result['opponent_defense']['center_3p_pct_allowed']:.1%}")
                print(f"  Overall: {result['opponent_defense']['opp_3p_pct_allowed']:.1%}")
            else:
                print("Could not generate prediction for this player.")

            continue

        # For today's/tomorrow's games - same structure
        days_ahead = 0 if choice == '1' else 1
        day_label = "Today" if choice == '1' else "Tomorrow"

        print(f"\nFetching {day_label.lower()}'s games...")
        scoreboard = fetcher.get_todays_games(days_ahead)

        if not scoreboard:
            print(f"Could not fetch {day_label.lower()}'s games.")
            continue

        games = parser.parse_scoreboard(scoreboard)

        if not games:
            print(f"No games scheduled for {day_label.lower()}.")
            continue

        print(f"\n{day_label}'s Games:")
        print("=" * 60)

        all_predictions = []

        for idx, game in enumerate(games, 1):
            home_team = fetcher.find_team_by_id(game['home_team_id'])
            away_team = fetcher.find_team_by_id(game['visitor_team_id'])

            if not home_team or not away_team:
                continue

            print(f"\n{idx}. {away_team['full_name']} @ {home_team['full_name']}")
            print(f"   Status: {game['status']}")
            print(f"   Analyzing players...")

            # Analyze both teams
            for team, opponent in [(home_team, away_team), (away_team, home_team)]:
                print(f"\n   {team['abbreviation']} shooters:")

                # Get roster
                roster_response = fetcher.get_team_roster(team['id'])
                if not roster_response:
                    print(f"     Could not fetch roster")
                    continue

                player_ids = parser.parse_team_roster(roster_response)

                # Analyze each player
                count = 0
                for player_id in player_ids[:10]:
                    player_obj = next((p for p in fetcher.all_players if p['id'] == player_id), None)
                    if not player_obj:
                        continue

                    result = analyze_player(
                        fetcher, parser, predictor, pos_def,
                        player_id, player_obj['full_name'],
                        opponent['id'], opponent['abbreviation']
                    )

                    if result:
                        result['opponent_abbrev'] = opponent['abbreviation']
                        result['matchup'] = f"{team['abbreviation']} vs {opponent['abbreviation']}"
                        all_predictions.append(result)

                        if result['confidence_tier'] in ['HIGH', 'MEDIUM']:
                            print(f"     ✓ {result['name']}: {result['prediction']} ({result['confidence_tier']})")
                            count += 1

                if count == 0:
                    print(f"     No qualifying shooters found")

        # Show high confidence picks
        print(f"\n{'=' * 60}")
        print(f"HIGH CONFIDENCE PICKS FOR {day_label.upper()}:")
        print(f"{'=' * 60}\n")

        high_conf = [p for p in all_predictions if p['confidence_tier'] == 'HIGH']
        high_conf.sort(key=lambda x: x['confidence_score'], reverse=True)

        if high_conf:
            for i, pick in enumerate(high_conf[:10], 1):
                print(f"{i}. {pick['name']} ({pick['matchup']})")
                print(f"   Prediction: {pick['prediction']} threes | Confidence: {pick['confidence_score']}/100")
                print(f"   Recent avg: {sum(pick['stats']['last_5_3pm']) / 5:.1f} per game")
                print(f"   Opponent allows: {pick['opponent_defense']['opp_3p_pct_allowed']:.1%} from three\n")
        else:
            print("No high confidence picks found.\n")


if __name__ == "__main__":
    main()