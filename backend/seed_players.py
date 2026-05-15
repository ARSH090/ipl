"""
Seed Players into Supabase Database
One-time script to migrate players.json into Supabase players table

Usage: python seed_players.py
"""
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from supabase_client import supabase

def load_players_json():
    """Load players from players.json"""
    players_path = Path(__file__).parent / "data" / "players.json"
    if not players_path.exists():
        print(f"Error: {players_path} not found")
        sys.exit(1)
    
    with open(players_path, "r") as f:
        return json.load(f)

def seed_players():
    """Seed players into Supabase"""
    players = load_players_json()
    
    print(f"Loading {len(players)} players from players.json...")
    
    total = len(players)
    success = 0
    failed = 0
    
    for idx, player in enumerate(players, 1):
        try:
            # Ensure all boolean fields default to False
            player_data = {
                "name": player.get("name", ""),
                "team": player.get("team"),
                "role": player.get("role"),
                **{
                    key: player.get(key, False)
                    for key in [
                        "overseas", "captain", "finisher", "opener",
                        "death_bowler", "spinner", "pace_bowler", "left_handed",
                        "wicket_keeper", "csk_player", "mi_player", "rcb_player",
                        "kkr_player", "srh_player", "dc_player", "rr_player",
                        "pbks_player", "gt_player", "lsg_player", "centuries",
                        "world_cup_player", "retired", "under_25", "over_35",
                        "high_strike_rate", "economy_under_7", "batting_avg_over_40",
                        "wickets_over_100", "played_before_2015", "ipl_champion",
                        "orange_cap", "purple_cap"
                    ]
                }
            }
            
            response = supabase.table("players").insert(player_data).execute()
            success += 1
            if idx % 25 == 0:
                print(f"  ✓ Inserted {idx}/{total} players...")
        
        except Exception as e:
            failed += 1
            print(f"  ✗ Failed to insert {player.get('name', 'Unknown')}: {str(e)}")
    
    print(f"\n✓ Seeding complete!")
    print(f"  Success: {success}/{total}")
    print(f"  Failed:  {failed}/{total}")
    
    if failed == 0:
        print("\n✅ All players seeded successfully!")
    else:
        print(f"\n⚠️  {failed} players failed to seed")

if __name__ == "__main__":
    try:
        seed_players()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
