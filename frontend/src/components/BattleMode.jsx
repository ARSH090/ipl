import { useState, useEffect, useRef } from 'react';
import { supabase } from '../lib/supabase';
import '../styles/BattleMode.css';

export default function BattleMode({ username, sessionId, onClose, onGameEnd }) {
  const [screen, setScreen] = useState('lobby'); // lobby, waiting, countdown, active, round_result, finished
  const [roomCode, setRoomCode] = useState('');
  const [joinCode, setJoinCode] = useState('');
  const [roomData, setRoomData] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [myAnswer, setMyAnswer] = useState(null);
  const [timeLeft, setTimeLeft] = useState(30);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [playerRole, setPlayerRole] = useState(null); // 'host' or 'guest'
  const [copied, setCopied] = useState(false);
  
  const timerRef = useRef(null);
  const channelRef = useRef(null);
  const startTimerRef = useRef(null);
  const pollingRef = useRef(null);

  // Clean up all timers and channels when component unmounts
  useEffect(() => {
    return () => {
      if (channelRef.current) supabase.removeChannel(channelRef.current);
      if (pollingRef.current) clearInterval(pollingRef.current);
      if (startTimerRef.current) clearTimeout(startTimerRef.current);
    };
  }, []);

  // --- ROOM MANAGEMENT ---

  const createRoom = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/battle/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username })
      });
      const data = await response.json();
      setRoomCode(data.room_code);
      setPlayerRole('host');
      setScreen('waiting');
      subscribeToRoom(data.room_code);
    } catch (err) {
      setError('Failed to create room');
    } finally {
      setLoading(false);
    }
  };

  const joinRoom = async () => {
    if (!joinCode.trim()) {
      setError('Please enter a room code');
      return;
    }
    setLoading(true);
    try {
      const response = await fetch('/api/battle/join', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_code: joinCode.toUpperCase(),
          username
        })
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Room not found');
      }
      const data = await response.json();
      setRoomCode(data.room_code);
      setPlayerRole('guest');
      setRoomData(data);
      subscribeToRoom(data.room_code);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // --- REALTIME SUBSCRIPTION ---

  const subscribeToRoom = (code) => {
    // Clean up any existing channels and polling intervals
    if (channelRef.current) supabase.removeChannel(channelRef.current);
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }

    // 1. Supabase Realtime Subscription
    console.log(`Subscribing to Realtime channel room:${code}`);
    channelRef.current = supabase
      .channel(`room:${code}`)
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'battle_rooms',
          filter: `room_code=eq.${code}`
        },
        (payload) => {
          console.log('Realtime Update Received:', payload);
          if (payload.new) {
            handleRoomUpdate(payload.new);
          }
        }
      )
      .subscribe((status, err) => {
        console.log(`Realtime room:${code} status changed to:`, status);
        if (err) {
          console.error("Realtime subscription error:", err);
        }
      });

    // 2. High-performance Polling Fallback (runs every 2 seconds to guarantee sync)
    console.log(`Setting up polling fallback for room:${code}`);
    pollingRef.current = setInterval(() => {
      fetchRoomState(code);
    }, 2000);

    // Initial fetch to populate state immediately
    fetchRoomState(code);
  };

  const fetchRoomState = async (code) => {
    const { data, error } = await supabase
      .from('battle_rooms')
      .select('*')
      .eq('room_code', code)
      .single();
    
    if (data) handleRoomUpdate(data);
  };

  const handleRoomUpdate = (newRoom) => {
    setRoomData(newRoom);
    setScreen(newRoom.status);

    // If active, fetch question if needed
    if (newRoom.status === 'active') {
      if (!currentQuestion || currentQuestion.id !== newRoom.question_ids[newRoom.current_round - 1]) {
        fetchCurrentQuestion(newRoom.room_code);
      }
    }

    // Reset my answer if round advanced
    if (newRoom.status === 'active' && (!roomData || roomData.current_round !== newRoom.current_round)) {
      setMyAnswer(null);
    }

    // Both players can trigger the start of the first round to ensure synchronization
    if (newRoom.status === 'countdown' && !startTimerRef.current) {
      startTimerRef.current = setTimeout(() => {
        startRound(newRoom.room_code);
        startTimerRef.current = null;
      }, 3000);
    }

    // Host handles round transitions for consistency
    if (playerRole === 'host' && newRoom.status === 'round_result') {
      setTimeout(() => nextRound(newRoom.room_code), 5000);
    }
  };

  const fetchCurrentQuestion = async (code) => {
    try {
      const response = await fetch(`/api/battle/question/${code}`);
      const data = await response.json();
      setCurrentQuestion(data);
    } catch (err) {
      console.error("Error fetching question:", err);
    }
  };

  // --- GAME ACTIONS ---

  const startRound = async (code) => {
    await fetch('/api/battle/start_round', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ room_code: code })
    });
  };

  const nextRound = async (code) => {
    await fetch('/api/battle/next_round', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ room_code: code })
    });
  };

  const submitAnswer = async (answer) => {
    if (myAnswer || screen !== 'active') return;
    setMyAnswer(answer);
    
    try {
      await fetch('/api/battle/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_code: roomCode,
          player_role: playerRole,
          answer
        })
      });
    } catch (err) {
      console.error("Error submitting answer:", err);
    }
  };

  // --- TIMER LOGIC ---

  useEffect(() => {
    if (screen === 'active' && roomData?.round_start_at) {
      const startAt = new Date(roomData.round_start_at).getTime();
      
      const updateTimer = () => {
        const now = Date.now();
        const elapsed = (now - startAt) / 1000;
        const remaining = Math.max(0, 30 - elapsed);
        setTimeLeft(Math.floor(remaining));

        if (remaining <= 0) {
          clearInterval(timerRef.current);
          if (!myAnswer) submitAnswer('TIMEOUT');
        }
      };

      updateTimer();
      timerRef.current = setInterval(updateTimer, 1000);
    } else {
      clearInterval(timerRef.current);
    }

    return () => clearInterval(timerRef.current);
  }, [screen, roomData?.round_start_at, myAnswer]);

  // --- UI RENDERING ---

  if (screen === 'lobby') {
    return (
      <div className="battle-mode">
        <button className="battle-close" onClick={onClose}>×</button>
        <div className="battle-header">⚔️ IPL BATTLE ARENA</div>
        <div className="battle-lobby">
          <div className="lobby-option">
            <h3>HOST A BATTLE</h3>
            <p>Create a private arena and challenge a friend</p>
            <button onClick={createRoom} disabled={loading} className="battle-button primary">
              {loading ? 'INITIALIZING...' : 'CREATE ROOM'}
            </button>
          </div>
          <div className="lobby-divider">OR</div>
          <div className="lobby-option">
            <h3>JOIN BATTLE</h3>
            <p>Enter arena code to start showdown</p>
            <input
              type="text"
              placeholder="ENTER CODE"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
              maxLength="6"
              className="battle-input"
            />
            <button onClick={joinRoom} disabled={loading} className="battle-button primary">
              {loading ? 'JOINING...' : 'ENTER ARENA'}
            </button>
          </div>
        </div>
        {error && <div className="battle-error">{error}</div>}
      </div>
    );
  }

  if (screen === 'waiting') {
    return (
      <div className="battle-mode">
        <button className="battle-close" onClick={onClose}>×</button>
        <div className="battle-header">⚔️ WAITING FOR CHALLENGER</div>
        <div className="battle-waiting">
          <div className="room-code-display">
            <span className="label">ARENA CODE</span>
            <span className="code">{roomCode}</span>
            <button 
              onClick={() => {
                navigator.clipboard.writeText(roomCode);
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
              }} 
              className="copy-button"
            >
              {copied ? '✅ COPIED!' : '📋 COPY CODE'}
            </button>
          </div>
          <div className="waiting-animation">
            <div className="dot"></div><div className="dot"></div><div className="dot"></div>
          </div>
          <p className="waiting-text">Share this code with your opponent to start the battle</p>
        </div>
      </div>
    );
  }

  if (screen === 'countdown') {
    return (
      <div className="battle-mode countdown-overlay">
        <div className="countdown-content">
          <div className="battle-header">PREPARE FOR BATTLE</div>
          <div className="vs-display">
            <span className="player-name">{roomData?.host_username}</span>
            <span className="vs-text">VS</span>
            <span className="player-name">{roomData?.guest_username}</span>
          </div>
          <div className="countdown-timer">BATTLE STARTING...</div>
        </div>
      </div>
    );
  }

  if (screen === 'active' || screen === 'round_result') {
    const isHost = playerRole === 'host';
    const myScore = isHost ? roomData.host_score : roomData.guest_score;
    const oppScore = isHost ? roomData.guest_score : roomData.host_score;
    const oppName = isHost ? roomData.guest_username : roomData.host_username;
    const myStreak = isHost ? roomData.host_streak : roomData.guest_streak;
    
    return (
      <div className="battle-mode">
        <div className="battle-top-bar">
          <div className="player-stat">
            <span className="stat-label">YOU</span>
            <span className="stat-value">{myScore}</span>
            {myStreak > 1 && <span className="streak-badge">🔥 {myStreak}</span>}
          </div>
          <div className="battle-timer-container">
            <div className={`timer-circle ${timeLeft <= 10 ? 'warning' : ''} ${timeLeft <= 5 ? 'critical' : ''}`}>
              {timeLeft}
            </div>
          </div>
          <div className="player-stat right">
            <span className="stat-label">{oppName}</span>
            <span className="stat-value">{oppScore}</span>
          </div>
        </div>

        <div className="round-indicator">ROUND {roomData.current_round} / {roomData.total_rounds}</div>

        <div className="battle-arena">
          <div className="question-box">
            {currentQuestion?.question || 'GETTING QUESTION...'}
          </div>

          <div className="options-grid">
            {currentQuestion?.options?.map((option, idx) => {
              const isSelected = myAnswer === option;
              const isCorrect = screen === 'round_result' && option === currentQuestion.correct_answer;
              const isWrong = screen === 'round_result' && isSelected && option !== currentQuestion.correct_answer;
              
              return (
                <button
                  key={idx}
                  onClick={() => submitAnswer(option)}
                  disabled={myAnswer !== null || screen === 'round_result'}
                  className={`option-btn ${isSelected ? 'selected' : ''} ${isCorrect ? 'correct' : ''} ${isWrong ? 'wrong' : ''}`}
                >
                  {option}
                  {isCorrect && <span className="result-icon">✅</span>}
                  {isWrong && <span className="result-icon">❌</span>}
                </button>
              );
            })}
          </div>

          {screen === 'round_result' && (
            <div className="round-feedback-overlay">
              <div className="feedback-content">
                {myAnswer === currentQuestion.correct_answer ? (
                  <div className="feedback-status win">CORRECT! +{isHost ? roomData.host_last_points : roomData.guest_last_points} pts</div>
                ) : (
                  <div className="feedback-status loss">{myAnswer === 'TIMEOUT' ? 'TIME UP!' : 'WRONG!'}</div>
                )}
                <div className="next-round-tip">Next round starting soon...</div>
              </div>
            </div>
          )}
          
          {myAnswer && screen === 'active' && (
            <div className="waiting-for-opponent">
              Waiting for {oppName} to answer...
            </div>
          )}
        </div>
      </div>
    );
  }

  if (screen === 'finished') {
    const isWinner = roomData.winner_username === username;
    const isDraw = roomData.winner_username === 'draw';
    
    return (
      <div className="battle-mode result-screen">
        <div className="battle-header result">
          {isWinner ? '🏆 VICTORY!' : isDraw ? '🤝 DRAW' : '💀 DEFEAT'}
        </div>
        
        <div className="final-scoreboard">
          <div className="score-card">
            <span className="player">{username}</span>
            <span className="score">{playerRole === 'host' ? roomData.host_score : roomData.guest_score}</span>
          </div>
          <div className="vs-divider">VS</div>
          <div className="score-card">
            <span className="player">{playerRole === 'host' ? roomData.guest_username : roomData.host_username}</span>
            <span className="score">{playerRole === 'host' ? roomData.guest_score : roomData.host_score}</span>
          </div>
        </div>

        <div className="battle-stats">
          <div className="stat-item">
            <span>Accuracy</span>
            <span>{Math.round(((playerRole === 'host' ? roomData.host_score : roomData.guest_score) / (roomData.total_rounds * 150)) * 100)}%</span>
          </div>
        </div>

        <button onClick={onGameEnd} className="battle-button primary">BACK TO LOBBY</button>
      </div>
    );
  }

  return null;
}
