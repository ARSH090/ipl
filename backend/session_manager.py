"""
Session Manager - Supabase Session CRUD
Replaces in-memory session dict with persistent Supabase storage
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from supabase_client import supabase

class SessionManager:
    """Manages game sessions in Supabase"""
    
    TABLE_NAME = "game_sessions"
    
    @staticmethod
    def create_session(
        session_id: Optional[str] = None,
        mode: str = "solo",
        room_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new game session in Supabase
        
        Args:
            session_id: Optional custom session ID (auto-generated if None)
            mode: 'solo' or 'battle'
            room_code: Battle room code if mode is 'battle'
        
        Returns:
            Created session dict
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        session_data = {
            "session_id": session_id,
            "mode": mode,
            "room_code": room_code,
            "status": "active",
            "questions_asked": 0,
            "candidate_probs": {},
            "answer_log": []
        }
        
        response = supabase.table(SessionManager.TABLE_NAME).insert(
            session_data
        ).execute()
        
        return response.data[0] if response.data else session_data
    
    @staticmethod
    def get_session(session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session by ID
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session dict or None if not found
        """
        response = supabase.table(SessionManager.TABLE_NAME).select(
            "*"
        ).eq("session_id", session_id).execute()
        
        return response.data[0] if response.data else None
    
    @staticmethod
    def update_session(session_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update session fields
        
        Args:
            session_id: Session identifier
            updates: Dict of fields to update
        
        Returns:
            Updated session dict
        """
        updates["updated_at"] = datetime.utcnow().isoformat()
        
        response = supabase.table(SessionManager.TABLE_NAME).update(
            updates
        ).eq("session_id", session_id).execute()
        
        return response.data[0] if response.data else {}
    
    @staticmethod
    def save_answer_log(session_id: str, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Append entry to answer_log JSONB array
        
        Args:
            session_id: Session identifier
            entry: Answer entry {question, attribute, answer, timestamp}
        
        Returns:
            Updated session dict
        """
        session = SessionManager.get_session(session_id)
        if not session:
            return {}
        
        answer_log = session.get("answer_log", []) or []
        answer_log.append({
            **entry,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return SessionManager.update_session(
            session_id,
            {
                "answer_log": answer_log,
                "questions_asked": len(answer_log)
            }
        )
    
    @staticmethod
    def update_candidate_probs(
        session_id: str,
        candidate_probs: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Update candidate probability distribution
        
        Args:
            session_id: Session identifier
            candidate_probs: {player_id: probability}
        
        Returns:
            Updated session dict
        """
        return SessionManager.update_session(
            session_id,
            {"candidate_probs": candidate_probs}
        )
    
    @staticmethod
    def close_session(
        session_id: str,
        final_guess: str,
        correct: bool,
        actual_player: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Close session and mark as guessed/failed
        
        Args:
            session_id: Session identifier
            final_guess: AI's final guess
            correct: Whether AI guessed correctly
            actual_player: Actual player if AI was wrong
        
        Returns:
            Updated session dict
        """
        return SessionManager.update_session(
            session_id,
            {
                "status": "guessed" if correct else "failed",
                "final_guess": final_guess,
                "correct": correct,
                "actual_player": actual_player
            }
        )
    
    @staticmethod
    def get_all_sessions_by_mode(mode: str = "solo") -> List[Dict[str, Any]]:
        """
        Get all sessions of a specific mode
        
        Args:
            mode: 'solo' or 'battle'
        
        Returns:
            List of sessions
        """
        response = supabase.table(SessionManager.TABLE_NAME).select(
            "*"
        ).eq("mode", mode).execute()
        
        return response.data or []

# Singleton instance
session_manager = SessionManager()

__all__ = ["SessionManager", "session_manager"]
