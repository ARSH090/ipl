from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Optional
import uuid
from api.models import (
    SessionState, StartRequest, StartResponse, AnswerRequest, 
    NextQuestionResponse, GuessResponse, FeedbackRequest, SubmitScoreRequest,
    TopPlayer, XAIExplanation
)
from services.engine_service import EngineService
from services.supabase_service import SupabaseService

router = APIRouter()
engine_service = EngineService()
supabase_service = SupabaseService()

# In-memory session storage (In production, use Redis)
sessions: Dict[str, SessionState] = {}

@router.post("/start", response_model=StartResponse)
async def start_game(request: StartRequest):
    session_id = str(uuid.uuid4())
    player_id = str(uuid.uuid4())[:6]
    
    state = SessionState(
        session_id=session_id,
        player_name=request.player_name,
        player_id=player_id,
        probabilities={},
        game_mode=request.game_mode,
        max_questions=request.max_questions or 8
    )
    
    engine = engine_service._get_probability_engine(state)
    state.probabilities = engine.probabilities
    sessions[session_id] = state
    
    # Get first action
    # Returns: (type, text, confidence, remaining_candidates, is_disambiguation, banter, top_players)
    action_type, text, confidence, remaining, is_disamb, banter, _ = engine_service.get_next_action(state)
    
    return StartResponse(
        session_id=session_id,
        player_id=player_id,
        player_name=request.player_name,
        question=text,
        attribute=state.last_attribute or "initial",
        confidence=confidence,
        remaining_candidates=remaining,
        banter=banter,
        max_questions=state.max_questions
    )

@router.post("/submit_answer", response_model=NextQuestionResponse)
async def submit_answer(request: AnswerRequest):
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = sessions[request.session_id]
    engine_service.process_answer(state, request.answer)
    
    # ⚡ REAL-TIME SCORE SYNC: Push update to Supabase immediately
    await supabase_service.upsert_score_live(
        player_name=state.player_name,
        player_id=state.player_id,
        score=state.final_score,
        question_count=state.question_count,
        trick_bonus=state.trick_bonus,
        result="PLAYING"
    )
    
    action_type, text, confidence, remaining, is_disamb, banter, top_players = engine_service.get_next_action(state)
    
    # Convert top_players to model
    top_players_models = [TopPlayer(name=p["name"], probability=p["probability"]) for p in top_players]

    if action_type == "guess":
        # Check for Trick bonus message
        if state.inconsistency_score > 3.0:
            banter = f"You tried to mislead me 😏... But I found him! {banter}"
            
        return NextQuestionResponse(
            question=text, 
            attribute="guess",
            confidence=confidence,
            remaining_candidates=remaining,
            is_disambiguation=False,
            banter=banter,
            current_score=state.final_score,
            top_players=top_players_models
        )
    
    return NextQuestionResponse(
        question=text,
        attribute=state.last_attribute or "",
        confidence=confidence,
        remaining_candidates=remaining,
        is_disambiguation=is_disamb,
        banter=banter,
        current_score=state.final_score,
        top_players=top_players_models
    )

@router.post("/submit_back", response_model=NextQuestionResponse)
async def submit_back(request: Dict[str, str]):
    session_id = request.get("session_id")
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = sessions[session_id]
    engine_service.revert_state(state)
    
    action_type, text, confidence, remaining, is_disamb, banter, top_players = engine_service.get_next_action(state)
    top_players_models = [TopPlayer(name=p["name"], probability=p["probability"]) for p in top_players]

    return NextQuestionResponse(
        question=text,
        attribute=state.last_attribute or "",
        confidence=confidence,
        remaining_candidates=remaining,
        is_disambiguation=is_disamb,
        banter="Let's try that again...",
        current_score=state.final_score,
        top_players=top_players_models
    )

@router.post("/submit_feedback")
async def submit_feedback(request: FeedbackRequest):
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    state = sessions[request.session_id]
    
    # 🧠 SELF-LEARNING MEMORY: Store incorrect pattern if AI failed
    if not request.was_correct:
        try:
            await supabase_service.submit_learning_sample(
                player_name=request.correct_player,
                answer_history=state.answer_history
            )
        except Exception as e:
            print(f"Learning storage failed: {e}")

    # Generate XAI Explanation
    explanation_data = engine_service.get_explanation(state, request.correct_player)
    explanation = [XAIExplanation(**ex) for ex in explanation_data]
    
    if not request.was_correct:
        state.final_score += 200
        
    return {
        "status": "success", 
        "new_score": state.final_score,
        "explanation": explanation
    }

@router.post("/submit_score")
async def submit_score(request: SubmitScoreRequest):
    if request.session_id in sessions:
        state = sessions[request.session_id]
        return await supabase_service.upsert_score_live(
            player_name=request.player_name,
            player_id=request.player_id,
            score=request.score,
            question_count=state.question_count,
            trick_bonus=state.trick_bonus,
            result=request.result
        )
    return await supabase_service.submit_score(
        player_name=request.player_name,
        player_id=request.player_id,
        score=request.score,
        result=request.result
    )

@router.get("/leaderboard")
async def get_leaderboard():
    return await supabase_service.get_leaderboard()

@router.get("/recent_games")
async def get_recent_games():
    return await supabase_service.get_recent_games()
