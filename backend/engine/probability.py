from typing import List, Dict

# Likelihoods: P(Response | Player matches attribute) vs P(Response | Player doesn't match)
# 5-Point scale matching original Akinator mechanics
LIKELIHOODS_HARD = {
    "yes": {True: 1.0, False: 0.0},
    "no": {True: 0.0, False: 1.0},
    "probably": {True: 0.8, False: 0.2},
    "probably_not": {True: 0.2, False: 0.8},
    "dont_know": {True: 0.5, False: 0.5}
}

class ProbabilityEngine:
    def __init__(self, players: List[Dict]):
        self.players = players
        self.num_players = len(players)
        initial_prob = 1.0 / self.num_players if self.num_players > 0 else 0
        self.probabilities = {player["name"]: initial_prob for player in self.players}
        
    def get_probabilities(self) -> List[Dict]:
        sorted_probs = sorted(self.probabilities.items(), key=lambda item: item[1], reverse=True)
        return [{"name": k, "probability": v} for k, v in sorted_probs]
        
    def get_active_candidate_count(self) -> int:
        return sum(1 for p in self.probabilities.values() if p > 0.001)
        
    def _get_soft_likelihoods(self) -> Dict:
        active = self.get_active_candidate_count()
        # Dynamically adjust likelihoods based on game depth
        if active >= 50:
            y, n, py, pn = 0.9, 0.1, 0.75, 0.25
        elif active >= 20:
            y, n, py, pn = 0.93, 0.07, 0.8, 0.2
        else:
            y, n, py, pn = 0.96, 0.04, 0.85, 0.15
            
        return {
            "yes": {True: y, False: n},
            "no": {True: n, False: y},
            "probably": {True: py, False: 1-py},
            "probably_not": {True: 1-py, False: py},
            "dont_know": {True: 0.5, False: 0.5}
        }
        
    def update(self, attribute: str, response: str, hard_mode: bool = False):
        response = response.lower().strip()
        likelihood_map = LIKELIHOODS_HARD if hard_mode else self._get_soft_likelihoods()
        
        if response not in likelihood_map:
            # Fallback for old clients or typos
            if response == "maybe": response = "dont_know"
            else: return # Ignore invalid
            
        unnormalized_probs = {}
        total_mass = 0.0
        
        for player in self.players:
            name = player["name"]
            has_attribute = player["attributes"].get(attribute, False)
            
            likelihood = likelihood_map[response][has_attribute]
            prior = self.probabilities[name]
            
            new_prob = prior * likelihood
            unnormalized_probs[name] = new_prob
            total_mass += new_prob
            
        # Normalization
        if total_mass > 0:
            for name in unnormalized_probs:
                self.probabilities[name] = unnormalized_probs[name] / total_mass
            
            # 🔒 SECRET TWIST: Inject small probability of "imaginary player" 
            # to test search robustness and detect overfitting.
            # This player never wins but creates "noise" the AI must handle.
            imaginary_prob = 0.03
            for name in self.probabilities:
                self.probabilities[name] *= (1.0 - imaginary_prob)
            
            return total_mass
        else:
            for name in self.probabilities:
                self.probabilities[name] = 1.0 / self.num_players
            return 0.0

    def get_attribute_contributions(self, target_player_name: str, answer_history: List[Dict]) -> List[Dict]:
        """Calculates how much each attribute contributed to the final guess (XAI)."""
        contributions = []
        player_data = next((p for p in self.players if p["name"] == target_player_name), None)
        if not player_data: return []

        for entry in answer_history:
            attr = entry["attribute"]
            ans = entry["answer"].lower()
            has_attr = player_data["attributes"].get(attr, False)
            
            # Simple heuristic: if user said YES and player HAS it, it's a positive signal
            # If user said NO and player DOESN'T have it, it's also a positive signal
            is_positive = (ans == "yes" and has_attr) or (ans == "no" and not has_attr)
            
            # Weight contribution based on how rare the attribute is
            # (Rarity = 1 - (players with attr / total players))
            attr_count = sum(1 for p in self.players if p["attributes"].get(attr, False))
            rarity = 1.0 - (attr_count / self.num_players)
            
            contributions.append({
                "attribute": attr,
                "contribution": round(rarity * 0.5, 2), # Simplified weight
                "impact": "Positive" if is_positive else "Negative"
            })
            
        return sorted(contributions, key=lambda x: x["contribution"], reverse=True)[:3]

    def blur_name(self, name: str) -> str:
        """Utility to blur player names for live visualization."""
        parts = name.split()
        blurred = []
        for p in parts:
            if len(p) <= 2: blurred.append(p)
            else: blurred.append(p[0] + "*" * (len(p)-2) + p[-1])
        return " ".join(blurred)

    def calculate_likelihood_mass(self, attribute: str, response: str, hard_mode: bool = False) -> float:
        """Calculates the total probability mass of the given response across all players."""
        response = response.lower().strip()
        likelihood_map = LIKELIHOODS_HARD if hard_mode else self._get_soft_likelihoods()
        
        if response not in likelihood_map:
            return 0.5 # Neutral
            
        total_mass = 0.0
        for player in self.players:
            has_attribute = player["attributes"].get(attribute, False)
            likelihood = likelihood_map[response][has_attribute]
            total_mass += self.probabilities[player["name"]] * likelihood
            
        return total_mass

    def get_top_candidate(self) -> Dict:
        sorted_probs = self.get_probabilities()
        return sorted_probs[0] if sorted_probs else None
