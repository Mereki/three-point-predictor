from data_fetcher import NBADataFetcher
import json


def test_api():
    fetcher = NBADataFetcher()

    print("Testing API endpoints...\n")

    # Test with Stephen Curry
    player_id = 201939
    print(f"1. Testing player game log (Player ID: {player_id})...")
    response = fetcher.get_player_game_log(player_id)

    if response:
        print("✓ Success!")
        print(f"   Result sets: {len(response.get('resultSets', []))}")
        if response.get('resultSets'):
            headers = response['resultSets'][0].get('headers', [])
            rows = response['resultSets'][0].get('rowSet', [])
            print(f"   Columns: {len(headers)}")
            print(f"   Games found: {len(rows)}")
            print(f"   Headers: {headers[:5]}...")  # Show first 5 headers
    else:
        print("✗ Failed")
        print("\nTrying alternative season format...")
        response = fetcher.get_player_game_log(player_id, season="2024-25")
        if response:
            print("✓ Success with 2024-25 season!")
        else:
            print("✗ Still failed. NBA Stats API might be down or blocking requests.")

    print("\n" + "=" * 50 + "\n")

    # Test player info
    print(f"2. Testing player info (Player ID: {player_id})...")
    response = fetcher.get_player_info(player_id)

    if response:
        print("✓ Success!")
        if response.get('resultSets'):
            headers = response['resultSets'][0].get('headers', [])
            print(f"   Headers: {headers}")
    else:
        print("✗ Failed")

    print("\n" + "=" * 50 + "\n")

    # Test team defense
    team_id = 1610612757  # Portland
    print(f"3. Testing team defense (Team ID: {team_id})...")
    response = fetcher.get_team_defense_stats(team_id)

    if response:
        print("✓ Success!")
    else:
        print("✗ Failed")

    print("\n" + "=" * 50 + "\n")

    # Test injuries
    print("4. Testing injury data (GSW)...")
    response = fetcher.get_team_injuries('GSW')

    if response and 'injuries' in response:
        print(f"✓ Success! Found {len(response['injuries'])} injuries")
    else:
        print("✗ Failed or no injuries")


if __name__ == "__main__":
    test_api()