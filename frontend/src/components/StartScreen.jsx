import React, { useState } from 'react';
import mascotImg from '../assets/mascot_asad.png';

export const StartScreen = ({ onStart, onLeaderboard, loading, recentGames = [] }) => {
  const [name, setName] = useState('');
  const [mode, setMode] = useState('SINGLE');

  const handleStart = (qs) => {
    if (!name.trim()) {
      alert("Please enter your name first!");
      return;
    }
    onStart(name, qs, mode);
  };

  return (
    <div className="start-screen-container">
      {/* Recent Games Box */}
      {recentGames.length > 0 && (
        <div className="recent-games-sidebar">
          <div className="recent-games-box">
            <h3 className="recent-title">Last 10 games</h3>
            <div className="recent-divider"></div>
            <ul className="recent-list">
              {recentGames.map((name, i) => (
                <li key={i} className="recent-item">{name}</li>
              ))}
            </ul>
          </div>
          <button className="leaderboard-sidebar-btn" onClick={onLeaderboard}>
            🏆 Leaderboard
          </button>
        </div>
      )}

      {/* Background decorations */}
      <div className="bg-decorations">
        <div className="diamond d1"></div>
        <div className="diamond d2"></div>
        <div className="diamond d3"></div>
        <div className="diamond d4"></div>
        <div className="diamond d5"></div>
      </div>

      <div className="mascot-section">
        <div className="speech-bubble left-bubble">
          <p>Hello, I am APL-Akinator</p>
        </div>
        
        <img src={mascotImg} alt="Akinator Mascot" className="main-mascot" />

        <div className="speech-bubble right-bubble">
          <p>Think about a real Cricket Player of IPL all time.<br/>I will try to guess who it is</p>
        </div>
      </div>
      
      <div className="logo-container">
        <h1 className="logo-text">Akinator<span className="registered"></span></h1>
      </div>
      
      <div className="start-footer">
        <div className="player-input-section">
           <input 
             type="text" 
             className="name-input" 
             placeholder="ENTER YOUR NAME" 
             value={name}
             onChange={(e) => setName(e.target.value)}
           />
        </div>

        <div className="game-mode-selector">
          <button className={`mode-tab ${mode === 'SINGLE' ? 'active' : ''}`} onClick={() => setMode('SINGLE')}>SINGLE</button>
          <button className={`mode-tab ${mode === 'VS_AI' ? 'active' : ''}`} onClick={() => setMode('VS_AI')}>VS AI</button>
          <button className={`mode-tab ${mode === 'VS_PLAYER' ? 'active' : ''}`} onClick={() => setMode('VS_PLAYER')}>BATTLE</button>
        </div>

        <div className="store-buttons" style={{ flexDirection: 'column', marginTop: '10px', gap: '15px' }}>
           <div className="game-modes" style={{ display: 'flex', gap: '15px', marginBottom: '5px' }}>
             <button className="mode-btn" onClick={() => handleStart(8)} disabled={loading}>8 QUESTIONS</button>
             <button className="mode-btn" onClick={() => handleStart(20)} disabled={loading}>20 QUESTIONS</button>
           </div>
           
           <div className="play-btn-wrapper" style={{ cursor: 'pointer' }} onClick={() => handleStart(8)}>
               <span className="dots">♦ ♦</span>
               <button 
                 className="action-btn play-btn" 
                 disabled={loading}
               >
                 {loading ? 'WAIT...' : 'PLAY'}
               </button>
               <span className="dots">♦ ♦</span>
           </div>
        </div>
      </div>

      <div className="metrics-bottom">
        <p>It is a Cricket Player Guessing Game</p>
        <br />
        <p>Developed by Students of NSU</p>
      </div>
    </div>
  );
};
