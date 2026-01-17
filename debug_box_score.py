from nba_api.stats.endpoints import boxscoretraditionalv2
import json

# Test one of the failing games
game_id = '0022500587'

print(f"Fetching box score for game {game_id}...")
box_score = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)

box_data = box_score.get_dict()

print("\nAvailable result sets:")
for rs in box_data['resultSets']:
    name = rs['name']
    num_rows = len(rs['rowSet'])
    print(f"  - {name}: {num_rows} rows")
    if name == 'TeamStats' or name == 'LineScore':
        print(f"    Headers: {rs['headers']}")
        print(f"    First row: {rs['rowSet'][0] if rs['rowSet'] else 'No data'}")