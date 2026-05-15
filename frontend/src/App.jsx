import React, { useEffect, useRef, useState } from 'react';
import anime from 'animejs';
import { useGame } from './hooks/useGame';
import { StartScreen } from './components/StartScreen';
import { QuestionCard } from './components/QuestionCard';
import { DisambiguationCard } from './components/DisambiguationCard';
import { ResultCard } from './components/ResultCard';
import { CorrectionCard } from './components/CorrectionCard';
import LiveLeaderboard from './components/LiveLeaderboard';
import AIVisualizationPanel from './components/AIVisualizationPanel';
import XAIReveal from './components/XAIReveal';
import TrickAI from './components/TrickAI';
import BattleMode from './components/BattleMode';

import './styles.css';

function App() {
  const {
    sessionId,
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
    topSuspects,
    trickDetected,
    inconsistencyScore
  } = useGame();

  const [username, setUsername] = useState('');
  const [showBattleMode, setShowBattleMode] = useState(false);
  const [xaiExplanation, setXaiExplanation] = useState(null);

  const containerRef = useRef(null);

  useEffect(() => {
    if (phase === 'start') {
      fetchRecentGames();
    }
  }, [phase]);

  useEffect(() => {
    if (containerRef.current && !showBattleMode) {
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

      {/* Battle Mode Modal */}
      {showBattleMode && (
        <div className="battle-mode-modal">
          <BattleMode 
            username={username}
            sessionId={sessionId}
            onClose={() => setShowBattleMode(false)}
            onGameEnd={() => setShowBattleMode(false)}
          />
        </div>
      )}

      {/* XAI Reveal Modal */}
      {xaiExplanation && (
        <XAIReveal 
          explanation={xaiExplanation}
          onClose={() => {
            setXaiExplanation(null);
            resetGame();
          }}
        />
      )}

      {/* Main Layout */}
      <div className="app-layout">
        {/* Left Sidebar - Leaderboard */}
        {phase !== 'start' && !showBattleMode && (
          <div className="sidebar sidebar-left">
            <LiveLeaderboard />
          </div>
        )}

        {/* Center Content */}
        <div className="main-content">
          {phase === 'start' && (
            <StartScreen 
              onStart={(un, mode, questions) => {
                setUsername(un);
                if (mode === 'battle') {
                  setShowBattleMode(true);
                } else {
                  startGame(questions || 8);
                }
              }} 
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
              onBattle={() => setShowBattleMode(true)}
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
              username={username}
              questionsAsked={questionCount}
              sessionId={sessionId}
              trickDetected={trickDetected}
              onXAIGenerated={setXaiExplanation}
            />
          )}

          {phase === 'correction' && (
            <CorrectionCard 
              onRestart={resetGame}
              onSubmitFeedback={submitFeedback}
              username={username}
              questionsAsked={questionCount}
              sessionId={sessionId}
              trickDetected={trickDetected}
              onXAIGenerated={setXaiExplanation}
            />
          )}
        </div>

        {/* Right Sidebar - AI Visualization */}
        {phase !== 'start' && !showBattleMode && (
          <div className="sidebar sidebar-right">
            <AIVisualizationPanel
              confidence={confidence}
              topSuspects={topSuspects}
              trickDetected={trickDetected}
              thinking={loading}
            />
            {(trickDetected || inconsistencyScore > 0) && (
              <div style={{ marginTop: '16px' }}>
                <TrickAI 
                  trickDetected={trickDetected}
                  inconsistencyScore={inconsistencyScore}
                  gameWon={phase === 'result' && guess}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
