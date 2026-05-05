import { useState, useEffect } from 'react';
import { supabase } from '../api/supabase';
import { 
  startGameRequest, submitAnswerRequest, submitBackRequest, 
  getRecentGamesRequest, submitFeedbackRequest, submitScoreRequest, getLeaderboardRequest 
} from '../api/client';

export const useGame = () => {
  const [sessionId, setSessionId] = useState(null);
  const [phase, setPhase] = useState('start'); 
  const [playerName, setPlayerName] = useState('');
  const [playerId, setPlayerId] = useState('');
  const [score, setScore] = useState(0);
  const [trickBonus, setTrickBonus] = useState(0);
  const [leaderboard, setLeaderboard] = useState([]);
  const [gameMode, setGameMode] = useState('SINGLE');
  
  // Real-time Subscriptions State
  useEffect(() => {
    if (!playerId) return;

    // 1. Subscribe to CURRENT PLAYER changes (Live Score Updates)
    const playerSub = supabase
      .channel('player-score')
      .on(
        'postgres_changes',
        { event: 'UPDATE', schema: 'public', table: 'leaderboard', filter: `player_id=eq.${playerId}` },
        (payload) => {
          console.log('Realtime Update:', payload.new);
          if (payload.new.score !== undefined) setScore(payload.new.score);
          if (payload.new.trick_bonus !== undefined) setTrickBonus(payload.new.trick_bonus);
        }
      )
      .subscribe();

    // 2. Subscribe to GLOBAL LEADERBOARD changes
    const globalSub = supabase
      .channel('global-leaderboard')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'leaderboard' },
        async () => {
          const data = await getLeaderboardRequest();
          setLeaderboard(data);
        }
      )
      .subscribe();

    return () => {
      playerSub.unsubscribe();
      globalSub.unsubscribe();
    };
  }, [playerId]);
  
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

  // 📊 Live Visualization & XAI State
  const [topPlayers, setTopPlayers] = useState([]);
  const [explanation, setExplanation] = useState([]);

  const startGame = async (name, questions = 8, mode = "SINGLE") => {
    setPlayerName(name);
    setMaxQuestions(questions);
    setGameMode(mode);
    setLoading(true);
    setError('');
    setQuestionCount(0);
    setBanter('');
    setScore(0);
    setExplanation([]);
    setTopPlayers([]);
    try {
      const data = await startGameRequest(name, questions, mode);
      setSessionId(data.session_id);
      setPlayerId(data.player_id);
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

  const fetchLeaderboard = async () => {
    setLoading(true);
    try {
      const data = await getLeaderboardRequest();
      setLeaderboard(data);
      setPhase('leaderboard');
    } catch (err) {
      console.error('Failed to fetch leaderboard');
    } finally {
      setLoading(false);
    }
  };

  const processResponse = (data) => {
    setConfidence(data.confidence || 0);
    if (data.remaining_candidates !== undefined) {
      setRemainingCandidates(data.remaining_candidates);
    }
    
    if (data.current_score !== undefined) {
      setScore(data.current_score);
    }

    if (data.final_score !== undefined) {
      setScore(data.final_score);
    }
    
    if (data.banter) {
      setBanter(data.banter);
    }

    if (data.top_players) {
      setTopPlayers(data.top_players);
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
  };

  const submitAnswer = async (answer) => {
    setLoading(true);
    setError('');
    try {
      const data = await submitAnswerRequest(sessionId, answer);
      processResponse(data);
    } catch (err) {
      setError('Failed to submit answer.');
    } finally {
      setLoading(false);
    }
  };

  const submitScore = async (result) => {
    setLoading(true);
    try {
      await submitScoreRequest(sessionId, playerName, playerId, score, result);
      await fetchLeaderboard();
    } catch (err) {
      setError('Failed to submit score.');
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
      processResponse(data);
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
    setScore(0);
    setTopPlayers([]);
    setExplanation([]);
  };

  const submitFeedback = async (correctPlayer, wasCorrect) => {
    try {
      const data = await submitFeedbackRequest(sessionId, correctPlayer, wasCorrect);
      if (data.new_score !== undefined) setScore(data.new_score);
      if (data.explanation) setExplanation(data.explanation);
      
      fetchRecentGames(); // Refresh history
      
      // After feedback, we submit the final score
      const result = wasCorrect ? "AI Won" : "User Won";
      await submitScore(result);
    } catch (err) {
      console.error('Failed to submit feedback');
    }
  };

  return {
    sessionId,
    phase,
    playerName,
    playerId,
    score,
    leaderboard,
    gameMode,
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
    topPlayers,
    explanation,
    startGame,
    submitAnswer,
    submitDisambiguation,
    goToCorrection,
    goBack,
    resetGame,
    fetchRecentGames,
    submitFeedback,
    submitScore,
    fetchLeaderboard
  };
};
