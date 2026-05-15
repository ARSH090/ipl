import os
from datetime import datetime
from supabase_client import supabase

def seed_leaderboard():
    dummy_data = [
        {
            "username": "Virat_Fan_18",
            "avatar_emoji": "🏏",
            "total_score": 1250,
            "games_played": 15,
            "games_won": 12,
            "ai_guessed": 8,
            "trick_count": 2,
            "badges": ["AI Slayer", "IPL Expert"],
            "best_survival": 12,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "username": "MSD_Thala",
            "avatar_emoji": "🦁",
            "total_score": 980,
            "games_played": 10,
            "games_won": 9,
            "ai_guessed": 5,
            "trick_count": 0,
            "badges": ["Quick Thinker", "Survivor"],
            "best_survival": 15,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "username": "Hitman_45",
            "avatar_emoji": "⚔️",
            "total_score": 850,
            "games_played": 12,
            "games_won": 7,
            "ai_guessed": 10,
            "trick_count": 5,
            "badges": ["Master Manipulator"],
            "best_survival": 8,
            "created_at": datetime.utcnow().isoformat()
        }
    ]

    try:
        # Check if table exists and has data
        response = supabase.table("leaderboard").select("count").execute()
        
        print("Seeding leaderboard...")
        for player in dummy_data:
            supabase.table("leaderboard").upsert(player, on_conflict="username").execute()
        print("Leaderboard seeded successfully!")
    except Exception as e:
        print(f"Error seeding leaderboard: {e}")

if __name__ == "__main__":
    seed_leaderboard()
