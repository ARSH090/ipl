import os
from typing import Optional, Dict
from google import genai
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env'))

# Dictionary fallback for all schema.json attributes
FALLBACK_QUESTIONS = {
    "is_overseas": "Is your player an overseas (non-Indian) player?",
    "is_batsman": "Is your player primarily known as a batsman?",
    "is_bowler": "Is your player primarily known as a bowler?",
    "is_all_rounder": "Is your player considered an all-rounder?",
    "is_wicket_keeper": "Does your player keep wickets?",
    "is_right_handed_batsman": "Is your player a right-handed batsman?",
    "is_left_handed_batsman": "Is your player a left-handed batsman?",
    "is_fast_bowler": "Is your player a fast/pace bowler?",
    "is_spin_bowler": "Is your player a spin bowler?",
    "has_won_orange_cap": "Has your player ever won the Orange Cap (most runs in a season)?",
    "has_won_purple_cap": "Has your player ever won the Purple Cap (most wickets in a season)?",
    "has_won_ipl_title": "Has your player ever won an IPL title?",
    "has_scored_century": "Has your player scored a century in the IPL?",
    "has_taken_5_wicket_haul": "Has your player ever taken a 5-wicket haul in the IPL?",
    "has_taken_hat_trick": "Has your player ever taken a hat-trick in the IPL?",
    "has_captained": "Has your player ever captained an IPL franchise?",
    "has_played_internationally": "Has your player played international cricket for their country?",
    "played_for_csk": "Has your player ever played for the Chennai Super Kings (CSK)?",
    "played_for_mi": "Has your player ever played for the Mumbai Indians (MI)?",
    "played_for_rcb": "Has your player ever played for the Royal Challengers Bangalore (RCB)?",
    "played_for_kkr": "Has your player ever played for the Kolkata Knight Riders (KKR)?",
    "played_for_srh": "Has your player ever played for the Sunrisers Hyderabad (SRH) or Deccan Chargers?",
    "played_for_rr": "Has your player ever played for the Rajasthan Royals (RR)?",
    "played_for_dc": "Has your player ever played for the Delhi Capitals (DC) or Daredevils?",
    "played_for_pbks": "Has your player ever played for the Punjab Kings (PBKS) or Kings XI Punjab?",
    "played_for_gt": "Has your player ever played for the Gujarat Titans (GT)?",
    "played_for_lsg": "Has your player ever played for the Lucknow Super Giants (LSG)?",
    "is_australian": "Is your player from Australia?",
    "is_english": "Is your player from England?",
    "is_south_african": "Is your player from South Africa?",
    "is_west_indian": "Is your player from the West Indies?",
    "is_currently_active": "Is your player currently active in the IPL?",
    "is_uncapped": "Is your player an uncapped player (never played international cricket)?"
}

class QuestionGenerator:
    def __init__(self):
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    # Class-level cache to persist across instances in the same process
    _global_question_cache: Dict[str, str] = {}
    _global_banter_cache: Dict[str, str] = {}
    _global_tribute_cache: Dict[str, str] = {}

    def __init__(self):
        self.gemini_key = os.environ.get("GEMINI_API_KEY")
        self.openrouter_key = os.environ.get("OPENROUTER_API_KEY")
        
        # Auto-detect if GEMINI_API_KEY is actually an OpenRouter key
        if self.gemini_key and self.gemini_key.startswith("sk-or-v1-"):
            if not self.openrouter_key:
                self.openrouter_key = self.gemini_key
            self.gemini_key = None

        if self.openrouter_key:
            try:
                self.client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.openrouter_key,
                    timeout=3.0 # Reduced timeout for faster fallback
                )
                self.model_name = "google/gemini-2.0-flash-001"
                self.mode = "openrouter"
            except Exception as e:
                print(f"Error initializing OpenRouter client: {e}")
                self.client = None
                self.mode = "fallback"
        elif self.gemini_key:
            try:
                self.client = genai.Client(api_key=self.gemini_key)
                self.model_name = 'gemini-2.0-flash' # Upgraded to 2.0
                self.mode = "gemini"
            except Exception as e:
                print(f"Error initializing Gemini client: {e}")
                self.client = None
                self.mode = "fallback"
        else:
            self.client = None
            self.mode = "fallback"

    def generate_question(self, attribute: str, value: str = "Yes", history: str = "None", count: int = 0) -> str:
        # Check global cache first
        if attribute in self._global_question_cache:
            return self._global_question_cache[attribute]
            
        fallback_q = FALLBACK_QUESTIONS.get(attribute, f"Does your player have the attribute: {attribute}?")
        if not self.client or self.mode == "fallback": 
            return fallback_q
            
        try:
            prompt = f"""You are the conversational engine for an IPL Akinator AI system.
Transform this attribute into ONE natural, engaging IPL-themed yes/no question.
RULES: MAX 12 words. NO EMOJIS. NO MARKDOWN.
ATTRIBUTE: {attribute}
STYLE: Energetic IPL commentary tone."""
            
            q = fallback_q
            if self.mode == "openrouter":
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=50
                )
                if response.choices:
                    q = response.choices[0].message.content.strip().strip('"')
            elif self.mode == "gemini":
                response = self.client.models.generate_content(model=self.model_name, contents=prompt)
                if response and response.text:
                    q = response.text.strip().strip('"')
            
            # Store in global cache
            self._global_question_cache[attribute] = q
            return q
        except Exception as e:
            print(f"AI Generation error ({self.mode}): {e}")
            return fallback_q

    def generate_banter(self, confidence: float, remaining: int, question_count: int) -> str:
        # Key for banter cache based on rounded confidence and remaining range
        cache_key = f"{round(confidence, 1)}_{remaining // 10}_{question_count // 5}"
        if cache_key in self._global_banter_cache:
            return self._global_banter_cache[cache_key]
            
        if not self.client or self.mode == "fallback": 
            return "The chase is on!"
        
        try:
            prompt = f"You are a witty IPL commentator. Confidence: {confidence*100}%, Candidates left: {remaining}, Round: {question_count}. Give a 1-sentence witty remark."
            
            banter = "The chase is on!"
            if self.mode == "openrouter":
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=60
                )
                if response.choices:
                    banter = response.choices[0].message.content.strip().strip('"')
            elif self.mode == "gemini":
                response = self.client.models.generate_content(model=self.model_name, contents=prompt)
                if response and response.text:
                    banter = response.text.strip().strip('"')
            
            self._global_banter_cache[cache_key] = banter
            return banter
        except:
            return "The bowler is running in!"

    def generate_tribute(self, player_name: str, player_data: Dict) -> str:
        if player_name in self._global_tribute_cache:
            return self._global_tribute_cache[player_name]
            
        if not self.client or self.mode == "fallback": 
            return f"{player_name} is an IPL legend."
        
        try:
            prompt = f"Create a 1-sentence epic tribute for IPL player {player_name}. Focus on their impact and legacy. Keep it punchy."
            
            tribute = f"{player_name} is an IPL legend."
            if self.mode == "openrouter":
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=60
                )
                if response.choices:
                    tribute = response.choices[0].message.content.strip().strip('"')
            elif self.mode == "gemini":
                response = self.client.models.generate_content(model=self.model_name, contents=prompt)
                if response and response.text:
                    tribute = response.text.strip().strip('"')
            
            self._global_tribute_cache[player_name] = tribute
            return tribute
        except:
            return f"An indispensable part of IPL history."

    def generate_disambiguation(self, top_candidate_name: str) -> str:
        return f"Is your player {top_candidate_name}?"
