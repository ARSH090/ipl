import { useEffect, useState } from 'react';
import '../styles/TrickAI.css';

export default function TrickAI({ 
  trickDetected = false,
  inconsistencyScore = 0,
  gameWon = false 
}) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (trickDetected || gameWon) {
      setVisible(true);
    }
  }, [trickDetected, gameWon]);

  const getSuspicionLevel = () => {
    if (inconsistencyScore >= 3) return 'HIGH';
    if (inconsistencyScore >= 2) return 'MEDIUM';
    return 'LOW';
  };

  const getSuspicionColor = () => {
    const level = getSuspicionLevel();
    if (level === 'HIGH') return 'red';
    if (level === 'MEDIUM') return 'yellow';
    return 'green';
  };

  if (!visible) return null;

  return (
    <div className={`trick-ai-badge ${trickDetected ? 'trick-detected' : ''}`}>
      {gameWon && (
        <div className="ai-slayer-badge">
          🏆 AI Slayer
        </div>
      )}
      
      {trickDetected && (
        <div className={`suspicion-badge suspicion-${getSuspicionColor()}`}>
          <span className="suspicion-label">AI Suspicion:</span>
          <span className="suspicion-level">{getSuspicionLevel()}</span>
        </div>
      )}

      {trickDetected && (
        <div className="trick-alert">
          ⚠️ AI noticed inconsistencies in your answers!
        </div>
      )}
    </div>
  );
}
