import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

export const startGameRequest = async (playerName, maxQuestions = 8, gameMode = "SINGLE") => {
  const response = await api.post('/start', { 
    player_name: playerName,
    max_questions: maxQuestions,
    game_mode: gameMode
  });
  return response.data;
};

export const submitAnswerRequest = async (sessionId, answer) => {
  const response = await api.post('/submit_answer', {
    session_id: sessionId,
    answer: answer,
  });
  return response.data;
};

export const submitBackRequest = async (sessionId) => {
  const response = await api.post('/submit_back', {
    session_id: sessionId,
  });
  return response.data;
};

export const submitFeedbackRequest = async (sessionId, correctPlayer, wasCorrect) => {
  const response = await api.post('/submit_feedback', {
    session_id: sessionId,
    correct_player: correctPlayer,
    was_correct: wasCorrect,
  });
  return response.data;
};

export const submitScoreRequest = async (sessionId, playerName, playerId, score, result) => {
  const response = await api.post('/submit_score', {
    session_id: sessionId,
    player_name: playerName,
    player_id: playerId,
    score: score,
    result: result
  });
  return response.data;
};

export const getLeaderboardRequest = async () => {
  const response = await api.get('/leaderboard');
  return response.data;
};

export const getRecentGamesRequest = async () => {
  const response = await api.get('/recent_games');
  return response.data;
};
