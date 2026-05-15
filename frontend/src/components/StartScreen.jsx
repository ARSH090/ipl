import React, { useState } from 'react';
import mascotImg from '../assets/mascot_asad.png';
import LiveLeaderboard from './LiveLeaderboard';

export const StartScreen = ({ onStart, loading }) => {
  const [username, setUsername] = useState('');

  return (
    <div className="start-screen-container">
      {/* Background decorations */}
      <div className="bg-decorations">
        <div className="diamond d1"></div>
        <div className="diamond d2"></div>
        <div className="diamond d3"></div>
        <div className="diamond d4"></div>
        <div className="diamond d5"></div>
        <div className="diamond d6"></div>
        <div className="diamond d7"></div>
        <div className="diamond d8"></div>
      </div>

      <div className="start-main-layout">
        {/* Leaderboard - Now on the left side of mascot */}
        <div className="start-leaderboard-sidebar">
          <LiveLeaderboard />
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
      </div>
      
      <div className="logo-container">
        <h1 className="logo-text">Akinator<span className="registered">®</span></h1>
      </div>
      
      <div className="start-footer">
        <div className="settings-btn">
          <div className="settings-icon">
            <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
              <path d="M19.14,12.94c0.04-0.3,0.06-0.61,0.06-0.94c0-0.32-0.02-0.64-0.06-0.94l2.03-1.58c0.18-0.14,0.23-0.41,0.12-0.61 l-1.92-3.32c-0.12-0.22-0.37-0.29-0.59-0.22l-2.39,0.96c-0.5-0.38-1.03-0.7-1.62-0.94L14.4,2.81c-0.04-0.24-0.24-0.41-0.48-0.41 h-3.84c-0.24,0-0.43,0.17-0.47,0.41L9.25,5.35C8.66,5.59,8.12,5.92,7.63,6.29L5.24,5.33c-0.22-0.08-0.47,0-0.59,0.22L2.73,8.87 C2.62,9.08,2.66,9.34,2.86,9.48l2.03,1.58C4.84,11.36,4.8,11.69,4.8,12s0.02,0.64,0.06,0.94l-2.03,1.58 c-0.18,0.14-0.23,0.41-0.12,0.61l1.92,3.32c0.12,0.22,0.37,0.29,0.59,0.22l2.39-0.96c0.5,0.38,1.03,0.7,1.62,0.94l0.36,2.54 c0.05,0.24,0.24,0.41,0.48,0.41h3.84c0.24,0,0.43-0.17,0.47-0.41l0.36-2.54c0.59-0.24,1.13-0.56,1.62-0.94l2.39,0.96 c0.22,0.08,0.47,0,0.59-0.22l1.92-3.32c0.12-0.22,0.07-0.49-0.12-0.61L19.14,12.94z M12,15.6c-1.98,0-3.6-1.62-3.6-3.6 s1.62-3.6,3.6-3.6s3.6,1.62,3.6,3.6S13.98,15.6,12,15.6z" />
            </svg>
          </div>
          <span className="settings-text">Settings</span>
        </div>
        
        <div className="store-buttons">
           <div className="username-input-wrapper">
             <input
               type="text"
               placeholder="Enter player name..."
               value={username}
               onChange={(e) => setUsername(e.target.value)}
               className="username-input"
               maxLength={20}
             />
           </div>

           <div className="game-modes">
             <button className="mode-btn" onClick={() => onStart(username || 'Anonymous', 'solo', 8)} disabled={loading}>8 Questions</button>
             <button className="mode-btn" onClick={() => onStart(username || 'Anonymous', 'solo', 20)} disabled={loading}>20 Questions</button>
             <button className="mode-btn battle-mode-btn" onClick={() => onStart(username || 'Anonymous', 'battle')} disabled={loading}>Battle Mode</button>
           </div>
        </div>
      </div>

      <div className="metrics-bottom">
        <p>The Ultimate IPL Cricket Player Guessing Game</p>
        <p className="credit">Developed by Students of NSU</p>
      </div>
    </div>
  );
};
