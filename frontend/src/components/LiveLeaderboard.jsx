import { useState, useEffect, useCallback, useRef } from 'react';
import { supabase } from '../lib/supabase';
import { getLeaderboardRequest } from '../api/client';
import '../styles/LiveLeaderboard.css';

const badgeEmojis = {
  "AI Slayer": "🏆",
  "Master Manipulator": "🎭",
  "Survivor": "🛡️",
  "Quick Thinker": "⚡",
  "Battle Champion": "👑",
  "IPL Expert": "🧠",
  "Ghost Player": "👻"
};

export default function LiveLeaderboard() {
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const isMounted = useRef(true);

  const fetchLeaderboard = useCallback(async () => {
    try {
      if (supabase) {
        // Direct Supabase query: Order by score DESC, then by updated_at DESC for stability
        const { data, error: sbError } = await supabase
          .from('leaderboard')
          .select('*')
          .order('total_score', { ascending: false })
          .order('updated_at', { ascending: false })
          .limit(10);

        if (sbError) throw sbError;

        if (isMounted.current) {
          const rankedData = (data || []).map((player, idx) => ({
            ...player,
            rank: idx + 1
          }));
          setLeaderboard(rankedData);
          setError(null);
        }
      } else {
        // Fallback to API if Supabase client not available
        const data = await getLeaderboardRequest(10);
        if (isMounted.current) {
          setLeaderboard(data.leaderboard || []);
          setError(null);
        }
      }
    } catch (err) {
      console.error('Leaderboard Fetch Error:', err);
      if (isMounted.current) {
        setError('Failed to sync leaderboard');
      }
    } finally {
      if (isMounted.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    isMounted.current = true;
    fetchLeaderboard();
    
    let channel;
    if (supabase) {
      console.log('Initializing Leaderboard Real-time...');
      channel = supabase
        .channel('leaderboard-global')
        .on(
          'postgres_changes',
          {
            event: '*',
            schema: 'public',
            table: 'leaderboard'
          },
          (payload) => {
            console.log('🔥 Leaderboard Real-time Update:', payload);
            fetchLeaderboard();
          }
        )
        .subscribe((status) => {
          console.log('Leaderboard subscription status:', status);
        });
    }

    return () => {
      isMounted.current = false;
      if (channel) {
        supabase.removeChannel(channel);
      }
    };
  }, [fetchLeaderboard]);

  const renderBadge = (badge) => (
    <span key={badge} title={badge} className="badge">
      {badgeEmojis[badge] || '🎖️'}
    </span>
  );

  if (loading && leaderboard.length === 0) {
    return (
      <div className="leaderboard-container">
        <div className="leaderboard-header">⚡ Live Leaderboard</div>
        <div className="leaderboard-loading">
          <div className="spinner"></div>
          <span>Syncing Scores...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="leaderboard-container">
      <div className="leaderboard-header">
        <span>⚡ Live Leaderboard</span>
        {error && <span className="sync-error" title={error}>⚠️ Sync Error</span>}
      </div>
      
      <div className="leaderboard-list">
        {leaderboard.map((player) => (
          <div key={player.username} className="leaderboard-item">
            <div className="leaderboard-rank">#{player.rank}</div>
            
            <div className="leaderboard-avatar">
              {player.avatar_emoji || '🏏'}
            </div>
            
            <div className="leaderboard-info">
              <div className="leaderboard-username">{player.username}</div>
              <div className="leaderboard-score">{player.total_score.toLocaleString()} pts</div>
              <div className="leaderboard-stats">
                {player.games_won || 0}/{player.games_played || 0} wins
              </div>
            </div>
            
            <div className="leaderboard-badges">
              {Array.isArray(player.badges) && player.badges.slice(0, 2).map(renderBadge)}
              {Array.isArray(player.badges) && player.badges.length > 2 && (
                <span className="badge-more">+{player.badges.length - 2}</span>
              )}
            </div>
          </div>
        ))}

        {!loading && leaderboard.length === 0 && (
          <div className="leaderboard-empty">
            No players found.<br/>Be the first to score!
          </div>
        )}
      </div>
    </div>
  );
}

