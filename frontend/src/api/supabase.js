import { createClient } from '@supabase/supabase-js';

const supabaseUrl = 'https://yikvyjvzbtvtkjsmdlzg.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlpa3Z5anZ6YnR2dGtqc21kbHpnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc5OTQwMjUsImV4cCI6MjA5MzU3MDAyNX0.sAr_0Zoa7opwH48oBcZPRx3xf9n06V-UxnAbNJTH6v8';

export const supabase = createClient(supabaseUrl, supabaseKey);
