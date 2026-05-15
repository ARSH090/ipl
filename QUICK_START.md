# IPL Akinator - Quick Start (5 minutes)

## 1️⃣ Supabase Setup (2 min)

```bash
# Go to supabase.com → Create project → Name: ipl-akinator
# Wait 2-3 minutes...

# Then in SQL Editor: Paste supabase_setup.sql and RUN

# Settings > API: Copy URL and anon key
```

## 2️⃣ Backend Setup (2 min)

```bash
cd backend

# Copy .env
cp .env.template .env

# Edit .env with your Supabase credentials:
# SUPABASE_URL=https://xxxxx.supabase.co
# SUPABASE_KEY=your-key
# GOOGLE_API_KEY=your-existing-key

# Install & run
pip install -r requirements.txt
python seed_players.py
uvicorn main:app --reload
```

**Expected**: Server running on `http://localhost:8000`

## 3️⃣ Frontend Setup (1 min)

```bash
cd frontend

# Copy .env
cp .env.template .env

# Edit .env - same Supabase credentials

# Install & run
npm install
npm run dev
```

**Expected**: App running on `http://localhost:5173`

---

## ✅ Quick Test

1. **Go to** http://localhost:5173
2. **Enter username** (e.g., "TestPlayer")
3. **Click Solo Mode** → Answer questions
4. **See left sidebar**: Leaderboard updating in real-time
5. **See right sidebar**: AI confidence & suspects
6. **On wrong guess**: See XAI explanation modal

✅ **You're done!**

---

## 🎮 Features to Demo

### Solo Mode (3 min)
- Questions → Answer 8 → AI guesses
- **New**: Leaderboard sidebar (real-time)
- **New**: AI visualization panel (confidence %)
- **New**: XAI explanation modal

### Trick Detection (2 min)
- Answer "bowler" → "high strike rate" (contradiction!)
- See "AI Suspicion: HIGH" warning
- Get "Master Manipulator" badge

### Battle Mode (3 min)
- 🌐 Browser 1: Start → Battle Mode → Create Room → Copy code
- 🌐 Browser 2: Start → Battle Mode → Join Room → Paste code
- Answer shared questions
- Winner determined
- Scores updated on leaderboard

### XAI Explanation (2 min)
- Play until AI guesses wrong
- Click "I was thinking of..."
- See modal: "Why I thought that"
- See top 4 factors with weights

---

## 🚨 Troubleshooting

| Problem | Fix |
|---------|-----|
| "No module named supabase" | `pip install -r requirements.txt` |
| "SUPABASE_URL not found" | Check `.env` file exists |
| "Players table is empty" | Run `python seed_players.py` |
| "Cannot connect to localhost:8000" | Ensure backend running with `uvicorn main:app --reload` |
| "WebSocket connection refused" | Ensure backend on port 8000 (check terminal) |

---

## 📁 Key Files

**To Modify:**
- `backend/.env` - Add Supabase credentials
- `frontend/.env` - Add Supabase credentials

**Already Done:**
- ✅ 8 new backend services
- ✅ 5 new frontend components
- ✅ Database schema & tables
- ✅ All API endpoints
- ✅ WebSocket handlers
- ✅ Scoring system
- ✅ Badge system

---

## 🎯 Demo Script (10 minutes)

```
[0:00] "Welcome to IPL Akinator with AI Learning"

[0:30] Solo Mode Demo
- Select "Solo Mode"
- Answer 4 questions quickly
- "Notice the leaderboard on left - updating in real-time!"
- AI guesses you

[3:00] Trick Detection Demo
- "Let me try to trick the AI..."
- Answer contradictory questions
- "See the suspicion level? AI noticed inconsistencies!"
- Explain "Master Manipulator" badge

[5:30] XAI Explanation Demo
- "What if AI gets it wrong?"
- Play until wrong guess
- "Click here to see AI reasoning"
- Show factors & weights
- "AI learns from mistakes!"

[7:30] Battle Mode Demo
- Open 2 browser windows
- Create room in window 1
- Join in window 2
- Answer shared question together
- "Real-time WebSocket sync!"
- Show winner screen

[10:00] Leaderboard & Badges
- Scroll leaderboard
- Show badge system
- "7 different achievements"
- Explain scoring formula
```

---

## 💾 Backups & Rollback

If something breaks:

```bash
# Backend - reset to clean state
rm backend/.env
cp backend/.env.template backend/.env
# Re-edit .env with Supabase details

# Frontend - reset node_modules
rm -rf frontend/node_modules
npm install

# Database - reset all data
# In Supabase SQL Editor: DROP TABLE leaderboard CASCADE;
# Then re-run supabase_setup.sql
```

---

## 📊 What's New (vs Old Version)

| Feature | Before | After |
|---------|--------|-------|
| Sessions | In-memory dict | Supabase DB |
| Leaderboard | None | Real-time top 10 |
| Multiplayer | None | Full battle mode |
| Trick Detection | None | Inconsistency scoring |
| XAI | None | Top 4 factors modal |
| Self-Learning | None | Failed guesses logged |
| Badges | None | 7 achievements |
| Real-time Updates | None | WebSocket sync |

---

## ⏰ Timeline

- **Setup**: 5-10 minutes
- **Testing**: 5-10 minutes
- **Demo Prep**: 5 minutes
- **Live Demo**: 10 minutes
- **Q&A**: 5+ minutes

**Total**: ~40 minutes for full presentation

---

## 🔗 Useful Links

- Supabase: https://supabase.com
- Documentation: `/DEPLOYMENT_GUIDE.md`
- Implementation Details: `/IMPLEMENTATION_SUMMARY.md`
- Database Schema: `/supabase_setup.sql`

---

## ✨ Pro Tips

1. **Faster Setup**: Pre-create Supabase project before demo
2. **Offline Demo**: Export leaderboard data, show screenshots
3. **Impressive**: Show real-time leaderboard update (2 windows)
4. **Engaging**: Let audience answer questions
5. **Interactive**: Have battle mode working in 2 browsers

---

## 🎬 Record This!

Great content for demo video:
- Solo game walkthrough
- Real-time leaderboard sync
- Battle mode action
- Trick detection surprise
- XAI explanation reveal

**Duration**: ~3-5 minutes perfect length

---

**Ready? Let's go! 🚀**

```bash
cd backend && uvicorn main:app --reload &
cd ../frontend && npm run dev
```

Open browser → http://localhost:5173 → **PLAY!**
