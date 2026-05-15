import { useState, useEffect } from 'react';
import '../styles/XAIReveal.css';

export default function XAIReveal({ 
  explanation = {}, 
  onClose = () => {} 
}) {
  const [displayReasons, setDisplayReasons] = useState([]);

  useEffect(() => {
    // Stagger the appearance of reasons
    const reasons = explanation.reasons || [];
    reasons.forEach((reason, idx) => {
      setTimeout(() => {
        setDisplayReasons(prev => [...prev, reason]);
      }, idx * 150);
    });
  }, [explanation]);

  const getWeightBar = (weight) => {
    const percentage = Math.min(Math.abs(weight) * 100, 100);
    const isPositive = weight >= 0;
    return { percentage, isPositive };
  };

  return (
    <div className="xai-overlay">
      <div className="xai-reveal">
        <button className="xai-close" onClick={onClose}>×</button>

        <div className="xai-header">
          {explanation.correct ? '✅ Got You!' : '❌ I Was Wrong...'}
        </div>

        <div className="xai-message">
          {explanation.message || 'Analyzing the game...'}
        </div>

        {explanation.actual_player && (
          <div className="xai-actual-player">
            <span className="label">You were thinking of:</span>
            <span className="player-name">{explanation.actual_player}</span>
          </div>
        )}

        <div className="xai-reasons">
          <div className="reasons-header">💡 Here's why I thought that:</div>
          
          {displayReasons.length > 0 ? (
            <div className="reasons-list">
              {displayReasons.map((reason, idx) => {
                const { percentage, isPositive } = getWeightBar(reason.weight);
                return (
                  <div key={idx} className="reason-item">
                    <div className="reason-factor">
                      {reason.factor}
                    </div>
                    <div className="reason-weight-container">
                      <div className="reason-weight-bar">
                        <div
                          className={`reason-weight-fill ${isPositive ? 'positive' : 'negative'}`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                      <span className={`reason-weight ${isPositive ? 'positive' : 'negative'}`}>
                        {reason.weight > 0 ? '+' : ''}{reason.weight.toFixed(2)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="reasons-loading">Processing reasons...</div>
          )}
        </div>

        {explanation.learning_message && (
          <div className="xai-learning">
            {explanation.learning_message}
          </div>
        )}

        {explanation.surprise_factor && (
          <div className="xai-surprise">
            🎲 This was a tricky guess! The answer attributes weren't strongly aligned.
          </div>
        )}

        <button className="xai-button" onClick={onClose}>
          Play Again
        </button>
      </div>
    </div>
  );
}
