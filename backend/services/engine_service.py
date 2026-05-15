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
        question_text = self.generator.generate_question(
            attribute=best_attr, 
            value="Yes", 
            history="None", 
            count=len(self.players)
        )
        banter = self.generator.generate_banter(0.0, len(self.players), 0)
        
        return best_attr, banter

    def process_answer(self, state: SessionState, answer: str) -> None:
        if not state.last_attribute: return
            
        engine = self._get_probability_engine(state)
        # Use hard filtering for first 3 questions to narrow pool fast
        is_hard_mode = state.question_count < 3 or engine.get_active_candidate_count() >= 100
        
        engine.update(state.last_attribute, answer, hard_mode=is_hard_mode)
        
        state.answer_history.append({"attribute": state.last_attribute, "answer": answer})
            
        state.probabilities = engine.probabilities.copy()
        state.asked_questions.append(state.last_attribute)
        state.question_count += 1

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
        
        history_str = ", ".join([h['attribute'] for h in state.answer_history]) if state.answer_history else "None"
        return self.generator.generate_question(
            attribute=last_attr, 
            value="Yes", 
            history=history_str, 
            count=engine.get_active_candidate_count()
        )
        
    def get_next_action(self, state: SessionState) -> Tuple[str, str, float, int, bool, str]:
        """
        Returns: (type, text, confidence, remaining_candidates, is_disambiguation, banter)
        """
        engine = self._get_probability_engine(state)
        probs = engine.get_probabilities()
        
        if not probs: return ("guess", "Unknown", 0.0, 0, False, "I'm stumped!")
            
        top1 = probs[0]
        top2 = probs[1] if len(probs) > 1 else {"probability": 0}
        
        t1_p = top1['probability']
        t2_p = top2['probability']
        confidence = t1_p / (t1_p + t2_p + 1e-9)
        active_count = engine.get_active_candidate_count()
        
        state.top_two_candidates = [top1['name'], top2['name']] if len(probs) > 1 else [top1['name']]

        # 1. Win Condition
        if confidence >= 0.85 and state.question_count >= 4:
            player_data = next((p for p in self.players if p["name"] == top1['name']), {})
            tribute = self.generator.generate_tribute(top1['name'], player_data)
            return ("guess", top1['name'], confidence, active_count, False, tribute)
            
        # 2. Max Question Limit
        max_q = state.max_questions if hasattr(state, 'max_questions') and state.max_questions else 8
        if state.question_count >= max_q:
            state.disambiguation_mode = True
            question_text = self.generator.generate_disambiguation(top1['name'])
            banter = self.generator.generate_banter(confidence, active_count, state.question_count)
            return ("question", question_text, confidence, active_count, True, banter)
            
        # 3. Normal Question Selection
        selector = self._get_selector(state, engine)
        best_attr = selector.get_best_attribute()
        
        if not best_attr:
            player_data = next((p for p in self.players if p["name"] == top1['name']), {})
            tribute = self.generator.generate_tribute(top1['name'], player_data)
            return ("guess", top1['name'], confidence, active_count, False, tribute)
            
        state.last_attribute = best_attr
        history_str = ", ".join([h['attribute'] for h in state.answer_history]) if state.answer_history else "None"
        question_text = self.generator.generate_question(
            attribute=best_attr, 
            value="Yes", 
            history=history_str, 
            count=active_count
        )
        banter = self.generator.generate_banter(confidence, active_count, state.question_count)
        
        return ("question", question_text, confidence, active_count, False, banter)

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
