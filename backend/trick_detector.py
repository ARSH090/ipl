"""
Trick Detector - Detect inconsistencies and rule violations in answer logs
"""
from typing import Dict, List, Any, Tuple

class TrickDetector:
    """Detects when users are giving inconsistent answers to fool AI"""
    
    # Attribute groups - answers in same group should be compatible
    ATTRIBUTE_GROUPS = {
        "role": ["bowler", "spinner", "pace_bowler", "death_bowler", "batter", "finisher"],
        "age": ["under_25", "over_35"],
        "format": ["ipl_player", "world_cup_player"],
        "team": ["csk_player", "mi_player", "rcb_player", "kkr_player", "srh_player",
                 "dc_player", "rr_player", "pbks_player", "gt_player", "lsg_player"],
    }
    
    # Logical implications: if X is yes, Y must be compatible
    IMPLICATIONS = {
        # If bowler-related, cannot be pure batsman
        "spinner": [("bowler", True), ("pace_bowler", False)],
        "pace_bowler": [("bowler", True), ("spinner", False)],
        "death_bowler": [("bowler", True)],
        
        # If finisher, probably high_strike_rate
        "finisher": [("batsman", True), ("high_strike_rate", True)],
        "opener": [("batsman", True)],
        
        # Age exclusivity
        "under_25": [("over_35", False)],
        "over_35": [("under_25", False)],
        
        # Retired cannot play
        "retired": [("ipl_player", False)],
        
        # If hundreds, batsman
        "centuries": [("batsman", True)],
        
        # Wickets > 100 means bowler
        "wickets_over_100": [("bowler", True)],
        
        # Low economy means bowler
        "economy_under_7": [("bowler", True)],
    }
    
    @staticmethod
    def check_consistency(answer_log: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check for inconsistencies in answer log
        
        Args:
            answer_log: [{attribute, answer, ...}, ...]
        
        Returns:
            {
                is_consistent: bool,
                inconsistency_score: int,
                contradictions: [list of contradictory pairs],
                trick_detected: bool,
                severity: 'low' | 'medium' | 'high'
            }
        """
        answer_dict = {}
        for entry in answer_log:
            attribute = entry.get("attribute")
            answer = entry.get("answer")
            if attribute:
                answer_dict[attribute] = answer.lower() in ["yes", "true", "1"]
        
        contradictions = []
        
        # Check direct contradictions (mutually exclusive attributes)
        for attr_group, attrs in TrickDetector.ATTRIBUTE_GROUPS.items():
            yes_answers = [a for a in attrs if answer_dict.get(a) is True]
            
            # Certain groups allow only one answer
            if attr_group == "age" and len(yes_answers) > 1:
                contradictions.append({
                    "type": "mutual_exclusion",
                    "group": attr_group,
                    "conflicting": yes_answers
                })
        
        # Check implications
        for attribute, implications in TrickDetector.IMPLICATIONS.items():
            if answer_dict.get(attribute) is True:
                for implied_attr, should_be in implications:
                    actual = answer_dict.get(implied_attr)
                    if actual is not None and actual != should_be:
                        contradictions.append({
                            "type": "logical_implication",
                            "violated": attribute,
                            "implies": implied_attr,
                            "expected": should_be,
                            "actual": actual
                        })
        
        inconsistency_score = len(contradictions)
        is_consistent = inconsistency_score == 0
        
        # Determine severity
        severity = "low"
        if inconsistency_score >= 3:
            severity = "high"
        elif inconsistency_score == 2:
            severity = "medium"
        
        trick_detected = inconsistency_score >= 3
        
        return {
            "is_consistent": is_consistent,
            "inconsistency_score": inconsistency_score,
            "contradictions": contradictions,
            "trick_detected": trick_detected,
            "severity": severity
        }
    
    @staticmethod
    def get_contradiction_explanation(contradiction: Dict[str, Any]) -> str:
        """
        Human-readable explanation of a contradiction
        
        Args:
            contradiction: Single contradiction dict
        
        Returns:
            Explanation string
        """
        if contradiction["type"] == "mutual_exclusion":
            return (
                f"You said the player is both "
                f"{' and '.join(contradiction['conflicting'])}, "
                f"but these are mutually exclusive"
            )
        
        elif contradiction["type"] == "logical_implication":
            expected_str = "yes" if contradiction["expected"] else "no"
            actual_str = "yes" if contradiction["actual"] else "no"
            return (
                f"You said {contradiction['violated']} is yes, "
                f"which implies {contradiction['implies']} must be {expected_str}, "
                f"but you said {actual_str}"
            )
        
        return "Unknown contradiction"
    
    @staticmethod
    def summarize_trick_attempt(answer_log: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Summarize a trick attempt for UI display
        
        Args:
            answer_log: Full answer log
        
        Returns:
            Summary dict
        """
        consistency = TrickDetector.check_consistency(answer_log)
        
        summary = {
            "trick_detected": consistency["trick_detected"],
            "severity": consistency["severity"],
            "explanation": None,
            "contradiction_count": consistency["inconsistency_score"]
        }
        
        if consistency["trick_detected"] and consistency["contradictions"]:
            first_contradiction = consistency["contradictions"][0]
            summary["explanation"] = TrickDetector.get_contradiction_explanation(
                first_contradiction
            )
        
        return summary

# Singleton instance
trick_detector = TrickDetector()

__all__ = ["TrickDetector", "trick_detector"]
