import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

// ============================================================
// EXISTING GAME ENDPOINTS
// ============================================================

export const startGameRequest = async (maxQuestions = 8) => {
  const response = await api.post('/start', { max_questions: maxQuestions });
  return response.data;
};

export const getRecentGamesRequest = async () => {
  const response = await api.get('/recent');
  return response.data;
};

export const submitAnswerRequest = async (sessionId, answer) => {
  const response = await api.post('/answer', {
    session_id: sessionId,
    answer: answer,
  });
  return response.data;
};

export const submitBackRequest = async (sessionId) => {
  const response = await api.post('/back', {
    session_id: sessionId,
  });
  return response.data;
};

export const submitFeedbackRequest = async (sessionId, correctPlayer, wasCorrect) => {
  const response = await api.post('/feedback', {
    session_id: sessionId,
    correct_player: correctPlayer,
    was_correct: wasCorrect,
  });
  return response.data;
};

// ============================================================
// NEW SUPABASE ENDPOINTS
// ============================================================

/** Create a Supabase-backed game session */
export const startSupabaseSession = async (username, mode = 'solo') => {
  const response = await api.post('/session/start', { username, mode });
  return response.data;
};

/** Get session state — top candidates for AI visualization */
export const getSessionState = async (sessionId) => {
  const response = await api.get(`/state/${sessionId}`);
  return response.data;
};

/** Check trick detection on current answer log */
export const checkTrickDetection = async (sessionId) => {
  const response = await api.post('/trick/check', { session_id: sessionId });
  return response.data;
};

/** Confirm AI guess — triggers XAI explanation + leaderboard update */
export const confirmGuess = async (body) => {
  const response = await api.post('/guess/confirm', body);
  return response.data;
};

/** Fetch top leaderboard */
export const getLeaderboardRequest = async (limit = 10) => {
  const response = await api.get(`/leaderboard?limit=${limit}`);
  return response.data;
};

/** Generate XAI explanation for a guess */
export const getXAIExplanation = async (body) => {
  const response = await api.post('/xai/explain', body);
  return response.data;
};
