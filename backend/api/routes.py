from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Union, Optional, List

from api.models import StartResponse, AnswerRequest, NextQuestionResponse, GuessResponse, StateResponse, FeedbackRequest, StartRequest
from services.session_service import session_service
from services.engine_service import engine_service
from services.telemetry import telemetry_service
from session_manager import session_manager
from leaderboard_service import leaderboard_service
from battle_service import battle_service
from trick_detector import trick_detector
from xai_explainer import xai_explainer
from supabase_client import supabase

router = APIRouter()

@router.post("/start", response_model=StartResponse)
async def start_game(request: Optional[StartRequest] = None):
    max_q = request.max_questions if request else 8
    session = session_service.create_session()
    session.max_questions = max_q
    first_attr, banter = engine_service.initialize_state(session)
    question_text = engine_service.generator.generate_question(first_attr)
    session_service.save_session(session)
    
    return StartResponse(
        session_id=session.session_id,
        question=question_text,
        attribute=first_attr,
        confidence=0.0,
        remaining_candidates=len(engine_service.players),
        banter=banter,
        max_questions=max_q
    )

@router.get("/recent", response_model=List[str])
async def get_recent_games():
    return engine_service.get_recent_games()

@router.post("/answer", response_model=Union[NextQuestionResponse, GuessResponse])
async def answer_question(request: AnswerRequest):
    session = session_service.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    answer = request.answer.lower().strip()
    
    if session.disambiguation_mode:
        guess = session.top_two_candidates[0] if answer == "yes" else (session.top_two_candidates[1] if len(session.top_two_candidates) > 1 else session.top_two_candidates[0])
        # Do not delete session here, let the user confirm/reject
        player_data = next((p for p in engine_service.players if p["name"] == guess), {})
        tribute = engine_service.generator.generate_tribute(guess, player_data)
        return GuessResponse(guess=guess, confidence=1.0, banter=tribute)

    engine_service.process_answer(session, answer)
    action_type, text, confidence, remaining, is_disambiguation, banter = engine_service.get_next_action(session)
    
    if action_type == "guess":
        # Do not delete session yet, keep it for back/correction
        return GuessResponse(guess=text, confidence=confidence, banter=banter)
        
    session_service.save_session(session)
    return NextQuestionResponse(
        question=text,
        attribute=session.last_attribute or "",
        confidence=confidence,
        remaining_candidates=remaining,
        is_disambiguation=is_disambiguation,
        banter=banter
    )

@router.post("/back", response_model=NextQuestionResponse)
async def go_back(request: Request):
    body = await request.json()
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
        
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    question_text = engine_service.revert_state(session)
    if not question_text:
        raise HTTPException(status_code=400, detail="Cannot go back further")
        
    session_service.save_session(session)
    
    # Get current engine metrics for response
    engine = engine_service._get_probability_engine(session)
    probs = engine.get_probabilities()
    top1 = probs[0] if probs else {"probability": 1.0}
    top2 = probs[1] if len(probs) > 1 else {"probability": 0}
    confidence = top1['probability'] / (top1['probability'] + top2['probability'] + 1e-9)
    
    return NextQuestionResponse(
        question=question_text,
        attribute=session.last_attribute or "",
        confidence=confidence,
        remaining_candidates=engine.get_active_candidate_count(),
        is_disambiguation=session.disambiguation_mode,
        banter="Let's try that again..."
    )

@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    engine_service.record_feedback(request.correct_player, request.was_correct, request.session_id)
    return {"status": "success"}

@router.get("/state/{session_id}", response_model=StateResponse)
async def get_state(session_id: str):
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    sorted_probs = sorted(session.probabilities.items(), key=lambda x: x[1], reverse=True)[:5]
    return StateResponse(
        top_candidates=[{"name": k, "probability": v} for k, v in sorted_probs],
        question_count=session.question_count,
        asked_questions=session.asked_questions,
        disambiguation_mode=session.disambiguation_mode
    )

# ============================================================
# NEW SUPABASE ENDPOINTS (Part 2 - Backend)
# ============================================================

@router.post("/session/start")
async def start_supabase_session(body: dict):
    """
    Create a Supabase-backed game session
    
    Body: {username, mode: "solo"|"battle", room_code?: string}
    """
    username = body.get("username", "Anonymous")
    mode = body.get("mode", "solo")
    room_code = body.get("room_code")
    
    # Get or create user on leaderboard
    leaderboard_service.get_or_create_user(username)
    
    # Create Supabase session (Optional, handle missing tables)
    try:
        supabase_session = session_manager.create_session(
            mode=mode,
            room_code=room_code
        )
        sid = supabase_session["session_id"]
    except Exception as e:
        print(f"Supabase error (session create): {e}")
        import uuid
        sid = str(uuid.uuid4())
    
    return {
        "session_id": sid,
        "mode": mode,
        "username": username,
        "status": "active"
    }

@router.get("/leaderboard")
async def get_leaderboard(limit: int = 10):
    """Get top leaderboard"""
    try:
        top_players = leaderboard_service.get_top_leaderboard(limit=limit)
    except Exception as e:
        print(f"Supabase error (leaderboard): {e}")
        return {"leaderboard": []}
    
    return {
        "leaderboard": [
            {
                "rank": idx + 1,
                "username": p["username"],
                "avatar_emoji": p.get("avatar_emoji", "🏏"),
                "total_score": p["total_score"],
                "games_played": p["games_played"],
                "games_won": p["games_won"],
                "badges": p.get("badges", []),
                "best_survival": p.get("best_survival", 0)
            }
            for idx, p in enumerate(top_players)
        ]
    }

@router.get("/leaderboard/user/{username}")
async def get_user_stats(username: str):
    """Get user's leaderboard stats"""
    stats = leaderboard_service.get_user_stats(username)
    return {
        "username": stats["username"],
        "rank": stats["rank"],
        "total_score": stats["total_score"],
        "games_played": stats["games_played"],
        "games_won": stats["games_won"],
        "badges": stats.get("badges", []),
        "best_survival": stats.get("best_survival", 0)
    }

@router.post("/guess/confirm")
async def confirm_guess(body: dict):
    """
    Confirm AI guess and resolve game
    
    Body: {
        session_id: string,
        correct: bool,
        actual_player?: string,
        username: string,
        questions_asked: int,
        trick_detected: bool
    }
    """
    session_id = body.get("session_id")
    correct = body.get("correct", False)
    actual_player = body.get("actual_player")
    username = body.get("username", "Anonymous")
    questions_asked = body.get("questions_asked", 0)
    trick_detected = body.get("trick_detected", False)
    
    final_guess = "Unknown"
    
    # Close Supabase session
    try:
        session = session_manager.get_session(session_id)
        if session:
            final_guess = session.get("final_guess", "Unknown")
            
            session_manager.close_session(
                session_id,
                final_guess=final_guess,
                correct=correct,
                actual_player=actual_player
            )
            
            # Save to learning log if wrong
            if not correct:
                answer_log = session.get("answer_log", [])
                supabase.table("ai_learning_log").insert({
                    "session_id": session_id,
                    "answer_path": answer_log,
                    "wrong_guess": final_guess,
                    "correct_player": actual_player or "Unknown",
                    "confidence_at_guess": session.get("candidate_probs", {}).get(final_guess, 0)
                }).execute()
    except Exception as e:
        print(f"Supabase error (confirm guess): {e}")
    
    # Generate XAI explanation
    xai = xai_explainer.explain_guess(
        session_id,
        final_guess,
        correct=correct,
        actual_player=actual_player
    )
    
    # Calculate score
    if correct:
        # AI won, but player gets points for surviving long enough
        score = max(5, questions_asked * 2)  # Small bonus for longevity
        game_won = False
    else:
        # Player won (AI lost)
        score = 100  # Base: AI lost
        score += max(0, (questions_asked - 5) * 20)  # Bonus for surviving past Q5
        game_won = True
    
    # Add trick bonuses
    if trick_detected:
        score += 25
    
    # Update leaderboard
    badges_to_add = []
    if game_won and not trick_detected:
        badges_to_add.append("AI Slayer")
    if trick_detected:
        badges_to_add.append("Master Manipulator")
    
    leaderboard_service.update_score(
        username,
        score_delta=score,
        game_won=game_won,
        badges_to_add=badges_to_add,
        best_survival_update=questions_asked
    )
    
    return {
        "xai_explanation": xai,
        "score_earned": score,
        "badges_earned": badges_to_add,
        "game_won": game_won
    }

# ============================================================
# BATTLE MODE ENDPOINTS (UPGRADED)
# ============================================================

@router.post("/battle/create")
async def create_battle_room(body: dict):
    """
    Create a multiplayer quiz battle room
    """
    username = body.get("username", "Anonymous")
    
    room = battle_service.create_room(username)
    
    return {
        "room_code": room["room_code"],
        "host_username": room["host_username"],
        "status": "waiting"
    }

@router.post("/battle/join")
async def join_battle_room(body: dict):
    """
    Join a quiz battle room
    """
    room_code = body.get("room_code")
    username = body.get("username", "Anonymous")
    
    try:
        room = battle_service.join_room(room_code, username)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found or not joinable")
    
    return room

@router.get("/battle/room/{room_code}")
async def get_battle_room(room_code: str):
    """Get battle room state"""
    room = battle_service.get_room(room_code)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@router.get("/battle/question/{room_code}")
async def get_battle_question(room_code: str):
    """Fetch current round question details"""
    question = battle_service.get_current_question(room_code)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.post("/battle/answer")
async def submit_battle_answer(body: dict):
    """
    Submit answer in quiz battle mode
    """
    room_code = body.get("room_code")
    player_role = body.get("player_role")
    answer = body.get("answer")
    
    room = battle_service.submit_answer(room_code, player_role, answer)
    if "error" in room:
        raise HTTPException(status_code=400, detail=room["error"])
    return room

@router.post("/battle/start_round")
async def start_battle_round(body: dict):
    """Start the timer for the current round"""
    room_code = body.get("room_code")
    room = battle_service.start_round(room_code)
    return room

@router.post("/battle/next_round")
async def advance_battle_round(body: dict):
    """Move to next round or end game"""
    room_code = body.get("room_code")
    room = battle_service.next_round(room_code)
    return room


# ============================================================
# TRICK DETECTION & XAI ENDPOINTS
# ============================================================

@router.post("/trick/check")
async def check_trick_in_session(body: dict):
    """
    Check if trick detected in session answer log
    
    Body: {session_id}
    """
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return {"is_consistent": True, "inconsistency_score": 0}
        
        answer_log = session.get("answer_log", [])
        consistency_check = trick_detector.check_consistency(answer_log)
        return consistency_check
    except Exception as e:
        print(f"Supabase error (trick check): {e}")
        return {"is_consistent": True, "inconsistency_score": 0}

@router.post("/xai/explain")
async def explain_ai_guess(body: dict):
    """
    Generate XAI explanation for a guess
    
    Body: {session_id, guessed_player, correct, actual_player?}
    """
    session_id = body.get("session_id")
    guessed_player = body.get("guessed_player")
    correct = body.get("correct", False)
    actual_player = body.get("actual_player")
    
    explanation = xai_explainer.explain_guess(
        session_id,
        guessed_player,
        correct=correct,
        actual_player=actual_player
    )
    
    return explanation
