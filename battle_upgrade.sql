-- ============================================================
-- UPGRADED BATTLE MODE SCHEMA & SEED DATA
-- ============================================================

-- 1. Create battle_questions table
CREATE TABLE IF NOT EXISTS battle_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question TEXT NOT NULL,
    options JSONB NOT NULL, -- ["Option A", "Option B", "Option C", "Option D"]
    correct_answer TEXT NOT NULL,
    difficulty TEXT DEFAULT 'medium', -- easy, medium, hard, legendary
    category TEXT DEFAULT 'General',
    points INTEGER DEFAULT 100,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Update battle_rooms table for synchronized gameplay
ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS current_round INTEGER DEFAULT 0;
ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS question_ids JSONB DEFAULT '[]';
ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS round_start_at TIMESTAMP;
ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS host_streak INTEGER DEFAULT 0;
ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS guest_streak INTEGER DEFAULT 0;
ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS host_last_answer TEXT;
ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS guest_last_answer TEXT;
ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS host_answer_time FLOAT; -- seconds taken
ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS guest_answer_time FLOAT; -- seconds taken
ALTER TABLE battle_rooms ADD COLUMN IF NOT EXISTS winner_username TEXT;

-- 3. Enable Realtime for battle_questions
ALTER TABLE battle_questions REPLICA IDENTITY FULL;
-- Ensure battle_rooms is already in replication (from previous setup)

-- 4. Seed battle_questions with premium IPL content
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
('Who holds the record for the fastest IPL fifty (13 balls)?', '["Yashasvi Jaiswal", "KL Rahul", "Pat Cummins", "Yusuf Pathan"]', 'Yashasvi Jaiswal', 'medium', 'Records', 150);

-- 5. Add necessary indexes
CREATE INDEX IF NOT EXISTS idx_battle_questions_difficulty ON battle_questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_battle_questions_category ON battle_questions(category);
