import React from 'react';

export const Leaderboard = ({ data, onHome }) => {
  return (
    <div className="game-screen-container leaderboard-screen">
      <div className="bg-decorations">
        <div className="diamond d1"></div>
        <div className="diamond d2"></div>
        <div className="diamond d3"></div>
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
          </div>
        </div>
      </div>

      <div className="leaderboard-content">
        <h1 className="leaderboard-title">🏆 Global Leaderboard</h1>
        <div className="leaderboard-table-container">
          <table className="leaderboard-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Player</th>
                <th>Score</th>
                <th>Result</th>
              </tr>
            </thead>
            <tbody>
              {data && data.length > 0 ? (
                data.map((entry, index) => (
                  <tr key={entry.id || index} className={index < 3 ? `rank-${index + 1}` : ''}>
                    <td>{index + 1}</td>
                    <td>{entry.player_name || 'Legendary Player'}</td>
                    <td className="score-cell">{entry.score}</td>
                    <td>
                      <span className={`result-tag ${entry.result === 'User Won' ? 'tag-win' : (entry.result === 'PLAYING' ? 'tag-playing' : 'tag-loss')}`}>
                        {entry.result || 'PLAYING'}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="4" className="empty-msg">No scores yet. Be the first!</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <button className="action-btn play-again-btn" onClick={onHome}>
          PLAY AGAIN
        </button>
      </div>
    </div>
  );
};
