-- ============================================================
-- BATTLE MODE V2 - PREMIUM REAL-TIME SCHEMA
-- ============================================================

-- 1. Create battle_questions table
CREATE TABLE IF NOT EXISTS battle_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question TEXT UNIQUE NOT NULL,
    options JSONB NOT NULL, -- ["Option A", "Option B", "Option C", "Option D"]
    correct_answer TEXT NOT NULL,
    difficulty TEXT DEFAULT 'medium', -- easy, medium, hard, legendary
    category TEXT DEFAULT 'General',
    points INTEGER DEFAULT 100,
    explanation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ensure question column is unique for upserts
DO $$ 
BEGIN
    -- Delete duplicates if they exist
    DELETE FROM battle_questions
    WHERE id IN (
        SELECT id
        FROM (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY question ORDER BY id) as row_num
            FROM battle_questions
        ) t
        WHERE t.row_num > 1
    );

    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'battle_questions_question_key') THEN
        ALTER TABLE battle_questions ADD CONSTRAINT battle_questions_question_key UNIQUE (question);
    END IF;
END $$;

-- 2. Create battle_rooms table
-- If it already exists, we upgrade it.
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'battle_rooms') THEN
        CREATE TABLE battle_rooms (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            room_code TEXT UNIQUE NOT NULL,
            host_username TEXT,
            guest_username TEXT,
            status TEXT DEFAULT 'waiting',
            current_round INTEGER DEFAULT 0,
            total_rounds INTEGER DEFAULT 10,
            question_ids JSONB DEFAULT '[]',
            round_start_at TIMESTAMP WITH TIME ZONE,
            host_score INTEGER DEFAULT 0,
            guest_score INTEGER DEFAULT 0,
            host_streak INTEGER DEFAULT 0,
            guest_streak INTEGER DEFAULT 0,
            host_last_points INTEGER DEFAULT 0,
            guest_last_points INTEGER DEFAULT 0,
            host_last_answer TEXT,
            guest_last_answer TEXT,
            host_answer_time FLOAT,
            guest_answer_time FLOAT,
            winner_username TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    ELSE
        -- Upgrade existing table
        ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS current_round INTEGER DEFAULT 0;
        ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS total_rounds INTEGER DEFAULT 10;
        ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS question_ids JSONB DEFAULT '[]';
        ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS round_start_at TIMESTAMP WITH TIME ZONE;
        ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS host_streak INTEGER DEFAULT 0;
        ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS guest_streak INTEGER DEFAULT 0;
        ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS host_last_points INTEGER DEFAULT 0;
        ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS guest_last_points INTEGER DEFAULT 0;
        ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS host_last_answer TEXT;
        ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS guest_last_answer TEXT;
        ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS host_answer_time FLOAT;
        ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS guest_answer_time FLOAT;
        ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS winner_username TEXT;
    END IF;
END $$;

-- 3. Create battle_answers table
CREATE TABLE IF NOT EXISTS battle_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID REFERENCES battle_rooms(id) ON DELETE CASCADE,
    player_username TEXT,
    round_number INTEGER,
    question_id UUID REFERENCES battle_questions(id),
    selected_answer TEXT,
    is_correct BOOLEAN,
    points_earned INTEGER,
    time_taken FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Enable Realtime & Replication
ALTER TABLE battle_rooms REPLICA IDENTITY FULL;
ALTER TABLE battle_questions REPLICA IDENTITY FULL;

-- Ensure supabase_realtime publication exists and tables are added
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_publication WHERE pubname = 'supabase_realtime'
  ) THEN
    CREATE PUBLICATION supabase_realtime;
  END IF;
  
  -- Add battle_rooms to publication
  BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE battle_rooms;
  EXCEPTION WHEN others THEN
    RAISE NOTICE 'Table battle_rooms already in publication or other error';
  END;

  -- Add battle_questions to publication (optional but good practice)
  BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE battle_questions;
  EXCEPTION WHEN others THEN
    RAISE NOTICE 'Table battle_questions already in publication or other error';
  END;
END $$;

-- 5. Row Level Security (RLS) & Policies
-- To ensure frontend clients can read and write rooms without permission issues
ALTER TABLE battle_rooms ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public Battle Rooms Access" ON battle_rooms;
CREATE POLICY "Public Battle Rooms Access" ON battle_rooms
FOR ALL USING (true) WITH CHECK (true);

-- 5. Seed initial premium questions
-- (Will also do this via Python to ensure data integrity)
INSERT INTO battle_questions (question, options, correct_answer, difficulty, category, points) VALUES
('Who won the first ever IPL season in 2008?', '["CSK", "RR", "MI", "DC"]', 'RR', 'easy', 'History', 100),
('Which player holds the record for the highest individual score in IPL history?', '["Chris Gayle", "AB de Villiers", "Virat Kohli", "Brendon McCullum"]', 'Chris Gayle', 'easy', 'Records', 100),
('Who has won the most IPL titles as a captain?', '["MS Dhoni", "Rohit Sharma", "Gautam Gambhir", "Hardik Pandya"]', 'Rohit Sharma', 'easy', 'Captaincy', 100),
('Which team defeated CSK in the 2012 IPL Final?', '["MI", "KKR", "SRH", "RR"]', 'KKR', 'medium', 'History', 150),
('How many runs did Virat Kohli score in his legendary 2016 season?', '["848", "973", "945", "890"]', '973', 'medium', 'Records', 150),
('Who was the first player to reach 5000 runs in IPL?', '["Virat Kohli", "Suresh Raina", "Rohit Sharma", "David Warner"]', 'Suresh Raina', 'medium', 'Records', 150),
('Which bowler has the most hat-tricks in IPL history?', '["Amit Mishra", "Lasith Malinga", "Yuzvendra Chahal", "Rashid Khan"]', 'Amit Mishra', 'hard', 'Records', 200),
('In which year did the IPL move to South Africa due to elections?', '["2009", "2010", "2014", "2012"]', '2009', 'medium', 'History', 150),
('Who was the captain of Deccan Chargers when they won in 2009?', '["Adam Gilchrist", "Kumar Sangakkara", "VVS Laxman", "Rohit Sharma"]', 'Adam Gilchrist', 'medium', 'Captaincy', 150),
('Which player won the Orange Cap in the 2023 season?', '["Shubman Gill", "Faf du Plessis", "Virat Kohli", "Yashasvi Jaiswal"]', 'Shubman Gill', 'easy', 'Records', 100),
('Who hit 5 sixes in the final over against GT to win the match for KKR in 2023?', '["Andre Russell", "Rinku Singh", "Nitish Rana", "Venkatesh Iyer"]', 'Rinku Singh', 'easy', 'Moments', 100),
('Which team has the lowest innings total in IPL history?', '["RCB", "DD", "PWI", "RR"]', 'RCB', 'medium', 'Records', 150),
('Who was the Most Valuable Player (MVP) in IPL 2021?', '["Harshal Patel", "Ruturaj Gaikwad", "Faf du Plessis", "KL Rahul"]', 'Harshal Patel', 'hard', 'Awards', 200),
('Which venue hosted the first ever IPL match?', '["Wankhede Stadium", "M. Chinnaswamy Stadium", "Eden Gardens", "DY Patil Stadium"]', 'M. Chinnaswamy Stadium', 'hard', 'Venues', 200),
('How many teams participated in the 2011 IPL season?', '["8", "10", "9", "12"]', '10', 'hard', 'History', 200),
('Who was the first ever Purple Cap winner in IPL?', '["Sohail Tanvir", "RP Singh", "Pragyan Ojha", "Lasith Malinga"]', 'Sohail Tanvir', 'hard', 'Awards', 200),
('Which player has played the most IPL matches?', '["MS Dhoni", "Dinesh Karthik", "Rohit Sharma", "Virat Kohli"]', 'MS Dhoni', 'easy', 'Records', 100),
('Who was the captain of the Kochi Tuskers Kerala?', '["Mahela Jayawardene", "Sreesanth", "Ravindra Jadeja", "Brendon McCullum"]', 'Mahela Jayawardene', 'legendary', 'History', 300),
('Which player scored the first ever century in IPL history?', '["Brendon McCullum", "Chris Gayle", "Manish Pandey", "Adam Gilchrist"]', 'Brendon McCullum', 'medium', 'History', 150),
('Who holds the record for the fastest IPL fifty (13 balls)?', '["Yashasvi Jaiswal", "KL Rahul", "Pat Cummins", "Yusuf Pathan"]', 'Yashasvi Jaiswal', 'medium', 'Records', 150)
ON CONFLICT DO NOTHING;
