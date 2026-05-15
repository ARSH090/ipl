-- ============================================================
-- LEADERBOARD FIXES & REAL-TIME SETUP
-- Run these commands in Supabase SQL Editor
-- ============================================================

-- 1. Ensure RLS is configured for public read access
-- If RLS is enabled, we need a policy. If disabled, it's public.
-- To be safe, we enable RLS and add a SELECT policy for anon.
ALTER TABLE leaderboard ENABLE ROW LEVEL SECURITY;

-- Allow anyone to read the leaderboard
DROP POLICY IF EXISTS "Public Leaderboard Read" ON leaderboard;
CREATE POLICY "Public Leaderboard Read" ON leaderboard
FOR SELECT USING (true);

-- Allow backend/anon to update (usually backend uses service role, 
-- but if using anon key, it needs a policy for UPDATE/INSERT)
DROP POLICY IF EXISTS "Public Leaderboard Update" ON leaderboard;
CREATE POLICY "Public Leaderboard Update" ON leaderboard
FOR ALL USING (true) WITH CHECK (true);

-- 2. Enable Real-time for leaderboard table
-- Ensure REPLICA IDENTITY is set to FULL for detailed updates
ALTER TABLE leaderboard REPLICA IDENTITY FULL;

-- Add leaderboard to the supabase_realtime publication
-- Note: Some Supabase projects already have this publication
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_publication WHERE pubname = 'supabase_realtime'
  ) THEN
    CREATE PUBLICATION supabase_realtime;
  END IF;
  
  -- Add the table to publication (ignore error if already added)
  BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE leaderboard;
  EXCEPTION WHEN others THEN
    RAISE NOTICE 'Table leaderboard already in publication or other error';
  END;
END $$;

-- 3. Verify column types for badges (ensure it is text array)
-- This was already in setup but good to ensure
-- ALTER TABLE leaderboard ALTER COLUMN badges SET DEFAULT '{}';

-- 4. Add index for performance on total_score
CREATE INDEX IF NOT EXISTS idx_leaderboard_score ON leaderboard(total_score DESC);
