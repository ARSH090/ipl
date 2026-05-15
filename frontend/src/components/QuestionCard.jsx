import React from 'react';
import mascotImg from '../assets/front_mascot.png';
import downloadVideo from '../assets/Untitled design.mp4';

export const QuestionCard = ({ 
  question, 
  confidence, 
  remainingCandidates, 
  loading, 
  onAnswer,
  onBack,
  onHome,
  questionCount,
  maxQuestions,
  banter
}) => {
  const progressPercent = Math.min(Math.round(((questionCount - 1) / maxQuestions) * 100), 100);

  return (
    <div className="game-screen-container">
      {/* Background decorations shared with start screen */}
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
          <div className="header-actions">
            <button className="home-btn" onClick={onHome} title="Go to Home">
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
          <div className="progress-container">
            <div className="progress-bar-bg">
              <div className="progress-bar-fill" style={{ width: `${progressPercent}%` }}></div>
            </div>
            <span className="progress-text">{progressPercent}%</span>
          </div>
          <div className="diamond d6"></div>
        <div className="diamond d7"></div>
        <div className="diamond d8"></div>

          <div className="question-bubble-wrapper">
            <div className="question-number-tab">
              <span className="diamond-bullet top-diamond">♦</span>
              <span className="q-num">{questionCount || '1'}</span>
              <span className="diamond-bullet bottom-diamond">♦</span>
            </div>
            <div className={`question-bubble-body ${loading ? 'loading-pulse' : ''}`}>
              {loading ? (
                <div className="thinking-container">
                  <span className="thinking-text">CONSULTING THE THIRD UMPIRE...</span>
                  <div className="thinking-dots">
                    <span></span><span></span><span></span>
                  </div>
                </div>
              ) : (
                <div className="question-content">
                  <div className="question-label">AI INQUIRY</div>
                  <div className="question-text">{question}</div>
                </div>
              )}
            </div>
          </div>
          
          <div className="answer-options-box">
            <button className="answer-text-btn btn-yes" onClick={() => onAnswer('yes')} disabled={loading}>Yes</button>
            <button className="answer-text-btn btn-no" onClick={() => onAnswer('no')} disabled={loading}>No</button>
            <button className="answer-text-btn btn-dont-know" onClick={() => onAnswer('dont_know')} disabled={loading}>Don't know</button>
            <button className="answer-text-btn btn-probably" onClick={() => onAnswer('probably')} disabled={loading}>Probably</button>
            <button className="answer-text-btn btn-probably-not" onClick={() => onAnswer('probably_not')} disabled={loading}>Probably not</button>
            <div className="back-btn-separator"></div>
            <button className="answer-text-btn back-btn" onClick={onBack} disabled={loading || questionCount <= 1}>Back to Previous</button>
          </div>
        </div>
      </div>
    </div>
  );
};
