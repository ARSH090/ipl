import json
import os
from typing import Dict, List
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from the root .env file BEFORE importing local modules
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up the AI cache in the background to avoid blocking startup
    import asyncio
    from services.engine_service import engine_service
    
    async def warm_cache():
        hard_filters = ["is_overseas", "is_batsman", "is_bowler", "is_wicket_keeper"]
        print(f"Background warming AI cache for {len(hard_filters)} attributes...")
        for attr in hard_filters:
            try:
                # Run sync generation in a thread pool to avoid blocking event loop
                await asyncio.to_thread(engine_service.generator.generate_question, attr)
            except Exception as e:
                print(f"Warming error for {attr}: {e}")
        print("AI Cache warming complete.")

    asyncio.create_task(warm_cache())
    yield

app = FastAPI(
    title="IPL Akinator AI API",
    description="Backend API for the IPL AI Akinator game using Bayesian inference and entropy selection.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
# Using a permissive configuration for local development. Adjust for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection managers
class BattleRoomManager:
    """Manage battle room WebSocket connections"""
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, room_code: str, websocket: WebSocket):
        await websocket.accept()
        if room_code not in self.active_connections:
            self.active_connections[room_code] = []
        self.active_connections[room_code].append(websocket)
    
    async def disconnect(self, room_code: str, websocket: WebSocket):
        self.active_connections[room_code].remove(websocket)
        if not self.active_connections[room_code]:
            del self.active_connections[room_code]
    
    async def broadcast_to_room(self, room_code: str, message: dict):
        if room_code in self.active_connections:
            for connection in self.active_connections[room_code]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error sending to WebSocket: {e}")

class LeaderboardManager:
    """Manage leaderboard WebSocket connections"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending to WebSocket: {e}")

battle_room_manager = BattleRoomManager()
leaderboard_manager = LeaderboardManager()

# Mount API router
app.include_router(router, prefix="/api", tags=["Akinator Game"])

@app.get("/")
async def root():
    return {"message": "Welcome to the IPL AI Akinator API. Go to /docs for the Swagger UI."}

# ============================================================
# WEBSOCKET ENDPOINTS
# ============================================================

@app.websocket("/ws/battle/{room_code}")
async def websocket_battle_room(websocket: WebSocket, room_code: str):
    """
    WebSocket endpoint for battle room real-time sync
    
    Events from server:
    - PLAYER_JOINED: {type, guest_username, room_code}
    - QUESTION_READY: {type, question, attribute, question_number}
    - ANSWER_RECEIVED: {type, player_role, message}
    - BOTH_ANSWERED: {type, host_answer, guest_answer, processing}
    - GAME_OVER: {type, host_guess, host_correct, guest_guess, guest_correct, winner, scores}
    - SCORE_UPDATE: {type, host_score, guest_score}
    
    Events from client:
    - SUBMIT_ANSWER: {type, room_code, player_role, answer}
    """
    await battle_room_manager.connect(room_code, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            event_type = message.get("type")
            
            if event_type == "SUBMIT_ANSWER":
                # Broadcast that an answer was received
                player_role = message.get("player_role")
                await battle_room_manager.broadcast_to_room(
                    room_code,
                    {
                        "type": "ANSWER_RECEIVED",
                        "player_role": player_role,
                        "message": f"{player_role} answered"
                    }
                )
            elif event_type == "PLAYER_JOINED":
                await battle_room_manager.broadcast_to_room(
                    room_code,
                    {
                        "type": "PLAYER_JOINED",
                        "guest_username": message.get("guest_username"),
                        "room_code": room_code
                    }
                )
            elif event_type == "NEXT_QUESTION":
                # Send the next question to both players
                await battle_room_manager.broadcast_to_room(
                    room_code,
                    {
                        "type": "QUESTION_READY",
                        "question": message.get("question", "Is the player a batsman?"),
                        "attribute": message.get("attribute", "role"),
                        "question_number": message.get("question_number", 1)
                    }
                )
            elif event_type == "GAME_OVER":
                # Send game over to both players
                await battle_room_manager.broadcast_to_room(
                    room_code,
                    {
                        "type": "GAME_OVER",
                        "winner": message.get("winner"),
                        "host_guess": message.get("host_guess"),
                        "host_score": message.get("host_score"),
                        "guest_score": message.get("guest_score")
                    }
                )
            
            # Echo back to sender for confirmation
            await websocket.send_json({"status": "received", "event": event_type})
    
    except WebSocketDisconnect:
        await battle_room_manager.disconnect(room_code, websocket)
        await battle_room_manager.broadcast_to_room(
            room_code,
            {"type": "PLAYER_DISCONNECTED", "message": "A player disconnected"}
        )

@app.websocket("/ws/leaderboard")
async def websocket_leaderboard(websocket: WebSocket):
    """
    WebSocket endpoint for live leaderboard updates
    
    Server sends updates whenever leaderboard changes:
    - {type: "LEADERBOARD_UPDATE", leaderboard: [...]}
    - {type: "SCORE_UPDATE", username, new_score, new_rank}
    """
    await leaderboard_manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive and receive any client messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Could implement client-side filters here
            # For now, just acknowledge
            await websocket.send_json({"status": "acknowledged"})
    
    except WebSocketDisconnect:
        await leaderboard_manager.disconnect(websocket)
