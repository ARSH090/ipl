import { useState, useEffect } from 'react';
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

  // Define fetch logic inside useEffect or wrap in useCallback
  useEffect(() => {
    let isMounted = true;

    async function fetchLeaderboard() {
      try {
        if (supabase) {
          // Direct Supabase query: Ensure correct table query and sorting
          const { data, error } = await supabase
            .from('leaderboard')
            .select('*')
            .order('total_score', { ascending: false })
            .limit(10);

          if (error) throw error;

          if (isMounted) {
            // Assign ranks client-side based on sorted array
            const rankedData = (data || []).map((player, idx) => ({
              ...player,
              rank: idx + 1
            }));
            setLeaderboard(rankedData);
          }
        } else {
          // Fallback if no Supabase credentials
          const data = await getLeaderboardRequest(10);
          if (isMounted) setLeaderboard(data.leaderboard || []);
        }
      } catch (error) {
        console.error('Error fetching leaderboard:', error);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    fetchLeaderboard();
    
    let channel;
    if (supabase) {
      // Subscribe to real-time updates via Supabase
      channel = supabase
        .channel('leaderboard-updates')
        .on(
          'postgres_changes',
          {
            event: '*',
            schema: 'public',
            table: 'leaderboard'
          },
          (payload) => {
            console.log('Leaderboard update:', payload);
            fetchLeaderboard(); // Instantly fetch latest ordered data
          }
        )
        .subscribe();
    }

    return () => {
      isMounted = false;
      if (channel) {
        channel.unsubscribe();
      }
    };
  }, []);

  if (loading) {
    return (
      <div className="leaderboard-container">
        <div className="leaderboard-header">⚡ Live Leaderboard</div>
        <div className="leaderboard-loading">Loading...</div>
      </div>
    );
  }

  return (
    <div className="leaderboard-container">
      <div className="leaderboard-header">⚡ Live Leaderboard</div>
      
      <div className="leaderboard-list">
        {leaderboard.map((player, idx) => (
          <div key={player.username} className="leaderboard-item">
            <div className="leaderboard-rank">#{player.rank}</div>
            
            <div className="leaderboard-avatar">
              {player.avatar_emoji}
            </div>
            
            <div className="leaderboard-info">
              <div className="leaderboard-username">{player.username}</div>
              <div className="leaderboard-score">{player.total_score} pts</div>
              <div className="leaderboard-stats">
                {player.games_won}/{player.games_played} wins
              </div>
            </div>
            
            <div className="leaderboard-badges">
              {player.badges && player.badges.slice(0, 2).map(badge => (
                <span key={badge} title={badge} className="badge">
                  {badgeEmojis[badge] || '🎖️'}
                </span>
              ))}
              {player.badges && player.badges.length > 2 && (
                <span className="badge-more">+{player.badges.length - 2}</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {leaderboard.length === 0 && (
        <div className="leaderboard-empty">
          No players yet. Start a game to appear here!
        </div>
      )}
    </div>
  );
}
