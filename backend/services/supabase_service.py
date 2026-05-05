import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

try:
    from supabase import create_client, Client
except ImportError:
    # Fallback if library not installed yet
    Client = Any

class SupabaseService:
    def __init__(self):
        self.url: str = os.environ.get("SUPABASE_URL", "")
        self.key: str = os.environ.get("SUPABASE_KEY", "")
        self.client: Optional[Client] = None
        
        if self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
            except Exception as e:
                print(f"Failed to initialize Supabase client: {e}")

    async def upsert_score_live(self, player_name: str, player_id: str, score: int, question_count: int, trick_bonus: int, result: str = "PLAYING"):
        if not self.client: return
        try:
            data = {
                "player_name": player_name,
                "player_id": player_id,
                "score": score,
                "question_count": question_count,
                "trick_bonus": trick_bonus,
                "result": result
            }
            # UPSERT based on player_id to keep the record live
            self.client.table("leaderboard").upsert(data, on_conflict="player_id").execute()
        except Exception as e:
            print(f"Supabase Realtime Upsert Error: {e}")

    async def submit_score(self, player_name: str, player_id: str, score: int, result: str):
        if not self.client:
            print("Supabase client not initialized. Skipping submission.")
            return False
            
        try:
            data = {
                "player_name": player_name,
                "player_id": player_id,
                "score": score,
                "result": result,
                "created_at": datetime.utcnow().isoformat()
            }
            self.client.table("leaderboard").insert(data).execute()
            return True
        except Exception as e:
            print(f"Error submitting score to Supabase: {e}")
            return False

    async def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.client:
            print("Supabase client not initialized. Returning empty leaderboard.")
            return []
            
        try:
            response = self.client.table("leaderboard") \
                .select("*") \
                .order("score", desc=True) \
                .limit(limit) \
                .execute()
            return response.data
        except Exception as e:
            print(f"Error fetching leaderboard from Supabase: {e}")
            return []

    async def get_recent_games(self, limit: int = 10) -> List[str]:
        if not self.client: return []
        try:
            response = self.client.table("leaderboard") \
                .select("player_name") \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            return [r['player_name'] for r in response.data]
        except Exception as e:
            print(f"Error fetching recent games: {e}")
            return []

    async def submit_learning_sample(self, player_name: str, answer_history: List[Dict]):
        if not self.client: return
        try:
            pattern = {entry["attribute"]: entry["answer"] for entry in answer_history}
            self.client.table('learning_samples').insert({
                "player_name": player_name,
                "pattern": pattern
            }).execute()
        except Exception as e:
            print(f"Supabase learning error: {e}")

# Singleton instance
supabase_service = SupabaseService()
