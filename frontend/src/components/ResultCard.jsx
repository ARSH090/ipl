import React, { useState } from 'react';
import downloadVideo from '../assets/Untitled design.mp4';
import { confirmGuess } from '../api/client';

export const ResultCard = ({
  guess,
  confidence,
  onRestart,
  onBack,
  onWrong,
  banter,
  onSubmitFeedback,
  username = 'Anonymous',
  questionsAsked = 0,
  sessionId,
  trickDetected = false,
  onXAIGenerated
}) => {
  const [confirming, setConfirming] = useState(false);

  const handleYes = async () => {
    if (onSubmitFeedback) {
      onSubmitFeedback(guess, true);
    }

    // Call guess/confirm for XAI + leaderboard update
    setConfirming(true);
    try {
      const result = await confirmGuess({
        session_id: sessionId,
        correct: true,
        actual_player: guess,
        username,
        questions_asked: questionsAsked,
        trick_detected: trickDetected
      });

      // Show XAI explanation modal
      if (onXAIGenerated && result.xai_explanation) {
        onXAIGenerated({
          ...result.xai_explanation,
          correct: true,
          score_earned: result.score_earned,
          badges_earned: result.badges_earned
        });
        return; // XAI modal will handle restart
      }
    } catch (err) {
      console.error('Failed to confirm guess:', err);
    } finally {
      setConfirming(false);
    }

    onRestart();
  };

  return (
    <div className="game-screen-container">
      <div className="bg-decorations">
        <div className="diamond d1"></div>
        <div className="diamond d2"></div>
        <div className="diamond d3"></div>
        <div className="diamond d4"></div>
        <div className="diamond d5"></div>
      </div>

      <div className="game-header">
        <div className="mini-logo-container">
          <h2 className="mini-logo-text" onClick={onRestart} style={{ cursor: 'pointer' }}>
            akinator<span className="registered">®</span>
          </h2>
          <div className="header-actions">
            <button className="home-btn" onClick={onRestart} title="Go to Home">
              <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
              </svg>
            </button>
            <div className="language-selector">English</div>
          </div>
        </div>
      </div>

      <div className="game-content-row">
        <div className="game-mascot-col">
          <div className="mascot-video-container">
            <video 
              src={downloadVideo} 
              autoPlay 
              loop 
              muted 
              playsInline 
              className="mascot-video"
            />
          </div>
        </div>
        
        <div className="game-question-col">
          <div className="question-bubble-wrapper">
            <div className="result-top-box">
              <div className="result-header">I THINK OF</div>
              <div className="result-body">
                <h3 className="guess-name-text">{guess}</h3>
                <p className="guess-subtitle">{banter || 'Guessed by Akinator'}</p>
                
                <div className="result-image-box">
                  <div className="placeholder-image">
                    <img 
                      src={`https://tse1.mm.bing.net/th?q=${encodeURIComponent(guess)}+IPL+player+official+profile+photo`} 
                      alt={guess} 
                      onError={(e) => {
                        e.target.src = 'https://via.placeholder.com/300x400.png?text=Player+Image+Not+Found';
                      }}
                    />
                  </div>
                </div>

                <div className="result-actions">
                  <button className="result-btn btn-yes" onClick={handleYes} disabled={confirming}>
                    {confirming ? '...' : 'Yes'}
                  </button>
                  <div className="result-diamond">♦</div>
                  <button className="result-btn btn-no" onClick={onWrong} disabled={confirming}>No</button>
                </div>
              </div>
            </div>
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'center', gap: '30px', marginTop: '20px' }}>
            <button className="result-back-link" onClick={onBack} disabled={confirming} style={{ margin: 0, zIndex: 10, cursor: 'pointer', padding: '10px 20px', border: '1px solid #5d7c99', borderRadius: '20px', color: '#f8fafc', background: 'transparent' }}>
              &larr; Go back
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
