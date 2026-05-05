import React, { useEffect, useRef } from 'react';
import anime from 'animejs';
import { useGame } from './hooks/useGame';
import { StartScreen } from './components/StartScreen';
import { QuestionCard } from './components/QuestionCard';
import { DisambiguationCard } from './components/DisambiguationCard';
import { ResultCard } from './components/ResultCard';
import { CorrectionCard } from './components/CorrectionCard';
import { Leaderboard } from './components/Leaderboard';

import './styles.css';

function App() {
  const {
    phase,
    question,
    confidence,
    remainingCandidates,
    loading,
    guess,
    error,
    banter,
    startGame,
    submitAnswer,
    submitDisambiguation,
    goBack,
    goToCorrection,
    resetGame,
    questionCount,
    recentGames,
    fetchRecentGames,
    submitFeedback,
    maxQuestions,
    playerName,
    playerId,
    score,
    leaderboard,
    fetchLeaderboard,
    topPlayers,
    explanation
  } = useGame();

  const containerRef = useRef(null);

  useEffect(() => {
    if (phase === 'start') {
      fetchRecentGames();
    }
  }, [phase]);

  useEffect(() => {
    if (containerRef.current) {
      anime({
        targets: containerRef.current,
        translateY: [20, 0],
        opacity: [0, 1],
        easing: 'easeOutExpo',
        duration: 800,
      });
    }
  }, [phase]);

  return (
    <div className="app-container" ref={containerRef}>
      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      {phase === 'start' && (
        <StartScreen 
          onStart={startGame} 
          onLeaderboard={fetchLeaderboard}
          loading={loading} 
          recentGames={recentGames} 
        />
      )}

      {phase === 'question' && (
        <QuestionCard 
          question={question}
          confidence={confidence}
          remainingCandidates={remainingCandidates}
          loading={loading}
          onAnswer={submitAnswer}
          onBack={goBack}
          onHome={resetGame}
          questionCount={questionCount}
          maxQuestions={maxQuestions}
          banter={banter}
          score={score}
          topPlayers={topPlayers}
        />
      )}

      {phase === 'disambiguation' && (
        <DisambiguationCard 
          question={question}
          loading={loading}
          onAnswer={submitDisambiguation}
          onBack={goBack}
          onHome={resetGame}
          questionCount={questionCount}
          maxQuestions={maxQuestions}
          score={score}
        />
      )}

      {phase === 'result' && (
        <ResultCard 
          guess={guess}
          confidence={confidence}
          onRestart={resetGame}
          onBack={goBack}
          onWrong={goToCorrection}
          onSubmitFeedback={submitFeedback}
          banter={banter}
          score={score}
          playerId={playerId}
          playerName={playerName}
          explanation={explanation}
        />
      )}

      {phase === 'correction' && (
        <CorrectionCard 
          onRestart={resetGame}
          onSubmitFeedback={submitFeedback}
        />
      )}

      {phase === 'leaderboard' && (
        <Leaderboard 
          data={leaderboard}
          onHome={resetGame}
        />
      )}
    </div>
  );
}

export default App;
