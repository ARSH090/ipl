"""
Supabase Client Singleton
Initialize and manage connection to Supabase PostgreSQL database
"""
import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables from the root .env file
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None

if not SUPABASE_URL or not SUPABASE_KEY or "your-project" in SUPABASE_URL:
    print("\n" + "!"*60)
    print("WARNING: Missing or default Supabase credentials.")
    print("Set SUPABASE_URL and SUPABASE_KEY in .env file.")
    print("Leaderboard and Battle Mode will be disabled.")
    print("!"*60 + "\n")
else:
    # Initialize Supabase client
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"ERROR: Failed to initialize Supabase: {e}")

__all__ = ["supabase"]
