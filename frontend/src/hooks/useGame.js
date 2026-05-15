import { useState } from 'react';
import {
  startGameRequest,
  submitAnswerRequest,
  submitBackRequest,
  getRecentGamesRequest,
  submitFeedbackRequest,
  getSessionState,
  checkTrickDetection
} from '../api/client';

export const useGame = () => {
  const [sessionId, setSessionId] = useState(null);
  const [phase, setPhase] = useState('start'); // 'start', 'question', 'disambiguation', 'result', 'correction'
  const [question, setQuestion] = useState('');
  const [confidence, setConfidence] = useState(0);
  const [remainingCandidates, setRemainingCandidates] = useState(250);
  const [loading, setLoading] = useState(false);
  const [guess, setGuess] = useState('');
  const [banter, setBanter] = useState('');
  const [maxQuestions, setMaxQuestions] = useState(8);
  const [questionCount, setQuestionCount] = useState(0);
  const [error, setError] = useState('');
  const [recentGames, setRecentGames] = useState([]);

  // New: AI Visualization + Trick Detection state
  const [topSuspects, setTopSuspects] = useState([]);
  const [trickDetected, setTrickDetected] = useState(false);
  const [inconsistencyScore, setInconsistencyScore] = useState(0);

  /** Fetch top suspects + trick detection in background after each answer */
  const fetchSuspectsAndTrick = async (sid) => {
    try {
      const state = await getSessionState(sid);
      if (state.top_candidates) {
        setTopSuspects(state.top_candidates.slice(0, 3));
      }
    } catch (err) {
      console.error('Failed to fetch suspects:', err);
    }
    try {
      const trick = await checkTrickDetection(sid);
      setTrickDetected(!trick.is_consistent);
      setInconsistencyScore(trick.inconsistency_score || 0);
    } catch (err) {
      console.error('Failed to check trick:', err);
    }
  };

  const startGame = async (questions = 8) => {
    setMaxQuestions(questions);
    setLoading(true);
    setError('');
    setQuestionCount(0);
    setBanter('');
    setTopSuspects([]);
    setTrickDetected(false);
    setInconsistencyScore(0);
    try {
      const data = await startGameRequest(questions);
      setSessionId(data.session_id);
      setQuestion(data.question);
      setConfidence(data.confidence || 0);
      setRemainingCandidates(data.remaining_candidates);
      setQuestionCount(1);
      setPhase('question');
    } catch (err) {
      setError('Failed to start the game. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  const fetchRecentGames = async () => {
    try {
      const data = await getRecentGamesRequest();
      setRecentGames(data);
    } catch (err) {
      console.error('Failed to fetch recent games');
    }
  };

  const processResponse = (data, sid) => {
    setConfidence(data.confidence || 0);
    if (data.remaining_candidates !== undefined) {
      setRemainingCandidates(data.remaining_candidates);
    }

    if (data.banter) {
      setBanter(data.banter);
    }

    if (data.guess) {
      setGuess(data.guess);
      setPhase('result');
    } else if (data.is_disambiguation) {
      setQuestion(data.question);
      setPhase('disambiguation');
    } else {
      setQuestion(data.question);
      if (data.banter === "Let's try that again...") {
        setQuestionCount(prev => Math.max(1, prev - 1));
      } else {
        setQuestionCount(prev => prev + 1);
      }
      setPhase('question');
    }

    // Fetch AI visualization data in background (only if game continues)
    if (sid && !data.guess) {
      fetchSuspectsAndTrick(sid);
    }
  };

  const submitAnswer = async (answer) => {
    setLoading(true);
    setError('');
    try {
      const data = await submitAnswerRequest(sessionId, answer);
      processResponse(data, sessionId);
    } catch (err) {
      setError('Failed to submit answer.');
    } finally {
      setLoading(false);
    }
  };

  const submitDisambiguation = async (answer) => {
    submitAnswer(answer);
  };

  const goToCorrection = () => {
    setPhase('correction');
  };

  const goBack = async () => {
    if (questionCount <= 1) return;
    setLoading(true);
    try {
      const data = await submitBackRequest(sessionId);
      processResponse(data, sessionId);
    } catch (err) {
      setError('Failed to go back.');
    } finally {
      setLoading(false);
    }
  };

  const resetGame = () => {
    setSessionId(null);
    setPhase('start');
    setQuestion('');
    setConfidence(0);
    setRemainingCandidates(250);
    setGuess('');
    setBanter('');
    setQuestionCount(0);
    setError('');
    setTopSuspects([]);
    setTrickDetected(false);
    setInconsistencyScore(0);
  };

  const submitFeedback = async (correctPlayer, wasCorrect) => {
    try {
      await submitFeedbackRequest(sessionId, correctPlayer, wasCorrect);
      fetchRecentGames(); // Refresh history
    } catch (err) {
      console.error('Failed to submit feedback');
    }
  };

  return {
    sessionId,
    phase,
    question,
    confidence,
    remainingCandidates,
    loading,
    guess,
    banter,
    questionCount,
    error,
    recentGames,
    maxQuestions,
    topSuspects,
    trickDetected,
    inconsistencyScore,
    startGame,
    submitAnswer,
    submitDisambiguation,
    goToCorrection,
    goBack,
    resetGame,
    fetchRecentGames,
    submitFeedback,
  };
};
