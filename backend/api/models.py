from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class TopPlayer(BaseModel):
    name: str # Blurred name for frontend
    probability: float

class XAIExplanation(BaseModel):
    attribute: str
    contribution: float
    impact: str # "Positive" or "Negative"

class SessionState(BaseModel):
    session_id: str
    player_name: str = "Anonymous"
    player_id: str = ""
    probabilities: Dict[str, float]
    asked_questions: List[str] = Field(default_factory=list)
    question_count: int = 0
    wrong_guess_attempts: int = 0
    inconsistency_score: float = 0.0
    trick_bonus: int = 0
    final_score: int = 0
    stage: str = "HARD_FILTER" # HARD_FILTER or PROBABILISTIC
    last_attribute: Optional[str] = None
    answer_history: List[Dict[str, str]] = Field(default_factory=list) # List of {"attribute": attr, "answer": ans}
    disambiguation_mode: bool = False
    top_two_candidates: List[str] = Field(default_factory=list)
    max_questions: int = 8
    game_mode: str = "SINGLE" # SINGLE, VS_AI, VS_PLAYER
    vs_session_id: Optional[str] = None

class StartRequest(BaseModel):
    player_name: str
    max_questions: Optional[int] = 8
    game_mode: str = "SINGLE"

class StartResponse(BaseModel):
    session_id: str
    player_id: str
    player_name: str
    question: str
    attribute: str
    confidence: float
    remaining_candidates: int
    banter: Optional[str] = None
    max_questions: int = 8

class AnswerRequest(BaseModel):
    session_id: str
    answer: str # yes, no, dont_know, probably, probably_not

class NextQuestionResponse(BaseModel):
    question: str
    attribute: str
    confidence: float
    remaining_candidates: int
    is_disambiguation: bool = False
    banter: Optional[str] = None
    current_score: int = 0
    top_players: List[TopPlayer] = Field(default_factory=list)

class GuessResponse(BaseModel):
    guess: str
    confidence: float
    banter: Optional[str] = None
    final_score: int = 0
    is_correct: Optional[bool] = None
    explanation: List[XAIExplanation] = Field(default_factory=list)

class FeedbackRequest(BaseModel):
    session_id: str
    correct_player: str
    was_correct: bool
    final_score: Optional[int] = None

class SubmitScoreRequest(BaseModel):
    session_id: str
    player_name: str
    player_id: str
    score: int
    result: str # "AI Won" or "User Won"

class LeaderboardEntry(BaseModel):
    player_name: str
    score: int
    result: str
    created_at: str

class StateResponse(BaseModel):
    top_candidates: List[Dict[str, Any]]
    question_count: int
    asked_questions: List[str]
    disambiguation_mode: bool
    score_data: Dict[str, Any]
