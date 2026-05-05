import React from 'react';
import downloadVideo from '../assets/Untitled design.mp4';

export const DisambiguationCard = ({ 
  question, 
  loading, 
  onAnswer, 
  onBack, 
  onHome,
  questionCount,
  maxQuestions,
  score
}) => {
  const progressPercent = Math.min(Math.round(((questionCount - 1) / maxQuestions) * 100), 100);

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
          <h2 className="mini-logo-text" onClick={onHome} style={{ cursor: 'pointer' }}>
            akinator<span className="registered">®</span>
          </h2>
          <div className="score-display">
            <span className="score-label">SCORE:</span>
            <span className="score-value">{score || 0}</span>
          </div>
          <div className="header-actions">
            <button className="home-btn" onClick={onHome} title="Go to Home">
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
        </div>
        
        <div className="game-question-col">
          <div className="progress-container">
            <div className="progress-bar-bg">
              <div className="progress-bar-fill" style={{ width: `${progressPercent}%` }}></div>
            </div>
            <span className="progress-text">{progressPercent}%</span>
          </div>

          <div className="question-bubble-wrapper">
            <div className="question-number-tab" style={{ background: '#e74c3c' }}>
              <span className="diamond-bullet top-diamond">♦</span>
              <span className="q-num">!</span>
              <span className="diamond-bullet bottom-diamond">♦</span>
            </div>
            <div className="question-bubble-body">
              {loading ? "Analyzing..." : question}
            </div>
          </div>
          
          <div className="answer-options-box">
            <button className="answer-text-btn" onClick={() => onAnswer('yes')} disabled={loading}>Yes</button>
            <button className="answer-text-btn" onClick={() => onAnswer('no')} disabled={loading}>No</button>
            <div className="back-btn-separator"></div>
            <button className="answer-text-btn back-btn" onClick={onBack} disabled={loading}>Back</button>
          </div>
        </div>
      </div>
    </div>
  );
};
