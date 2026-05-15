import { useState, useEffect, useRef } from 'react';
import '../styles/BattleMode.css';

export default function BattleMode({ username, sessionId, onClose, onGameEnd }) {
  const [screen, setScreen] = useState('lobby'); // lobby, join, waiting, battle, result
  const [roomCode, setRoomCode] = useState('');
  const [joinCode, setJoinCode] = useState('');
  const [opponentUsername, setOpponentUsername] = useState('');
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [currentAttribute, setCurrentAttribute] = useState('');
  const [myAnswer, setMyAnswer] = useState(null);
  const [opponentAnswered, setOpponentAnswered] = useState(false);
  const [gameState, setGameState] = useState({
    questionNumber: 0,
    myScore: 0,
    opponentScore: 0,
    status: 'waiting'
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [playerRole, setPlayerRoleState] = useState(null); // 'host' or 'guest'
  const [battleSessionId, setBattleSessionId] = useState(sessionId);
  const playerRoleRef = useRef(null);
  
  const setPlayerRole = (role) => {
    setPlayerRoleState(role);
    playerRoleRef.current = role;
  };
  const ws = useRef(null);

  const createRoom = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/battle/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, session_id: sessionId })
      });
      const data = await response.json();
      setRoomCode(data.room_code);
      setPlayerRole('host');
      connectWebSocket(data.room_code, 'host', username);
      setScreen('waiting');
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
          username,
          session_id: sessionId
        })
      });
      if (!response.ok) throw new Error('Room not found');
      const data = await response.json();
      setRoomCode(data.room_code);
      setOpponentUsername(data.host_username);
      setPlayerRole('guest');
      connectWebSocket(data.room_code, 'guest', username);
      setScreen('battle');
    } catch (err) {
      setError('Invalid room code or room not found');
    } finally {
      setLoading(false);
    }
  };

  const connectWebSocket = (code, role, currentUsername) => {
    const wsHost = window.location.host; // Works with vite proxy in dev
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws.current = new WebSocket(`${protocol}//${wsHost}/ws/battle/${code}`);
    
    ws.current.onopen = () => {
      if (role === 'guest') {
        ws.current.send(JSON.stringify({
          type: 'PLAYER_JOINED',
          room_code: code,
          guest_username: currentUsername
        }));
      }
    };
    
    ws.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      handleWebSocketMessage(message);
    };
    
    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('Connection error');
    };
  };

  const handleWebSocketMessage = (message) => {
    const { type } = message;
    
    switch (type) {
      case 'PLAYER_JOINED':
        setOpponentUsername(message.guest_username);
        setScreen('battle');
        if (playerRoleRef.current === 'host') {
          fetchNextQuestion(true); // isFirst = true
        }
        break;
      case 'QUESTION_READY':
        setCurrentQuestion(message.question);
        setCurrentAttribute(message.attribute);
        setGameState(prev => ({ ...prev, questionNumber: message.question_number }));
        setMyAnswer(null);
        setOpponentAnswered(false);
        break;
      case 'ANSWER_RECEIVED':
        if (message.player_role !== playerRoleRef.current) {
          setOpponentAnswered(true);
        }
        break;
      case 'BOTH_ANSWERED':
        // Both answered, wait for next question
        setTimeout(() => {
          setMyAnswer(null);
          setOpponentAnswered(false);
        }, 1500);
        break;
      case 'GAME_OVER':
        setResult(message);
        setScreen('result');
        break;
      case 'SCORE_UPDATE':
        setGameState(prev => ({
          ...prev,
          myScore: message.host_score,
          opponentScore: message.guest_score
        }));
        break;
      default:
        break;
    }
  };

  const submitAnswer = (answer) => {
    setMyAnswer(answer);
    
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: 'SUBMIT_ANSWER',
        room_code: roomCode,
        player_role: playerRole,
        answer
      }));
    }
  };

  const closeConnection = () => {
    if (ws.current) {
      ws.current.close();
    }
  };

  const fetchNextQuestion = async (isFirst = false) => {
    try {
      let data;
      if (isFirst) {
        const response = await fetch('/api/start', { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ max_questions: 8 })
        });
        data = await response.json();
        setBattleSessionId(data.session_id);
      } else {
        const response = await fetch('/api/answer', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: battleSessionId, answer: myAnswer })
        });
        data = await response.json();
      }

      if (data.guess) {
        // Game over
        ws.current.send(JSON.stringify({
          type: 'GAME_OVER',
          room_code: roomCode,
          winner: 'draw', // simplified for now
          host_guess: data.guess,
          host_score: gameState.myScore,
          guest_score: gameState.opponentScore
        }));
      } else {
        ws.current.send(JSON.stringify({
          type: 'NEXT_QUESTION',
          room_code: roomCode,
          question: data.question,
          attribute: data.attribute,
          question_number: gameState.questionNumber + 1
        }));
      }
    } catch (err) {
      console.error("Error fetching next question:", err);
    }
  };

  useEffect(() => {
    if (playerRole === 'host' && myAnswer && opponentAnswered) {
      setTimeout(() => {
        fetchNextQuestion(false);
      }, 1500);
    }
  }, [myAnswer, opponentAnswered, playerRole]);

  useEffect(() => {
    return () => closeConnection();
  }, []);

  // Lobby Screen
  if (screen === 'lobby') {
    return (
      <div className="battle-mode">
        <button className="battle-close" onClick={onClose}>×</button>
        
        <div className="battle-header">⚔️ Battle Mode</div>
        
        <div className="battle-lobby">
          <div className="lobby-option">
            <h3>Create Room</h3>
            <p>Start a new battle and share your code</p>
            <button 
              onClick={createRoom} 
              disabled={loading}
              className="battle-button primary"
            >
              {loading ? 'Creating...' : 'Create Room'}
            </button>
          </div>

          <div className="lobby-divider">OR</div>

          <div className="lobby-option">
            <h3>Join Room</h3>
            <p>Enter a friend's battle code</p>
            <input
              type="text"
              placeholder="e.g., CSK421"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
              maxLength="6"
              className="battle-input"
            />
            <button 
              onClick={joinRoom} 
              disabled={loading}
              className="battle-button primary"
            >
              {loading ? 'Joining...' : 'Join Room'}
            </button>
          </div>
        </div>

        {error && <div className="battle-error">{error}</div>}
      </div>
    );
  }

  // Waiting Screen
  if (screen === 'waiting') {
    return (
      <div className="battle-mode">
        <button className="battle-close" onClick={() => { closeConnection(); onClose(); }}>×</button>
        
        <div className="battle-header">⚔️ Waiting for Opponent</div>
        
        <div className="battle-waiting">
          <div className="room-code-display">
            <span className="label">Your Room Code:</span>
            <span className="code">{roomCode}</span>
            <button 
              onClick={() => navigator.clipboard.writeText(roomCode)}
              className="copy-button"
            >
              📋 Copy
            </button>
          </div>

          <div className="waiting-animation">
            <div className="dot"></div>
            <div className="dot"></div>
            <div className="dot"></div>
          </div>

          <p className="waiting-text">Waiting for your friend to join...</p>
        </div>
      </div>
    );
  }

  // Battle Screen
  if (screen === 'battle') {
    return (
      <div className="battle-mode">
        <div className="battle-header">⚔️ Battle!</div>
        
        <div className="battle-scores">
          <div className="score-you">
            <div className="score-label">You</div>
            <div className="score-value">{gameState.myScore}</div>
          </div>
          <div className="score-vs">VS</div>
          <div className="score-opponent">
            <div className="score-label">{opponentUsername}</div>
            <div className="score-value">{gameState.opponentScore}</div>
          </div>
        </div>

        <div className="question-number">Question {gameState.questionNumber}</div>

        <div className="battle-question">
          {currentQuestion || 'Waiting for question...'}
        </div>

        <div className="answer-options">
          {['yes', 'no', 'maybe', 'dont_know'].map(option => (
            <button
              key={option}
              onClick={() => submitAnswer(option)}
              disabled={myAnswer !== null}
              className={`answer-btn ${myAnswer === option ? 'selected' : ''}`}
            >
              {option === 'yes' && '✅ Yes'}
              {option === 'no' && '❌ No'}
              {option === 'maybe' && '❓ Maybe'}
              {option === 'dont_know' && '🤷 Dont Know'}
            </button>
          ))}
        </div>

        {myAnswer && !opponentAnswered && (
          <div className="opponent-waiting">
            ⏳ Waiting for {opponentUsername}...
          </div>
        )}

        {myAnswer && opponentAnswered && (
          <div className="both-answered">
            Both answered! Getting next question...
          </div>
        )}
      </div>
    );
  }

  // Result Screen
  if (screen === 'result') {
    const isWinner = result?.winner === 'host';
    const isDraw = result?.winner === 'draw';

    return (
      <div className="battle-mode">
        <div className="battle-header">
          {isWinner ? '🎉 You Win!' : isDraw ? '🤝 It\'s a Draw!' : '😢 You Lost'}
        </div>

        <div className="result-scores">
          <div className="final-score">
            <div>{gameState.myScore}</div>
            <div className="versus">vs</div>
            <div>{gameState.opponentScore}</div>
          </div>
        </div>

        <div className="result-details">
          <p>Final Result: {result?.winner === 'host' ? 'You survived longer!' : 'Your opponent survived longer'}</p>
        </div>

        <button 
          onClick={() => {
            closeConnection();
            onGameEnd?.();
          }}
          className="battle-button primary"
        >
          Play Again
        </button>
      </div>
    );
  }

  return null;
}
