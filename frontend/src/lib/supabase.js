import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL;
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;

let supabaseClient = null;

if (!SUPABASE_URL || !SUPABASE_KEY || SUPABASE_URL.includes('your-project')) {
  console.warn(
    'Missing Supabase credentials. ' +
    'Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in .env. ' +
    'Leaderboard and real-time features will be unavailable.'
  );
} else {
  supabaseClient = createClient(SUPABASE_URL, SUPABASE_KEY);
}

export const supabase = supabaseClient;
