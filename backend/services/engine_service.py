import json
import os
import datetime
from typing import Tuple, List, Dict, Any, Optional

from api.models import SessionState
from engine.probability import ProbabilityEngine
from engine.selector import QuestionSelector
from engine.prompts import QuestionGenerator

class EngineService:
    def __init__(self):
        self.generator = QuestionGenerator()
        self.players = self._load_dataset()
        self.all_attributes = list(self.players[0]["attributes"].keys()) if self.players else []
        self.feedback_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'feedback.json')
        self.max_questions_map = {"8": 8, "20": 20}
        
    def _load_dataset(self) -> List[Dict[str, Any]]:
        data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'players.json')
        try:
            with open(data_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading dataset: {e}")
            return []

    def _get_probability_engine(self, state: SessionState) -> ProbabilityEngine:
        engine = ProbabilityEngine(self.players)
        if state.probabilities:
            engine.probabilities = state.probabilities.copy()
        return engine

    def _get_selector(self, state: SessionState, prob_engine: ProbabilityEngine) -> QuestionSelector:
        selector = QuestionSelector(prob_engine, self.all_attributes)
        selector.asked_attributes = set(state.asked_questions)
        # Convert history list to dict for the selector
        selector.answered_attributes = {item["attribute"]: (item["answer"] == "yes") for item in state.answer_history if item["answer"] in ["yes", "no"]}
        return selector

    def initialize_state(self, state: SessionState) -> Tuple[str, str]:
        """Initializes state and returns the first attribute and banter."""
        engine = self._get_probability_engine(state)
        state.probabilities = engine.probabilities.copy()
        
        selector = self._get_selector(state, engine)
        best_attr = selector.get_best_attribute(use_heuristic=False)
        
        state.last_attribute = best_attr
        question_text = self.generator.generate_question(best_attr)
        banter = self.generator.generate_banter(0.0, len(self.players), 0)
        
        return best_attr, banter

    def process_answer(self, state: SessionState, answer: str) -> None:
        if not state.last_attribute: return
            
        engine = self._get_probability_engine(state)
        # Use hard filtering for first 3 questions to narrow pool fast
        is_hard_mode = state.question_count < 3 or engine.get_active_candidate_count() >= 100
        
        # Track inconsistency before updating
        mass = engine.calculate_likelihood_mass(state.last_attribute, answer, hard_mode=is_hard_mode)
        if mass < 0.1 and answer in ["yes", "no"]:
            state.inconsistency_score += (0.1 - mass) * 20
            
        engine.update(state.last_attribute, answer, hard_mode=is_hard_mode)
        
        state.answer_history.append({"attribute": state.last_attribute, "answer": answer})
            
        state.probabilities = engine.probabilities.copy()
        state.asked_questions.append(state.last_attribute)
        state.question_count += 1
        
        # Update current score
        state.final_score = self.calculate_current_score(state)

    def calculate_current_score(self, state: SessionState) -> int:
        """
        Formula: (question_count * 10) + (wrong_guess_attempts * 50) + trick_bonus
        trick_bonus is derived from inconsistency_score if AI is struggling.
        """
        base_score = state.question_count * 10
        penalty_score = state.wrong_guess_attempts * 50
        
        # If inconsistency is high, it means the user is successfully "tricking" the AI's search path
        trick_bonus = int(state.inconsistency_score * 20)
        state.trick_bonus = trick_bonus
        
        return base_score + penalty_score + trick_bonus

    def revert_state(self, state: SessionState) -> Optional[str]:
        if not state.answer_history:
            return None
            
        # Pop the last entry
        last_entry = state.answer_history.pop()
        last_attr = last_entry["attribute"]
        
        # Pop from asked_questions too
        if state.asked_questions and state.asked_questions[-1] == last_attr:
            state.asked_questions.pop()
            
        # Re-calculate probabilities from scratch
        engine = ProbabilityEngine(self.players)
        for entry in state.answer_history:
            # Re-apply all previous answers
            # Use same logic as process_answer (hard mode for first 3 or many players)
            # This is slightly simplified but should be consistent
            is_hard = len(state.answer_history) < 3 or engine.get_active_candidate_count() >= 100
            engine.update(entry["attribute"], entry["answer"], hard_mode=is_hard)
            
        state.probabilities = engine.probabilities.copy()
        state.question_count -= 1
        state.last_attribute = last_attr
        state.disambiguation_mode = False
        return self.generator.generate_question(last_attr)
        
    def get_personality_phrasing(self, attribute: str) -> str:
        """Transforms robotic attributes into conversational expert phrasing."""
        phrasings = {
            "batsman": "Does your player shine more with the bat than the ball?",
            "bowler": "Is he primarily known for his variations and pace on the pitch?",
            "wicketkeeper": "Would I find him standing right behind the stumps?",
            "all_rounder": "Is he one of those rare gems who can do it all for the team?",
            "csk_player": "Has he ever donned the famous yellow jersey of Chennai?",
            "mi_player": "Does he call the Wankhede Stadium his true home?",
            "captain": "Is he a leader of men, often seen making the big calls?",
            "legend": "Is he considered one of the all-time greats of the tournament?",
            "overseas": "Did he have to travel across the oceans to play in the IPL?",
        }
        # Fallback to template
        return phrasings.get(attribute, f"Tell me, is your player related to {attribute.replace('_', ' ')}?")

    def get_dynamic_reaction(self, confidence: float, remaining: int) -> str:
        """Dynamic expert reactions based on AI confidence."""
        if remaining > 200: return "Interesting... a vast field to search. Let's start narrow."
        if remaining < 10: return "I'm zeroing in... I can almost see the player now!"
        if confidence > 0.7: return "The pieces are falling into place... narrowing it down!"
        if confidence < 0.2: return "You're keeping me on my toes! A tricky one indeed..."
        return "Hmm... interesting choice. Let's keep digging."

    def get_next_action(self, state: SessionState) -> Tuple[str, str, float, int, bool, str, List[Dict]]:
        """
        Returns: (type, text, confidence, remaining_candidates, is_disambiguation, banter, top_players)
        """
        engine = self._get_probability_engine(state)
        probs = engine.get_probabilities()
        
        if not probs: return ("guess", "Unknown", 0.0, 0, False, "I'm stumped!", [])
            
        top1 = probs[0]
        top2 = probs[1] if len(probs) > 1 else {"probability": 0}
        
        t1_p = top1['probability']
        t2_p = top2['probability']
        confidence = t1_p / (t1_p + t2_p + 1e-9)
        active_count = engine.get_active_candidate_count()
        
        state.top_two_candidates = [top1['name'], top2['name']] if len(probs) > 1 else [top1['name']]

        # Live Visualization Data (Top 3 blurred)
        top_viz = []
        for p in probs[:3]:
            top_viz.append({
                "name": engine.blur_name(p["name"]),
                "probability": round(p["probability"] * 100, 1)
            })

        # 1. Win Condition
        if confidence >= 0.85 and state.question_count >= 4:
            player_data = next((p for p in self.players if p["name"] == top1['name']), {})
            tribute = self.generator.generate_tribute(top1['name'], player_data)
            return ("guess", top1['name'], confidence, active_count, False, tribute, top_viz)
            
        # 2. Max Question Limit / Disambiguation
        max_q = state.max_questions or 8
        if state.question_count >= max_q:
            # If we already asked a disambiguation question (count > max_q), force a guess
            if state.question_count > max_q:
                 player_data = next((p for p in self.players if p["name"] == top1['name']), {})
                 tribute = self.generator.generate_tribute(top1['name'], player_data)
                 return ("guess", top1['name'], confidence, active_count, False, tribute, top_viz)
            
            state.disambiguation_mode = True
            question_text = self.generator.generate_disambiguation(top1['name'])
            banter = self.get_dynamic_reaction(confidence, active_count)
            return ("question", question_text, confidence, active_count, True, banter, top_viz)
            
        # 3. Normal Question Selection
        selector = self._get_selector(state, engine)
        best_attr = selector.get_best_attribute()
        
        if not best_attr:
            player_data = next((p for p in self.players if p["name"] == top1['name']), {})
            tribute = self.generator.generate_tribute(top1['name'], player_data)
            return ("guess", top1['name'], confidence, active_count, False, tribute, top_viz)
            
        state.last_attribute = best_attr
        question_text = self.get_personality_phrasing(best_attr)
        banter = self.get_dynamic_reaction(confidence, active_count)
        
        return ("question", question_text, confidence, active_count, False, banter, top_viz)

    def get_explanation(self, state: SessionState, player_name: str) -> List[Dict]:
        """XAI Layer: Explain the guess."""
        engine = self._get_probability_engine(state)
        return engine.get_attribute_contributions(player_name, state.answer_history)

    def record_feedback(self, correct_player: str, was_correct: bool, session_id: str):
        """Reinforcement layer: Record feedback to improve future weighting."""
        feedback_entry = {
            "session_id": session_id,
            "correct_player": correct_player,
            "was_correct": was_correct,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        try:
            data = []
            if os.path.exists(self.feedback_path):
                with open(self.feedback_path, 'r') as f:
                    data = json.load(f)
            data.append(feedback_entry)
            # Keep only last 50 for performance
            data = data[-50:]
            with open(self.feedback_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error recording feedback: {e}")

    def get_recent_games(self, limit: int = 10) -> List[str]:
        try:
            if not os.path.exists(self.feedback_path):
                return []
            with open(self.feedback_path, 'r') as f:
                data = json.load(f)
            # Get names of players guessed/corrected
            recent = []
            for entry in reversed(data):
                player = entry.get("correct_player")
                if player and player not in recent:
                    recent.append(player)
                if len(recent) >= limit:
                    break
            return recent
        except Exception as e:
            print(f"Error getting recent games: {e}")
            return []

engine_service = EngineService()
