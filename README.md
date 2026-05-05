# 🏏 IPL AI Akinator

A real-time, Bayesian-powered Cricket Player guessing game for IPL. Think of any IPL player, and the AI will try to guess who it is through a series of intelligent questions.

## 🚀 Features

- **Bayesian Engine**: Uses probabilistic logic to narrow down candidates with high accuracy.
- **Real-time Scoring**: Live score updates synced with Supabase.
- **Global Leaderboard**: Competitive leaderboard showing top players globally in real-time.
- **XAI (Explainable AI)**: High-fidelity visualizations explaining why the AI made a specific guess.
- **Premium UI**: Modern, glassmorphic design with smooth animations and transitions.
- **Self-Learning**: The AI improves its engine based on user feedback and corrections.

## 🛠️ Tech Stack

- **Frontend**: React (Vite), Anime.js, Supabase Realtime
- **Backend**: FastAPI (Python), Bayesian Probability Engine
- **Database**: Supabase (PostgreSQL + Realtime)

## 🏁 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- Supabase Account

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ARSH090/ipl.git
   cd ipl
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
   Create a `.env` file in the `backend` folder:
   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

3. **Frontend Setup**
   ```bash
   cd ../frontend
   npm install
   ```
   Create a `.env` file in the `frontend` folder:
   ```env
   VITE_SUPABASE_URL=your_supabase_url
   VITE_SUPABASE_ANON_KEY=your_supabase_key
   ```

### Running the App

1. **Start Backend**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. **Start Frontend**
   ```bash
   cd frontend
   npm run dev
   ```

## 📊 Database Setup

Run the SQL provided in `supabase_setup.sql` in your Supabase SQL Editor to initialize the leaderboard table and enable Realtime subscriptions.

## 📜 License

MIT License - Developed by Students of NSU.
