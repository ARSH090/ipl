"""
XAI Explainer - Explainable AI for guess reasoning
Show why AI guessed a particular player
"""
from typing import Dict, List, Any, Optional
import json
from supabase_client import supabase

class XAIExplainer:
    """Generates human-readable explanations for AI guesses"""
    
    # Friendly attribute names for display
    ATTRIBUTE_DISPLAY_NAMES = {
        "captain": "Team Captain",
        "overseas": "Overseas Player",
        "finisher": "Finishing Batsman",
        "opener": "Opening Batsman",
        "death_bowler": "Death Bowler",
        "spinner": "Spinner",
        "pace_bowler": "Pace Bowler",
        "left_handed": "Left-Handed",
        "wicket_keeper": "Wicketkeeper",
        "csk_player": "CSK Association",
        "mi_player": "Mumbai Indians Player",
        "rcb_player": "RCB Player",
        "kkr_player": "KKR Player",
        "srh_player": "SRH Player",
        "dc_player": "DC Player",
        "rr_player": "Rajasthan Royals",
        "pbks_player": "PBKS Player",
        "gt_player": "GT Player",
        "lsg_player": "LSG Player",
        "centuries": "Has International Centuries",
        "world_cup_player": "World Cup Player",
        "retired": "Retired",
        "under_25": "Under 25 Years",
        "over_35": "Over 35 Years",
        "high_strike_rate": "High Strike Rate (>130)",
        "economy_under_7": "Economy Under 7",
        "batting_avg_over_40": "Batting Average > 40",
        "wickets_over_100": "Wickets > 100",
        "played_before_2015": "Played Before 2015",
        "ipl_champion": "IPL Champion",
        "orange_cap": "Orange Cap Winner",
        "purple_cap": "Purple Cap Winner"
    }
    
    @staticmethod
    def explain_guess(
        session_id: str,
        guessed_player_name: str,
        correct: bool,
        actual_player: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate XAI explanation for a guess
        
        Args:
            session_id: Session ID
            guessed_player_name: Player name AI guessed
            correct: Whether guess was correct
            actual_player: Correct player if AI was wrong
        
        Returns:
            {
                player: str,
                correct: bool,
                reasons: [{factor, weight, contribution}, ...],
                top_factors: [list of top 3-4 factors],
                surprise_factor: bool (if guess was unexpected)
            }
        """
        # Get session from Supabase to access answer_log
        try:
            response = supabase.table("game_sessions").select(
                "*"
            ).eq("session_id", session_id).execute()
            session = response.data[0] if response.data else None
        except Exception as e:
            print(f"Error fetching session: {e}")
            return XAIExplainer._fallback_explanation(guessed_player_name, correct)
        
        if not session:
            return XAIExplainer._fallback_explanation(guessed_player_name, correct)
        
        answer_log = session.get("answer_log", []) or []
        
        # Get player data
        try:
            player_response = supabase.table("players").select(
                "*"
            ).eq("name", guessed_player_name).execute()
            player = player_response.data[0] if player_response.data else None
        except Exception as e:
            print(f"Error fetching player: {e}")
            return XAIExplainer._fallback_explanation(guessed_player_name, correct)
        
        if not player:
            return XAIExplainer._fallback_explanation(guessed_player_name, correct)
        
        # Extract factors that match the guess
        reasons = []
        
        for entry in answer_log:
            attribute = entry.get("attribute", "")
            answer = entry.get("answer", "").lower()
            
            if attribute in player:
                player_has = player.get(attribute, False)
                user_said_yes = answer in ["yes", "true"]
                
                # Calculate weight (simplified - in production use proper Bayesian weights)
                if player_has == user_said_yes:
                    weight = 0.25 + (0.05 * (len(answer_log) - answer_log.index(entry)))
                else:
                    weight = -0.15
                
                if abs(weight) > 0.05:  # Filter out negligible factors
                    display_name = XAIExplainer.ATTRIBUTE_DISPLAY_NAMES.get(
                        attribute, attribute
                    )
                    reasons.append({
                        "factor": display_name,
                        "attribute": attribute,
                        "weight": round(weight, 3),
                        "player_has": player_has,
                        "user_said": user_said_yes
                    })
        
        # Sort by weight descending
        reasons.sort(key=lambda x: x["weight"], reverse=True)
        
        # Get top reasons
        top_factors = reasons[:4]
        
        # Determine surprise factor (if guess seems off-type)
        surprise_factor = len(top_factors) < 2 or (
            top_factors and abs(top_factors[0]["weight"]) < 0.15
        )
        
        return {
            "player": guessed_player_name,
            "correct": correct,
            "actual_player": actual_player,
            "reasons": top_factors,
            "total_confidence_factors": len(reasons),
            "surprise_factor": surprise_factor,
            "message": XAIExplainer._get_message(correct, guessed_player_name, actual_player)
        }
    
    @staticmethod
    def _get_message(correct: bool, guess: str, actual: Optional[str] = None) -> str:
        """Generate message based on outcome"""
        if correct:
            return f"✅ I guessed {guess}! Got you!"
        else:
            return f"❌ I thought it was {guess}, but it was actually {actual or 'someone else'}. You fooled me!"
    
    @staticmethod
    def _fallback_explanation(player_name: str, correct: bool) -> Dict[str, Any]:
        """Fallback explanation when data unavailable"""
        return {
            "player": player_name,
            "correct": correct,
            "reasons": [],
            "message": "I guessed " + player_name + ("!" if correct else ", but seems I was wrong!")
        }
    
    @staticmethod
    def explain_wrong_guess(
        session_id: str,
        guessed_player_name: str,
        correct_player_name: str
    ) -> Dict[str, Any]:
        """
        Special explanation when AI guessed wrong
        
        Args:
            session_id: Session ID
            guessed_player_name: What AI guessed
            correct_player_name: What it actually was
        
        Returns:
            Detailed explanation
        """
        explanation = XAIExplainer.explain_guess(
            session_id,
            guessed_player_name,
            correct=False,
            actual_player=correct_player_name
        )
        
        # Add learning message
        explanation["learning_message"] = (
            f"🧠 I'm learning from this mistake! I'll update my understanding "
            f"that those attributes typically belong to {correct_player_name}."
        )
        
        return explanation

# Singleton instance
xai_explainer = XAIExplainer()

__all__ = ["XAIExplainer", "xai_explainer"]
