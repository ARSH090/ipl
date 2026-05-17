"""
Battle Service V2 - Professional Real-time Multiplayer Quiz Engine
Handles synchronized rounds, 30s timers, and advanced scoring logic.
"""
import random
import string
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from supabase_client import supabase

class BattleService:
    """Manages synchronized real-time battle rooms with quiz logic"""
    
    ROOM_TABLE = "battle_rooms"
    QUESTION_TABLE = "battle_questions"
    ANSWER_TABLE = "battle_answers"
    ROUND_LIMIT = 10
    TIMER_SECONDS = 30
    
    @staticmethod
    def _generate_room_code(length: int = 6) -> str:
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

    @staticmethod
    def create_room(host_username: str) -> Dict[str, Any]:
        """Create room and pre-select 10 random questions"""
        room_code = BattleService._generate_room_code()
        
        try:
            # 1. Fetch all question IDs to pick random ones
            questions_resp = supabase.table(BattleService.QUESTION_TABLE).select("id").execute()
            all_ids = [q["id"] for q in questions_resp.data] if questions_resp.data else []
            
            if len(all_ids) < BattleService.ROUND_LIMIT:
                # If not enough questions, just take what we have
                selected_ids = all_ids
                random.shuffle(selected_ids)
            else:
                selected_ids = random.sample(all_ids, BattleService.ROUND_LIMIT)
            
            if not selected_ids:
                raise ValueError("No questions found in database. Please seed the battle_questions table.")
                
            room_data = {
                "room_code": room_code,
                "host_username": host_username,
                "status": "waiting",
                "current_round": 0,
                "total_rounds": len(selected_ids),
                "question_ids": selected_ids,
                "host_score": 0,
                "guest_score": 0,
                "host_streak": 0,
                "guest_streak": 0
            }
            
            response = supabase.table(BattleService.ROOM_TABLE).insert(room_data).execute()
            return response.data[0] if response.data else room_data
        except Exception as e:
            print(f"Error creating room: {e}")
            raise

    @staticmethod
    def get_room(room_code: str) -> Optional[Dict[str, Any]]:
        response = supabase.table(BattleService.ROOM_TABLE).select("*").eq("room_code", room_code).execute()
        return response.data[0] if response.data else None

    @staticmethod
    def join_room(room_code: str, guest_username: str) -> Dict[str, Any]:
        """Join room and trigger start countdown"""
        room = BattleService.get_room(room_code)
        if not room:
            raise ValueError("Room not found")
        if room.get("status") != "waiting":
            raise ValueError("Room is already full or in progress")

        # Start game countdown
        updates = {
            "guest_username": guest_username,
            "status": "countdown",
            "current_round": 1,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        response = supabase.table(BattleService.ROOM_TABLE).update(updates).eq("room_code", room_code).execute()
        return response.data[0] if response.data else {}

    @staticmethod
    def start_round(room_code: str) -> Dict[str, Any]:
        """Starts the timer for the current round"""
        room = BattleService.get_room(room_code)
        if not room: return {}
        
        # If already active, don't reset the timer
        if room.get("status") == "active" and room.get("round_start_at"):
            return room
        
        updates = {
            "status": "active",
            "round_start_at": datetime.now(timezone.utc).isoformat(),
            "host_last_answer": None,
            "guest_last_answer": None,
            "host_answer_time": None,
            "guest_answer_time": None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        response = supabase.table(BattleService.ROOM_TABLE).update(updates).eq("room_code", room_code).execute()
        return response.data[0] if response.data else {}

    @staticmethod
    def submit_answer(room_code: str, player_role: str, answer: str) -> Dict[str, Any]:
        """
        Validate answer and calculate score server-side based on server-side timing.
        """
        room = BattleService.get_room(room_code)
        if not room or room["status"] != "active":
            return {"error": "Room not active"}

        # Check if already answered
        if player_role == "host" and room.get("host_last_answer"): return room
        if player_role == "guest" and room.get("guest_last_answer"): return room

        # Calculate time taken based on server clock
        start_time = datetime.fromisoformat(room["round_start_at"].replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        time_diff = (now - start_time).total_seconds()
        
        # 30s limit
        time_left = max(0, BattleService.TIMER_SECONDS - time_diff)
        
        # Get current question
        q_ids = room.get("question_ids", [])
        current_idx = room["current_round"] - 1
        if current_idx >= len(q_ids): return room
        
        q_id = q_ids[current_idx]
        q_resp = supabase.table(BattleService.QUESTION_TABLE).select("*").eq("id", q_id).execute()
        question = q_resp.data[0] if q_resp.data else None
        if not question: return room

        is_correct = (answer == question["correct_answer"])
        
        # Advanced Scoring
        points_earned = 0
        streak_update = room.get(f"{player_role}_streak", 0)
        
        if is_correct:
            base_points = question.get("points", 100)
            # Speed bonus: max 50 points
            speed_bonus = int((time_left / BattleService.TIMER_SECONDS) * 50)
            # Streak bonus
            streak_bonus = min(50, streak_update * 10)
            
            points_earned = base_points + speed_bonus + streak_bonus
            streak_update += 1
        else:
            streak_update = 0

        # Update room state
        updates = {
            f"{player_role}_last_answer": answer,
            f"{player_role}_answer_time": time_left,
            f"{player_role}_score": room.get(f"{player_role}_score", 0) + points_earned,
            f"{player_role}_last_points": points_earned,
            f"{player_role}_streak": streak_update,
            "updated_at": now.isoformat()
        }

        # Check if both have now answered
        other_role = "guest" if player_role == "host" else "host"
        if room.get(f"{other_role}_last_answer"):
            updates["status"] = "round_result"

        # Log to battle_answers
        try:
            supabase.table(BattleService.ANSWER_TABLE).insert({
                "room_id": room["id"],
                "player_username": room[f"{player_role}_username"],
                "round_number": room["current_round"],
                "question_id": q_id,
                "selected_answer": answer,
                "is_correct": is_correct,
                "points_earned": points_earned,
                "time_taken": time_diff
            }).execute()
        except Exception as e:
            print(f"Error logging answer: {e}")

        response = supabase.table(BattleService.ROOM_TABLE).update(updates).eq("room_code", room_code).execute()
        return response.data[0] if response.data else {}

    @staticmethod
    def next_round(room_code: str) -> Dict[str, Any]:
        """Advance round counter or finish game"""
        room = BattleService.get_room(room_code)
        if not room: return {}
        
        next_r = room["current_round"] + 1
        if next_r > room["total_rounds"]:
            # End game
            winner = "draw"
            if room["host_score"] > room["guest_score"]: 
                winner = room["host_username"]
            elif room["guest_score"] > room["host_score"]: 
                winner = room["guest_username"]
            
            updates = {
                "status": "finished",
                "winner_username": winner,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        else:
            updates = {
                "status": "active",
                "current_round": next_r,
                "round_start_at": datetime.now(timezone.utc).isoformat(),
                "host_last_answer": None,
                "guest_last_answer": None,
                "host_answer_time": None,
                "guest_answer_time": None,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
        response = supabase.table(BattleService.ROOM_TABLE).update(updates).eq("room_code", room_code).execute()
        return response.data[0] if response.data else {}

    @staticmethod
    def get_current_question(room_code: str) -> Optional[Dict[str, Any]]:
        room = BattleService.get_room(room_code)
        if not room or not room.get("question_ids"): return None
        
        idx = room["current_round"] - 1
        if idx < 0 or idx >= len(room["question_ids"]): return None
        
        q_id = room["question_ids"][idx]
        response = supabase.table(BattleService.QUESTION_TABLE).select("*").eq("id", q_id).execute()
        return response.data[0] if response.data else None

# Singleton instance
battle_service = BattleService()
__all__ = ["BattleService", "battle_service"]
