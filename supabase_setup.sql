-- ============================================================
-- IPL AKINATOR SUPABASE SETUP SQL
-- Run these commands in Supabase SQL Editor
-- ============================================================

-- Create players table
CREATE TABLE players (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  team TEXT,
  role TEXT,
  overseas BOOLEAN DEFAULT false,
  captain BOOLEAN DEFAULT false,
  finisher BOOLEAN DEFAULT false,
  opener BOOLEAN DEFAULT false,
  death_bowler BOOLEAN DEFAULT false,
  spinner BOOLEAN DEFAULT false,
  pace_bowler BOOLEAN DEFAULT false,
  left_handed BOOLEAN DEFAULT false,
  wicket_keeper BOOLEAN DEFAULT false,
  csk_player BOOLEAN DEFAULT false,
  mi_player BOOLEAN DEFAULT false,
  rcb_player BOOLEAN DEFAULT false,
  kkr_player BOOLEAN DEFAULT false,
  srh_player BOOLEAN DEFAULT false,
  dc_player BOOLEAN DEFAULT false,
  rr_player BOOLEAN DEFAULT false,
  pbks_player BOOLEAN DEFAULT false,
  gt_player BOOLEAN DEFAULT false,
  lsg_player BOOLEAN DEFAULT false,
  centuries BOOLEAN DEFAULT false,
  world_cup_player BOOLEAN DEFAULT false,
  retired BOOLEAN DEFAULT false,
  under_25 BOOLEAN DEFAULT false,
  over_35 BOOLEAN DEFAULT false,
  high_strike_rate BOOLEAN DEFAULT false,
  economy_under_7 BOOLEAN DEFAULT false,
  batting_avg_over_40 BOOLEAN DEFAULT false,
  wickets_over_100 BOOLEAN DEFAULT false,
  played_before_2015 BOOLEAN DEFAULT false,
  ipl_champion BOOLEAN DEFAULT false,
  orange_cap BOOLEAN DEFAULT false,
  purple_cap BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create game_sessions table
CREATE TABLE game_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id TEXT UNIQUE NOT NULL,
  mode TEXT DEFAULT 'solo',
  room_code TEXT,
  status TEXT DEFAULT 'active',
  questions_asked INTEGER DEFAULT 0,
  candidate_probs JSONB,
  answer_log JSONB DEFAULT '[]',
  final_guess TEXT,
  correct BOOLEAN,
  actual_player TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create leaderboard table
CREATE TABLE leaderboard (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username TEXT UNIQUE NOT NULL,
  avatar_emoji TEXT DEFAULT '🏏',
  total_score INTEGER DEFAULT 0,
  games_played INTEGER DEFAULT 0,
  games_won INTEGER DEFAULT 0,
  ai_guessed INTEGER DEFAULT 0,
  trick_count INTEGER DEFAULT 0,
  badges TEXT[] DEFAULT '{}',
  best_survival INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create battle_rooms table
CREATE TABLE battle_rooms (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  room_code TEXT UNIQUE NOT NULL,
  host_session TEXT,
  guest_session TEXT,
  host_username TEXT,
  guest_username TEXT,
  status TEXT DEFAULT 'waiting',
  current_question TEXT,
  current_attribute TEXT,
  host_answer TEXT,
  guest_answer TEXT,
  question_number INTEGER DEFAULT 0,
  host_score INTEGER DEFAULT 0,
  guest_score INTEGER DEFAULT 0,
  winner TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create ai_learning_log table
CREATE TABLE ai_learning_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id TEXT,
  answer_path JSONB,
  wrong_guess TEXT,
  correct_player TEXT,
  confidence_at_guess FLOAT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Enable Realtime (run these after tables are created)
ALTER TABLE leaderboard REPLICA IDENTITY FULL;
ALTER TABLE battle_rooms REPLICA IDENTITY FULL;

-- ============================================================
-- NEXT STEPS IN SUPABASE DASHBOARD:
-- 1. Go to Database > Replication
-- 2. Enable replication for: leaderboard and battle_rooms
-- 3. Copy SUPABASE_URL and SUPABASE_KEY from Settings > API
-- 4. Add to backend/.env and frontend/.env
-- ============================================================
