"""
Leaderboard Service - Manage player rankings and scores
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from supabase_client import supabase

class LeaderboardService:
    """Manages leaderboard and user scores"""
    
    TABLE_NAME = "leaderboard"
    
    @staticmethod
    def get_or_create_user(username: str, avatar_emoji: str = "🏏") -> Dict[str, Any]:
        """
        Get existing user or create new one
        
        Args:
            username: Unique username
            avatar_emoji: Player's avatar emoji (default cricket bat)
        
        Returns:
            User dict
        """
        # Try to get existing user
        response = supabase.table(LeaderboardService.TABLE_NAME).select(
            "*"
        ).eq("username", username).execute()
        
        if response.data:
            return response.data[0]
        
        # Create new user
        user_data = {
            "username": username,
            "avatar_emoji": avatar_emoji,
            "total_score": 0,
            "games_played": 0,
            "games_won": 0,
            "ai_guessed": 0,
            "trick_count": 0,
            "badges": [],
            "best_survival": 0
        }
        
        response = supabase.table(LeaderboardService.TABLE_NAME).insert(
            user_data
        ).execute()
        
        return response.data[0] if response.data else user_data
    
    @staticmethod
    def update_score(
        username: str,
        score_delta: int,
        game_won: bool = False,
        ai_guessed_count_delta: int = 0,
        trick_count_delta: int = 0,
        badges_to_add: List[str] = None,
        best_survival_update: int = 0
    ) -> Dict[str, Any]:
        """
        Update user score and stats
        
        Args:
            username: Username
            score_delta: Points to add (can be negative)
            game_won: Whether user won this game
            ai_guessed_count_delta: Increment AI guessed correct count
            trick_count_delta: Increment trick count
            badges_to_add: List of badge names to add
            best_survival_update: Update best_survival if greater
        
        Returns:
            Updated user dict
        """
        user = LeaderboardService.get_or_create_user(username)
        
        new_total_score = max(0, user.get("total_score", 0) + score_delta)
        new_games_played = user.get("games_played", 0) + 1
        new_games_won = user.get("games_won", 0) + (1 if game_won else 0)
        new_ai_guessed = user.get("ai_guessed", 0) + ai_guessed_count_delta
        new_trick_count = user.get("trick_count", 0) + trick_count_delta
        
        # Update badges
        existing_badges = set(user.get("badges", []) or [])
        if badges_to_add:
            existing_badges.update(badges_to_add)
        new_badges = list(existing_badges)
        
        # Update best survival
        new_best_survival = user.get("best_survival", 0)
        if best_survival_update > new_best_survival:
            new_best_survival = best_survival_update
        
        update_data = {
            "total_score": new_total_score,
            "games_played": new_games_played,
            "games_won": new_games_won,
            "ai_guessed": new_ai_guessed,
            "trick_count": new_trick_count,
            "badges": new_badges,
            "best_survival": new_best_survival,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        response = supabase.table(LeaderboardService.TABLE_NAME).update(
            update_data
        ).eq("username", username).execute()
        
        return response.data[0] if response.data else update_data
    
    @staticmethod
    def get_top_leaderboard(limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top N players by score
        
        Args:
            limit: Number of top players to return
        
        Returns:
            List of top players
        """
        response = supabase.table(LeaderboardService.TABLE_NAME).select(
            "*"
        ).order("total_score", desc=True).limit(limit).execute()
        
        return response.data or []
    
    @staticmethod
    def get_user_rank(username: str) -> int:
        """
        Get user's rank on leaderboard
        
        Args:
            username: Username
        
        Returns:
            Rank (1-indexed)
        """
        user = LeaderboardService.get_or_create_user(username)
        user_score = user.get("total_score", 0)
        
        response = supabase.table(LeaderboardService.TABLE_NAME).select(
            "total_score"
        ).gt("total_score", user_score).execute()
        
        # Rank = (count of players with higher score) + 1
        return len(response.data) + 1 if response.data else 1
    
    @staticmethod
    def get_user_stats(username: str) -> Dict[str, Any]:
        """
        Get complete user statistics
        
        Args:
            username: Username
        
        Returns:
            User stats dict with rank
        """
        user = LeaderboardService.get_or_create_user(username)
        rank = LeaderboardService.get_user_rank(username)
        
        return {
            **user,
            "rank": rank
        }
    
    @staticmethod
    def add_badge(username: str, badge: str) -> Dict[str, Any]:
        """
        Add badge to user
        
        Args:
            username: Username
            badge: Badge name
        
        Returns:
            Updated user dict
        """
        user = LeaderboardService.get_or_create_user(username)
        badges = set(user.get("badges", []) or [])
        badges.add(badge)
        
        response = supabase.table(LeaderboardService.TABLE_NAME).update(
            {
                "badges": list(badges),
                "updated_at": datetime.utcnow().isoformat()
            }
        ).eq("username", username).execute()
        
        return response.data[0] if response.data else user
    
    @staticmethod
    def reset_all_scores() -> bool:
        """
        Reset all leaderboard data (for testing/reset)
        
        Returns:
            Success status
        """
        try:
            response = supabase.table(LeaderboardService.TABLE_NAME).delete().gt(
                "created_at", "1970-01-01"
            ).execute()
            return True
        except Exception as e:
            print(f"Error resetting leaderboard: {e}")
            return False

# Singleton instance
leaderboard_service = LeaderboardService()

__all__ = ["LeaderboardService", "leaderboard_service"]
