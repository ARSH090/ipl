"""
Battle Service - Manage multiplayer battle rooms
"""
import random
import string
from typing import Optional, Dict, Any, List
from datetime import datetime
from supabase_client import supabase

class BattleService:
    """Manages battle room state and operations"""
    
    TABLE_NAME = "battle_rooms"
    
    @staticmethod
    def _generate_room_code(length: int = 6) -> str:
        """Generate random 6-char room code (e.g. "CSK421")"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    
    @staticmethod
    def create_room(
        host_username: str,
        host_session: str
    ) -> Dict[str, Any]:
        """
        Create a new battle room
        
        Args:
            host_username: Username of room creator
            host_session: Session ID of host
        
        Returns:
            Created room dict with room_code
        """
        room_code = BattleService._generate_room_code()
        
        try:
            # Ensure unique room code
            while BattleService.get_room(room_code):
                room_code = BattleService._generate_room_code()
            
            room_data = {
                "room_code": room_code,
                "host_session": host_session,
                "host_username": host_username,
                "status": "waiting",
                "question_number": 0,
                "host_score": 0,
                "guest_score": 0
            }
            
            response = supabase.table(BattleService.TABLE_NAME).insert(
                room_data
            ).execute()
            
            return response.data[0] if response.data else room_data
        except Exception as e:
            print(f"Error creating room: {e}")
            raise ValueError(f"Database error: {e}")
    
    @staticmethod
    def get_room(room_code: str) -> Optional[Dict[str, Any]]:
        """
        Get battle room by code
        
        Args:
            room_code: Room code
        
        Returns:
            Room dict or None
        """
        response = supabase.table(BattleService.TABLE_NAME).select(
            "*"
        ).eq("room_code", room_code).execute()
        
        return response.data[0] if response.data else None
    
    @staticmethod
    def join_room(
        room_code: str,
        guest_username: str,
        guest_session: str
    ) -> Dict[str, Any]:
        """
        Join existing battle room as guest
        
        Args:
            room_code: Room code
            guest_username: Guest username
            guest_session: Guest session ID
        
        Returns:
            Updated room dict
        """
        try:
            # Check if room exists and is 'waiting'
            room_resp = supabase.table(BattleService.TABLE_NAME).select("*").eq("room_code", room_code).execute()
            if not room_resp.data:
                return {} # Room not found
                
            room = room_resp.data[0]
            if room.get("status") != "waiting":
                return {} # Room not available
                
            updates = {
                "guest_session": guest_session,
                "guest_username": guest_username,
                "status": "active",
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = supabase.table(BattleService.TABLE_NAME).update(
                updates
            ).eq("room_code", room_code).execute()
            
            return response.data[0] if response.data else {}
        except Exception as e:
            print(f"Error joining room: {e}")
            return {}
    
    @staticmethod
    def submit_answer(
        room_code: str,
        player_role: str,
        answer: str
    ) -> Dict[str, Any]:
        """
        Submit answer from host or guest
        
        Args:
            room_code: Room code
            player_role: 'host' or 'guest'
            answer: 'yes', 'no', 'maybe', 'dont_know'
        
        Returns:
            Updated room dict
        """
        field = "host_answer" if player_role == "host" else "guest_answer"
        
        response = supabase.table(BattleService.TABLE_NAME).update(
            {field: answer}
        ).eq("room_code", room_code).execute()
        
        return response.data[0] if response.data else {}
    
    @staticmethod
    def set_current_question(
        room_code: str,
        question: str,
        attribute: str
    ) -> Dict[str, Any]:
        """
        Set current question for both players
        
        Args:
            room_code: Room code
            question: Question text
            attribute: Attribute being asked about
        
        Returns:
            Updated room dict
        """
        response = supabase.table(BattleService.TABLE_NAME).update(
            {
                "current_question": question,
                "current_attribute": attribute,
                "host_answer": None,
                "guest_answer": None,
                "question_number": supabase.table(BattleService.TABLE_NAME).select(
                    "question_number"
                ).eq("room_code", room_code).execute().data[0]["question_number"] + 1
                if supabase.table(BattleService.TABLE_NAME).select(
                    "question_number"
                ).eq("room_code", room_code).execute().data else 1
            }
        ).eq("room_code", room_code).execute()
        
        return response.data[0] if response.data else {}
    
    @staticmethod
    def update_scores(
        room_code: str,
        host_score_delta: int = 0,
        guest_score_delta: int = 0
    ) -> Dict[str, Any]:
        """
        Update battle scores
        
        Args:
            room_code: Room code
            host_score_delta: Points to add to host
            guest_score_delta: Points to add to guest
        
        Returns:
            Updated room dict
        """
        room = BattleService.get_room(room_code)
        if not room:
            return {}
        
        new_host_score = room.get("host_score", 0) + host_score_delta
        new_guest_score = room.get("guest_score", 0) + guest_score_delta
        
        response = supabase.table(BattleService.TABLE_NAME).update(
            {
                "host_score": new_host_score,
                "guest_score": new_guest_score
            }
        ).eq("room_code", room_code).execute()
        
        return response.data[0] if response.data else {}
    
    @staticmethod
    def resolve_battle(
        room_code: str,
        host_guess: str,
        host_correct: bool,
        guest_guess: str,
        guest_correct: bool
    ) -> Dict[str, Any]:
        """
        Resolve battle and determine winner
        
        Args:
            room_code: Room code
            host_guess: Host's final guess
            host_correct: Whether host guessed correctly
            guest_guess: Guest's final guess
            guest_correct: Whether guest guessed correctly
        
        Returns:
            Updated room dict with winner
        """
        room = BattleService.get_room(room_code)
        if not room:
            return {}
        
        # Determine winner based on survival + correctness
        # Survival = question_number (how many questions before guessing)
        # Higher survival = better unless you guessed
        
        # For now: if both correct or both wrong, highest score wins
        # If one correct and one wrong, correct one wins
        
        winner = None
        if host_correct and not guest_correct:
            winner = "host"
        elif guest_correct and not host_correct:
            winner = "guest"
        else:
            # Both correct or both wrong - compare scores
            host_score = room.get("host_score", 0)
            guest_score = room.get("guest_score", 0)
            if host_score > guest_score:
                winner = "host"
            elif guest_score > host_score:
                winner = "guest"
            else:
                winner = "draw"
        
        response = supabase.table(BattleService.TABLE_NAME).update(
            {
                "status": "finished",
                "winner": winner,
                "updated_at": datetime.utcnow().isoformat()
            }
        ).eq("room_code", room_code).execute()
        
        return response.data[0] if response.data else {}
    
    @staticmethod
    def get_active_rooms() -> List[Dict[str, Any]]:
        """
        Get all active battle rooms waiting for guests
        
        Returns:
            List of active rooms
        """
        response = supabase.table(BattleService.TABLE_NAME).select(
            "*"
        ).eq("status", "waiting").execute()
        
        return response.data or []
    
    @staticmethod
    def close_room(room_code: str) -> bool:
        """
        Close/delete a battle room
        
        Args:
            room_code: Room code
        
        Returns:
            Success status
        """
        try:
            supabase.table(BattleService.TABLE_NAME).delete().eq(
                "room_code", room_code
            ).execute()
            return True
        except Exception as e:
            print(f"Error closing room {room_code}: {e}")
            return False

# Singleton instance
battle_service = BattleService()

__all__ = ["BattleService", "battle_service"]
