import { useEffect, useState } from 'react';
import '../styles/AIVisualizationPanel.css';

export default function AIVisualizationPanel({ 
  confidence = 0, 
  topSuspects = [],
  trickDetected = false,
  thinking = false 
}) {
  const [displayConfidence, setDisplayConfidence] = useState(0);

  useEffect(() => {
    // Animate confidence bar
    const timer = setTimeout(() => {
      setDisplayConfidence(Math.min(confidence * 100, 100));
    }, 100);
    return () => clearTimeout(timer);
  }, [confidence]);

  const maskName = (name) => {
    if (!name || name.length < 3) return name;
    return name[0] + '*'.repeat(name.length - 2) + name[name.length - 1];
  };

  return (
    <div className="ai-visualization-panel">
      <div className="ai-header">🤖 AI Thinking</div>

      {/* Confidence Bar */}
      <div className="confidence-section">
        <div className="confidence-label">
          <span>Confidence</span>
          <span className="confidence-value">{Math.round(displayConfidence)}%</span>
        </div>
        <div className="confidence-bar-container">
          <div 
            className={`confidence-bar ${
              trickDetected ? 'trick-detected' : ''
            }`}
            style={{ width: `${displayConfidence}%` }}
          />
        </div>
        {trickDetected && (
          <div className="trick-warning">
            ⚠️ Inconsistency detected! The AI noticed something odd...
          </div>
        )}
      </div>

      {/* Top Suspects */}
      <div className="suspects-section">
        <div className="suspects-label">
          {thinking ? '🔍 Analyzing...' : '🎯 Top Suspects'}
        </div>
        
        <div className="suspects-list">
          {topSuspects.length > 0 ? (
            topSuspects.map((suspect, idx) => (
              <div 
                key={idx} 
                className="suspect-item"
                style={{ animationDelay: `${idx * 0.1}s` }}
              >
                <div className="suspect-rank">#{idx + 1}</div>
                <div className="suspect-name">{maskName(suspect.name)}</div>
                <div className="suspect-probability">
                  {(suspect.probability * 100).toFixed(0)}%
                </div>
              </div>
            ))
          ) : (
            <div className="suspects-empty">
              Gathering information...
            </div>
          )}
        </div>
      </div>

      {/* Thinking Animation */}
      {thinking && (
        <div className="ai-thinking-animation">
          <div className="dot"></div>
          <div className="dot"></div>
          <div className="dot"></div>
        </div>
      )}
    </div>
  );
}
