# NBA Three-Point Predictor

A Python application that predicts the number of three-pointers NBA players will make in upcoming games using statistical analysis, opponent defense metrics, and injury data. This is the "public" edition of the three-point predictor.

## Features

- **Player Performance Analysis**: Analyzes recent shooting trends (last 5 and 10 games)
- **Position-Specific Defense**: Accounts for how opposing teams defend different positions
- **Injury Tracking**: Adjusts predictions when elite defenders are out
- **Confidence Scoring**: Provides confidence ratings (High/Medium/Low) for each prediction
- **Today's/Tomorrow's Games**: Automatically scans upcoming games and identifies high-confidence picks
- **Individual Player Search**: Look up predictions for specific players

## Installation

### Prerequisites
- Python 3.7+
- pip

### Setup

1. **Clone the repository** (or download the files)

2. **Install dependencies**:
```bash
pip install nba_api beautifulsoup4 requests pandas numpy
```

3. **Run the application**:
```bash
python main.py
```

## Usage

### Main Menu

When you run the program, you'll see:

```
=== NBA 3PT Prediction Console ===

Options:
  1. Today's games
  2. Tomorrow's games
  3. Search specific player
  4. Quit
```

### Option 1 & 2: Today's/Tomorrow's Games

Automatically analyzes all scheduled games and provides:
- High-confidence picks for the day
- Position-specific defensive matchups
- Recent player performance trends

Example output:
```
HIGH CONFIDENCE PICKS FOR TODAY:

1. Stephen Curry (GSW vs POR)
   Prediction: 5.2 threes | Confidence: 82/100
   Recent avg: 5.4 per game
   Opponent allows: 37.5% from three
```

### Option 3: Search Specific Player

Search for any player by name and specify their opponent:

```
Enter player name: Damian Lillard
Found: Damian Lillard

Enter opponent team abbreviation: LAL

Analyzing Damian Lillard vs LAL...

==================================================
Damian Lillard (PG) vs LAL
==================================================
Prediction: 4.2 threes
Confidence: MEDIUM (65/100)

Key factors:
  Averaging 4.0 3PM last 5 games
  Opponent allows 36.8% to guards (league avg: 36.5%)
  High volume shooter (9.2 3PA/game)
  Consistent shooter (variance: 1.3)

Recent games:
  1/24/2026: 4 threes
  1/22/2026: 5 threes
  1/20/2026: 3 threes
  1/18/2026: 4 threes
  1/16/2026: 4 threes

3PA Stats:
  Season average: 9.2 3PA/game
  Last 10 games: 9.5 3PA/game

LAL Defense:
  vs Guards: 36.8%
  vs Forwards: 36.2%
  vs Centers: 34.5%
  Overall: 36.5%
```

## How It Works

### Prediction Algorithm

#### Step 1: Base Prediction
```python
base_prediction = (last_10_game_average) × (defense_multiplier)

defense_multiplier = (opponent_position_defense) / (league_average)
```

**Example:**
- Player averaged 4.0 threes over last 10 games
- Opponent allows 38% to guards (league avg: 36.5%)
- Defense multiplier = 0.38 / 0.365 = 1.04
- **Base prediction = 4.0 × 1.04 = 4.2 threes**

#### Step 2: Injury Adjustment
If an elite defender is OUT, add **+0.3 threes** to the prediction.

### Confidence Score (0-100)

| Factor | Weight | Description |
|--------|--------|-------------|
| **Recent Performance** | 35% | Average 3PM over last 5 games |
| **Matchup** | 30% | How opponent defends the player's position |
| **Volume** | 15% | 3-point attempts per game (higher = more reliable) |
| **Consistency** | 10% | Variance in recent shooting (lower = more consistent) |
| **Injuries** | 10% | Elite defenders out = easier matchup |

**Confidence Tiers:**
- **HIGH**: 70-100 points (strong indicators align)
- **MEDIUM**: 50-69 points (mixed signals)
- **LOW**: 0-49 points (unfavorable conditions)

### Data Sources

1. **Player Stats**: NBA Stats API via `nba_api` package
   - Game logs (last 10 games)
   - Season averages
   - Player positions

2. **Defense Metrics**: Scraped from [HashtagBasketball](https://hashtagbasketball.com/nba-defense-vs-position)
   - Position-specific 3P% allowed
   - Updated regularly throughout season

3. **Injury Reports**: ESPN API
   - Current injury status
   - Elite defender tracking

## Project Structure

```
three-point-predictor/
├── main.py                          # Main application entry point
├── data_fetcher.py                  # NBA API data retrieval
├── parser.py                        # JSON response parsing
├── predictor.py                     # Prediction algorithm & confidence scoring
├── scrape_position_defense.py      # Web scraping for defense stats
└── README.md                        # This file
```

## Key Classes

### `NBADataFetcher`
Handles all API calls to the NBA Stats API:
- Player game logs
- Team defense statistics
- Rosters and schedules
- Injury reports

### `NBADataParser`
Parses JSON responses into usable data structures:
- Game logs → 3PM/3PA arrays
- Player info → positions
- Scoreboards → today's games

### `ThreePointPredictor`
Core prediction engine:
- Calculates base predictions
- Adjusts for injuries
- Computes confidence scores
- Maps elite defenders by team

### `PositionDefenseScraper`
Web scraper for position-specific defense:
- Scrapes HashtagBasketball defense table
- Caches results for performance
- Maps team abbreviations

## Customization

### Adjust Minimum Volume Threshold

In `main.py`, change the minimum 3PA filter:
```python
# Current: only analyze players with 3+ 3PA/game
if player_stats['3pa_per_game'] < 3.0:
    return None

# More selective (5+ 3PA/game):
if player_stats['3pa_per_game'] < 5.0:
    return None
```

### Modify Confidence Weights

In `predictor.py`, adjust weights in `calculate_confidence()`:
```python
# Recent performance (currently 35%)
recent_score = min((last_5_avg / 5) * 35, 35)

# Matchup (currently 30%)
matchup_bonus = ((opp_3p_allowed - self.league_avg_3p_pct) / self.league_avg_3p_pct) * 30
```

### Add Elite Defenders

In `predictor.py`, update the `elite_defenders` dictionary:
```python
self.elite_defenders = {
    'BOS': ['Jrue Holiday', 'Derrick White'],
    'MIA': ['Bam Adebayo', 'Jimmy Butler'],
    'LAL': ['Anthony Davis'],
    # Add more teams/defenders here
}
```

## Limitations

- **API Rate Limits**: NBA Stats API may throttle requests if you query too frequently
- **Data Lag**: Position defense data from HashtagBasketball may be 1-2 days behind
- **Sample Size**: Early in the season, predictions are less reliable due to limited games
- **Blowouts**: Does not account for garbage time or reduced playing time in lopsided games
- **Starting Status**: Does not filter for starters vs bench players (uses all players on roster)

## Future Improvements

- [ ] Add home/away splits
- [ ] Include back-to-back game fatigue factor
- [ ] Track historical head-to-head matchups
- [ ] Integrate Vegas betting lines for comparison
- [ ] Add rest days analysis
- [ ] Machine learning model for more sophisticated predictions
- [ ] Export predictions to CSV/Excel
- [ ] Web interface for easier access
- [ ] Real-time game tracking and prediction accuracy

## Troubleshooting

### "Could not find player"
- Make sure you're using the player's full name or close variant
- Try partial names (e.g., "Curry" instead of "Stephen Curry")

### "Error fetching games"
- Check your internet connection
- NBA API may be temporarily down (wait and retry)

### "No qualifying shooters found"
- Team may not have volume 3-point shooters (threshold is 3+ 3PA/game)
- Adjust the threshold in `analyze_player()` function

### API Rate Limiting
- Add longer delays between requests in `data_fetcher.py`:
```python
time.sleep(1.0)  # Increase from 0.6 to 1.0 seconds
```

## Contributing

Suggestions and improvements are welcome! Areas of focus:
- Improving prediction accuracy
- Adding new data sources
- Optimizing API usage
- UI/UX enhancements

## License

This project is for educational and personal use. NBA data is property of the NBA.

## Acknowledgments

- [nba_api](https://github.com/swar/nba_api) - Python API client for NBA stats
- [HashtagBasketball](https://hashtagbasketball.com/) - Position defense statistics
- ESPN - Injury report data

---

**Disclaimer**: This tool is for informational and entertainment purposes only. Always gamble responsibly and within your means.
