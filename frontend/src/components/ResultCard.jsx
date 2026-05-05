import React from 'react';
import mascotImg from '../assets/front_mascot.png';
import downloadVideo from '../assets/Untitled design.mp4';

export const ResultCard = ({ guess, confidence, onRestart, onBack, onWrong, banter, onSubmitFeedback, score, playerId, playerName, explanation = [] }) => {
  const handleYes = () => {
    if (onSubmitFeedback) {
      onSubmitFeedback(guess, true);
    }
  };
  
  return (
    <div className="game-screen-container">
      <div className="bg-decorations">
        <div className="diamond d1"></div>
        <div className="diamond d2"></div>
        <div className="diamond d3"></div>
      </div>

      <div className="game-header">
        <div className="mini-logo-container">
          <h2 className="mini-logo-text" onClick={onRestart} style={{ cursor: 'pointer' }}>
            akinator<span className="registered">®</span>
          </h2>
          <div className="player-id-badge">ID: {playerId}</div>
          <div className="header-actions">
            <button className="home-btn" onClick={onRestart} title="Go to Home">
              <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
              </svg>
            </button>
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
          {score > 1000 && (
            <div className="badge-notification">
              🎖️ Master Manipulator
            </div>
          )}
        </div>
        
        <div className="game-question-col">
          <div className="result-top-box">
            <div className="final-score-badge">
              FINAL SCORE: {score}
            </div>
            <div className="result-header">I THINK OF</div>
            <div className="result-body">
              <h3 className="guess-name-text">{guess}</h3>
              <p className="guess-subtitle">{banter || 'Guessed by Akinator'}</p>
              
              <div className="result-actions">
                <button className="result-btn btn-yes" onClick={handleYes}>Yes</button>
                <div className="result-diamond">♦</div>
                <button className="result-btn btn-no" onClick={onBack}>No</button>
              </div>
            </div>
          </div>

          {/* XAI Explanation Section */}
          {explanation && explanation.length > 0 && (
            <div className="xai-container">
              <h4 className="xai-title">I guessed {guess} because:</h4>
              <div className="xai-grid">
                {explanation.map((item, i) => (
                  <div key={i} className="xai-card">
                    <span className="xai-attr">{item.attribute.replace('_', ' ')}</span>
                    <span className={`xai-contrib ${item.impact.toLowerCase()}`}>
                      +{item.contribution}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
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

          <div style={{ display: 'flex', justifyContent: 'center', gap: '30px', marginTop: '20px' }}>
            <button className="result-back-link" onClick={onBack} style={{ margin: 0, zIndex: 10, cursor: 'pointer', padding: '10px 20px', border: '1px solid #5d7c99', borderRadius: '20px' }}>
              &larr; Go back
            </button>
            <button className="result-back-link" onClick={onWrong} style={{ margin: 0, zIndex: 10, cursor: 'pointer', padding: '10px 20px', border: '1px solid #5d7c99', borderRadius: '20px' }}>
              I was wrong
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
